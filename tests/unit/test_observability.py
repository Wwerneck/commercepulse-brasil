from pathlib import Path

import pandas as pd

from src.config import Settings
from src.monitoring.observability import REQUIRED_GOLD_DATASETS, build_observability_report
from src.utils.parquet import write_parquet


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        log_level="INFO",
        data_dir=tmp_path / "data",
        models_dir=tmp_path / "models",
        bcb_base_url="https://example.com/bcb",
        ibge_sidra_base_url="https://example.com/ibge",
        request_timeout_seconds=30,
        request_retries=3,
        postgres_host="localhost",
        postgres_port=55432,
        postgres_db="commercepulse",
        postgres_user="commercepulse",
        postgres_password="commercepulse",
        mlflow_tracking_uri=f"sqlite:///{tmp_path / 'mlflow.db'}",
    )


def test_observability_report_fails_when_required_gold_dataset_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("src.monitoring.observability.REQUIRED_MODEL_OUTPUTS", [])
    monkeypatch.setattr("src.monitoring.observability.REQUIRED_REPORT_GLOBS", {})

    report = build_observability_report(_settings(tmp_path))

    assert report.status == "failed"
    assert report.checks_failed == len(REQUIRED_GOLD_DATASETS)
    assert report.checks_warned == 0
    assert Path(report.report_path).exists()


def test_observability_report_passes_dataset_check_when_file_is_readable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr("src.monitoring.observability.REQUIRED_GOLD_DATASETS", ["sales_daily"])
    monkeypatch.setattr("src.monitoring.observability.REQUIRED_MODEL_OUTPUTS", [])
    monkeypatch.setattr("src.monitoring.observability.REQUIRED_REPORT_GLOBS", {})
    path = tmp_path / "data" / "gold" / "sales_daily" / "sales_daily.parquet"
    write_parquet(pd.DataFrame({"date": ["2018-01-01"], "gmv": [100.0]}), path)

    report = build_observability_report(_settings(tmp_path))

    assert report.status == "passed"
    assert report.checks_failed == 0
    assert report.checks[0].details["rows"] == 1
