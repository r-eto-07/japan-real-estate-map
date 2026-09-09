"""e-Stat getStatsData レスポンスから市区町村の平均家賃を抽出する。

レスポンス構造:
  GET_STATS_DATA -> STATISTICAL_DATA -> CLASS_INF.CLASS_OBJ  … 分類定義（id / code / name）
                                    -> DATA_INF.VALUE         … 統計値（@area/@cat.. と "$"）

対象分類（住宅の種類=総数 / 住宅の家賃の平均=家賃0円を含まない / 時間=調査年）の
コードは推測で固定せず、CLASS_INF の「名称」から解決する。
"""

from __future__ import annotations

from typing import Any

from app import config
from app.utils.estat_area_code import to_estat_area_code

_NULLISH = {"", "-", "‐", "－", "―", "***", "…", "x", "X", "*"}


def parse_rent_value(raw: Any) -> int | None:
    """e-Stat の値文字列を円の整数へ。数値でない / 空 / "-" / None は None。NaN は返さない。"""
    if raw is None:
        return None
    text = str(raw).strip()
    if text in _NULLISH:
        return None
    try:
        value = float(text.replace(",", ""))
    except ValueError:
        return None
    if value != value:  # NaN
        return None
    return int(round(value))


def _as_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _find_id_and_code(
    class_objs: list[dict[str, Any]], name_contains: str
) -> tuple[str | None, str | None]:
    """CLASS_OBJ 群から、CLASS 名称に name_contains を含む分類の (@id, @code) を返す。"""
    for obj in class_objs:
        for cls in _as_list(obj.get("CLASS")):
            if name_contains in (cls.get("@name") or ""):
                return obj.get("@id"), cls.get("@code")
    return None, None


def extract_average_rent(
    response: dict[str, Any], municipality_code: str
) -> int | None:
    """指定市区町村の「総数・家賃0円を含まない」平均家賃（円）。無ければ None。"""
    try:
        statistical_data = response["GET_STATS_DATA"]["STATISTICAL_DATA"]
        class_objs = _as_list(statistical_data["CLASS_INF"]["CLASS_OBJ"])
        values = _as_list(statistical_data["DATA_INF"]["VALUE"])
    except (KeyError, TypeError):
        return None
    if not class_objs or not values:
        return None

    # 対象分類のコードをメタの名称から解決する
    filters: dict[str, str | None] = {}
    for name in (config.ESTAT_RENT_HOUSING_TYPE_MATCH, config.ESTAT_RENT_AVERAGE_MATCH):
        obj_id, code = _find_id_and_code(class_objs, name)
        if obj_id is not None:
            filters[obj_id] = code
    # 時間軸に調査年が複数あれば、調査年（例: 2023）に一致するものへ絞る
    time_id, time_code = _find_id_and_code(class_objs, str(config.ESTAT_RENT_YEAR))
    if time_id is not None:
        filters[time_id] = time_code

    area_code = to_estat_area_code(municipality_code)

    for value in values:
        if value.get("@area") != area_code:
            continue
        if any(value.get(f"@{obj_id}") != code for obj_id, code in filters.items()):
            continue
        return parse_rent_value(value.get("$"))
    return None
