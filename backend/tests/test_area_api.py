"""Area API / AreaService の統合テスト（Phase 5: PostgreSQL 中心）。"""

from __future__ import annotations

import asyncio

import pytest

from app.clients.estat_client import EStatError
from app.clients.reinfolib_client import ReinfolibError
from app.repositories.land_price_repository import LandPriceRepository
from app.repositories.rent_repository import RentRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.area_service import AreaService
from tests import db_seed
from tests.estat_fixtures import RENT_RESPONSE
from tests.xit001_fixtures import build_xit001_response

PARAMS = {"lat": 35.86, "lon": 139.97}

# XPT002 GeoJSON（city_code 12217 の地点 3 つ + 他自治体 1 つ）
GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.97, 35.86]},
            "properties": {
                "city_code": "12217",
                "u_current_years_price_ja": "150,000(円/㎡)",
                "use_category_name_ja": "住宅地",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.98, 35.87]},
            "properties": {
                "city_code": "12217",
                "u_current_years_price_ja": "165,000(円/㎡)",
                "land_price_type": "宅地",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.99, 35.88]},
            "properties": {
                "city_code": "12217",
                "u_current_years_price_ja": "170,000(円/㎡)",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.70, 35.69]},
            "properties": {
                "city_code": "13104",
                "u_current_years_price_ja": "900,000(円/㎡)",
            },
        },
    ],
}
XIT001_RESPONSE = build_xit001_response(["100000", "150000", "200000"])


class FakeReinfolibClient:
    def __init__(
        self,
        *,
        geojson: dict | None = None,
        transaction: dict | None = None,
        error: Exception | None = None,
    ) -> None:
        self._geojson = geojson if geojson is not None else GEOJSON
        self._transaction = transaction if transaction is not None else XIT001_RESPONSE
        self._error = error
        self.land_calls = 0
        self.tx_calls = 0

    async def get_land_price_points(self, z: int, x: int, y: int, year: int) -> dict:
        self.land_calls += 1
        if self._error is not None:
            raise self._error
        return self._geojson

    async def get_transaction_prices(self, municipality_code: str, year: int) -> dict:
        self.tx_calls += 1
        if self._error is not None:
            raise self._error
        return self._transaction


class FakeEStatClient:
    def __init__(self, response: dict | None = None, *, error: Exception | None = None):
        self._response = response if response is not None else RENT_RESPONSE
        self._error = error
        self.calls = 0

    async def get_rent_data(self, estat_area_code: str | None = None) -> dict:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._response


class ExplodingClient:
    async def get_rent_data(self, *a, **k):
        raise AssertionError("e-Stat must not be called when DB has data")

    async def get_land_price_points(self, *a, **k):
        raise AssertionError("XPT002 must not be called when DB has data")

    async def get_transaction_prices(self, *a, **k):
        raise AssertionError("XIT001 must not be called when DB has data")


# ---------------------------------------------------------------------------
# §50 Integration: DB に投入済みなら Area API が全項目を返す
# ---------------------------------------------------------------------------
def test_area_api_returns_all_from_db(api_client, db) -> None:
    db_seed.add_municipality(db, "12217", "千葉県", "柏市")
    db_seed.add_rent(db, "12217", 2023, 68200)
    db_seed.add_land_points(db, "12217", 2026, [150000, 165000, 170000])
    db_seed.add_transactions(db, "12217", 2025, [100000, 150000, 200000])
    db.commit()

    res = api_client.get("/api/areas/12217", params=PARAMS)

    assert res.status_code == 200
    body = res.json()
    assert body["prefecture"] == "千葉県"
    assert body["city"] == "柏市"
    assert body["averageRent"] == 68200
    assert body["landPricePerSqm"] == 165000  # median
    assert body["landPrice100sqm"] == 16500000
    assert body["landPriceSampleCount"] == 3
    assert body["transactionLandPricePerSqm"] == 150000  # median, 宅地(土地)のみ
    assert body["transactionSampleCount"] == 3
    assert body["transactionPriceYear"] == 2025


def test_area_api_unknown_code_returns_404(api_client, db) -> None:
    res = api_client.get("/api/areas/99999", params=PARAMS)
    assert res.status_code == 404
    assert res.json()["detail"] == "Area not found"


