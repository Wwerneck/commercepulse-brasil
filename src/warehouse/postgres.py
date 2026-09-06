from collections.abc import Iterable
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src.config import Settings, get_settings
from src.utils.parquet import read_parquet
from src.warehouse.ddl import TRUNCATE_ANALYTICS_SQL, WAREHOUSE_DDL


class WarehouseConnectionError(RuntimeError):
    """Raised when PostgreSQL is unavailable or unreachable."""


def connect(settings: Settings | None = None):
    cfg = settings or get_settings()
    try:
        return psycopg2.connect(
            host=cfg.postgres_host,
            port=cfg.postgres_port,
            dbname=cfg.postgres_db,
            user=cfg.postgres_user,
            password=cfg.postgres_password,
        )
    except Exception as exc:
        raise WarehouseConnectionError(
            "Could not connect to PostgreSQL. Start the postgres service with Docker "
            "Compose or provide POSTGRES_* variables pointing to an available server."
        ) from exc


def initialize_warehouse(settings: Settings | None = None) -> None:
    with connect(settings) as connection:
        with connection.cursor() as cursor:
            cursor.execute(WAREHOUSE_DDL)


def _records(df: pd.DataFrame, columns: list[str]) -> Iterable[tuple]:
    normalized = df[columns].where(pd.notna(df[columns]), None)
    return (tuple(row) for row in normalized.itertuples(index=False, name=None))


def _insert_dataframe(cursor, table: str, df: pd.DataFrame, columns: list[str]) -> int:
    if df.empty:
        return 0
    column_sql = ", ".join(columns)
    sql = f"insert into {table} ({column_sql}) values %s"
    execute_values(cursor, sql, list(_records(df, columns)))
    return len(df)


def load_gold_to_postgres(settings: Settings | None = None) -> dict[str, int]:
    cfg = settings or get_settings()
    gold = cfg.gold_dir
    datasets = {
        "dim_date": read_parquet(gold / "dim_date" / "dim_date.parquet"),
        "customer_metrics": read_parquet(gold / "customer_metrics" / "customer_metrics.parquet"),
        "seller_metrics": read_parquet(gold / "seller_metrics" / "seller_metrics.parquet"),
        "category_performance": read_parquet(
            gold / "category_performance" / "category_performance.parquet"
        ),
        "economic_indicators": read_parquet(
            gold / "economic_indicators" / "economic_indicators.parquet"
        ),
        "sales_daily": read_parquet(gold / "sales_daily" / "sales_daily.parquet"),
        "sales_monthly": read_parquet(gold / "sales_monthly" / "sales_monthly.parquet"),
    }
    datasets["sales_daily"]["date_key"] = (
        pd.to_datetime(datasets["sales_daily"]["date"]).dt.strftime("%Y%m%d").astype(int)
    )

    counts: dict[str, int] = {}
    with connect(cfg) as connection:
        with connection.cursor() as cursor:
            cursor.execute(WAREHOUSE_DDL)
            cursor.execute(TRUNCATE_ANALYTICS_SQL)

            counts["analytics.dim_date"] = _insert_dataframe(
                cursor,
                "analytics.dim_date",
                datasets["dim_date"],
                [
                    "date_key",
                    "date",
                    "day",
                    "day_of_week",
                    "day_name",
                    "week",
                    "month",
                    "month_name",
                    "quarter",
                    "year",
                    "is_weekend",
                ],
            )
            counts["analytics.dim_customer"] = _insert_dataframe(
                cursor,
                "analytics.dim_customer",
                datasets["customer_metrics"],
                ["customer_id", "customer_unique_id", "customer_state", "customer_city"],
            )
            counts["analytics.dim_seller"] = _insert_dataframe(
                cursor,
                "analytics.dim_seller",
                datasets["seller_metrics"],
                ["seller_id", "seller_state", "seller_city"],
            )
            category_df = datasets["category_performance"][["category"]].drop_duplicates()
            counts["analytics.dim_category"] = _insert_dataframe(
                cursor,
                "analytics.dim_category",
                category_df,
                ["category"],
            )
            indicator_df = pd.DataFrame(
                {
                    "indicator_name": ["selic_target", "usd_brl", "ibc_br", "ipca"],
                    "source": ["bcb_sgs", "bcb_sgs", "bcb_sgs", "ibge_sidra"],
                }
            )
            counts["analytics.dim_economic_indicator"] = _insert_dataframe(
                cursor,
                "analytics.dim_economic_indicator",
                indicator_df,
                ["indicator_name", "source"],
            )
            counts["analytics.fact_sales_daily"] = _insert_dataframe(
                cursor,
                "analytics.fact_sales_daily",
                datasets["sales_daily"],
                [
                    "date_key",
                    "orders",
                    "customers",
                    "items_sold",
                    "revenue",
                    "freight_value",
                    "gmv",
                    "average_ticket",
                    "average_freight",
                ],
            )
            counts["analytics.fact_sales_monthly"] = _insert_dataframe(
                cursor,
                "analytics.fact_sales_monthly",
                datasets["sales_monthly"],
                [
                    "month",
                    "orders",
                    "customers",
                    "items_sold",
                    "revenue",
                    "freight_value",
                    "gmv",
                    "average_ticket",
                    "gmv_mom_growth",
                ],
            )
            counts["analytics.fact_category_performance"] = _insert_dataframe(
                cursor,
                "analytics.fact_category_performance",
                datasets["category_performance"],
                [
                    "category",
                    "orders",
                    "items_sold",
                    "revenue",
                    "freight_value",
                    "gmv",
                    "average_ticket",
                ],
            )
            counts["analytics.fact_economic_indicators"] = _insert_dataframe(
                cursor,
                "analytics.fact_economic_indicators",
                datasets["economic_indicators"],
                ["reference_month", "selic_target", "usd_brl", "ibc_br", "ipca"],
            )
    return counts


def expected_gold_paths(settings: Settings | None = None) -> list[Path]:
    cfg = settings or get_settings()
    return [
        cfg.gold_dir / "dim_date" / "dim_date.parquet",
        cfg.gold_dir / "customer_metrics" / "customer_metrics.parquet",
        cfg.gold_dir / "seller_metrics" / "seller_metrics.parquet",
        cfg.gold_dir / "category_performance" / "category_performance.parquet",
        cfg.gold_dir / "economic_indicators" / "economic_indicators.parquet",
        cfg.gold_dir / "sales_daily" / "sales_daily.parquet",
        cfg.gold_dir / "sales_monthly" / "sales_monthly.parquet",
    ]


def check_warehouse_inputs(settings: Settings | None = None) -> dict[str, bool]:
    return {str(path): path.exists() for path in expected_gold_paths(settings)}
