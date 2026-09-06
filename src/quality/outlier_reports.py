import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.analytics.outliers import OutlierSummary, iqr_outlier_summary
from src.utils.lake import latest_parquets_by_leaf
from src.utils.parquet import read_parquet

OUTLIER_COLUMNS = {
    "order_items": ["price", "freight_value"],
    "order_payments": ["payment_value"],
    "orders": [],
    "products": ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"],
    "selic_target": ["value"],
    "usd_brl": ["value"],
    "ibc_br": ["value"],
    "ipca": ["value"],
}


@dataclass(frozen=True)
class DatasetOutlierReport:
    dataset: str
    source_path: str
    summaries: list[OutlierSummary]


@dataclass(frozen=True)
class SilverOutlierReport:
    generated_at: datetime
    datasets: list[DatasetOutlierReport]
    report_path: str


def generate_silver_outlier_report(silver_dir: Path) -> SilverOutlierReport:
    generated_at = datetime.now(UTC)
    datasets: list[DatasetOutlierReport] = []

    for source in ["olist", "bcb", "ibge"]:
        for dataset, path in latest_parquets_by_leaf(silver_dir / source).items():
            columns = OUTLIER_COLUMNS.get(dataset, [])
            if not columns:
                continue
            df = read_parquet(path)
            summaries = [
                iqr_outlier_summary(df[column], column=column)
                for column in columns
                if column in df.columns
            ]
            datasets.append(
                DatasetOutlierReport(
                    dataset=f"{source}.{dataset}",
                    source_path=str(path),
                    summaries=summaries,
                )
            )

    report_path = (
        silver_dir / "_quality_reports" / f"silver_outliers_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    report = SilverOutlierReport(
        generated_at=generated_at,
        datasets=datasets,
        report_path=str(report_path),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**asdict(report), "generated_at": report.generated_at.isoformat()}
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
