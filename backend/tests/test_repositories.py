"""Repository 層のテスト（§47-49）。"""

from __future__ import annotations

from app.repositories.land_price_repository import (
    LandPricePointInput,
    LandPriceRepository,
)
from app.repositories.municipality_repository import MunicipalityRepository
from app.repositories.rent_repository import RentRepository
from app.repositories.transaction_repository import TransactionRepository
from tests import db_seed


def test_municipality_repository_get(db) -> None:
    db_seed.add_municipality(db, "12217", "千葉県", "柏市")

    row = MunicipalityRepository(db).get("12217")

    assert row is not None
    assert row.prefecture_name == "千葉県"
    assert row.municipality_name == "柏市"
    assert MunicipalityRepository(db).get("99999") is None


def test_rent_repository_get_and_upsert(db) -> None:
    db_seed.add_municipality(db)
    repo = RentRepository(db)

    repo.upsert("12217", 2023, 68200, db_seed.RENT_SOURCE)
    row = repo.get_by_municipality_and_year("12217", 2023)
    assert row is not None and row.average_rent == 68200

    # 同一キーの再 UPSERT は重複せず更新
    repo.upsert("12217", 2023, 70000, db_seed.RENT_SOURCE)
    assert repo.get_by_municipality_and_year("12217", 2023).average_rent == 70000
    assert repo.get_by_municipality_and_year("12217", 2022) is None


def test_land_price_repository_filters_by_muni_and_year(db) -> None:
    db_seed.add_municipality(db, "12217")
    db_seed.add_municipality(db, "13104", "東京都", "新宿区")
    db_seed.add_land_points(db, "12217", 2026, [150000, 170000, 200000])
    db_seed.add_land_points(db, "12217", 2025, [90000])
    db_seed.add_land_points(db, "13104", 2026, [900000])

    repo = LandPriceRepository(db)
    assert sorted(repo.list_prices("12217", 2026)) == [150000, 170000, 200000]
    assert repo.has_points("12217", 2026) is True
    assert repo.has_points("12217", 2024) is False


def test_land_price_repository_replace_points(db) -> None:
    db_seed.add_municipality(db)
    repo = LandPriceRepository(db)
    repo.replace_points(
        "12217", 2026, [LandPricePointInput(100000), LandPricePointInput(200000)], "x"
    )
    repo.replace_points("12217", 2026, [LandPricePointInput(300000)], "x")
    assert repo.list_prices("12217", 2026) == [300000]


def test_transaction_repository_filters_by_muni_year_type(db) -> None:
    db_seed.add_municipality(db, "12217")
    db_seed.add_transactions(db, "12217", 2025, [100000, 150000, 200000])

    repo = TransactionRepository(db)
    prices = repo.list_unit_prices("12217", 2025, "宅地(土地)")
    assert sorted(prices) == [100000, 150000, 200000]  # 宅地(土地と建物) は含まれない
    assert repo.has_rows("12217", 2025) is True
    assert repo.list_unit_prices("12217", 2024, "宅地(土地)") == []
