from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Municipality(Base, TimestampMixin):
    """全国市区町村マスタ（N03 由来。scripts/import_municipalities.py で投入）。"""

    __tablename__ = "municipalities"

    municipality_code: Mapped[str] = mapped_column(String(5), primary_key=True)
    prefecture_code: Mapped[str | None] = mapped_column(String(2))
    prefecture_name: Mapped[str] = mapped_column(String(50), nullable=False)
    municipality_name: Mapped[str] = mapped_column(String(100), nullable=False)
