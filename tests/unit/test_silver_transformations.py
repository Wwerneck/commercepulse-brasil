import pandas as pd

from src.transformation.silver import (
    transform_bcb_dataset,
    transform_ibge_sidra_dataset,
    transform_olist_dataset,
)


def test_transform_olist_orders_parses_date_columns() -> None:
    df = pd.DataFrame(
        {
            "order_id": ["o1"],
            "customer_id": ["c1"],
            "order_purchase_timestamp": ["2024-01-01 10:00:00"],
        }
    )

    output, notes = transform_olist_dataset("orders", df)

    assert pd.api.types.is_datetime64_any_dtype(output["order_purchase_timestamp"])
    assert "typed_dates_and_normalized_strings" in notes


def test_transform_bcb_dataset_types_value_and_date() -> None:
    df = pd.DataFrame({"date": ["2024-01-01"], "value": ["10.5"], "series_code": ["432"]})

    output, _ = transform_bcb_dataset(df)

    assert pd.api.types.is_datetime64_any_dtype(output["date"])
    assert output.loc[0, "value"] == 10.5


def test_transform_ibge_sidra_dataset_removes_header_row() -> None:
    df = pd.DataFrame(
        {
            "V": ["Valor", "0.5"],
            "MN": ["Unidade de Medida", "%"],
            "D1C": ["Brasil (Código)", "1"],
            "D1N": ["Brasil", "Brasil"],
            "D2C": ["Variável (Código)", "63"],
            "D2N": ["Variável", "IPCA"],
            "D3C": ["Mês (Código)", "202401"],
            "D3N": ["Mês", "janeiro 2024"],
            "indicator_name": ["ipca", "ipca"],
            "source": ["ibge_sidra", "ibge_sidra"],
            "ingestion_timestamp": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-01")],
            "batch_id": ["batch", "batch"],
        }
    )

    output, notes = transform_ibge_sidra_dataset(df)

    assert len(output) == 1
    assert output.loc[1, "value"] == 0.5
    assert "removed_sidra_header_row" in notes
