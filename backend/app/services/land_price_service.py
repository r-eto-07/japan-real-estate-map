"""地価公示（XPT002）: PostgreSQL 優先・DB ミス時のみ外部 API（cache-aside）。

  land_price_points に対象自治体・対象年の地点があれば DB から中央値を算出。
  無ければ XPT002（クリック地点のタイル）から取得 → DB 保存 → 中央値。
"""

from __future__ import annotations

import logging
import statistics

from sqlalchemy.orm import Session

from app import config
from app.clients.reinfolib_client import ReinfolibClient
from app.parsers.land_price_parser import extract_land_points
from app.repositories.land_price_repository import (
    LandPricePointInput,
    LandPriceRepository,
)
from app.utils.tile import latlon_to_tile

logger = logging.getLogger(__name__)


class LandPriceResult:
    __slots__ = ("price_per_sqm", "sample_count")

    def __init__(self, price_per_sqm: int | None, sample_count: int) -> None:
        self.price_per_sqm = price_per_sqm
        self.sample_count = sample_count


def aggregate_prices(prices: list[int]) -> int | None:
    """外れ値に強い中央値。"""
    if not prices:
        return None
    return int(statistics.median(prices))


class LandPriceService:
    def __init__(self, db: Session, client: ReinfolibClient | None = None) -> None:
        self._repo = LandPriceRepository(db)
        self._client = client

    def _get_client(self) -> ReinfolibClient:
        if self._client is None:
            self._client = ReinfolibClient(api_key=config.require_api_key())
        return self._client

    async def get_land_price(
        self, municipality_code: str, lat: float, lon: float
    ) -> LandPriceResult:
        year = config.LAND_PRICE_YEAR

        prices = self._repo.list_prices(municipality_code, year)
        if prices:
            return LandPriceResult(aggregate_prices(prices), len(prices))

        # DB ミス → XPT002（クリック地点のタイル）→ DB 保存
        zoom = config.LAND_PRICE_TILE_ZOOM
        x, y = latlon_to_tile(lat, lon, zoom)
        geojson = await self._get_client().get_land_price_points(zoom, x, y, year)
        points = extract_land_points(geojson, municipality_code)
        logger.info(
            "Fetched %d land price points from XPT002 for %s (DB miss)",
            len(points),
            municipality_code,
        )
        self._repo.replace_points(
            municipality_code,
            year,
            (
                LandPricePointInput(
                    price_per_sqm=p.price_per_sqm,
                    latitude=p.latitude,
                    longitude=p.longitude,
                    land_price_type=p.land_price_type,
                )
                for p in points
            ),
            source=config.LAND_PRICE_SOURCE_LABEL,
        )
        values = [p.price_per_sqm for p in points]
        return LandPriceResult(aggregate_prices(values), len(values))
