"""FastAPI 依存関係。"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.area_service import AreaService

__all__ = ["get_db", "get_area_service"]


def get_area_service(db: Session = Depends(get_db)) -> AreaService:
    return AreaService(db)
