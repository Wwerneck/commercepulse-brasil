import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import Settings, get_settings
from src.ingestion.http import get_json
from src.ingestion.indicator_config import BcbSgsIndicator
from src.ingestion.manifest import BronzeIngestionManifest, BronzeTableManifest, write_manifest
from src.utils.batches import new_batch_id
from src.utils.parquet import write_parquet

logger = logging.getLogger(__name__)


def build_sgs_url(base_url: str, series_code: int) -> str:
    return f"{base_url}/bcdata.sgs.{series_code}/dados"


def fetch_bcb_sgs_series(
    series_code: int,
    start_date: str | None = None,
    end_date: str | None = None,
    settings: Settings | None = None,
) -> pd.DataFrame:
    cfg = settings or get_settings()
    params: dict[str, str] = {"formato": "json"}
    if start_date:
        params["dataInicial"] = start_date
    if end_date:
        params["dataFinal"] = end_date

    url = build_sgs_url(cfg.bcb_base_url, series_code)
    payload = get_json(
        url,
        params=params,
        timeout=cfg.request_timeout_seconds,
        retries=cfg.request_retries,
    )
    df = pd.DataFrame(payload)
    if df.empty:
        return pd.DataFrame(columns=["date", "value", "series_code"])

    df = df.rename(columns={"data": "date", "valor": "value"})
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["value"] = pd.to_numeric(df["value"].str.replace(",", ".", regex=False), errors="coerce")
    df["series_code"] = series_code
    return df[["date", "value", "series_code"]]


def ingest_bcb_sgs_series(
    series_code: int,
    indicator_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
    settings: Settings | None = None,
) -> Path:
    cfg = settings or get_settings()
    batch_id = new_batch_id("bcb")
    started_at = datetime.now(UTC)
    logger.info("pipeline_started source=bcb indicator=%s batch_id=%s", indicator_name, batch_id)

    df = fetch_bcb_sgs_series(series_code, start_date, end_date, cfg)
    df["indicator_name"] = indicator_name
    df["source"] = "bcb_sgs"
    df["ingestion_timestamp"] = started_at
    df["batch_id"] = batch_id

    destination = cfg.bronze_dir / "bcb" / indicator_name / f"{batch_id}.parquet"
    write_parquet(df, destination)
    logger.info(
        "pipeline_finished source=bcb indicator=%s rows=%s columns=%s destination=%s batch_id=%s",
        indicator_name,
        len(df),
        len(df.columns),
        destination,
        batch_id,
    )
    return destination


def ingest_configured_bcb_indicators(
    indicators: list[BcbSgsIndicator],
    start_date: str | None = None,
    end_date: str | None = None,
    settings: Settings | None = None,
) -> BronzeIngestionManifest:
    cfg = settings or get_settings()
    batch_id = new_batch_id("bcb")
    started_at = datetime.now(UTC)
    tables: list[BronzeTableManifest] = []

    for indicator in indicators:
        logger.info(
            "pipeline_started source=bcb indicator=%s batch_id=%s",
            indicator.name,
            batch_id,
        )
        df = fetch_bcb_sgs_series(indicator.series_code, start_date, end_date, cfg)
        df["indicator_name"] = indicator.name
        df["source"] = "bcb_sgs"
        df["ingestion_timestamp"] = started_at
        df["batch_id"] = batch_id

        destination = cfg.bronze_dir / "bcb" / indicator.name / f"{batch_id}.parquet"
        write_parquet(df, destination)
        tables.append(
            BronzeTableManifest(
                name=indicator.name,
                destination=str(destination),
                rows_read=len(df),
                columns_read=len(df.columns),
                source_reference=str(indicator.series_code),
            )
        )

    finished_at = datetime.now(UTC)
    manifest_path = cfg.bronze_dir / "bcb" / "_manifests" / f"{batch_id}.json"
    result = BronzeIngestionManifest(
        batch_id=batch_id,
        source="bcb_sgs",
        started_at=started_at,
        finished_at=finished_at,
        tables=tables,
        missing_references=[],
        manifest_path=str(manifest_path),
    )
    write_manifest(result, manifest_path)
    logger.info(
        "pipeline_finished source=bcb files_written=%s records_read=%s batch_id=%s",
        result.files_written,
        result.records_read,
        batch_id,
    )
    return result
