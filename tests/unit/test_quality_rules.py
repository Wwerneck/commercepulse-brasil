import pandas as pd

from src.quality.olist_checks import validate_order_items, validate_reviews


def test_validate_order_items_flags_invalid_price() -> None:
    df = pd.DataFrame(
        {
            "order_id": ["a", "b"],
            "product_id": ["p1", "p2"],
            "seller_id": ["s1", "s2"],
            "price": [10.0, -1.0],
            "freight_value": [3.0, 4.0],
        }
    )

    results = validate_order_items(df)

    assert any(result.rule_name == "price_non_negative" and not result.passed for result in results)


def test_validate_reviews_accepts_scores_between_one_and_five() -> None:
    df = pd.DataFrame({"review_id": ["r1"], "order_id": ["o1"], "review_score": [5]})

    assert all(result.passed for result in validate_reviews(df))
