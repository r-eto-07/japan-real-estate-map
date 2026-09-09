"""国土交通省「不動産情報ライブラリ」API との HTTP 通信のみを担当する。

  - XPT002: 地価公示ポイント（GeoJSON）
  - XIT001: 不動産取引価格情報

レスポンスの解析や集計はここでは行わない（AreaService / *_service / utils の責務）。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app import config

logger = logging.getLogger(__name__)


class ReinfolibError(Exception):
    """XPT002 呼び出しの失敗（ネットワーク / タイムアウト / 4xx / 5xx など）。"""


class ReinfolibAuthError(ReinfolibError):
    """認証失敗（401 / 403）。API キーに関する詳細は外へ出さない。"""


class ReinfolibRateLimitError(ReinfolibError):
    """レート制限（429）。"""


class ReinfolibClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = config.REINFOLIB_XPT002_URL,
        transaction_url: str = config.REINFOLIB_XIT001_URL,
        timeout: float = config.REINFOLIB_TIMEOUT_SECONDS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._transaction_url = transaction_url
        self._timeout = timeout
        self._transport = transport  # テスト時に httpx.MockTransport を差し込むための口

    async def get_land_price_points(
        self, z: int, x: int, y: int, year: int
    ) -> dict[str, Any]:
        """XYZ タイルと年を指定して地価公示ポイントの GeoJSON を取得する。"""
        params = {
            "response_format": "geojson",
            "z": z,
            "x": x,
            "y": y,
            "year": year,
            "priceClassification": config.LAND_PRICE_CLASSIFICATION,
        }
        # API キーは Ocp-Apim-Subscription-Key ヘッダーで送る（query に含めない）
        headers = {"Ocp-Apim-Subscription-Key": self._api_key}

        logger.info(
            "Requesting Reinfolib XPT002 tile z=%d x=%d y=%d year=%d", z, x, y, year
        )

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(
                    self._base_url, params=params, headers=headers
                )
        except httpx.TimeoutException as exc:
            raise ReinfolibError("Reinfolib request timed out") from exc
        except httpx.HTTPError as exc:
            raise ReinfolibError("Reinfolib request failed") from exc

        if response.status_code in (401, 403):
            raise ReinfolibAuthError("Reinfolib authentication failed")
        if response.status_code == 429:
            raise ReinfolibRateLimitError("Reinfolib rate limit exceeded")
        if response.status_code >= 400:
            raise ReinfolibError(f"Reinfolib returned HTTP {response.status_code}")

        try:
            data: Any = response.json()
        except ValueError as exc:
            raise ReinfolibError("Reinfolib returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise ReinfolibError("Reinfolib returned an unexpected payload")

        feature_count = len(data.get("features", []))
        logger.info("Reinfolib XPT002 returned %d features", feature_count)
        return data

    async def get_transaction_prices(
        self, municipality_code: str, year: int
    ) -> dict[str, Any]:
        """市区町村コードと年を指定して不動産取引価格情報を取得する。

        XIT001 は対象データが無いと HTTP 404 を返す。これは外部 API 障害では
        なく「対象条件のデータなし」なので、空データ相当を返す（例外にしない）。
        """
        params = {
            "year": year,
            "city": municipality_code,
            "priceClassification": config.TRANSACTION_PRICE_CLASSIFICATION,
        }
        headers = {"Ocp-Apim-Subscription-Key": self._api_key}

        logger.info(
            "Requesting Reinfolib XIT001 city=%s year=%d", municipality_code, year
        )

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(
                    self._transaction_url, params=params, headers=headers
                )
        except httpx.TimeoutException as exc:
            raise ReinfolibError("Reinfolib request timed out") from exc
        except httpx.HTTPError as exc:
            raise ReinfolibError("Reinfolib request failed") from exc

        if response.status_code in (401, 403):
            raise ReinfolibAuthError("Reinfolib authentication failed")
        if response.status_code == 429:
            raise ReinfolibRateLimitError("Reinfolib rate limit exceeded")
        if response.status_code == 404:
            logger.info("Reinfolib XIT001 returned 404 (no data) for %s", municipality_code)
            return {"status": "NO_DATA", "data": []}
        if response.status_code >= 400:
            raise ReinfolibError(f"Reinfolib returned HTTP {response.status_code}")

        try:
            data: Any = response.json()
        except ValueError as exc:
            raise ReinfolibError("Reinfolib returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise ReinfolibError("Reinfolib returned an unexpected payload")

        logger.info(
            "Reinfolib XIT001 returned %d records", len(data.get("data", []))
        )
        return data
