from __future__ import annotations

from sqlalchemy import BigInteger, Double, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LandPricePoint(Base, TimestampMixin):
    """地価公示の地点データ（XPT002 由来）。中央値ではなく地点そのものを保存する。"""

    __tablename__ = "land_price_points"
    __table_args__ = (
        Index("ix_land_price_points_muni_year", "municipality_code", "survey_year"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    municipality_code: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("municipalities.municipality_code"),
        nullable=False,
    )
    survey_year: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_sqm: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Double)
    longitude: Mapped[float | None] = mapped_column(Double)
    land_price_type: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str] = mapped_column(String(255), nullable=False)
