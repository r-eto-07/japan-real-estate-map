"""XIT001（不動産取引価格情報）の値の数値化と㎡単価の算出。

文字列解析ロジックは Service / Router に書かず、ここに閉じ込める。
"""

from __future__ import annotations

import re

_NULLISH = {"", "-", "‐", "－", "―", None}
_PERIOD_RE = re.compile(r"(\d{4})\s*年\s*第\s*([1-4１-４])\s*四半期")


def parse_int(value: str | None) -> int | None:
    """整数へ。数値でない / 空 / "-" / None は None。"""
    if value is None:
        return None
    text = str(value).strip()
    if text in _NULLISH:
        return None
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return None
    if number != number:  # NaN
        return None
    return int(number)


def parse_float(value: str | None) -> float | None:
    """float へ。数値でない / 空 / "-" / None は None。「2000㎡以上」等も None。"""
    if value is None:
        return None
    text = str(value).strip()
    if text in _NULLISH:
        return None
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return None
    if number != number:  # NaN
        return None
    return number


def parse_period(value: str | None) -> tuple[int | None, int | None]:
    """"2025年第1四半期" -> (2025, 1)。解釈できなければ (None, None)。"""
    if value is None:
        return None, None
    match = _PERIOD_RE.search(str(value))
    if match is None:
        return None, None
    year = int(match.group(1))
    quarter = int(str(match.group(2)).translate(str.maketrans("１２３４", "1234")))
    return year, quarter


def calculate_unit_price(
    unit_price: str | None,
    trade_price: str | None,
    area: str | None,
) -> int | None:
    """㎡単価（円/㎡）。

    基本は UnitPrice。空なら TradePrice / Area で算出する。
    価格 <= 0 / 面積 <= 0 / 単価 <= 0 は欠損として None。
    """
    unit = parse_int(unit_price)
    if unit is not None and unit > 0:
        return unit

    total = parse_int(trade_price)
    size = parse_int(area)
    if total is not None and total > 0 and size is not None and size > 0:
        computed = int(total / size)
        return computed if computed > 0 else None
    return None
