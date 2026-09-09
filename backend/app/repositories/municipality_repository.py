"""municipalities テーブルへのアクセス。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Municipality


class MunicipalityRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, municipality_code: str) -> Municipality | None:
        return self._db.get(Municipality, municipality_code)

    def exists(self, municipality_code: str) -> bool:
        stmt = select(Municipality.municipality_code).where(
            Municipality.municipality_code == municipality_code
        )
        return self._db.scalar(stmt) is not None
