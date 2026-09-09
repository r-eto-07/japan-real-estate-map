"""land_price_points テーブルへのアクセス。中央値ではなく地点そのものを保存する。"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import LandPricePoint


class LandPricePointInput:
    __slots__ = ("price_per_sqm", "latitude", "longitude", "land_price_type")

    def __init__(
        self,
        price_per_sqm: int,
        latitude: float | None = None,
        longitude: float | None = None,
        land_price_type: str | None = None,
    ) -> None:
        self.price_per_sqm = price_per_sqm
        self.latitude = latitude
        self.longitude = longitude
        self.land_price_type = land_price_type


class LandPriceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_prices(
        self, municipality_code: str, survey_year: int
    ) -> list[int]:
        stmt = select(LandPricePoint.price_per_sqm).where(
            LandPricePoint.municipality_code == municipality_code,
            LandPricePoint.survey_year == survey_year,
        )
        return list(self._db.scalars(stmt))

    def has_points(self, municipality_code: str, survey_year: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(LandPricePoint)
            .where(
                LandPricePoint.municipality_code == municipality_code,
                LandPricePoint.survey_year == survey_year,
            )
        )
        return (self._db.scalar(stmt) or 0) > 0

    def replace_points(
        self,
        municipality_code: str,
        survey_year: int,
        points: Iterable[LandPricePointInput],
        source: str,
    ) -> None:
        """対象自治体・対象年の地点を入れ替える（再取得時の重複を防ぐ）。"""
        self._db.query(LandPricePoint).filter(
            LandPricePoint.municipality_code == municipality_code,
            LandPricePoint.survey_year == survey_year,
        ).delete(synchronize_session=False)
        self._db.add_all(
            LandPricePoint(
                municipality_code=municipality_code,
                survey_year=survey_year,
                price_per_sqm=p.price_per_sqm,
                latitude=p.latitude,
                longitude=p.longitude,
                land_price_type=p.land_price_type,
                source=source,
            )
            for p in points
        )
        self._db.flush()
