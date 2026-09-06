from pathlib import Path

import pandas as pd

from src.quality.bronze_checks import validate_bronze_file, validate_bronze_layer
from src.utils.parquet import write_parquet


def test_validate_bronze_file_requires_metadata_columns(tmp_path: Path) -> None:
    path = tmp_path / "data" / "bronze" / "sample.parquet"
    write_parquet(pd.DataFrame({"source": ["x"], "batch_id": ["b"]}), path)

    result = validate_bronze_file(path)

    assert not result.passed
    assert result.missing_columns == ["ingestion_timestamp"]


def test_validate_bronze_layer_writes_report(tmp_path: Path) -> None:
    bronze_dir = tmp_path / "data" / "bronze"
    path = bronze_dir / "source" / "table" / "batch.parquet"
    write_parquet(
        pd.DataFrame(
            {
                "source": ["olist"],
                "ingestion_timestamp": pd.Timestamp("2024-01-01"),
                "batch_id": ["batch"],
            }
        ),
        path,
    )

    report = validate_bronze_layer(bronze_dir)

    assert report.passed
    assert report.files_checked == 1
    assert Path(report.report_path).exists()
