"""TransactionService（DB 優先 + XIT001 cache-aside）のテスト（§43, §44）。"""

from __future__ import annotations

import asyncio

from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import (
    TransactionService,
    aggregate_unit_prices,
    build_transaction_rows,
)
from tests import db_seed
from tests.xit001_fixtures import build_xit001_response


class FakeReinfolibClient:
    def __init__(self, response: dict) -> None:
        self._response = response
        self.calls = 0

    async def get_transaction_prices(self, municipality_code: str, year: int) -> dict:
        self.calls += 1
        return self._response


# §43: 宅地(土地) 3 件のみ中央値。宅地(土地と建物) 等は除外。
def test_median_of_land_transactions_only_from_db(db) -> None:
    db_seed.add_municipality(db)
    db_seed.add_transactions(db, "12217", 2025, [100000, 150000, 200000])
    db.commit()

    result = asyncio.run(
        TransactionService(db).get_land_transaction_price("12217")
    )
    assert result.price_per_sqm == 150000
    assert result.sample_count == 3


# §44: 外れ値に強い中央値
def test_median_robust_to_outlier(db) -> None:
    db_seed.add_municipality(db)
    db_seed.add_transactions(
        db, "12217", 2025, [100000, 120000, 5000000], include_noise=False
    )
    db.commit()

    result = asyncio.run(
        TransactionService(db).get_land_transaction_price("12217")
    )
    assert result.price_per_sqm == 120000
    assert result.sample_count == 3


def test_db_miss_fetches_from_xit001_and_persists(db) -> None:
    db_seed.add_municipality(db)
    db.commit()
    fake = FakeReinfolibClient(build_xit001_response(["100000", "150000", "200000"]))
    service = TransactionService(db, client=fake)

    result = asyncio.run(service.get_land_transaction_price("12217"))
    db.commit()

    assert fake.calls == 1
    assert result.price_per_sqm == 150000
    assert result.sample_count == 3
    assert TransactionRepository(db).has_rows("12217", 2025) is True

    # 2 回目は DB ヒット
    asyncio.run(TransactionService(db, client=fake).get_land_transaction_price("12217"))
    assert fake.calls == 1


def test_no_transaction_data_returns_zero(db) -> None:
    db_seed.add_municipality(db)
    db.commit()
    fake = FakeReinfolibClient({"status": "NO_DATA", "data": []})
    result = asyncio.run(
        TransactionService(db, client=fake).get_land_transaction_price("12217")
    )
    assert result.price_per_sqm is None
    assert result.sample_count == 0


def test_build_transaction_rows_normalizes_fields() -> None:
    response = {
        "status": "OK",
        "data": [
            {
                "Type": "宅地(土地)",
                "MunicipalityCode": "12217",
                "DistrictName": "西口",
                "TradePrice": "18000000",
                "Area": "100",
                "UnitPrice": "",
                "Period": "2025年第2四半期",
            }
        ],
    }
    rows = build_transaction_rows(response, "12217", "src")
    assert len(rows) == 1
    row = rows[0]
    assert row["property_type"] == "宅地(土地)"
    assert row["transaction_year"] == 2025
    assert row["transaction_quarter"] == 2
    assert row["district_name"] == "西口"
    assert row["unit_price"] == 180000  # TradePrice / Area フォールバック
    assert row["area_sqm"] == 100.0


def test_aggregate_unit_prices_empty() -> None:
    result = aggregate_unit_prices([])
    assert result.price_per_sqm is None
    assert result.sample_count == 0
