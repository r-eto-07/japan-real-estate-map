import asyncio

import httpx
import pytest

from app.clients.reinfolib_client import (
    ReinfolibAuthError,
    ReinfolibClient,
    ReinfolibError,
    ReinfolibRateLimitError,
)


def _run(coro):
    return asyncio.run(coro)


def _client(handler) -> ReinfolibClient:
    # 本物の国交省 API は呼ばず、HTTP 層をモックする
    return ReinfolibClient(api_key="test-key", transport=httpx.MockTransport(handler))


def test_success_returns_geojson() -> None:
    captured: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Ocp-Apim-Subscription-Key")
        return httpx.Response(
            200, json={"type": "FeatureCollection", "features": [{"a": 1}]}
        )

    result = _run(_client(handler).get_land_price_points(13, 7274, 3226, 2026))

    assert result["type"] == "FeatureCollection"
    assert captured["auth"] == "test-key"
    assert "z=13" in (captured["url"] or "")
    assert "test-key" not in (captured["url"] or "")  # キーは query に出さない


def test_401_raises_auth_error() -> None:
    with pytest.raises(ReinfolibAuthError):
        _run(_client(lambda r: httpx.Response(401)).get_land_price_points(13, 1, 1, 2026))


def test_429_raises_rate_limit_error() -> None:
    with pytest.raises(ReinfolibRateLimitError):
        _run(_client(lambda r: httpx.Response(429)).get_land_price_points(13, 1, 1, 2026))


def test_500_raises_error() -> None:
    with pytest.raises(ReinfolibError):
        _run(_client(lambda r: httpx.Response(500)).get_land_price_points(13, 1, 1, 2026))


def test_timeout_raises_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(ReinfolibError):
        _run(_client(handler).get_land_price_points(13, 1, 1, 2026))


# ----- XIT001（不動産取引価格情報）§45 -----
def test_xit001_success_returns_records() -> None:
    captured: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Ocp-Apim-Subscription-Key")
        return httpx.Response(
            200, json={"status": "OK", "data": [{"Type": "宅地(土地)", "UnitPrice": "150000"}]}
        )

    result = _run(_client(handler).get_transaction_prices("12217", 2025))

    assert result["status"] == "OK"
    assert result["data"][0]["UnitPrice"] == "150000"
    assert "city=12217" in (captured["url"] or "")
    assert "priceClassification=01" in (captured["url"] or "")
    assert captured["auth"] == "test-key"
    assert "test-key" not in (captured["url"] or "")


def test_xit001_404_is_no_data_not_error() -> None:
    # §32: XIT001 の 404 は「対象条件のデータなし」。例外にせず空データ相当を返す。
    result = _run(
        _client(lambda r: httpx.Response(404)).get_transaction_prices("47381", 2025)
    )
    assert result["data"] == []


def test_xit001_401_raises_auth_error() -> None:
    with pytest.raises(ReinfolibAuthError):
        _run(_client(lambda r: httpx.Response(401)).get_transaction_prices("12217", 2025))


def test_xit001_403_raises_auth_error() -> None:
    with pytest.raises(ReinfolibAuthError):
        _run(_client(lambda r: httpx.Response(403)).get_transaction_prices("12217", 2025))


def test_xit001_429_raises_rate_limit_error() -> None:
    with pytest.raises(ReinfolibRateLimitError):
        _run(_client(lambda r: httpx.Response(429)).get_transaction_prices("12217", 2025))


def test_xit001_500_raises_error() -> None:
    with pytest.raises(ReinfolibError):
        _run(_client(lambda r: httpx.Response(500)).get_transaction_prices("12217", 2025))


def test_xit001_timeout_raises_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    with pytest.raises(ReinfolibError):
        _run(_client(handler).get_transaction_prices("12217", 2025))
