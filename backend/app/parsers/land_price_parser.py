"""XPT002 GeoJSON から、指定市区町村の地価公示「地点」を取り出す。

中央値ではなく地点そのもの（価格・座標・用途）を返す。中央値は Service で算出する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.utils.price_parser import parse_yen_per_sqm


@dataclass(frozen=True)
class LandPoint:
    price_per_sqm: int
    latitude: float | None
    longitude: float | None
    land_price_type: str | None


def extract_land_points(
    geojson: dict[str, Any], municipality_code: str
) -> list[LandPoint]:
    features = geojson.get("features", []) if isinstance(geojson, dict) else []
    points: list[LandPoint] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties") or {}
        if str(properties.get("city_code")) != municipality_code:
            continue
        price = parse_yen_per_sqm(properties.get("u_current_years_price_ja"))
        if price is None or price <= 0:
            continue

        lon, lat = _coordinates(feature.get("geometry"))
        land_type = (
            properties.get("land_price_type")
            or properties.get("use_category_name_ja")
            or None
        )
        if land_type is not None:
            land_type = str(land_type)[:50]

        points.append(
            LandPoint(
                price_per_sqm=price,
                latitude=lat,
                longitude=lon,
                land_price_type=land_type,
            )
        )
    return points


def _coordinates(geometry: Any) -> tuple[float | None, float | None]:
    if not isinstance(geometry, dict):
        return None, None
    coords = geometry.get("coordinates")
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None, None
    return None, None
