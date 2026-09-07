from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException

from api.schemas import (
    AnomalyDay,
    CategoryPerformance,
    CustomerSegmentSummary,
    DatasetInfo,
    KpiResponse,
    ObservabilityResponse,
    SalesPoint,
)
from src.config import Settings, get_settings
from src.monitoring.observability import build_observability_report
from src.utils.parquet import read_parquet

REPORT_PATTERNS = {
    "kpis": ("gold", Path("_analytics_reports/kpis_*.json")),
    "economic": ("gold", Path("_analytics_reports/economic_*.json")),
    "forecast": ("models", Path("reports/sales_forecast_*.json")),
    "segmentation": ("models", Path("reports/customer_segmentation_*.json")),
    "anomaly": ("models", Path("reports/anomaly_detection_*.json")),
    "reviews": ("models", Path("reports/review_intelligence_*.json")),
}


def _settings(settings: Settings | None = None) -> Settings:
    return settings or get_settings()


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    clean = df.replace({pd.NA: None})
    clean = clean.where(pd.notna(clean), None)
    records = clean.to_dict(orient="records")
    return [_json_safe(record) for record in records]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, str):
        return normalize_path(value)
    return value


def normalize_path(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def _read_gold(dataset: str, settings: Settings | None = None) -> pd.DataFrame:
    cfg = _settings(settings)
    path = cfg.gold_dir / dataset / f"{dataset}.parquet"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Gold dataset not found: {dataset}")
    return read_parquet(path)


def _report_pattern(report_type: str, settings: Settings | None = None) -> Path:
    cfg = _settings(settings)
    pattern_config = REPORT_PATTERNS.get(report_type)
    if pattern_config is None:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")
    base_name, relative_pattern = pattern_config
    base_dir = cfg.gold_dir if base_name == "gold" else cfg.models_dir
    return base_dir / relative_pattern


def _read_model_output(filename: str, settings: Settings | None = None) -> pd.DataFrame:
    path = _settings(settings).models_dir / "outputs" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Model output not found: {filename}")
    return read_parquet(path)


def latest_report_path(report_type: str, settings: Settings | None = None) -> Path:
    pattern = _report_pattern(report_type, settings)
    matches = sorted(pattern.parent.glob(pattern.name))
    if not matches:
        raise HTTPException(status_code=404, detail=f"No reports found for type: {report_type}")
    return matches[-1]


def latest_report(report_type: str, settings: Settings | None = None) -> dict[str, Any]:
    path = latest_report_path(report_type, settings)
    return _json_safe(json.loads(path.read_text(encoding="utf-8")))


def dataset_info(path: Path, name: str) -> DatasetInfo:
    df = read_parquet(path)
    return DatasetInfo(
        name=name,
        path=normalize_path(path),
        rows=len(df),
        columns=list(df.columns),
    )


def catalog(settings: Settings | None = None) -> dict[str, Any]:
    cfg = _settings(settings)
    gold_infos = [
        dataset_info(path, path.parent.name)
        for path in sorted(cfg.gold_dir.glob("*/*.parquet"))
    ]
    model_infos = [
        dataset_info(path, path.stem)
        for path in sorted((cfg.models_dir / "outputs").glob("*.parquet"))
    ]
    reports = {}
    for report_type in REPORT_PATTERNS:
        try:
            reports[report_type] = normalize_path(latest_report_path(report_type, cfg))
        except HTTPException:
            continue
    return {"gold": gold_infos, "model_outputs": model_infos, "latest_reports": reports}


def kpis(settings: Settings | None = None) -> KpiResponse:
    payload = latest_report("kpis", settings)
    metrics = payload["metrics"]
    top_categories_payload = metrics.get("top_categories") or []
    top_category = top_categories_payload[0]["category"] if top_categories_payload else None
    return KpiResponse(
        period_start=metrics["period_start"],
        period_end=metrics["period_end"],
        gmv_total=metrics["gmv_total"],
        revenue_total=metrics["revenue_total"],
        orders_total=metrics["orders_total"],
        customers_total=metrics["customers_total"],
        items_sold_total=metrics["items_sold_total"],
        average_ticket=metrics["average_ticket_per_item"],
        average_freight=metrics["average_freight"],
        active_sellers=metrics.get("active_sellers"),
        average_delivery_days=metrics.get("average_delivery_days"),
        average_delay_rate=metrics.get("average_delay_rate"),
        average_review_score=metrics.get("average_review_score"),
        best_month_by_gmv=metrics.get("best_month_by_gmv"),
        top_category_by_gmv=top_category,
        report_path=payload["report_path"],
    )


def sales_daily(limit: int, settings: Settings | None = None) -> list[SalesPoint]:
    df = _read_gold("sales_daily", settings).sort_values("date", ascending=False).head(limit)
    return [
        SalesPoint(
            period=record["date"],
            orders=record["orders"],
            customers=record["customers"],
            items_sold=record["items_sold"],
            revenue=record["revenue"],
            freight_value=record["freight_value"],
            gmv=record["gmv"],
            average_ticket=record["average_ticket"],
        )
        for record in _records(df)
    ]


def sales_monthly(limit: int, settings: Settings | None = None) -> list[SalesPoint]:
    df = _read_gold("sales_monthly", settings).sort_values("month", ascending=False).head(limit)
    return [
        SalesPoint(
            period=record["month"],
            orders=record["orders"],
            customers=record["customers"],
            items_sold=record["items_sold"],
            revenue=record["revenue"],
            freight_value=record["freight_value"],
            gmv=record["gmv"],
            average_ticket=record["average_ticket"],
        )
        for record in _records(df)
    ]


def top_categories(limit: int, settings: Settings | None = None) -> list[CategoryPerformance]:
    df = (
        _read_gold("category_performance", settings)
        .sort_values("gmv", ascending=False)
        .head(limit)
    )
    return [CategoryPerformance(**record) for record in _records(df)]


def customer_segments(settings: Settings | None = None) -> list[CustomerSegmentSummary]:
    df = _read_model_output("customer_segments.parquet", settings)
    summary = (
        df.groupby("ml_segment", dropna=False)
        .agg(
            customers=("customer_id", "count"),
            average_recency_days=("recency_days", "mean"),
            average_frequency=("frequency", "mean"),
            average_monetary=("monetary", "mean"),
        )
        .reset_index()
        .sort_values("customers", ascending=False)
    )
    return [CustomerSegmentSummary(**record) for record in _records(summary)]


def anomalies(
    limit: int,
    only_overlap: bool = False,
    settings: Settings | None = None,
) -> list[AnomalyDay]:
    df = _read_model_output("anomaly_method_comparison.parquet", settings)
    if only_overlap:
        df = df[df["anomaly_method_overlap"]]
    else:
        df = df[df["any_zscore_anomaly"] | df["isolation_forest_anomaly"]]
    df = df.sort_values("date", ascending=False).head(limit)
    return [AnomalyDay(**record) for record in _records(df)]


def observability(settings: Settings | None = None) -> ObservabilityResponse:
    report = build_observability_report(_settings(settings))
    return ObservabilityResponse(**_json_safe(asdict(report)))
