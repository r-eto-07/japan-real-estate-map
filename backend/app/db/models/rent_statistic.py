from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RentStatistic(Base, TimestampMixin):
    """市区町村別の平均家賃（e-Stat 住宅・土地統計調査）。"""

    __tablename__ = "rent_statistics"
    __table_args__ = (
        UniqueConstraint(
            "municipality_code", "survey_year", name="uq_rent_statistics_muni_year"
        ),
        Index("ix_rent_statistics_muni_year", "municipality_code", "survey_year"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    municipality_code: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("municipalities.municipality_code"),
        nullable=False,
    )
    survey_year: Mapped[int] = mapped_column(Integer, nullable=False)
    average_rent: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
