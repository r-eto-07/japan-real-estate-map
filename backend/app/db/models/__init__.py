"""全モデルをここで import して Base.metadata に登録する（Alembic 用）。"""

from app.db.models.land_price_point import LandPricePoint
from app.db.models.municipality import Municipality
from app.db.models.rent_statistic import RentStatistic
from app.db.models.transaction import RealEstateTransaction

__all__ = [
    "Municipality",
    "RentStatistic",
    "LandPricePoint",
    "RealEstateTransaction",
]
