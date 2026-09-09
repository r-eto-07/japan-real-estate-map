"""API レスポンスモデル。

レスポンスは dict のまま返さず、必ずこの Pydantic モデルを通す。
"""

from pydantic import BaseModel


class AreaResponse(BaseModel):
    municipalityCode: str
    prefecture: str
    city: str

    # 平均家賃: e-Stat 令和5年住宅・土地統計調査（2023 年・市区町村単位の借家平均家賃）
    # データが無い市区町村は averageRent=null（rentYear / rentSource は常に返す）
    averageRent: int | None = None
    rentYear: int | None = None
    rentSource: str | None = None

    # クリック地点周辺タイル内・同一市区町村の地価公示地点の中央値（円/㎡）
    landPricePerSqm: int | None = None
    landPrice100sqm: int | None = None

    landPriceSource: str | None = None
    landPriceYear: int | None = None
    landPriceSampleCount: int

    # 市区町村内の宅地(土地)取引の㎡単価中央値（国土交通省 XIT001 / 不動産取引価格情報）
    # クリック地点そのものの価格ではなく市区町村単位の集計値
    transactionLandPricePerSqm: int | None = None
    transactionLandPrice100sqm: int | None = None
    transactionSampleCount: int = 0
    transactionPriceYear: int | None = None
    transactionPriceSource: str | None = None
