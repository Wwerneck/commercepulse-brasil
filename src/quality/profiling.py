from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ColumnProfile:
    column: str
    dtype: str
    null_count: int
    null_ratio: float
    unique_count: int


@dataclass(frozen=True)
class DatasetProfile:
    rows: int
    columns: int
    duplicate_rows: int
    column_profiles: list[ColumnProfile]


def profile_dataframe(df: pd.DataFrame) -> DatasetProfile:
    rows = len(df)
    profiles: list[ColumnProfile] = []
    for column in df.columns:
        null_count = int(df[column].isna().sum())
        profiles.append(
            ColumnProfile(
                column=column,
                dtype=str(df[column].dtype),
                null_count=null_count,
                null_ratio=0.0 if rows == 0 else null_count / rows,
                unique_count=int(df[column].nunique(dropna=True)),
            )
        )
    return DatasetProfile(
        rows=rows,
        columns=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        column_profiles=profiles,
    )


def profile_to_dict(profile: DatasetProfile) -> dict[str, Any]:
    return {
        "rows": profile.rows,
        "columns": profile.columns,
        "duplicate_rows": profile.duplicate_rows,
        "column_profiles": [vars(column) for column in profile.column_profiles],
    }
