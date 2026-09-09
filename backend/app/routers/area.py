"""/api/areas ルーター。

router は HTTP の入出力だけを担当し、データ取得・SQL は AreaService / Repository に委譲する。
外部 API（e-Stat / XPT002 / XIT001）の失敗は Service 側で独立に握りつぶし null 化するため、
ここは 404 のみ扱う。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_area_service
from app.schemas.area import AreaResponse
from app.services.area_service import AreaNotFound, AreaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/areas", tags=["areas"])


@router.get("/{municipality_code}", response_model=AreaResponse)
async def get_area(
    municipality_code: str,
    lat: float = Query(..., ge=-90.0, le=90.0, description="クリック地点の緯度"),
    lon: float = Query(..., ge=-180.0, le=180.0, description="クリック地点の経度"),
    service: AreaService = Depends(get_area_service),
) -> AreaResponse:
    try:
        area = await service.get_area(municipality_code, lat, lon)
    except AreaNotFound:
        raise HTTPException(status_code=404, detail="Area not found")

    return AreaResponse(**area)
