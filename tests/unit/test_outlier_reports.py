from pathlib import Path

import pandas as pd

from src.quality.outlier_reports import generate_silver_outlier_report
from src.utils.parquet import write_parquet


def test_generate_silver_outlier_report_writes_json(tmp_path: Path) -> None:
    silver_dir = tmp_path / "silver"
    write_parquet(
        pd.DataFrame(
            {
                "order_id": ["o1", "o2", "o3", "o4", "o5"],
                "order_item_id": [1, 1, 1, 1, 1],
                "price": [10, 11, 12, 13, 500],
                "freight_value": [1, 1, 1, 1, 1],
                "source": ["olist"] * 5,
                "ingestion_timestamp": [pd.Timestamp("2024-01-01")] * 5,
                "batch_id": ["b"] * 5,
            }
        ),
        silver_dir / "olist" / "order_items" / "batch.parquet",
    )

    report = generate_silver_outlier_report(silver_dir)

    assert Path(report.report_path).exists()
    assert report.datasets[0].summaries[0].outlier_count == 1
