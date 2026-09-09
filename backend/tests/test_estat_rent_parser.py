from app.parsers.estat_rent_parser import extract_average_rent, parse_rent_value
from tests.estat_fixtures import RENT_RESPONSE, build_rent_response


# ----- parse_rent_value（§39）-----
def test_parse_normal_value() -> None:
    assert parse_rent_value("68200") == 68200


def test_parse_value_with_comma() -> None:
    assert parse_rent_value("68,200") == 68200


def test_parse_empty_string_is_none() -> None:
    assert parse_rent_value("") is None


def test_parse_hyphen_is_none() -> None:
    assert parse_rent_value("-") is None


def test_parse_none_is_none() -> None:
    assert parse_rent_value(None) is None


def test_parse_non_numeric_is_none() -> None:
    assert parse_rent_value("***") is None


# ----- extract_average_rent（§41 / §42）-----
def test_extracts_total_excluding_zero_rent_for_municipality() -> None:
    # 総数・家賃0円を含まない の値（68200）を取る。ノイズ（60000/70000）は無視
    assert extract_average_rent(RENT_RESPONSE, "12217") == 68200
    assert extract_average_rent(RENT_RESPONSE, "13104") == 102300


def test_returns_none_when_municipality_absent() -> None:
    assert extract_average_rent(RENT_RESPONSE, "99999") is None


def test_returns_none_when_value_is_blank() -> None:
    response = build_rent_response({"12217": "-"})
    assert extract_average_rent(response, "12217") is None


def test_returns_none_for_broken_response() -> None:
    assert extract_average_rent({}, "12217") is None
