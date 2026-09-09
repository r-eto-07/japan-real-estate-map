"""FastAPI アプリのエントリポイント。"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.routers import area, meta

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# httpx は INFO でリクエスト URL（appId 等を含む）を出すため WARNING に下げる
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="不動産エリア分析 API", version="0.5.0")


@app.exception_handler(OperationalError)
async def _database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
    # DB 接続不能時。無限待機はせず（connect_timeout）、分かりやすく 503。
    # 例外文字列（接続情報を含みうる）はレスポンス／ログに出さない。
    logger.error("Database unavailable for %s", request.url.path)
    return JSONResponse(status_code=503, content={"detail": "database unavailable"})

# 開発環境の frontend のみ許可する。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(area.router)
