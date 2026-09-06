from dataclasses import dataclass
from typing import Literal

import pandas as pd

Severity = Literal["critical", "warning", "informational"]


@dataclass(frozen=True)
class QualityResult:
    rule_name: str
    severity: Severity
    passed: bool
    failed_count: int
    total_count: int
    message: str


def not_null(df: pd.DataFrame, column: str, severity: Severity = "critical") -> QualityResult:
    failed = int(df[column].isna().sum()) if column in df.columns else len(df)
    total = len(df)
    return QualityResult(
        rule_name=f"{column}_not_null",
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=total,
        message=f"{failed} null values found in {column}",
    )


def non_negative(df: pd.DataFrame, column: str, severity: Severity = "critical") -> QualityResult:
    if column not in df.columns:
        failed = len(df)
    else:
        values = pd.to_numeric(df[column], errors="coerce")
        failed = int((values < 0).sum() + values.isna().sum())
    total = len(df)
    return QualityResult(
        rule_name=f"{column}_non_negative",
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=total,
        message=f"{failed} negative or invalid values found in {column}",
    )


def between(
    df: pd.DataFrame,
    column: str,
    minimum: float,
    maximum: float,
    severity: Severity = "critical",
) -> QualityResult:
    if column not in df.columns:
        failed = len(df)
    else:
        values = pd.to_numeric(df[column], errors="coerce")
        failed = int(((values < minimum) | (values > maximum) | values.isna()).sum())
    total = len(df)
    return QualityResult(
        rule_name=f"{column}_between_{minimum}_{maximum}",
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=total,
        message=f"{failed} values outside [{minimum}, {maximum}] found in {column}",
    )


def unique_key(
    df: pd.DataFrame,
    columns: list[str],
    rule_name: str | None = None,
    severity: Severity = "critical",
) -> QualityResult:
    missing_columns = [column for column in columns if column not in df.columns]
    if missing_columns:
        failed = len(df)
        message = f"Missing key columns: {missing_columns}"
    else:
        failed = int(df.duplicated(subset=columns, keep=False).sum())
        message = f"{failed} duplicate key rows found for {columns}"
    return QualityResult(
        rule_name=rule_name or f"{'_'.join(columns)}_unique",
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=len(df),
        message=message,
    )


def relationship_exists(
    child_df: pd.DataFrame,
    child_column: str,
    parent_df: pd.DataFrame,
    parent_column: str,
    rule_name: str,
    severity: Severity = "critical",
) -> QualityResult:
    if child_column not in child_df.columns or parent_column not in parent_df.columns:
        failed = len(child_df)
        message = f"Missing relationship columns: {child_column}, {parent_column}"
    else:
        child_values = child_df[child_column].dropna()
        parent_values = set(parent_df[parent_column].dropna())
        failed = int((~child_values.isin(parent_values)).sum())
        message = f"{failed} orphan rows found for {child_column} -> {parent_column}"
    return QualityResult(
        rule_name=rule_name,
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=len(child_df),
        message=message,
    )


def accepted_values(
    df: pd.DataFrame,
    column: str,
    values: set[str],
    severity: Severity = "critical",
) -> QualityResult:
    if column not in df.columns:
        failed = len(df)
        message = f"Missing accepted-values column: {column}"
    else:
        normalized = df[column].astype("string")
        failed = int((~normalized.isin(values)).sum())
        message = f"{failed} values outside accepted set found in {column}"
    return QualityResult(
        rule_name=f"{column}_accepted_values",
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=len(df),
        message=message,
    )


def false_flag(df: pd.DataFrame, column: str, severity: Severity = "critical") -> QualityResult:
    if column not in df.columns:
        failed = len(df)
        message = f"Missing quality flag column: {column}"
    else:
        failed = int(df[column].fillna(False).astype(bool).sum())
        message = f"{failed} rows flagged by {column}"
    return QualityResult(
        rule_name=f"{column}_false",
        severity=severity,
        passed=failed == 0,
        failed_count=failed,
        total_count=len(df),
        message=message,
    )
