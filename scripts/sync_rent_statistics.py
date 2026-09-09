"""e-Stat から全市区町村の平均家賃を取得し rent_statistics へ UPSERT する。

住宅・土地統計調査は 5 年周期なので、通常はこのスクリプトを一度流せば
以後の画面操作は PostgreSQL だけで完結する（AreaService は e-Stat を呼ばない）。

getStatsData を 1 回（地域指定なし）呼び、全地域を含む応答を parser で
市区町村ごとに解釈する。

使い方:
  backend/.venv/Scripts/python.exe scripts/sync_rent_statistics.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / "backend" / ".env")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import config  # noqa: E402
from app.clients.estat_client import EStatClient  # noqa: E402
from app.parsers.estat_rent_parser import extract_average_rent  # noqa: E402
from app.repositories.rent_repository import RentRepository  # noqa: E402

MUNICIPALITIES_JSON = _ROOT / "backend" / "app" / "data" / "municipalities.json"


async def main() -> int:
    if not config.ESTAT_APP_ID:
        print("ESTAT_APP_ID is not configured (backend/.env)", file=sys.stderr)
        return 1

    codes = sorted(json.loads(MUNICIPALITIES_JSON.read_text(encoding="utf-8")))
    print(f"municipalities: {len(codes)}")

    response = await EStatClient(app_id=config.ESTAT_APP_ID).get_rent_data()

    engine = create_engine(config.require_database_url())
    written = 0
    with Session(engine) as session:
        repo = RentRepository(session)
        for code in codes:
            rent = extract_average_rent(response, code)
            repo.upsert(
                code, config.ESTAT_RENT_YEAR, rent, config.ESTAT_RENT_SOURCE_LABEL
            )
            if rent is not None:
                written += 1
        session.commit()

    print(
        f"upserted rent_statistics for {len(codes)} municipalities "
        f"({written} with a value, year {config.ESTAT_RENT_YEAR})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
