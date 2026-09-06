from dashboard.app import format_currency, format_number


def test_format_currency_uses_brazilian_display() -> None:
    assert format_currency(1234.56) == "R$ 1.234,56"


def test_format_number_uses_brazilian_thousands() -> None:
    assert format_number(12345) == "12.345"


def test_formatters_handle_none() -> None:
    assert format_currency(None) == "-"
    assert format_number(None) == "-"
