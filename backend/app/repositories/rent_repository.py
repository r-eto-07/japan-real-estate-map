"""rent_statistics テーブルへのアクセス。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import RentStatistic


class RentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_municipality_and_year(
        self, municipality_code: str, survey_year: int
    ) -> RentStatistic | None:
        stmt = select(RentStatistic).where(
            RentStatistic.municipality_code == municipality_code,
            RentStatistic.survey_year == survey_year,
        )
        return self._db.scalars(stmt).first()

    def upsert(
        self,
        municipality_code: str,
        survey_year: int,
        average_rent: int | None,
        source: str,
    ) -> None:
        """(municipality_code, survey_year) をキーに INSERT または UPDATE。"""
        stmt = insert(RentStatistic).values(
            municipality_code=municipality_code,
            survey_year=survey_year,
            average_rent=average_rent,
            source=source,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_rent_statistics_muni_year",
            set_={"average_rent": average_rent, "source": source},
        )
        self._db.execute(stmt)
        # Core の UPSERT は identity map を更新しないため、
        # 同一 Session での後続 get() が古い値を返さないよう期限切れにする。
        self._db.expire_all()
