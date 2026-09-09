"""backend/app/data/municipalities.json を PostgreSQL の municipalities へ投入する。

Phase 2.5 の生成物（N03 由来）を DB マスタへ移す。再実行可能（UPSERT）。

使い方:
  backend/.venv/Scripts/python.exe scripts/import_municipalities.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / "backend" / ".env")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import config  # noqa: E402
from app.db.models import Municipality  # noqa: E402

MUNICIPALITIES_JSON = _ROOT / "backend" / "app" / "data" / "municipalities.json"


def main() -> int:
    data: dict[str, dict[str, str]] = json.loads(
        MUNICIPALITIES_JSON.read_text(encoding="utf-8")
    )
    rows = [
        {
            "municipality_code": code,
            "prefecture_code": code[:2],
            "prefecture_name": value["prefecture"],
            "municipality_name": value["city"],
        }
        for code, value in sorted(data.items())
    ]

    engine = create_engine(config.require_database_url())
    with Session(engine) as session:
        # チャンクごとに ON CONFLICT DO UPDATE
        for start in range(0, len(rows), 1000):
            chunk = rows[start : start + 1000]
            stmt = insert(Municipality).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["municipality_code"],
                set_={
                    "prefecture_code": stmt.excluded.prefecture_code,
                    "prefecture_name": stmt.excluded.prefecture_name,
                    "municipality_name": stmt.excluded.municipality_name,
                },
            )
            session.execute(stmt)
        session.commit()

    print(f"upserted {len(rows)} municipalities into PostgreSQL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
