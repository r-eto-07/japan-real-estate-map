"""テスト DB へレコードを投入するヘルパー。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import (
    LandPricePoint,
    Municipality,
    RealEstateTransaction,
    RentStatistic,
)

RENT_SOURCE = "e-Stat 令和5年住宅・土地統計調査"
LAND_SOURCE = "国土交通省 地価公示"
TX_SOURCE = "国土交通省 不動産取引価格情報"


def add_municipality(
    db: Session,
    code: str = "12217",
    prefecture: str = "千葉県",
    city: str = "柏市",
) -> None:
    db.add(
        Municipality(
            municipality_code=code,
            prefecture_code=code[:2],
            prefecture_name=prefecture,
            municipality_name=city,
        )
    )
    db.flush()


def add_rent(
    db: Session, code: str = "12217", year: int = 2023, average_rent: int | None = 68200
) -> None:
    db.add(
        RentStatistic(
            municipality_code=code,
            survey_year=year,
            average_rent=average_rent,
            source=RENT_SOURCE,
        )
    )
    db.flush()


def add_land_points(
    db: Session, code: str = "12217", year: int = 2026, prices: list[int] | None = None
) -> None:
    for price in prices or [150000, 165000, 170000]:
        db.add(
            LandPricePoint(
                municipality_code=code,
                survey_year=year,
                price_per_sqm=price,
                latitude=35.86,
                longitude=139.97,
                land_price_type="住宅地",
                source=LAND_SOURCE,
            )
        )
    db.flush()


def add_transactions(
    db: Session,
    code: str = "12217",
    year: int = 2025,
    land_unit_prices: list[int] | None = None,
    include_noise: bool = True,
) -> None:
    for up in land_unit_prices or [100000, 150000, 200000]:
        db.add(
            RealEstateTransaction(
                municipality_code=code,
                transaction_year=year,
                transaction_quarter=1,
                district_name="中央",
                property_type="宅地(土地)",
                trade_price=up * 100,
                area_sqm=100.0,
                unit_price=up,
                source=TX_SOURCE,
            )
        )
    if include_noise:
        db.add(
            RealEstateTransaction(
                municipality_code=code,
                transaction_year=year,
                property_type="宅地(土地と建物)",
                trade_price=54000000,
                area_sqm=220.0,
                unit_price=None,
                source=TX_SOURCE,
            )
        )
    db.flush()
