import pandas as pd

from src.analytics.outliers import iqr_outlier_summary, zscore_flags


def test_iqr_outlier_summary_detects_extreme_value() -> None:
    summary = iqr_outlier_summary(pd.Series([10, 11, 12, 13, 500]), column="price")

    assert summary.column == "price"
    assert summary.outlier_count == 1
    assert summary.total_count == 5


def test_zscore_flags_returns_boolean_series() -> None:
    flags = zscore_flags(pd.Series([1, 1, 1, 1, 100]), threshold=1.5)

    assert flags.dtype == bool
    assert flags.sum() == 1
