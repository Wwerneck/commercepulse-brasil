import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.utils.parquet import read_parquet

REQUIRED_BRONZE_COLUMNS = {"source", "ingestion_timestamp", "batch_id"}


@dataclass(frozen=True)
class BronzeFileCheck:
    path: str
    passed: bool
    rows: int
    columns: int
    missing_columns: list[str]
    message: str


@dataclass(frozen=True)
class BronzeValidationReport:
    generated_at: datetime
    bronze_dir: str
    files_checked: int
    files_failed: int
    checks: list[BronzeFileCheck]
    report_path: str

    @property
    def passed(self) -> bool:
        return self.files_failed == 0


def validate_bronze_file(path: Path) -> BronzeFileCheck:
    try:
        df = read_parquet(path)
    except Exception as exc:
        return BronzeFileCheck(
            path=str(path),
            passed=False,
            rows=0,
            columns=0,
            missing_columns=sorted(REQUIRED_BRONZE_COLUMNS),
            message=f"Could not read parquet file: {exc}",
        )

    missing = sorted(REQUIRED_BRONZE_COLUMNS.difference(df.columns))
    passed = not missing
    return BronzeFileCheck(
        path=str(path),
        passed=passed,
        rows=len(df),
        columns=len(df.columns),
        missing_columns=missing,
        message="passed" if passed else f"Missing required bronze columns: {missing}",
    )


def validate_bronze_layer(
    bronze_dir: Path,
    report_dir: Path | None = None,
) -> BronzeValidationReport:
    parquet_files = sorted(
        path for path in bronze_dir.rglob("*.parquet") if "_quality_reports" not in path.parts
    )
    checks = [validate_bronze_file(path) for path in parquet_files]
    failed = sum(not check.passed for check in checks)
    generated_at = datetime.now(UTC)
    output_dir = report_dir or bronze_dir / "_quality_reports"
    report_path = output_dir / f"bronze_validation_{generated_at:%Y%m%dT%H%M%SZ}.json"

    report = BronzeValidationReport(
        generated_at=generated_at,
        bronze_dir=str(bronze_dir),
        files_checked=len(checks),
        files_failed=failed,
        checks=checks,
        report_path=str(report_path),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        **asdict(report),
        "generated_at": report.generated_at.isoformat(),
        "passed": report.passed,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
