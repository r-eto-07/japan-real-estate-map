"""緯度経度 → XYZ タイル座標（Web Mercator / スリッピーマップ方式）の変換。"""

from __future__ import annotations

import math

# Web Mercator で扱える緯度の上限。これを超える値はここでクランプする。
_MAX_LATITUDE = 85.05112878


def latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """指定ズームでの (x, y) タイル座標を返す。

    範囲外の緯度経度はタイル格子内に収まるようクランプする。
    """
    lat = max(min(lat, _MAX_LATITUDE), -_MAX_LATITUDE)
    lon = max(min(lon, 180.0), -180.0)

    n = 2**zoom
    x = int((lon + 180.0) / 360.0 * n)

    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

    x = min(max(x, 0), n - 1)
    y = min(max(y, 0), n - 1)
    return x, y
