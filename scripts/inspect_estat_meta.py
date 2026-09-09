"""e-Stat 統計表のメタ情報（分類の id / code / name / level）をダンプする。

Phase 3 の実装前チェック用。表 112-3-2（統計表 ID 0004021480）の
  表章項目 / 住宅の種類 / 住宅の家賃の平均 / 全国・都道府県・市区町村 / 時間軸
の実際のコードを確認し、backend/app/config.py の想定
  ESTAT_RENT_HOUSING_TYPE_MATCH = "総数"
  ESTAT_RENT_AVERAGE_MATCH      = "含まない"
および app/utils/estat_area_code.py（地域コード形式）と突き合わせる。

使い方:
  1. backend/.env に ESTAT_APP_ID を設定
  2. backend/.venv/Scripts/python.exe scripts/inspect_estat_meta.py
     （第 2 引数で statsDataId を上書き可能）

※ appId はコンソールに出力しない。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / "backend" / ".env")

GETMETAINFO_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getMetaInfo"
DEFAULT_STATS_DATA_ID = "0004021480"


def main() -> int:
    app_id = os.getenv("ESTAT_APP_ID")
    if not app_id:
        print("ESTAT_APP_ID is not configured (backend/.env)", file=sys.stderr)
        return 1

    stats_data_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STATS_DATA_ID

    response = httpx.get(
        GETMETAINFO_URL,
        params={"appId": app_id, "statsDataId": stats_data_id, "lang": "J"},
        timeout=30.0,
    )
    response.raise_for_status()
    body = response.json()

    result = body.get("GET_META_INFO", {}).get("RESULT", {})
    if str(result.get("STATUS")) not in ("0", "None"):
        print(f"e-Stat error: STATUS={result.get('STATUS')} {result.get('ERROR_MSG')}")
        return 1

    meta = body["GET_META_INFO"]["METADATA_INF"]
    print("TABLE:", meta.get("TABLE_INF", {}).get("TITLE"))
    class_objs = meta["CLASS_INF"]["CLASS_OBJ"]
    if isinstance(class_objs, dict):
        class_objs = [class_objs]

    for obj in class_objs:
        print(f"\n[{obj.get('@id')}] {obj.get('@name')}")
        classes = obj.get("CLASS")
        if isinstance(classes, dict):
            classes = [classes]
        for cls in classes or []:
            print(
                f"  code={cls.get('@code'):<14} "
                f"level={cls.get('@level', '-'):<3} name={cls.get('@name')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
