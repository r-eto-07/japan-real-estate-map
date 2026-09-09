"""real_estate_transactions テーブルへのアクセス。"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import RealEstateTransaction


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_unit_prices(
        self,
        municipality_code: str,
        transaction_year: int,
        property_type: str,
    ) -> list[int]:
        stmt = select(RealEstateTransaction.unit_price).where(
            RealEstateTransaction.municipality_code == municipality_code,
            RealEstateTransaction.transaction_year == transaction_year,
            RealEstateTransaction.property_type == property_type,
            RealEstateTransaction.unit_price.is_not(None),
            RealEstateTransaction.unit_price > 0,
        )
        return list(self._db.scalars(stmt))

    def has_rows(self, municipality_code: str, transaction_year: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(RealEstateTransaction)
            .where(
                RealEstateTransaction.municipality_code == municipality_code,
                RealEstateTransaction.transaction_year == transaction_year,
            )
        )
        return (self._db.scalar(stmt) or 0) > 0

    def replace_rows(
        self,
        municipality_code: str,
        transaction_year: int,
        rows: Iterable[dict],
    ) -> None:
        """対象自治体・対象年の取引を入れ替える。rows はカラム名の dict。"""
        self._db.query(RealEstateTransaction).filter(
            RealEstateTransaction.municipality_code == municipality_code,
            RealEstateTransaction.transaction_year == transaction_year,
        ).delete(synchronize_session=False)
        self._db.add_all(RealEstateTransaction(**row) for row in rows)
        self._db.flush()
