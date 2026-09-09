"""municipalityCode（N03 由来の 5 桁標準地域コード）を e-Stat の地域コードへ変換する。

コード変換ロジックはここだけに置く（EStatClient / AreaService / Router に書かない）。

現状: e-Stat「統計に用いる標準地域コード」は市区町村が 5 桁で、
Phase 2.5 の municipalityCode（例: 柏市 = "12217"）と一致するため恒等変換。
実際のメタ情報（scripts/inspect_estat_meta.py）で 6 桁など別形式が判明した場合は
この関数だけを修正する。
"""

from __future__ import annotations


def to_estat_area_code(municipality_code: str) -> str:
    return municipality_code.strip()
