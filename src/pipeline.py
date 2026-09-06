import argparse
from pathlib import Path

from src.analytics.economic import build_economic_analysis
from src.analytics.kpis import build_analytics_report
from src.config import get_settings
from src.ingestion.bcb_ingestion import ingest_configured_bcb_indicators
from src.ingestion.ibge_ingestion import ingest_configured_sidra_indicators
from src.ingestion.indicator_config import load_economic_indicator_config
from src.ingestion.olist_ingestion import ingest_olist_csvs
from src.ml.anomaly_detection import compare_anomaly_methods
from src.ml.forecast import train_sales_forecast_baseline
from src.ml.review_intelligence import build_review_intelligence
from src.ml.segmentation import build_customer_segmentation
from src.monitoring.observability import build_observability_report
from src.quality.bronze_checks import validate_bronze_layer
from src.quality.gold_checks import validate_gold_layer
from src.quality.outlier_reports import generate_silver_outlier_report
from src.quality.silver_checks import validate_silver_layer
from src.transformation.gold import build_gold_layer
from src.transformation.silver import build_silver_layer
from src.utils.logging import configure_logging
from src.warehouse.postgres import (
    check_warehouse_inputs,
    initialize_warehouse,
    load_gold_to_postgres,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CommercePulse Brasil pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_olist = subparsers.add_parser("ingest-olist", help="Ingest Olist CSVs into Bronze")
    ingest_olist.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory containing the original Olist CSV files",
    )

    ingest_bcb = subparsers.add_parser("ingest-bcb", help="Ingest configured BCB SGS series")
    ingest_bcb.add_argument(
        "--config",
        type=Path,
        default=Path("config/economic_indicators.json"),
        help="Path to economic indicator configuration",
    )
    ingest_bcb.add_argument("--start-date", help="Start date in DD/MM/YYYY format")
    ingest_bcb.add_argument("--end-date", help="End date in DD/MM/YYYY format")

    ingest_ibge = subparsers.add_parser("ingest-ibge", help="Ingest configured IBGE SIDRA queries")
    ingest_ibge.add_argument(
        "--config",
        type=Path,
        default=Path("config/economic_indicators.json"),
        help="Path to economic indicator configuration",
    )

    subparsers.add_parser("validate-bronze", help="Validate Bronze parquet metadata")
    subparsers.add_parser("build-silver", help="Transform latest Bronze datasets into Silver")
    subparsers.add_parser("validate-silver", help="Validate Silver datasets")
    subparsers.add_parser("silver-outliers", help="Generate Silver IQR outlier report")
    subparsers.add_parser("build-gold", help="Build Gold business datasets with DuckDB")
    subparsers.add_parser("validate-gold", help="Validate Gold business datasets")
    subparsers.add_parser("init-warehouse", help="Create PostgreSQL warehouse schemas and tables")
    subparsers.add_parser("load-warehouse", help="Load Gold datasets into PostgreSQL")
    subparsers.add_parser("check-warehouse-inputs", help="Check Gold datasets required by loader")
    subparsers.add_parser("analytics-report", help="Build KPI analytics report from Gold")
    subparsers.add_parser("economic-analysis", help="Build economic correlation report")
    subparsers.add_parser("train-forecast", help="Train sales forecast baseline models")
    subparsers.add_parser("segment-customers", help="Run RFM KMeans customer segmentation")
    subparsers.add_parser("detect-anomalies", help="Compare z-score and Isolation Forest anomalies")
    subparsers.add_parser("review-intelligence", help="Build review intelligence report")
    subparsers.add_parser("observability-report", help="Build operational observability report")
    return parser


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    args = build_parser().parse_args()

    if args.command == "ingest-olist":
        result = ingest_olist_csvs(args.source_dir, settings=settings)
        print(
            "Olist Bronze ingestion finished: "
            f"batch_id={result.batch_id}, files_written={result.files_written}, "
            f"records_read={result.records_read}, missing_files={len(result.missing_references)}, "
            f"manifest={result.manifest_path}"
        )
    elif args.command == "ingest-bcb":
        config = load_economic_indicator_config(args.config)
        result = ingest_configured_bcb_indicators(
            config.bcb_sgs,
            start_date=args.start_date,
            end_date=args.end_date,
            settings=settings,
        )
        print(
            "BCB Bronze ingestion finished: "
            f"batch_id={result.batch_id}, files_written={result.files_written}, "
            f"records_read={result.records_read}, manifest={result.manifest_path}"
        )
    elif args.command == "ingest-ibge":
        config = load_economic_indicator_config(args.config)
        result = ingest_configured_sidra_indicators(config.ibge_sidra, settings=settings)
        print(
            "IBGE Bronze ingestion finished: "
            f"batch_id={result.batch_id}, files_written={result.files_written}, "
            f"records_read={result.records_read}, manifest={result.manifest_path}"
        )
    elif args.command == "validate-bronze":
        report = validate_bronze_layer(settings.bronze_dir)
        print(
            "Bronze validation finished: "
            f"passed={report.passed}, files_checked={report.files_checked}, "
            f"files_failed={report.files_failed}, report={report.report_path}"
        )
    elif args.command == "build-silver":
        result = build_silver_layer(settings)
        print(
            "Silver build finished: "
            f"files_written={result.files_written}, report={result.report_path}"
        )
    elif args.command == "validate-silver":
        report = validate_silver_layer(settings.silver_dir)
        print(
            "Silver validation finished: "
            f"passed={report.passed}, files_checked={report.files_checked}, "
            f"critical_failures={report.critical_failures}, report={report.report_path}"
        )
    elif args.command == "silver-outliers":
        report = generate_silver_outlier_report(settings.silver_dir)
        print(
            "Silver outlier report finished: "
            f"datasets={len(report.datasets)}, report={report.report_path}"
        )
    elif args.command == "build-gold":
        result = build_gold_layer(settings)
        print(
            "Gold build finished: "
            f"files_written={result.files_written}, report={result.report_path}"
        )
    elif args.command == "validate-gold":
        report = validate_gold_layer(settings.gold_dir)
        print(
            "Gold validation finished: "
            f"passed={report.passed}, datasets_checked={report.datasets_checked}, "
            f"critical_failures={report.critical_failures}, report={report.report_path}"
        )
    elif args.command == "init-warehouse":
        initialize_warehouse(settings)
        print("PostgreSQL warehouse initialized.")
    elif args.command == "load-warehouse":
        counts = load_gold_to_postgres(settings)
        loaded = sum(counts.values())
        print(f"PostgreSQL warehouse load finished: tables={len(counts)}, rows={loaded}")
    elif args.command == "check-warehouse-inputs":
        checks = check_warehouse_inputs(settings)
        missing = [path for path, exists in checks.items() if not exists]
        print(
            "Warehouse input check finished: "
            f"required={len(checks)}, missing={len(missing)}, passed={not missing}"
        )
    elif args.command == "analytics-report":
        report = build_analytics_report(settings)
        print(f"Analytics report finished: report={report.report_path}")
    elif args.command == "economic-analysis":
        report = build_economic_analysis(settings)
        print(
            "Economic analysis finished: "
            f"correlations={len(report.correlations)}, report={report.report_path}"
        )
    elif args.command == "train-forecast":
        report = train_sales_forecast_baseline(settings)
        print(
            "Forecast training finished: "
            f"best_model={report.best_model}, train_rows={report.train_rows}, "
            f"test_rows={report.test_rows}, report={report.report_path}"
        )
    elif args.command == "segment-customers":
        report = build_customer_segmentation(settings)
        print(
            "Customer segmentation finished: "
            f"selected_k={report.selected_k}, rows={report.rows}, report={report.report_path}"
        )
    elif args.command == "detect-anomalies":
        report = compare_anomaly_methods(settings)
        print(
            "Anomaly detection finished: "
            f"zscore_days={report.zscore_anomaly_days}, "
            f"isolation_forest_days={report.isolation_forest_anomaly_days}, "
            f"report={report.report_path}"
        )
    elif args.command == "review-intelligence":
        report = build_review_intelligence(settings)
        print(
            "Review intelligence finished: "
            f"text_coverage={report.text_coverage_ratio:.4f}, report={report.report_path}"
        )
    elif args.command == "observability-report":
        report = build_observability_report(settings)
        print(
            "Observability report finished: "
            f"status={report.status}, checks={report.checks_total}, "
            f"failed={report.checks_failed}, warned={report.checks_warned}, "
            f"report={report.report_path}"
        )


if __name__ == "__main__":
    main()
