"""テスト用の XIT001（不動産取引価格情報）レスポンス（本物の API は呼ばない）。"""

from __future__ import annotations

from typing import Any

MUNICIPALITY = "12217"


def _record(
    type_: str,
    *,
    unit_price: str = "",
    trade_price: str = "",
    area: str = "",
    district: str = "中央",
    code: str = MUNICIPALITY,
) -> dict[str, Any]:
    return {
        "Type": type_,
        "MunicipalityCode": code,
        "DistrictName": district,
        "TradePrice": trade_price,
        "Area": area,
        "UnitPrice": unit_price,
        "Period": "2025年第1四半期",
        "PriceCategory": "不動産取引価格情報",
    }


def build_xit001_response(
    land_unit_prices: list[str],
    *,
    include_noise: bool = True,
) -> dict[str, Any]:
    """宅地(土地) の UnitPrice リストからレスポンスを組む。

    include_noise=True で「宅地(土地と建物)」「中古マンション等」も混ぜる
    （TransactionService が正しく絞れることの確認用）。
    """
    data: list[dict[str, Any]] = [
        _record("宅地(土地)", unit_price=up) for up in land_unit_prices
    ]
    if include_noise:
        data.append(_record("宅地(土地と建物)", trade_price="54000000", area="220"))
        data.append(_record("中古マンション等", trade_price="30000000", area="70"))
        data.append(_record("農地", trade_price="5000000", area="1000"))
    return {"status": "OK", "data": data}


# §43: 100000 / 150000 / 200000（宅地土地）+ 900000（宅地土地と建物）→ median 150000, count 3
RESPONSE_THREE_LAND = build_xit001_response(["100000", "150000", "200000"])
