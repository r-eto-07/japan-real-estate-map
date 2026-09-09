"""prepare_municipalities.py の純粋関数（geopandas に依存しない部分）。

単体テストしやすいよう分離している。
"""

from __future__ import annotations


def parse_prefectures(spec: str) -> list[int]:
    """"1-47" / "13,27,47" / "1-5,13" のような指定を都道府県コードのリストへ。"""
    result: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = (int(v) for v in part.split("-", 1))
            result.extend(range(lo, hi + 1))
        else:
            result.append(int(part))
    return sorted({p for p in result if 1 <= p <= 47})


def _clean(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value != value:  # NaN
        return ""
    return str(value).strip()


def municipality_name(name: object, ward: object) -> str:
    """N03_004（市区町村名）と N03_005（政令市の行政区名）から表示名を作る。

    - 政令指定都市の行政区: N03_004="横浜市" + N03_005="西区" -> 「横浜市西区」
    - 東京 23 区: N03_004="千代田区"（N03_005 なし） -> 「千代田区」
    - 通常の市町村: N03_004="八王子市" / "檜原村" をそのまま使う
    """
    name_s = _clean(name)
    ward_s = _clean(ward)
    return f"{name_s}{ward_s}" if ward_s else name_s
