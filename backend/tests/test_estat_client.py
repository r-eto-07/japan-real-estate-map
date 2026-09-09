import asyncio

import httpx
import pytest

from app.clients.estat_client import (
    EStatAuthError,
    EStatClient,
    EStatError,
    EStatRateLimitError,
)
from tests.estat_fixtures import RENT_RESPONSE


def _run(coro):
    return asyncio.run(coro)


def _client(handler) -> EStatClient:
    # 本物の e-Stat は呼ばず HTTP 層をモックする
    return EStatClient(app_id="test-app-id", transport=httpx.MockTransport(handler))


def test_success_returns_json() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json=RENT_RESPONSE)

    body = _run(_client(handler).get_rent_data("12217"))

    assert body["GET_STATS_DATA"]["RESULT"]["STATUS"] == 0
    assert "appId=test-app-id" in captured["url"]
    assert "cdArea=12217" in captured["url"]


def test_status_1_no_data_is_not_an_error() -> None:
    # STATUS 1 = 「正常終了だが該当データなし」。エラーにせず body を返す（§19）。
    body = {
        "GET_STATS_DATA": {
            "RESULT": {
                "STATUS": 1,
                "ERROR_MSG": "正常に終了しましたが、該当データはありませんでした。",
            }
        }
    }
    result = _run(_client(lambda r: httpx.Response(200, json=body)).get_rent_data("47381"))
    assert result["GET_STATS_DATA"]["RESULT"]["STATUS"] == 1


def test_status_403_in_body_raises_auth_error() -> None:
    # e-Stat は HTTP 200 でも RESULT.STATUS で認証失敗を返す
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"GET_STATS_DATA": {"RESULT": {"STATUS": 403, "ERROR_MSG": "認証エラー"}}},
        )

    with pytest.raises(EStatAuthError):
        _run(_client(handler).get_rent_data("12217"))


def test_http_429_raises_rate_limit_error() -> None:
    with pytest.raises(EStatRateLimitError):
        _run(_client(lambda r: httpx.Response(429)).get_rent_data("12217"))


def test_http_500_raises_error() -> None:
    with pytest.raises(EStatError):
        _run(_client(lambda r: httpx.Response(500)).get_rent_data("12217"))


def test_timeout_raises_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(EStatError):
        _run(_client(handler).get_rent_data("12217"))
