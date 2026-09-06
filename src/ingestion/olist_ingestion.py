import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import Settings, get_settings
from src.ingestion.manifest import BronzeIngestionManifest, BronzeTableManifest, write_manifest
from src.utils.batches import new_batch_id
from src.utils.parquet import write_parquet

logger = logging.getLogger(__name__)


EXPECTED_OLIST_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv",
}


def ingest_olist_csvs(
    source_dir: Path,
    settings: Settings | None = None,
) -> BronzeIngestionManifest:
    cfg = settings or get_settings()
    batch_id = new_batch_id("olist")
    started_at = datetime.now(UTC)
    logger.info("pipeline_started source=olist source_dir=%s batch_id=%s", source_dir, batch_id)

    tables: list[BronzeTableManifest] = []
    missing_files: list[str] = []
    for table_name, file_name in EXPECTED_OLIST_FILES.items():
        source_file = source_dir / file_name
        if not source_file.exists():
            logger.warning("olist_file_missing table=%s source_file=%s", table_name, source_file)
            missing_files.append(file_name)
            continue

        df = pd.read_csv(source_file)
        df["source"] = "olist"
        df["source_file"] = file_name
        df["ingestion_timestamp"] = started_at
        df["batch_id"] = batch_id

        destination = cfg.bronze_dir / "olist" / table_name / f"{batch_id}.parquet"
        write_parquet(df, destination)
        logger.info(
            "olist_table_ingested table=%s rows=%s columns=%s destination=%s batch_id=%s",
            table_name,
            len(df),
            len(df.columns),
            destination,
            batch_id,
        )
        tables.append(
            BronzeTableManifest(
                name=table_name,
                destination=str(destination),
                rows_read=len(df),
                columns_read=len(df.columns),
                source_reference=str(source_file),
            )
        )

    finished_at = datetime.now(UTC)
    manifest_path = cfg.bronze_dir / "olist" / "_manifests" / f"{batch_id}.json"
    result = BronzeIngestionManifest(
        batch_id=batch_id,
        source="olist",
        started_at=started_at,
        finished_at=finished_at,
        tables=tables,
        missing_references=missing_files,
        manifest_path=str(manifest_path),
    )
    write_manifest(result, manifest_path)
    logger.info(
        "pipeline_finished source=olist files_written=%s missing_files=%s batch_id=%s",
        result.files_written,
        len(missing_files),
        batch_id,
    )
    return result