# ---------------------------------------------------------------------------
# §51 DB にデータが揃っていれば外部 API を一切呼ばない
# ---------------------------------------------------------------------------
def test_no_external_api_calls_when_db_is_populated(
    api_client, db, test_session_factory
) -> None:
    db_seed.add_municipality(db, "12217", "千葉県", "柏市")
    db_seed.add_rent(db, "12217", 2023, 68200)
    db_seed.add_land_points(db, "12217", 2026, [150000, 165000, 170000])
    db_seed.add_transactions(db, "12217", 2025, [100000, 150000, 200000])
    db.commit()

    from app.dependencies import get_area_service
    from app.main import app

    exploding = ExplodingClient()

    def _service_override():
        session = test_session_factory()
        try:
            yield AreaService(
                session, reinfolib_client=exploding, estat_client=exploding
            )
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_area_service] = _service_override
    try:
        res = api_client.get("/api/areas/12217", params=PARAMS)
    finally:
        app.dependency_overrides.pop(get_area_service, None)

    assert res.status_code == 200
    body = res.json()
    assert body["averageRent"] == 68200
    assert body["landPricePerSqm"] == 165000
    assert body["transactionLandPricePerSqm"] == 150000


# ---------------------------------------------------------------------------
# §52 DB ミス時のみ外部 API を呼び、結果を DB へ保存する
# ---------------------------------------------------------------------------
def test_db_miss_fetches_from_apis_and_persists(db) -> None:
    db_seed.add_municipality(db, "12217", "千葉県", "柏市")
    db.commit()

    reinfolib = FakeReinfolibClient()
    estat = FakeEStatClient()
    service = AreaService(db, reinfolib_client=reinfolib, estat_client=estat)

    body = asyncio.run(service.get_area("12217", 35.86, 139.97))
    db.commit()

    assert estat.calls == 1
    assert reinfolib.land_calls == 1
    assert reinfolib.tx_calls == 1
    assert body["averageRent"] == 68200
    assert body["landPricePerSqm"] == 165000  # median(150000,165000,170000)
    assert body["landPriceSampleCount"] == 3
    assert body["transactionLandPricePerSqm"] == 150000
    assert body["transactionSampleCount"] == 3

    # DB に保存されている
    assert (
        RentRepository(db).get_by_municipality_and_year("12217", 2023).average_rent
        == 68200
    )
    assert LandPriceRepository(db).has_points("12217", 2026) is True
    assert TransactionRepository(db).has_rows("12217", 2025) is True

    # 2 回目は DB ヒット（外部 API を呼ばない）
    service2 = AreaService(db, reinfolib_client=reinfolib, estat_client=estat)
    asyncio.run(service2.get_area("12217", 35.86, 139.97))
    assert estat.calls == 1
    assert reinfolib.land_calls == 1
    assert reinfolib.tx_calls == 1


# ---------------------------------------------------------------------------
# 外部 API の独立性（§36 相当）: 1 つ落ちても他は返る
# ---------------------------------------------------------------------------
def test_reinfolib_failure_still_returns_rent(db) -> None:
    db_seed.add_municipality(db, "12217", "千葉県", "柏市")
    db.commit()
    service = AreaService(
        db,
        reinfolib_client=FakeReinfolibClient(error=ReinfolibError("down")),
        estat_client=FakeEStatClient(),
    )
    body = asyncio.run(service.get_area("12217", 35.86, 139.97))

    assert body["averageRent"] == 68200
    assert body["landPricePerSqm"] is None
    assert body["landPriceSampleCount"] == 0
    assert body["transactionLandPricePerSqm"] is None


def test_estat_failure_still_returns_land_and_transaction(db) -> None:
    db_seed.add_municipality(db, "12217", "千葉県", "柏市")
    db.commit()
    service = AreaService(
        db,
        reinfolib_client=FakeReinfolibClient(),
        estat_client=FakeEStatClient(error=EStatError("down")),
    )
    body = asyncio.run(service.get_area("12217", 35.86, 139.97))

    assert body["averageRent"] is None
    assert body["rentYear"] == 2023
    assert body["landPricePerSqm"] == 165000
    assert body["transactionLandPricePerSqm"] == 150000


def test_api_health(api_client) -> None:
    body = api_client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["database"] in ("connected", "disconnected")
