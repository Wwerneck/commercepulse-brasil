import pandas as pd

from src.quality.profiling import profile_dataframe


def test_profile_dataframe_counts_nulls_and_duplicates() -> None:
    df = pd.DataFrame({"id": [1, 1, 2], "value": [10, 10, None]})

    profile = profile_dataframe(df)

    assert profile.rows == 3
    assert profile.duplicate_rows == 1
    assert profile.column_profiles[1].null_count == 1
