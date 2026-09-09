from app.utils.price_parser import parse_yen_per_sqm


def test_parses_plain_value() -> None:
    assert parse_yen_per_sqm("165,000(円/㎡)") == 165000


def test_parses_large_value() -> None:
    assert parse_yen_per_sqm("3,100,000(円/㎡)") == 3100000


def test_empty_string_returns_none() -> None:
    assert parse_yen_per_sqm("") is None


def test_none_returns_none() -> None:
    assert parse_yen_per_sqm(None) is None
