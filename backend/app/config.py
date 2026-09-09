"""環境変数・定数の集約。

API キーはソースコードにも README にも書かない。backend/.env に置く。
起動時に backend/.env を読み込む。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


class ConfigError(RuntimeError):
    """必須の設定値が存在しない場合に送出。"""


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# ---- PostgreSQL --------------------------------------------------------------
# 例: postgresql+psycopg://user:password@localhost:5432/dbname
# 値そのもの（パスワード含む）はログに出さない。
DATABASE_URL: str | None = os.getenv("DATABASE_URL")


def require_database_url() -> str:
    if not DATABASE_URL:
        raise ConfigError("DATABASE_URL is not configured")
    return DATABASE_URL


REINFOLIB_API_KEY: str | None = os.getenv("REINFOLIB_API_KEY")

# XPT002: 地価公示・地価調査のポイント（点）API
REINFOLIB_XPT002_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/XPT002"
# XIT001: 不動産価格（取引価格・成約価格）情報取得 API
REINFOLIB_XIT001_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/XIT001"
REINFOLIB_TIMEOUT_SECONDS = 10.0

# ---- 実取引土地価格（XIT001）------------------------------------------------
# 取得年。config 一箇所で変更できるようにする（将来 2026 通年へ）。
TRANSACTION_PRICE_YEAR = _int_env("TRANSACTION_PRICE_YEAR", 2025)
# 01 = 不動産取引価格情報のみ（成約価格情報と混在させない）
TRANSACTION_PRICE_CLASSIFICATION = "01"
# XIT001 レスポンスの Type フィルタ（実レスポンスで確認済みの表記）。
# 「宅地(土地と建物)」「中古マンション等」「農地」「林地」は集計に混ぜない。
TRANSACTION_LAND_TYPE = "宅地(土地)"
TRANSACTION_PRICE_SOURCE_LABEL = "国土交通省 不動産取引価格情報"
# XIT001 はリアルタイムデータではない。municipalityCode:year 単位でキャッシュ。
TRANSACTION_CACHE_TTL_SECONDS = _int_env("TRANSACTION_CACHE_TTL_SECONDS", 86400)

# ---- e-Stat（平均家賃 / 住宅・土地統計調査）--------------------------------
# e-Stat アプリケーション ID。Reinfolib のキーとは別物（e-Stat の無料登録で取得）。
ESTAT_APP_ID: str | None = os.getenv("ESTAT_APP_ID")

ESTAT_GETSTATSDATA_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
ESTAT_GETMETAINFO_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getMetaInfo"
ESTAT_TIMEOUT_SECONDS = 10.0

# 令和5年住宅・土地統計調査 / 表番号 112-3-2
# 「住宅の種類(2区分)別借家の住宅の1か月当たり家賃（全国、都道府県、市区町村）」
# 統計表 ID・調査年は複数ファイルに直書きせず、ここだけに置く。
ESTAT_STATS_DATA_ID_RENT = "0004021480"
ESTAT_RENT_YEAR = 2023
ESTAT_RENT_SOURCE_LABEL = "e-Stat 令和5年住宅・土地統計調査"

# レスポンスのメタ情報（CLASS_INF）から対象分類を「名称の部分一致」で選ぶ。
# コードは推測で固定せず、実データのメタから解決する。
# 実際の名称は scripts/inspect_estat_meta.py で確認できる。
#   住宅の種類        … 総数 / 専用住宅 / 店舗その他の併用住宅  -> 総数
#   住宅の家賃の平均  … 家賃0円を含む / 家賃0円を含まない       -> 含まない（通常の賃貸相場に近い）
ESTAT_RENT_HOUSING_TYPE_MATCH = "総数"
ESTAT_RENT_AVERAGE_MATCH = "含まない"

# 住宅・土地統計調査は 5 年周期。頻繁な再取得は不要。
ESTAT_RENT_CACHE_TTL_SECONDS = _int_env("ESTAT_RENT_CACHE_TTL_SECONDS", 86400)

# XPT002 はズームレベル 13〜15 を指定できる。まずは 13。
# コード中に 13 を直書きせず、必要なら .env で調整する。
LAND_PRICE_TILE_ZOOM = _int_env("LAND_PRICE_TILE_ZOOM", 13)

# 対象年。最新年が API 未提供の場合に備え、.env で変更可能にしておく。
# （自動的に何年も遡って大量リクエストする処理は Phase 2 では実装しない）
LAND_PRICE_YEAR = _int_env("LAND_PRICE_YEAR", 2026)

# タイル単位の簡易メモリキャッシュの有効期間（秒）。地価公示は
# リアルタイム更新される性質ではないため、短時間の再取得は不要。
LAND_PRICE_CACHE_TTL_SECONDS = _int_env("LAND_PRICE_CACHE_TTL_SECONDS", 3600)

# priceClassification=0 → 国土交通省 地価公示のみ（都道府県地価調査と混在させない）
LAND_PRICE_CLASSIFICATION = "0"
LAND_PRICE_SOURCE_LABEL = "国土交通省 地価公示"


def require_api_key() -> str:
    """Reinfolib API キーを返す。未設定なら分かりやすいエラー（値はログに出さない）。"""
    if not REINFOLIB_API_KEY:
        raise ConfigError("REINFOLIB_API_KEY is not configured")
    return REINFOLIB_API_KEY


def require_estat_app_id() -> str:
    """e-Stat アプリケーション ID を返す。未設定なら分かりやすいエラー（値はログに出さない）。"""
    if not ESTAT_APP_ID:
        raise ConfigError("ESTAT_APP_ID is not configured")
    return ESTAT_APP_ID
