import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src.analytics.outliers import zscore_flags
from src.config import Settings, get_settings
from src.transformation.dim_date import build_dim_date
from src.utils.lake import latest_parquets_by_leaf
from src.utils.parquet import write_parquet

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GoldDatasetResult:
    dataset: str
    destination_path: str
    rows: int
    columns: int
    grain: str


@dataclass(frozen=True)
class GoldBuildResult:
    generated_at: datetime
    datasets: list[GoldDatasetResult]
    report_path: str

    @property
    def files_written(self) -> int:
        return len(self.datasets)


def _latest_paths(settings: Settings) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for source in ["olist", "bcb", "ibge"]:
        for dataset, path in latest_parquets_by_leaf(settings.silver_dir / source).items():
            paths[f"{source}_{dataset}"] = path
    return paths


def _register_views(connection: duckdb.DuckDBPyConnection, paths: dict[str, Path]) -> None:
    for view_name, path in paths.items():
        normalized = str(path).replace("\\", "/")
        connection.execute(
            f"create or replace view {view_name} as select * from read_parquet('{normalized}')"
        )


def _query(connection: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return connection.execute(sql).df()


def _economic_indicators(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    bcb = _query(
        connection,
        """
        select
            date_trunc('month', date)::date as reference_month,
            indicator_name,
            avg(value) as value
        from (
            select * from bcb_selic_target
            union all
            select * from bcb_usd_brl
            union all
            select * from bcb_ibc_br
        )
        group by 1, 2
        """,
    )
    ipca = _query(
        connection,
        """
        select
            reference_month::date as reference_month,
            indicator_name,
            avg(value) as value
        from ibge_ipca
        group by 1, 2
        """,
    )
    indicators = pd.concat([bcb, ipca], ignore_index=True)
    return indicators.pivot_table(
        index="reference_month",
        columns="indicator_name",
        values="value",
        aggfunc="mean",
    ).reset_index()


def _customer_rfm(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = _query(
        connection,
        """
        with order_totals as (
            select
                o.customer_id,
                o.order_id,
                cast(o.order_purchase_timestamp as date) as order_date,
                sum(oi.price + oi.freight_value) as order_total
            from olist_orders o
            join olist_order_items oi using (order_id)
            where o.order_purchase_timestamp is not null
            group by 1, 2, 3
        ),
        max_date as (
            select max(order_date) as snapshot_date from order_totals
        )
        select
            customer_id,
            date_diff('day', max(order_date), max(snapshot_date)) as recency_days,
            count(distinct order_id) as frequency,
            sum(order_total) as monetary
        from order_totals
        cross join max_date
        group by customer_id
        """,
    )
    if df.empty:
        return df

    recency_score = pd.qcut(df["recency_days"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop")
    frequency_score = pd.qcut(df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    monetary_score = pd.qcut(df["monetary"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    df["recency_score"] = recency_score.astype("Int64")
    df["frequency_score"] = frequency_score.astype("Int64")
    df["monetary_score"] = monetary_score.astype("Int64")
    df["rfm_score"] = (
        df["recency_score"].astype(str)
        + df["frequency_score"].astype(str)
        + df["monetary_score"].astype(str)
    )
    df["segment"] = np.select(
        [
            (df["recency_score"] >= 4) & (df["frequency_score"] >= 4) & (df["monetary_score"] >= 4),
            (df["recency_score"] <= 2) & (df["frequency_score"] >= 3),
            (df["recency_score"] >= 4) & (df["frequency_score"] <= 2),
        ],
        ["vip", "at_risk", "recent"],
        default="standard",
    )
    return df


def _ml_features(sales_daily: pd.DataFrame) -> pd.DataFrame:
    df = sales_daily.sort_values("date").copy()
    df["sales_lag_1"] = df["gmv"].shift(1)
    df["sales_lag_7"] = df["gmv"].shift(7)
    df["sales_lag_30"] = df["gmv"].shift(30)
    df["rolling_mean_7"] = df["gmv"].rolling(7, min_periods=1).mean()
    df["rolling_mean_30"] = df["gmv"].rolling(30, min_periods=1).mean()
    df["rolling_std_7"] = df["gmv"].rolling(7, min_periods=2).std()
    df["rolling_std_30"] = df["gmv"].rolling(30, min_periods=2).std()
    df["log_gmv"] = np.log1p(df["gmv"])
    return df


def _anomaly_metrics(sales_daily: pd.DataFrame) -> pd.DataFrame:
    df = sales_daily[["date", "gmv", "orders", "average_ticket", "freight_value"]].copy()
    for column in ["gmv", "orders", "average_ticket", "freight_value"]:
        df[f"{column}_zscore_anomaly"] = zscore_flags(df[column], threshold=3.0)
    return df


def _write_gold_dataset(
    df: pd.DataFrame,
    settings: Settings,
    dataset: str,
    grain: str,
) -> GoldDatasetResult:
    destination = settings.gold_dir / dataset / f"{dataset}.parquet"
    write_parquet(df, destination)
    logger.info(
        "gold_dataset_built dataset=%s rows=%s destination=%s",
        dataset,
        len(df),
        destination,
    )
    return GoldDatasetResult(
        dataset=dataset,
        destination_path=str(destination),
        rows=len(df),
        columns=len(df.columns),
        grain=grain,
    )


def build_gold_layer(settings: Settings | None = None) -> GoldBuildResult:
    cfg = settings or get_settings()
    generated_at = datetime.now(UTC)
    paths = _latest_paths(cfg)
    connection = duckdb.connect(database=":memory:")
    _register_views(connection, paths)

    sales_daily = _query(
        connection,
        """
        select
            cast(o.order_purchase_timestamp as date) as date,
            count(distinct o.order_id) as orders,
            count(distinct o.customer_id) as customers,
            count(*) as items_sold,
            sum(oi.price) as revenue,
            sum(oi.freight_value) as freight_value,
            sum(oi.price + oi.freight_value) as gmv,
            avg(oi.price + oi.freight_value) as average_ticket,
            avg(oi.freight_value) as average_freight
        from olist_orders o
        join olist_order_items oi using (order_id)
        where o.order_purchase_timestamp is not null
        group by 1
        order by 1
        """,
    )
    sales_monthly = _query(
        connection,
        """
        select
            date_trunc('month', o.order_purchase_timestamp)::date as month,
            count(distinct o.order_id) as orders,
            count(distinct o.customer_id) as customers,
            count(*) as items_sold,
            sum(oi.price) as revenue,
            sum(oi.freight_value) as freight_value,
            sum(oi.price + oi.freight_value) as gmv,
            avg(oi.price + oi.freight_value) as average_ticket
        from olist_orders o
        join olist_order_items oi using (order_id)
        where o.order_purchase_timestamp is not null
        group by 1
        order by 1
        """,
    )
    sales_monthly["gmv_mom_growth"] = sales_monthly["gmv"].pct_change()
    category_performance = _query(
        connection,
        """
        select
            coalesce(
                t.product_category_name_english,
                p.product_category_name,
                'unknown'
            ) as category,
            count(distinct oi.order_id) as orders,
            count(*) as items_sold,
            sum(oi.price) as revenue,
            sum(oi.freight_value) as freight_value,
            sum(oi.price + oi.freight_value) as gmv,
            avg(oi.price + oi.freight_value) as average_ticket
        from olist_order_items oi
        left join olist_products p using (product_id)
        left join olist_product_category_name_translation t using (product_category_name)
        group by 1
        order by gmv desc
        """,
    )
    customer_metrics = _query(
        connection,
        """
        select
            c.customer_id,
            c.customer_unique_id,
            c.customer_state,
            c.customer_city,
            count(distinct o.order_id) as orders,
            sum(oi.price + oi.freight_value) as gmv,
            avg(oi.price + oi.freight_value) as average_ticket,
            min(o.order_purchase_timestamp)::date as first_order_date,
            max(o.order_purchase_timestamp)::date as last_order_date
        from olist_customers c
        left join olist_orders o using (customer_id)
        left join olist_order_items oi using (order_id)
        group by 1, 2, 3, 4
        """,
    )
    seller_metrics = _query(
        connection,
        """
        select
            s.seller_id,
            s.seller_state,
            s.seller_city,
            count(distinct oi.order_id) as orders,
            count(*) as items_sold,
            sum(oi.price) as revenue,
            sum(oi.freight_value) as freight_value,
            avg(oi.price + oi.freight_value) as average_ticket
        from olist_sellers s
        left join olist_order_items oi using (seller_id)
        group by 1, 2, 3
        """,
    )
    delivery_metrics = _query(
        connection,
        """
        select
            cast(order_purchase_timestamp as date) as date,
            count(*) as orders,
            avg(
                date_diff('day', order_purchase_timestamp, order_delivered_customer_date)
            ) as avg_delivery_days,
            avg(
                date_diff('day', order_purchase_timestamp, order_estimated_delivery_date)
            ) as avg_estimated_days,
            sum(
                case
                    when order_delivered_customer_date > order_estimated_delivery_date then 1
                    else 0
                end
            ) as delayed_orders,
            delayed_orders / nullif(count(*), 0) as delay_rate
        from olist_orders
        where order_purchase_timestamp is not null
        group by 1
        order by 1
        """,
    )
    review_metrics = _query(
        connection,
        """
        select
            cast(review_creation_date as date) as date,
            count(*) as reviews,
            avg(review_score) as average_review_score,
            sum(case when review_score >= 4 then 1 else 0 end) as positive_reviews,
            sum(case when review_score <= 2 then 1 else 0 end) as negative_reviews
        from olist_order_reviews
        where review_creation_date is not null
        group by 1
        order by 1
        """,
    )
    economic_indicators = _economic_indicators(connection)
    sales_economic_features = sales_monthly.merge(
        economic_indicators,
        left_on="month",
        right_on="reference_month",
        how="left",
    )
    for column in ["selic_target", "usd_brl", "ibc_br", "ipca"]:
        if column in sales_economic_features.columns:
            sales_economic_features[f"{column}_change"] = sales_economic_features[column].diff()
    sales_economic_features["sales_growth"] = sales_economic_features["gmv"].pct_change()
    sales_economic_features["ticket_growth"] = sales_economic_features[
        "average_ticket"
    ].pct_change()
    customer_rfm = _customer_rfm(connection)
    ml_features = _ml_features(sales_daily)
    anomaly_metrics = _anomaly_metrics(sales_daily)
    dim_date = build_dim_date(str(sales_daily["date"].min()), str(sales_daily["date"].max()))

    datasets = [
        _write_gold_dataset(sales_daily, cfg, "sales_daily", "one row per purchase date"),
        _write_gold_dataset(sales_monthly, cfg, "sales_monthly", "one row per purchase month"),
        _write_gold_dataset(
            category_performance,
            cfg,
            "category_performance",
            "one row per category",
        ),
        _write_gold_dataset(customer_metrics, cfg, "customer_metrics", "one row per customer_id"),
        _write_gold_dataset(seller_metrics, cfg, "seller_metrics", "one row per seller_id"),
        _write_gold_dataset(delivery_metrics, cfg, "delivery_metrics", "one row per purchase date"),
        _write_gold_dataset(
            review_metrics,
            cfg,
            "review_metrics",
            "one row per review creation date",
        ),
        _write_gold_dataset(economic_indicators, cfg, "economic_indicators", "one row per month"),
        _write_gold_dataset(
            sales_economic_features,
            cfg,
            "sales_economic_features",
            "one row per sales month",
        ),
        _write_gold_dataset(
            customer_rfm,
            cfg,
            "customer_rfm",
            "one row per customer_id with orders",
        ),
        _write_gold_dataset(ml_features, cfg, "ml_features", "one row per purchase date"),
        _write_gold_dataset(anomaly_metrics, cfg, "anomaly_metrics", "one row per purchase date"),
        _write_gold_dataset(dim_date, cfg, "dim_date", "one row per calendar date"),
    ]

    report_path = cfg.gold_dir / "_reports" / f"gold_build_{generated_at:%Y%m%dT%H%M%SZ}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result = GoldBuildResult(
        generated_at=generated_at,
        datasets=datasets,
        report_path=str(report_path),
    )
    payload = {**asdict(result), "generated_at": result.generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    connection.close()
    return result
