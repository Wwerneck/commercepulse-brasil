import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import Settings, get_settings
from src.ingestion.http import get_json
from src.ingestion.indicator_config import SidraIndicator
from src.ingestion.manifest import BronzeIngestionManifest, BronzeTableManifest, write_manifest
from src.utils.batches import new_batch_id
from src.utils.parquet import write_parquet

logger = logging.getLogger(__name__)


def build_sidra_url(base_url: str, table: str, path: str) -> str:
    normalized = path.strip("/")
    return f"{base_url}/t/{table}/{normalized}"


def fetch_sidra_query(table: str, path: str, settings: Settings | None = None) -> pd.DataFrame:
    cfg = settings or get_settings()
    url = build_sidra_url(cfg.ibge_sidra_base_url, table, path)
    payload = get_json(url, timeout=cfg.request_timeout_seconds, retries=cfg.request_retries)
    return pd.DataFrame(payload)


def ingest_sidra_query(
    table: str,
    path: str,
    indicator_name: str,
    settings: Settings | None = None,
) -> Path:
    cfg = settings or get_settings()
    batch_id = new_batch_id("ibge")
    started_at = datetime.now(UTC)
    logger.info("pipeline_started source=ibge indicator=%s batch_id=%s", indicator_name, batch_id)

    df = fetch_sidra_query(table, path, cfg)
    df["indicator_name"] = indicator_name
    df["source"] = "ibge_sidra"
    df["ingestion_timestamp"] = started_at
    df["batch_id"] = batch_id

    destination = cfg.bronze_dir / "ibge" / indicator_name / f"{batch_id}.parquet"
    write_parquet(df, destination)
    logger.info(
        "pipeline_finished source=ibge indicator=%s rows=%s columns=%s destination=%s batch_id=%s",
        indicator_name,
        len(df),
        len(df.columns),
        destination,
        batch_id,
    )
    return destination


def ingest_configured_sidra_indicators(
    indicators: list[SidraIndicator],
    settings: Settings | None = None,
) -> BronzeIngestionManifest:
    cfg = settings or get_settings()
    batch_id = new_batch_id("ibge")
    started_at = datetime.now(UTC)
    tables: list[BronzeTableManifest] = []

    for indicator in indicators:
        logger.info(
            "pipeline_started source=ibge indicator=%s batch_id=%s",
            indicator.name,
            batch_id,
        )
        df = fetch_sidra_query(indicator.table, indicator.path, cfg)
        df["indicator_name"] = indicator.name
        df["source"] = "ibge_sidra"
        df["ingestion_timestamp"] = started_at
        df["batch_id"] = batch_id

        destination = cfg.bronze_dir / "ibge" / indicator.name / f"{batch_id}.parquet"
        write_parquet(df, destination)
        tables.append(
            BronzeTableManifest(
                name=indicator.name,
                destination=str(destination),
                rows_read=len(df),
                columns_read=len(df.columns),
                source_reference=f"{indicator.table}/{indicator.path}",
            )
        )

    finished_at = datetime.now(UTC)
    manifest_path = cfg.bronze_dir / "ibge" / "_manifests" / f"{batch_id}.json"
    result = BronzeIngestionManifest(
        batch_id=batch_id,
        source="ibge_sidra",
        started_at=started_at,
        finished_at=finished_at,
        tables=tables,
        missing_references=[],
        manifest_path=str(manifest_path),
    )
    write_manifest(result, manifest_path)
    logger.info(
        "pipeline_finished source=ibge files_written=%s records_read=%s batch_id=%s",
        result.files_written,
        result.records_read,
        batch_id,
    )
    return result
