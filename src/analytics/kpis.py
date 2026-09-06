import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np

from src.config import Settings, get_settings
from src.utils.parquet import read_parquet


@dataclass(frozen=True)
class AnalyticsReport:
    generated_at: datetime
    metrics: dict[str, Any]
    report_path: str


def build_analytics_report(settings: Settings | None = None) -> AnalyticsReport:
    cfg = settings or get_settings()
    sales_daily = read_parquet(cfg.gold_dir / "sales_daily" / "sales_daily.parquet")
    sales_monthly = read_parquet(cfg.gold_dir / "sales_monthly" / "sales_monthly.parquet")
    categories = read_parquet(
        cfg.gold_dir / "category_performance" / "category_performance.parquet"
    )
    delivery = read_parquet(cfg.gold_dir / "delivery_metrics" / "delivery_metrics.parquet")
    reviews = read_parquet(cfg.gold_dir / "review_metrics" / "review_metrics.parquet")
    sellers = read_parquet(cfg.gold_dir / "seller_metrics" / "seller_metrics.parquet")

    top_categories = categories.head(10)[["category", "gmv", "orders"]].to_dict(orient="records")
    generated_at = datetime.now(UTC)
    metrics: dict[str, Any] = {
        "period_start": str(sales_daily["date"].min().date()),
        "period_end": str(sales_daily["date"].max().date()),
        "sales_daily_rows": int(len(sales_daily)),
        "sales_monthly_rows": int(len(sales_monthly)),
        "gmv_total": round(float(np.sum(sales_daily["gmv"])), 2),
        "revenue_total": round(float(np.sum(sales_daily["revenue"])), 2),
        "orders_total": int(np.sum(sales_daily["orders"])),
        "customers_total": int(np.sum(sales_daily["customers"])),
        "items_sold_total": int(np.sum(sales_daily["items_sold"])),
        "average_ticket_per_item": round(
            float(np.sum(sales_daily["gmv"]) / np.sum(sales_daily["items_sold"])),
            2,
        ),
        "average_freight": round(float(np.mean(sales_daily["average_freight"])), 2),
        "active_sellers": int((sellers["orders"] > 0).sum()),
        "average_delivery_days": round(float(np.nanmean(delivery["avg_delivery_days"])), 2),
        "average_delay_rate": round(float(np.nanmean(delivery["delay_rate"])), 4),
        "average_review_score": round(float(np.nanmean(reviews["average_review_score"])), 2),
        "best_month_by_gmv": str(
            sales_monthly.sort_values("gmv", ascending=False).iloc[0]["month"]
        ),
        "top_categories": top_categories,
    }
    report_path = cfg.gold_dir / "_analytics_reports" / f"kpis_{generated_at:%Y%m%dT%H%M%SZ}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = AnalyticsReport(
        generated_at=generated_at,
        metrics=metrics,
        report_path=str(report_path),
    )
    payload = {**asdict(report), "generated_at": generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
