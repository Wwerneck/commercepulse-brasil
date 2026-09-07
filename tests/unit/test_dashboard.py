from dashboard.app import (
    format_compact_currency,
    format_compact_number,
    format_currency,
    format_number,
    page_index_from_query,
    sample_response,
)


def test_format_currency_uses_brazilian_display() -> None:
    assert format_currency(1234.56) == "R$ 1.234,56"


def test_format_number_uses_brazilian_thousands() -> None:
    assert format_number(12345) == "12.345"


def test_formatters_handle_none() -> None:
    assert format_currency(None) == "-"
    assert format_number(None) == "-"


def test_compact_formatters_keep_large_cards_short() -> None:
    assert format_compact_currency(15_843_553.24) == "R$ 15,8 mi"
    assert format_compact_number(98_666) == "98,7 mil"


def test_page_index_from_query_supports_short_links() -> None:
    assert page_index_from_query("economia") > 0
    assert page_index_from_query("inexistente") == 0


def test_sample_response_supports_cloud_dashboard_data() -> None:
    assert sample_response("/kpis/latest")["orders_total"] > 0
    assert len(sample_response("/sales/monthly", {"limit": 3})) == 3
    assert "payload" in sample_response("/ml/reports/forecast/latest")
