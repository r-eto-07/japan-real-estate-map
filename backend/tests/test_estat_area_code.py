from app.utils.estat_area_code import to_estat_area_code


def test_identity_for_5digit_standard_code() -> None:
    assert to_estat_area_code("12217") == "12217"
    assert to_estat_area_code("13104") == "13104"


def test_strips_whitespace() -> None:
    assert to_estat_area_code(" 27127 ") == "27127"
