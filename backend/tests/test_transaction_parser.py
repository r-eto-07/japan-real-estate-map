from app.utils.transaction_parser import (
    calculate_unit_price,
    parse_float,
    parse_int,
    parse_period,
)


# ----- parse_int -----
def test_parse_int_normal() -> None:
    assert parse_int("180000") == 180000


def test_parse_int_with_comma() -> None:
    assert parse_int("18,000,000") == 18000000


def test_parse_int_empty_and_hyphen_and_none() -> None:
    assert parse_int("") is None
    assert parse_int("-") is None
    assert parse_int(None) is None


def test_parse_int_non_numeric() -> None:
    assert parse_int("2000㎡以上") is None


# ----- calculate_unit_price（§42）-----
def test_uses_unit_price_when_present() -> None:
    assert calculate_unit_price("180000", None, None) == 180000


def test_falls_back_to_trade_price_over_area() -> None:
    assert calculate_unit_price("", "18000000", "100") == 180000


def test_none_when_trade_price_missing() -> None:
    assert calculate_unit_price("", "", "100") is None
    assert calculate_unit_price(None, None, "100") is None


def test_none_when_area_is_zero() -> None:
    assert calculate_unit_price("", "18000000", "0") is None


def test_none_when_unit_price_not_positive() -> None:
    assert calculate_unit_price("0", None, None) is None
    assert calculate_unit_price("-5", None, None) is None


# ----- parse_float -----
def test_parse_float() -> None:
    assert parse_float("100") == 100.0
    assert parse_float("123.45") == 123.45
    assert parse_float("") is None
    assert parse_float("2000㎡以上") is None
    assert parse_float(None) is None


# ----- parse_period -----
def test_parse_period() -> None:
    assert parse_period("2025年第1四半期") == (2025, 1)
    assert parse_period("2024年第4四半期") == (2024, 4)
    assert parse_period("2025年第１四半期") == (2025, 1)  # 全角
    assert parse_period("") == (None, None)
    assert parse_period(None) == (None, None)
