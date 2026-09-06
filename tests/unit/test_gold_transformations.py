from pathlib import Path

import pandas as pd

from src.quality.gold_checks import validate_gold_layer
from src.transformation.gold import _anomaly_metrics, _ml_features
from src.utils.parquet import write_parquet


def test_ml_features_creates_lags_and_rolling_metrics() -> None:
    sales_daily = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=8),
            "gmv": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0],
        }
    )

    output = _ml_features(sales_daily)

    assert output.loc[1, "sales_lag_1"] == 10.0
    assert output.loc[7, "sales_lag_7"] == 10.0
    assert "rolling_mean_7" in output.columns
    assert "log_gmv" in output.columns


def test_anomaly_metrics_adds_zscore_flags() -> None:
    sales_daily = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5),
            "gmv": [1, 1, 1, 1, 100],
            "orders": [1, 1, 1, 1, 50],
            "average_ticket": [1, 1, 1, 1, 20],
            "freight_value": [1, 1, 1, 1, 10],
        }
    )

    output = _anomaly_metrics(sales_daily)

    assert "gmv_zscore_anomaly" in output.columns
    assert output["gmv_zscore_anomaly"].dtype == bool


def test_validate_gold_layer_reports_missing_datasets(tmp_path: Path) -> None:
    gold_dir = tmp_path / "gold"
    write_parquet(
        pd.DataFrame(
            {
                "date": [pd.Timestamp("2024-01-01")],
                "gmv": [10],
                "orders": [1],
                "average_ticket": [10],
            }
        ),
        gold_dir / "sales_daily" / "sales_daily.parquet",
    )

    report = validate_gold_layer(gold_dir)

    assert not report.passed
    assert "sales_monthly" in report.missing_datasets
