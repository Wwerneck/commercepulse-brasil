from pathlib import Path

from src.config import Settings
from src.warehouse.ddl import WAREHOUSE_DDL
from src.warehouse.postgres import check_warehouse_inputs, expected_gold_paths


def test_warehouse_ddl_contains_expected_schemas_and_fact_sales() -> None:
    assert "create schema if not exists analytics" in WAREHOUSE_DDL
    assert "create table if not exists analytics.fact_sales_daily" in WAREHOUSE_DDL
    assert "references analytics.dim_date" in WAREHOUSE_DDL


def test_expected_gold_paths_are_relative_to_settings(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        log_level="INFO",
        data_dir=tmp_path / "data",
        models_dir=tmp_path / "models",
        bcb_base_url="https://api.bcb.gov.br/dados/serie",
        ibge_sidra_base_url="https://apisidra.ibge.gov.br/values",
        request_timeout_seconds=1,
        request_retries=0,
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="commercepulse",
        postgres_user="commercepulse",
        postgres_password="commercepulse",
        mlflow_tracking_uri="http://localhost:5000",
    )

    paths = expected_gold_paths(settings)

    assert settings.gold_dir / "sales_daily" / "sales_daily.parquet" in paths


def test_check_warehouse_inputs_reports_missing_paths(tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        log_level="INFO",
        data_dir=tmp_path / "data",
        models_dir=tmp_path / "models",
        bcb_base_url="https://api.bcb.gov.br/dados/serie",
        ibge_sidra_base_url="https://apisidra.ibge.gov.br/values",
        request_timeout_seconds=1,
        request_retries=0,
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="commercepulse",
        postgres_user="commercepulse",
        postgres_password="commercepulse",
        mlflow_tracking_uri="http://localhost:5000",
    )

    checks = check_warehouse_inputs(settings)

    assert checks
    assert not all(checks.values())
