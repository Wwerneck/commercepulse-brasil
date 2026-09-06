from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class OutlierSummary:
    column: str
    q1: float
    q3: float
    iqr: float
    lower_bound: float
    upper_bound: float
    outlier_count: int
    total_count: int

    @property
    def outlier_ratio(self) -> float:
        return 0.0 if self.total_count == 0 else self.outlier_count / self.total_count


def iqr_outlier_summary(series: pd.Series, column: str | None = None) -> OutlierSummary:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    name = column or series.name or "value"

    if values.size == 0:
        return OutlierSummary(name, np.nan, np.nan, np.nan, np.nan, np.nan, 0, 0)

    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outlier_count = int(np.sum((values < lower_bound) | (values > upper_bound)))

    return OutlierSummary(
        column=name,
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower_bound=float(lower_bound),
        upper_bound=float(upper_bound),
        outlier_count=outlier_count,
        total_count=int(values.size),
    )


def zscore_flags(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(values)
    flags = np.zeros(values.shape, dtype=bool)
    if finite.sum() < 2:
        return pd.Series(flags, index=series.index)

    mean = np.mean(values[finite])
    std = np.std(values[finite])
    if std == 0:
        return pd.Series(flags, index=series.index)

    zscores = np.abs((values[finite] - mean) / std)
    flags[finite] = zscores > threshold
    return pd.Series(flags, index=series.index)
