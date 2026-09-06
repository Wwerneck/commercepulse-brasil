import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.quality.olist_checks import validate_order_items, validate_reviews
from src.quality.rules import (
    QualityResult,
    accepted_values,
    false_flag,
    not_null,
    relationship_exists,
    unique_key,
)
from src.utils.lake import latest_parquets_by_leaf
from src.utils.parquet import read_parquet


@dataclass(frozen=True)
class SilverQualityReport:
    generated_at: datetime
    files_checked: int
    critical_failures: int
    warning_failures: int
    results: list[QualityResult]
    report_path: str

    @property
    def passed(self) -> bool:
        return self.critical_failures == 0


def _validate_dataset(dataset: str, df: pd.DataFrame) -> list[QualityResult]:
    if dataset == "order_items":
        return [
            *validate_order_items(df),
            unique_key(df, ["order_id", "order_item_id"]),
            false_flag(df, "has_invalid_price"),
            false_flag(df, "has_invalid_freight_value"),
            false_flag(df, "has_invalid_shipping_limit_date"),
        ]
    if dataset == "order_payments":
        return [
            not_null(df, "order_id"),
            unique_key(df, ["order_id", "payment_sequential"]),
            accepted_values(
                df,
                "payment_type",
                {"credit_card", "boleto", "voucher", "debit_card", "not_defined"},
                severity="warning",
            ),
            false_flag(df, "has_invalid_payment_value"),
            false_flag(df, "has_invalid_payment_installments"),
        ]
    if dataset == "order_reviews":
        return [*validate_reviews(df), unique_key(df, ["review_id"], severity="warning")]
    if dataset == "orders":
        return [
            not_null(df, "order_id"),
            not_null(df, "customer_id"),
            unique_key(df, ["order_id"]),
            accepted_values(
                df,
                "order_status",
                {
                    "delivered",
                    "shipped",
                    "canceled",
                    "unavailable",
                    "invoiced",
                    "processing",
                    "created",
                    "approved",
                },
            ),
            false_flag(df, "has_invalid_order_purchase_timestamp"),
            false_flag(df, "has_delivery_before_purchase"),
            false_flag(df, "has_estimate_before_purchase"),
        ]
    if dataset == "customers":
        return [
            not_null(df, "customer_id"),
            not_null(df, "customer_unique_id"),
            unique_key(df, ["customer_id"]),
        ]
    if dataset == "products":
        return [not_null(df, "product_id"), unique_key(df, ["product_id"])]
    if dataset == "sellers":
        return [not_null(df, "seller_id"), unique_key(df, ["seller_id"])]
    if dataset in {"selic_target", "usd_brl", "ibc_br", "ipca"}:
        results = [not_null(df, "indicator_name"), not_null(df, "value")]
        if "has_invalid_value" in df.columns:
            results.append(false_flag(df, "has_invalid_value"))
        if "has_invalid_date" in df.columns:
            results.append(false_flag(df, "has_invalid_date"))
        if "has_invalid_reference_month" in df.columns:
            results.append(false_flag(df, "has_invalid_reference_month"))
        return results
    return []


def _load_silver_source(silver_dir: Path, source: str) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for dataset, path in latest_parquets_by_leaf(silver_dir / source).items():
        frames[dataset] = read_parquet(path)
    return frames


def _validate_olist_relationships(frames: dict[str, pd.DataFrame]) -> list[QualityResult]:
    required = {"orders", "customers", "order_items", "products", "sellers", "order_payments"}
    if not required.issubset(frames):
        return []
    return [
        relationship_exists(
            frames["orders"],
            "customer_id",
            frames["customers"],
            "customer_id",
            "orders_customer_id_relationship",
        ),
        relationship_exists(
            frames["order_items"],
            "order_id",
            frames["orders"],
            "order_id",
            "order_items_order_id_relationship",
        ),
        relationship_exists(
            frames["order_items"],
            "product_id",
            frames["products"],
            "product_id",
            "order_items_product_id_relationship",
            severity="warning",
        ),
        relationship_exists(
            frames["order_items"],
            "seller_id",
            frames["sellers"],
            "seller_id",
            "order_items_seller_id_relationship",
        ),
        relationship_exists(
            frames["order_payments"],
            "order_id",
            frames["orders"],
            "order_id",
            "order_payments_order_id_relationship",
        ),
    ]


def validate_silver_layer(silver_dir: Path) -> SilverQualityReport:
    generated_at = datetime.now(UTC)
    all_results: list[QualityResult] = []
    files_checked = 0

    for source in ["olist", "bcb", "ibge"]:
        frames = _load_silver_source(silver_dir, source)
        for dataset, df in frames.items():
            files_checked += 1
            all_results.extend(_validate_dataset(dataset, df))
        if source == "olist":
            all_results.extend(_validate_olist_relationships(frames))

    critical_failures = sum(
        not result.passed and result.severity == "critical" for result in all_results
    )
    warning_failures = sum(
        not result.passed and result.severity == "warning" for result in all_results
    )
    report_path = (
        silver_dir / "_quality_reports" / f"silver_quality_{generated_at:%Y%m%dT%H%M%SZ}.json"
    )
    report = SilverQualityReport(
        generated_at=generated_at,
        files_checked=files_checked,
        critical_failures=critical_failures,
        warning_failures=warning_failures,
        results=all_results,
        report_path=str(report_path),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **asdict(report),
        "generated_at": report.generated_at.isoformat(),
        "passed": report.passed,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
