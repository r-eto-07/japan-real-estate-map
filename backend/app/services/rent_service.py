"""平均家賃（e-Stat）: PostgreSQL 優先・DB ミス時のみ外部 API（cache-aside）。

  rent_statistics に (municipality_code, survey_year) の行があれば DB の値を返す
  （average_rent が NULL の行も「取得済み・データなし」として扱い再取得しない）。
  行が無ければ e-Stat から取得 → UPSERT → 値を返す。
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app import config
from app.clients.estat_client import EStatClient
from app.parsers.estat_rent_parser import extract_average_rent
from app.repositories.rent_repository import RentRepository
from app.utils.estat_area_code import to_estat_area_code

logger = logging.getLogger(__name__)


class RentService:
    def __init__(self, db: Session, client: EStatClient | None = None) -> None:
        self._repo = RentRepository(db)
        self._client = client

    def _get_client(self) -> EStatClient:
        if self._client is None:
            self._client = EStatClient(app_id=config.require_estat_app_id())
        return self._client

    async def get_average_rent(self, municipality_code: str) -> int | None:
        year = config.ESTAT_RENT_YEAR

        row = self._repo.get_by_municipality_and_year(municipality_code, year)
        if row is not None:
            return row.average_rent

        # DB ミス → e-Stat → UPSERT
        response = await self._get_client().get_rent_data(
            to_estat_area_code(municipality_code)
        )
        rent = extract_average_rent(response, municipality_code)
        logger.info(
            "Fetched rent from e-Stat for %s (DB miss): %s", municipality_code, rent
        )
        self._repo.upsert(
            municipality_code, year, rent, config.ESTAT_RENT_SOURCE_LABEL
        )
        return rent
