from src.transformation.dim_date import build_dim_date


def test_build_dim_date_contains_expected_calendar_fields() -> None:
    df = build_dim_date("2024-01-01", "2024-01-03")

    assert len(df) == 3
    assert df.loc[0, "date_key"] == 20240101
    assert "is_weekend" in df.columns
