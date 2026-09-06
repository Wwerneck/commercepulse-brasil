from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import Settings, get_settings
from src.utils.parquet import read_parquet


@dataclass(frozen=True)
class ObservabilityCheck:
    name: str
    status: str
    severity: str
    message: str
    details: dict[str, Any]


@dataclass(frozen=True)
class ObservabilityReport:
    generated_at: datetime
    status: str
    checks_total: int
    checks_failed: int
    checks_warned: int
    checks: list[ObservabilityCheck]
    report_path: str


REQUIRED_GOLD_DATASETS = [
    "sales_daily",
    "sales_monthly",
    "category_performance",
    "customer_metrics",
    "seller_metrics",
    "delivery_metrics",
    "review_metrics",
    "economic_indicators",
    "sales_economic_features",
    "customer_rfm",
    "ml_features",
    "anomaly_metrics",
    "dim_date",
]

REQUIRED_MODEL_OUTPUTS = [
    Path("models/outputs/customer_segments.parquet"),
    Path("models/outputs/anomaly_method_comparison.parquet"),
    Path("models/outputs/review_intelligence_summary.parquet"),
]

REQUIRED_REPORT_GLOBS = {
    "bronze_quality": Path("data/bronze/_quality_reports/bronze_validation_*.json"),
    "silver_quality": Path("data/silver/_quality_reports/silver_quality_*.json"),
    "gold_quality": Path("data/gold/_quality_reports/gold_quality_*.json"),
    "kpis": Path("data/gold/_analytics_reports/kpis_*.json"),
    "economic": Path("data/gold/_analytics_reports/economic_*.json"),
    "forecast": Path("models/reports/sales_forecast_*.json"),
    "segmentation": Path("models/reports/customer_segmentation_*.json"),
    "anomaly": Path("models/reports/anomaly_detection_*.json"),
    "reviews": Path("models/reports/review_intelligence_*.json"),
}


def _check(
    status: str,
    severity: str,
    name: str,
    message: str,
    **details: Any,
) -> ObservabilityCheck:
    return ObservabilityCheck(
        name=name,
        status=status,
        severity=severity,
        message=message,
        details=details,
    )


def _file_age_hours(path: Path, generated_at: datetime) -> float:
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return (generated_at - modified_at).total_seconds() / 3600


def _latest_match(pattern: Path) -> Path | None:
    matches = sorted(pattern.parent.glob(pattern.name))
    return matches[-1] if matches else None


def _dataset_check(path: Path, name: str, generated_at: datetime) -> ObservabilityCheck:
    if not path.exists():
        return _check("failed", "critical", name, "Required dataset is missing.", path=str(path))
    try:
        df = read_parquet(path)
    except Exception as exc:
        return _check(
            "failed",
            "critical",
            name,
            "Required dataset could not be read.",
            path=str(path),
            error=str(exc),
        )
    if df.empty:
        return _check("failed", "critical", name, "Required dataset is empty.", path=str(path))
    return _check(
        "passed",
        "info",
        name,
        "Dataset is readable and non-empty.",
        path=str(path),
        rows=len(df),
        columns=list(df.columns),
        age_hours=round(_file_age_hours(path, generated_at), 2),
    )


def _report_check(pattern: Path, name: str, generated_at: datetime) -> ObservabilityCheck:
    latest = _latest_match(pattern)
    if latest is None:
        return _check(
            "failed",
            "warning",
            name,
            "Expected report was not found.",
            pattern=str(pattern),
        )
    try:
        payload = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as exc:
        return _check(
            "failed",
            "warning",
            name,
            "Expected report could not be parsed.",
            path=str(latest),
            error=str(exc),
        )
    return _check(
        "passed",
        "info",
        name,
        "Latest report is available and parseable.",
        path=str(latest),
        age_hours=round(_file_age_hours(latest, generated_at), 2),
        keys=sorted(payload.keys()),
    )


def build_observability_report(settings: Settings | None = None) -> ObservabilityReport:
    cfg = settings or get_settings()
    generated_at = datetime.now(UTC)
    checks: list[ObservabilityCheck] = []

    for dataset in REQUIRED_GOLD_DATASETS:
        path = cfg.gold_dir / dataset / f"{dataset}.parquet"
        checks.append(_dataset_check(path, f"gold_{dataset}", generated_at))

    for output_path in REQUIRED_MODEL_OUTPUTS:
        checks.append(_dataset_check(output_path, f"model_output_{output_path.stem}", generated_at))

    for report_name, pattern in REQUIRED_REPORT_GLOBS.items():
        checks.append(_report_check(pattern, f"report_{report_name}", generated_at))

    checks_failed = sum(
        check.status == "failed" and check.severity == "critical" for check in checks
    )
    checks_warned = sum(
        check.status == "failed" and check.severity == "warning" for check in checks
    )
    status = "failed" if checks_failed else "warning" if checks_warned else "passed"

    report_path = (
        cfg.gold_dir
        / "_monitoring_reports"
        / f"observability_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    report = ObservabilityReport(
        generated_at=generated_at,
        status=status,
        checks_total=len(checks),
        checks_failed=checks_failed,
        checks_warned=checks_warned,
        checks=checks,
        report_path=str(report_path),
    )
    payload = asdict(report)
    payload["generated_at"] = generated_at.isoformat()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
