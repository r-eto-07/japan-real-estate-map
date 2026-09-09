"""市区町村の基本情報 + 家賃 + 地価公示 + 実取引を統合する層。

Phase 5: 通常の画面操作は PostgreSQL を参照する。
  AreaService
    ├ MunicipalityRepository        … 自治体名称（DB）
    ├ RentService                   … 家賃（DB 優先・ミス時 e-Stat → DB 保存）
    ├ LandPriceService             … 地価公示（DB 優先・ミス時 XPT002 → DB 保存）
    └ TransactionService           … 実取引（DB 優先・ミス時 XIT001 → DB 保存）

3 つの外部データソースは独立。どれか 1 つが落ちても他は返す
（該当項目のみ null / sampleCount 0。画面全体を 500 にしない）。
中央値・100㎡換算・公示地価比などの表示用計算はここで都度行い、DB へは保存しない。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app import config
from app.clients.estat_client import EStatClient, EStatError
from app.clients.reinfolib_client import ReinfolibClient, ReinfolibError
from app.config import ConfigError
from app.repositories.municipality_repository import MunicipalityRepository
from app.services.land_price_service import LandPriceResult, LandPriceService
from app.services.rent_service import RentService
from app.services.transaction_service import TransactionResult, TransactionService

logger = logging.getLogger(__name__)


class AreaNotFound(Exception):
    """municipalities テーブルに市区町村コードが存在しない場合に送出。"""


class AreaService:
    def __init__(
        self,
        db: Session,
        *,
        reinfolib_client: ReinfolibClient | None = None,
        estat_client: EStatClient | None = None,
    ) -> None:
        self._municipalities = MunicipalityRepository(db)
        self._rent = RentService(db, client=estat_client)
        self._land = LandPriceService(db, client=reinfolib_client)
        self._transaction = TransactionService(db, client=reinfolib_client)

    async def _safe_rent(self, municipality_code: str) -> int | None:
        try:
            return await self._rent.get_average_rent(municipality_code)
        except (EStatError, ConfigError) as exc:
            logger.warning(
                "Rent fetch failed for %s: %s", municipality_code, type(exc).__name__
            )
            return None

    async def _safe_land(
        self, municipality_code: str, lat: float, lon: float
    ) -> LandPriceResult:
        try:
            return await self._land.get_land_price(municipality_code, lat, lon)
        except (ReinfolibError, ConfigError) as exc:
            logger.warning(
                "Land price fetch failed for %s: %s",
                municipality_code,
                type(exc).__name__,
            )
            return LandPriceResult(None, 0)

    async def _safe_transaction(self, municipality_code: str) -> TransactionResult:
        try:
            return await self._transaction.get_land_transaction_price(municipality_code)
        except (ReinfolibError, ConfigError) as exc:
            logger.warning(
                "Transaction fetch failed for %s: %s",
                municipality_code,
                type(exc).__name__,
            )
            return TransactionResult(None, 0)

    async def get_area(
        self, municipality_code: str, lat: float, lon: float
    ) -> dict[str, Any]:
        base = self._municipalities.get(municipality_code)
        if base is None:
            raise AreaNotFound(municipality_code)

        rent = await self._safe_rent(municipality_code)
        land = await self._safe_land(municipality_code, lat, lon)
        transaction = await self._safe_transaction(municipality_code)

        has_land = land.price_per_sqm is not None
        has_transaction = transaction.price_per_sqm is not None

        return {
            "municipalityCode": municipality_code,
            "prefecture": base.prefecture_name,
            "city": base.municipality_name,
            "averageRent": rent,
            "rentYear": config.ESTAT_RENT_YEAR,
            "rentSource": config.ESTAT_RENT_SOURCE_LABEL,
            "landPricePerSqm": land.price_per_sqm,
            "landPrice100sqm": land.price_per_sqm * 100 if has_land else None,
            "landPriceSource": config.LAND_PRICE_SOURCE_LABEL if has_land else None,
            "landPriceYear": config.LAND_PRICE_YEAR if has_land else None,
            "landPriceSampleCount": land.sample_count,
            "transactionLandPricePerSqm": transaction.price_per_sqm,
            "transactionLandPrice100sqm": (
                transaction.price_per_sqm * 100 if has_transaction else None
            ),
            "transactionSampleCount": transaction.sample_count,
            "transactionPriceYear": (
                config.TRANSACTION_PRICE_YEAR if has_transaction else None
            ),
            "transactionPriceSource": (
                config.TRANSACTION_PRICE_SOURCE_LABEL if has_transaction else None
            ),
        }
