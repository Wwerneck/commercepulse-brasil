from pathlib import Path

import pandas as pd

from src.config import Settings
from src.ingestion.olist_ingestion import ingest_olist_csvs
from src.utils.parquet import read_parquet


def test_ingest_olist_csvs_writes_bronze_parquet_and_manifest(tmp_path: Path) -> None:
    source_dir = tmp_path / "raw" / "olist"
    source_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "customer_id": ["c1"],
            "customer_unique_id": ["u1"],
            "customer_zip_code_prefix": [12345],
            "customer_city": ["sao paulo"],
            "customer_state": ["SP"],
        }
    ).to_csv(source_dir / "olist_customers_dataset.csv", index=False)

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

    result = ingest_olist_csvs(source_dir, settings=settings)

    assert result.files_written == 1
    assert result.records_read == 1
    assert "olist_orders_dataset.csv" in result.missing_references
    assert Path(result.manifest_path).exists()

    written = Path(result.tables[0].destination)
    bronze_df = read_parquet(written)
    assert bronze_df.loc[0, "source"] == "olist"
    assert bronze_df.loc[0, "source_file"] == "olist_customers_dataset.csv"
