import pandas as pd

from src.analytics.economic import _corr_and_cov


def test_corr_and_cov_returns_values_when_enough_observations() -> None:
    df = pd.DataFrame({"gmv": [1.0, 2.0, 3.0], "selic_target": [2.0, 4.0, 6.0]})

    result = _corr_and_cov(df, "gmv", "selic_target")

    assert result.observations == 3
    assert result.correlation == 1.0


def test_corr_and_cov_returns_none_when_too_few_observations() -> None:
    df = pd.DataFrame({"gmv": [1.0, None], "selic_target": [2.0, 4.0]})

    result = _corr_and_cov(df, "gmv", "selic_target")

    assert result.observations == 1
    assert result.correlation is None
