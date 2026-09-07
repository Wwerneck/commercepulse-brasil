import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np

from src.config import Settings, get_settings
from src.ml.tracking import log_artifact_if_exists, log_dict_metrics, log_dict_params, mlflow_run
from src.utils.lake import latest_parquet
from src.utils.parquet import read_parquet, write_parquet


@dataclass(frozen=True)
class ReviewIntelligenceReport:
    generated_at: datetime
    rows: int
    text_coverage_ratio: float
    average_review_score: float
    negative_review_ratio: float
    nlp_recommendation: str
    output_path: str
    report_path: str


def build_review_intelligence(settings: Settings | None = None) -> ReviewIntelligenceReport:
    cfg = settings or get_settings()
    reviews_path = latest_parquet(cfg.silver_dir / "olist" / "order_reviews")
    orders_path = latest_parquet(cfg.silver_dir / "olist" / "orders")
    reviews = read_parquet(reviews_path)
    orders = read_parquet(orders_path)[
        ["order_id", "order_delivered_customer_date", "order_estimated_delivery_date"]
    ]
    df = reviews.merge(orders, on="order_id", how="left")
    df["has_review_text"] = df["review_comment_message"].fillna("").astype(str).str.strip() != ""
    df["is_negative_review"] = df["review_score"] <= 2
    df["was_delayed"] = df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    summary = (
        df.groupby(["review_score", "was_delayed"], dropna=False)
        .agg(reviews=("review_id", "count"), text_reviews=("has_review_text", "sum"))
        .reset_index()
    )
    generated_at = datetime.now(UTC)
    output_path = cfg.models_dir / "outputs" / "review_intelligence_summary.parquet"
    report_path = (
        cfg.models_dir / "reports" / f"review_intelligence_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    write_parquet(summary, output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    text_coverage = float(np.mean(df["has_review_text"]))
    recommendation = (
        "text_quality_sufficient_for_future_nlp"
        if text_coverage >= 0.2
        else "prioritize_score_delivery_analysis_before_nlp"
    )
    report = ReviewIntelligenceReport(
        generated_at=generated_at,
        rows=len(df),
        text_coverage_ratio=text_coverage,
        average_review_score=float(np.mean(df["review_score"])),
        negative_review_ratio=float(np.mean(df["is_negative_review"])),
        nlp_recommendation=recommendation,
        output_path=str(output_path),
        report_path=str(report_path),
    )
    payload: dict[str, Any] = {**asdict(report), "generated_at": generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with mlflow_run("review_intelligence", settings=cfg) as (mlflow, _run):
        log_dict_params(
            mlflow,
            {
                "method": "score_delivery_text_coverage",
                "rows": len(df),
                "recommendation": recommendation,
            },
        )
        log_dict_metrics(
            mlflow,
            {
                "text_coverage_ratio": report.text_coverage_ratio,
                "average_review_score": report.average_review_score,
                "negative_review_ratio": report.negative_review_ratio,
            },
        )
        log_artifact_if_exists(mlflow, output_path)
        log_artifact_if_exists(mlflow, report_path)
    return report
