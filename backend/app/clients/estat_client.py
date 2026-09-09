"""e-Stat API 3.0（getStatsData）との HTTP 通信のみを担当する。

レスポンスの解析（家賃の抽出）は estat_rent_parser の責務。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app import config

logger = logging.getLogger(__name__)


class EStatError(Exception):
    """e-Stat 呼び出しの失敗（ネットワーク / タイムアウト / 5xx / STATUS 異常）。"""


class EStatAuthError(EStatError):
    """認証失敗（appId 不正）。appId に関する詳細は外へ出さない。"""


class EStatRateLimitError(EStatError):
    """レート制限（429）。"""


class EStatClient:
    def __init__(
        self,
        app_id: str,
        *,
        base_url: str = config.ESTAT_GETSTATSDATA_URL,
        stats_data_id: str = config.ESTAT_STATS_DATA_ID_RENT,
        timeout: float = config.ESTAT_TIMEOUT_SECONDS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._app_id = app_id
        self._base_url = base_url
        self._stats_data_id = stats_data_id
        self._timeout = timeout
        self._transport = transport  # テスト時に httpx.MockTransport を差し込む口

    async def get_rent_data(
        self, estat_area_code: str | None = None
    ) -> dict[str, Any]:
        """統計表 JSON を取得する。

        estat_area_code を渡すとその地域だけに絞り込む。None（一括取得用）なら
        全地域を返す。いずれもメタ情報（CLASS_INF）付き。対象分類の選択は
        parser 側でメタの名称から解決する（コードを推測で固定しない）。
        """
        params = {
            "appId": self._app_id,
            "statsDataId": self._stats_data_id,
            "lang": "J",
            "metaGetFlg": "Y",
            "cntGetFlg": "N",
        }
        if estat_area_code is not None:
            params["cdArea"] = estat_area_code

        logger.info(
            "Requesting e-Stat rent data area=%s statsDataId=%s",
            estat_area_code or "(all)",
            self._stats_data_id,
        )

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(self._base_url, params=params)
        except httpx.TimeoutException as exc:
            raise EStatError("e-Stat request timed out") from exc
        except httpx.HTTPError as exc:
            raise EStatError("e-Stat request failed") from exc

        if response.status_code == 429:
            raise EStatRateLimitError("e-Stat rate limit exceeded")
        if response.status_code in (401, 403):
            raise EStatAuthError("e-Stat authentication failed")
        if response.status_code >= 400:
            raise EStatError(f"e-Stat returned HTTP {response.status_code}")

        try:
            body: Any = response.json()
        except ValueError as exc:
            raise EStatError("e-Stat returned invalid JSON") from exc
        if not isinstance(body, dict):
            raise EStatError("e-Stat returned an unexpected payload")

        # e-Stat は HTTP 200 でも RESULT.STATUS で結果を返す。
        #   0 = 正常終了（データあり）
        #   1 = 正常終了だが該当データなし  → エラーではない（§19）。
        #        データの有無は parser 側で判断する（該当自治体が無ければ None）。
        #   403 = 認証エラー / 100 以上 = 実エラー
        result = (body.get("GET_STATS_DATA") or {}).get("RESULT") or {}
        status = result.get("STATUS")
        if status not in (0, 1, "0", "1", None):
            message = result.get("ERROR_MSG", "")
            if str(status) == "403":
                raise EStatAuthError("e-Stat authentication failed")
            raise EStatError(f"e-Stat status {status}: {message}")

        return body
