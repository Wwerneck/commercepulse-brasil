import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.quality.rules import QualityResult, non_negative, not_null, unique_key
from src.utils.parquet import read_parquet

EXPECTED_GOLD_DATASETS = {
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
}


@dataclass(frozen=True)
class GoldQualityReport:
    generated_at: datetime
    datasets_checked: int
    missing_datasets: list[str]
    critical_failures: int
    warning_failures: int
    results: list[QualityResult]
    report_path: str

    @property
    def passed(self) -> bool:
        return not self.missing_datasets and self.critical_failures == 0


def _dataset_path(gold_dir: Path, dataset: str) -> Path:
    return gold_dir / dataset / f"{dataset}.parquet"


def _basic_dataset_result(dataset: str, df: pd.DataFrame) -> QualityResult:
    return QualityResult(
        rule_name=f"{dataset}_not_empty",
        severity="critical",
        passed=len(df) > 0,
        failed_count=0 if len(df) > 0 else 1,
        total_count=len(df),
        message=f"{dataset} has {len(df)} rows",
    )


def _validate_dataset(dataset: str, df: pd.DataFrame) -> list[QualityResult]:
    results = [_basic_dataset_result(dataset, df)]
    if dataset == "sales_daily":
        results.extend(
            [
                not_null(df, "date"),
                unique_key(df, ["date"]),
                non_negative(df, "gmv"),
                non_negative(df, "orders"),
                non_negative(df, "average_ticket"),
            ]
        )
    elif dataset == "sales_monthly":
        results.extend([not_null(df, "month"), unique_key(df, ["month"]), non_negative(df, "gmv")])
    elif dataset == "category_performance":
        results.extend(
            [not_null(df, "category"), unique_key(df, ["category"]), non_negative(df, "gmv")]
        )
    elif dataset == "customer_metrics":
        results.extend([not_null(df, "customer_id"), unique_key(df, ["customer_id"])])
    elif dataset == "seller_metrics":
        results.extend([not_null(df, "seller_id"), unique_key(df, ["seller_id"])])
    elif dataset == "economic_indicators":
        results.extend([not_null(df, "reference_month"), unique_key(df, ["reference_month"])])
    elif dataset == "customer_rfm":
        results.extend([not_null(df, "customer_id"), unique_key(df, ["customer_id"])])
    elif dataset == "dim_date":
        results.extend([not_null(df, "date_key"), unique_key(df, ["date_key"])])
    return results


def validate_gold_layer(gold_dir: Path) -> GoldQualityReport:
    generated_at = datetime.now(UTC)
    missing = sorted(
        dataset
        for dataset in EXPECTED_GOLD_DATASETS
        if not _dataset_path(gold_dir, dataset).exists()
    )
    all_results: list[QualityResult] = []
    checked = 0
    for dataset in sorted(EXPECTED_GOLD_DATASETS.difference(missing)):
        df = read_parquet(_dataset_path(gold_dir, dataset))
        checked += 1
        all_results.extend(_validate_dataset(dataset, df))

    critical_failures = sum(
        not result.passed and result.severity == "critical" for result in all_results
    )
    warning_failures = sum(
        not result.passed and result.severity == "warning" for result in all_results
    )
    report_path = gold_dir / "_quality_reports" / f"gold_quality_{generated_at:%Y%m%dT%H%M%SZ}.json"
    report = GoldQualityReport(
        generated_at=generated_at,
        datasets_checked=checked,
        missing_datasets=missing,
        critical_failures=critical_failures,
        warning_failures=warning_failures,
        results=all_results,
        report_path=str(report_path),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **asdict(report),
        "generated_at": report.generated_at.isoformat(),
        "passed": report.passed,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
