"""「165,000(円/㎡)」形式の文字列を整数（円/㎡）へ変換する。

文字列解析ロジックは Service / Router に直接書かず、ここに閉じ込める。
"""

from __future__ import annotations

import re

_NUMBER_RE = re.compile(r"\d+")


def parse_yen_per_sqm(value: str | None) -> int | None:
    """先頭の数値部分を円/㎡の整数として返す。数値が無い / None / 空文字は None。

    >>> parse_yen_per_sqm("165,000(円/㎡)")
    165000
    >>> parse_yen_per_sqm("3,100,000(円/㎡)")
    3100000
    >>> parse_yen_per_sqm("") is None
    True
    >>> parse_yen_per_sqm(None) is None
    True
    """
    if value is None:
        return None
    match = _NUMBER_RE.search(value.replace(",", ""))
    if match is None:
        return None
    return int(match.group())
