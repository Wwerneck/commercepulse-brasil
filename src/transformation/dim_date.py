import numpy as np
import pandas as pd


def build_dim_date(start: str, end: str) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="D")
    df = pd.DataFrame({"date": dates})
    df["date_key"] = df["date"].dt.strftime("%Y%m%d").astype(int)
    df["day"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_name"] = df["date"].dt.day_name()
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["is_weekend"] = np.where(df["day_of_week"].isin([5, 6]), True, False)
    return df[
        [
            "date_key",
            "date",
            "day",
            "day_of_week",
            "day_name",
            "week",
            "month",
            "month_name",
            "quarter",
            "year",
            "is_weekend",
        ]
    ]
