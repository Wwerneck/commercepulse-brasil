import pandas as pd

from src.quality.rules import QualityResult, between, non_negative, not_null


def validate_order_items(df: pd.DataFrame) -> list[QualityResult]:
    return [
        not_null(df, "order_id"),
        not_null(df, "product_id"),
        not_null(df, "seller_id"),
        non_negative(df, "price"),
        non_negative(df, "freight_value"),
    ]


def validate_reviews(df: pd.DataFrame) -> list[QualityResult]:
    return [
        not_null(df, "review_id"),
        not_null(df, "order_id"),
        between(df, "review_score", 1, 5),
    ]
