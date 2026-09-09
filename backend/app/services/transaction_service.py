"""実取引土地価格（XIT001）: PostgreSQL 優先・DB ミス時のみ外部 API（cache-aside）。

  real_estate_transactions に対象自治体・対象年の行があれば DB から
  property_type='宅地(土地)' の unit_price 中央値と件数を算出。
  無ければ XIT001 から取得 → 正規化して DB 保存 → 中央値・件数。
"""

from __future__ import annotations

import logging
import statistics
from typing import Any

from sqlalchemy.orm import Session

from app import config
from app.clients.reinfolib_client import ReinfolibClient
from app.repositories.transaction_repository import TransactionRepository
from app.utils.transaction_parser import (
    calculate_unit_price,
    parse_float,
    parse_int,
    parse_period,
)

logger = logging.getLogger(__name__)


class TransactionResult:
    __slots__ = ("price_per_sqm", "sample_count")

    def __init__(self, price_per_sqm: int | None, sample_count: int) -> None:
        self.price_per_sqm = price_per_sqm
        self.sample_count = sample_count


def aggregate_unit_prices(prices: list[int]) -> TransactionResult:
    if not prices:
        return TransactionResult(None, 0)
    return TransactionResult(int(statistics.median(prices)), len(prices))


def build_transaction_rows(
    response: dict[str, Any], municipality_code: str, source: str
) -> list[dict[str, Any]]:
    """XIT001 レスポンスの各取引を real_estate_transactions の行 dict へ正規化する。

    生 JSON は保存しない。必要な項目のみ正規化する。全 Type を保存し、
    集計時に property_type で絞る。
    """
    records = response.get("data", []) if isinstance(response, dict) else []
    rows: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        property_type = record.get("Type")
        if not property_type:
            continue
        code = record.get("MunicipalityCode")
        if code is not None and str(code) != municipality_code:
            continue

        year, quarter = parse_period(record.get("Period"))
        if year is None:
            year = config.TRANSACTION_PRICE_YEAR

        rows.append(
            {
                "municipality_code": municipality_code,
                "transaction_year": year,
                "transaction_quarter": quarter,
                "district_name": record.get("DistrictName") or None,
                "property_type": str(property_type)[:100],
                "trade_price": parse_int(record.get("TradePrice")),
                "area_sqm": parse_float(record.get("Area")),
                "unit_price": calculate_unit_price(
                    record.get("UnitPrice"),
                    record.get("TradePrice"),
                    record.get("Area"),
                ),
                "station_name": record.get("NearestStation") or None,
                "station_minutes": parse_int(record.get("TimeToNearestStation")),
                "source": source,
            }
        )
    return rows


class TransactionService:
    def __init__(self, db: Session, client: ReinfolibClient | None = None) -> None:
        self._repo = TransactionRepository(db)
        self._client = client

    def _get_client(self) -> ReinfolibClient:
        if self._client is None:
            self._client = ReinfolibClient(api_key=config.require_api_key())
        return self._client

    async def get_land_transaction_price(
        self, municipality_code: str
    ) -> TransactionResult:
        year = config.TRANSACTION_PRICE_YEAR
        land_type = config.TRANSACTION_LAND_TYPE

        if self._repo.has_rows(municipality_code, year):
            prices = self._repo.list_unit_prices(municipality_code, year, land_type)
            return aggregate_unit_prices(prices)

        # DB ミス → XIT001 → 正規化して DB 保存
        response = await self._get_client().get_transaction_prices(
            municipality_code, year
        )
        rows = build_transaction_rows(
            response, municipality_code, config.TRANSACTION_PRICE_SOURCE_LABEL
        )
        logger.info(
            "Fetched %d transactions from XIT001 for %s (DB miss)",
            len(rows),
            municipality_code,
        )
        self._repo.replace_rows(municipality_code, year, rows)

        prices = [
            r["unit_price"]
            for r in rows
            if r["property_type"] == land_type
            and r["unit_price"] is not None
            and r["unit_price"] > 0
        ]
        return aggregate_unit_prices(prices)
