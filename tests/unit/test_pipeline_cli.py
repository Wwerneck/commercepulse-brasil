from pathlib import Path

from src.pipeline import build_parser


def test_build_parser_accepts_ingest_olist_command() -> None:
    args = build_parser().parse_args(["ingest-olist", "--source-dir", "data/raw/olist"])

    assert args.command == "ingest-olist"
    assert args.source_dir == Path("data/raw/olist")


def test_build_parser_accepts_bcb_dates() -> None:
    args = build_parser().parse_args(
        ["ingest-bcb", "--start-date", "01/01/2020", "--end-date", "31/12/2020"]
    )

    assert args.command == "ingest-bcb"
    assert args.start_date == "01/01/2020"


def test_build_parser_accepts_validate_bronze_command() -> None:
    args = build_parser().parse_args(["validate-bronze"])

    assert args.command == "validate-bronze"


def test_build_parser_accepts_silver_commands() -> None:
    assert build_parser().parse_args(["build-silver"]).command == "build-silver"
    assert build_parser().parse_args(["validate-silver"]).command == "validate-silver"
    assert build_parser().parse_args(["silver-outliers"]).command == "silver-outliers"


def test_build_parser_accepts_gold_commands() -> None:
    assert build_parser().parse_args(["build-gold"]).command == "build-gold"
    assert build_parser().parse_args(["validate-gold"]).command == "validate-gold"


def test_build_parser_accepts_warehouse_commands() -> None:
    assert build_parser().parse_args(["init-warehouse"]).command == "init-warehouse"
    assert build_parser().parse_args(["load-warehouse"]).command == "load-warehouse"
    assert (
        build_parser().parse_args(["check-warehouse-inputs"]).command
        == "check-warehouse-inputs"
    )


def test_build_parser_accepts_analytics_and_ml_commands() -> None:
    assert build_parser().parse_args(["analytics-report"]).command == "analytics-report"
    assert build_parser().parse_args(["economic-analysis"]).command == "economic-analysis"
    assert build_parser().parse_args(["train-forecast"]).command == "train-forecast"
    assert build_parser().parse_args(["segment-customers"]).command == "segment-customers"
    assert build_parser().parse_args(["detect-anomalies"]).command == "detect-anomalies"
    assert build_parser().parse_args(["review-intelligence"]).command == "review-intelligence"
    assert build_parser().parse_args(["observability-report"]).command == "observability-report"
