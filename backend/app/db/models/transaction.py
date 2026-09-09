from __future__ import annotations

from sqlalchemy import BigInteger, Double, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RealEstateTransaction(Base, TimestampMixin):
    """不動産取引価格情報の 1 取引（XIT001 由来）。正規化して保存する。"""

    __tablename__ = "real_estate_transactions"
    __table_args__ = (
        Index(
            "ix_real_estate_transactions_muni_year",
            "municipality_code",
            "transaction_year",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    municipality_code: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("municipalities.municipality_code"),
        nullable=False,
    )
    transaction_year: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_quarter: Mapped[int | None] = mapped_column(Integer)
    district_name: Mapped[str | None] = mapped_column(String(255))
    property_type: Mapped[str] = mapped_column(String(100), nullable=False)
    trade_price: Mapped[int | None] = mapped_column(BigInteger)
    area_sqm: Mapped[float | None] = mapped_column(Double)
    unit_price: Mapped[int | None] = mapped_column(Integer)
    station_name: Mapped[str | None] = mapped_column(String(255))
    station_minutes: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
