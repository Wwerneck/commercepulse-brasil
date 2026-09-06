import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import Settings, get_settings
from src.quality.profiling import profile_dataframe, profile_to_dict
from src.utils.lake import latest_parquets_by_leaf
from src.utils.parquet import read_parquet, write_parquet

logger = logging.getLogger(__name__)

OLIST_DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}

STRING_NORMALIZATION_COLUMNS = {
    "customers": ["customer_city", "customer_state"],
    "sellers": ["seller_city", "seller_state"],
    "geolocation": ["geolocation_city", "geolocation_state"],
    "products": ["product_category_name"],
    "product_category_name_translation": [
        "product_category_name",
        "product_category_name_english",
    ],
}

DEDUP_KEYS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "product_category_name_translation": ["product_category_name"],
    "order_items": ["order_id", "order_item_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "order_reviews": ["review_id"],
}

NON_NEGATIVE_COLUMNS = {
    "order_items": ["price", "freight_value"],
    "order_payments": ["payment_value", "payment_installments"],
    "products": [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
}


@dataclass(frozen=True)
class SilverDatasetResult:
    dataset: str
    source_path: str
    destination_path: str
    rows_input: int
    rows_output: int
    columns_output: int
    notes: list[str]
    profile_before: dict
    profile_after: dict


@dataclass(frozen=True)
class SilverBuildResult:
    generated_at: datetime
    source: str
    datasets: list[SilverDatasetResult]
    report_path: str

    @property
    def files_written(self) -> int:
        return len(self.datasets)


def _normalize_strings(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip().str.lower()
    return df


def _parse_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _add_duplicate_key_flag(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    keys = DEDUP_KEYS.get(dataset, [])
    if keys and all(column in df.columns for column in keys):
        df["is_duplicate_key"] = df.duplicated(subset=keys, keep=False)
    else:
        df["is_duplicate_key"] = False
    return df


def _add_invalid_numeric_flags(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    for column in NON_NEGATIVE_COLUMNS.get(dataset, []):
        if column in df.columns:
            df[f"has_invalid_{column}"] = df[column].isna() | (df[column] < 0)
    return df


def _add_invalid_date_flags(df: pd.DataFrame, dataset: str) -> pd.DataFrame:
    if dataset == "orders":
        if "order_purchase_timestamp" in df.columns:
            purchase = df["order_purchase_timestamp"]
            df["has_invalid_order_purchase_timestamp"] = purchase.isna()
            if "order_delivered_customer_date" in df.columns:
                delivered = df["order_delivered_customer_date"]
                df["has_delivery_before_purchase"] = (
                    delivered.notna() & purchase.notna() & (delivered < purchase)
                )
            if "order_estimated_delivery_date" in df.columns:
                estimated = df["order_estimated_delivery_date"]
                df["has_estimate_before_purchase"] = (
                    estimated.notna() & purchase.notna() & (estimated < purchase)
                )
    elif dataset == "order_items":
        df["has_invalid_shipping_limit_date"] = df["shipping_limit_date"].isna()
    elif dataset == "order_reviews":
        df["has_invalid_review_creation_date"] = df["review_creation_date"].isna()
    return df


def transform_olist_dataset(dataset: str, df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    notes: list[str] = []
    output = df.copy()
    output = _parse_dates(output, OLIST_DATE_COLUMNS.get(dataset, []))
    output = _normalize_strings(output, STRING_NORMALIZATION_COLUMNS.get(dataset, []))

    if dataset == "order_items":
        output["price"] = pd.to_numeric(output["price"], errors="coerce")
        output["freight_value"] = pd.to_numeric(output["freight_value"], errors="coerce")
    elif dataset == "order_payments":
        output["payment_value"] = pd.to_numeric(output["payment_value"], errors="coerce")
    elif dataset == "order_reviews":
        output["review_score"] = pd.to_numeric(
            output["review_score"],
            errors="coerce",
        ).astype("Int64")
    elif dataset == "products":
        numeric_columns = [
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
        for column in numeric_columns:
            if column in output.columns:
                output[column] = pd.to_numeric(output[column], errors="coerce")

    output = _add_duplicate_key_flag(output, dataset)
    output = _add_invalid_numeric_flags(output, dataset)
    output = _add_invalid_date_flags(output, dataset)
    notes.append("typed_dates_and_normalized_strings")
    notes.append("added_quality_flags_without_dropping_rows")
    return output, notes


def transform_bcb_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    output = df.copy()
    output["date"] = pd.to_datetime(output["date"], errors="coerce")
    output["value"] = pd.to_numeric(output["value"], errors="coerce")
    output["series_code"] = pd.to_numeric(output["series_code"], errors="coerce").astype("Int64")
    output["has_invalid_date"] = output["date"].isna()
    output["has_invalid_value"] = output["value"].isna()
    key_columns = ["indicator_name", "series_code", "date"]
    output["is_duplicate_key"] = (
        output.duplicated(subset=key_columns, keep=False)
        if all(column in output.columns for column in key_columns)
        else False
    )
    return output, ["typed_bcb_time_series", "added_quality_flags_without_dropping_rows"]


def transform_ibge_sidra_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    output = df.copy()
    notes = ["removed_sidra_header_row", "normalized_sidra_columns"]
    if not output.empty and str(output.iloc[0].get("V", "")).lower() == "valor":
        output = output.iloc[1:].copy()

    output = output.rename(
        columns={
            "V": "value",
            "D1C": "territory_code",
            "D1N": "territory_name",
            "D2C": "variable_code",
            "D2N": "variable_name",
            "D3C": "period_code",
            "D3N": "period_name",
            "MN": "unit",
        }
    )
    output["value"] = pd.to_numeric(output["value"], errors="coerce")
    output["period_code"] = output["period_code"].astype("string")
    output["reference_month"] = pd.to_datetime(
        output["period_code"] + "01",
        format="%Y%m%d",
        errors="coerce",
    )
    output["has_invalid_value"] = output["value"].isna()
    output["has_invalid_reference_month"] = output["reference_month"].isna()
    output["is_duplicate_key"] = output.duplicated(
        subset=["indicator_name", "territory_code", "variable_code", "period_code"],
        keep=False,
    )
    keep_columns = [
        "indicator_name",
        "source",
        "ingestion_timestamp",
        "batch_id",
        "value",
        "unit",
        "territory_code",
        "territory_name",
        "variable_code",
        "variable_name",
        "period_code",
        "period_name",
        "reference_month",
        "has_invalid_value",
        "has_invalid_reference_month",
        "is_duplicate_key",
    ]
    return output[[column for column in keep_columns if column in output.columns]], notes


def _write_report(result: SilverBuildResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**asdict(result), "generated_at": result.generated_at.isoformat()}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def build_silver_layer(settings: Settings | None = None) -> SilverBuildResult:
    cfg = settings or get_settings()
    generated_at = datetime.now(UTC)
    results: list[SilverDatasetResult] = []

    source_roots = {
        "olist": cfg.bronze_dir / "olist",
        "bcb": cfg.bronze_dir / "bcb",
        "ibge": cfg.bronze_dir / "ibge",
    }
    for source, root in source_roots.items():
        for dataset, source_path in latest_parquets_by_leaf(root).items():
            df = read_parquet(source_path)
            profile_before = profile_dataframe(df)
            if source == "olist":
                silver_df, notes = transform_olist_dataset(dataset, df)
            elif source == "bcb":
                silver_df, notes = transform_bcb_dataset(df)
            else:
                silver_df, notes = transform_ibge_sidra_dataset(df)

            destination = cfg.silver_dir / source / dataset / source_path.name
            write_parquet(silver_df, destination)
            logger.info(
                "silver_dataset_built source=%s dataset=%s rows=%s destination=%s",
                source,
                dataset,
                len(silver_df),
                destination,
            )
            results.append(
                SilverDatasetResult(
                    dataset=f"{source}.{dataset}",
                    source_path=str(source_path),
                    destination_path=str(destination),
                    rows_input=len(df),
                    rows_output=len(silver_df),
                    columns_output=len(silver_df.columns),
                    notes=notes,
                    profile_before=profile_to_dict(profile_before),
                    profile_after=profile_to_dict(profile_dataframe(silver_df)),
                )
            )

    report_path = cfg.silver_dir / "_reports" / f"silver_build_{generated_at:%Y%m%dT%H%M%SZ}.json"
    result = SilverBuildResult(
        generated_at=generated_at,
        source="bronze",
        datasets=results,
        report_path=str(report_path),
    )
    _write_report(result, report_path)
    return result
