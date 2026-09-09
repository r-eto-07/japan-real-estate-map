"""国土数値情報 行政区域データ (N03) 2026 年版から、

  - frontend/public/data/municipalities.geojson  … 地図表示用の軽量 GeoJSON
  - backend/app/data/municipalities.json          … 市区町村コード -> 都道府県/市区町村名

を生成する。両方とも同一ソースから作るため、Frontend と Backend の
市区町村コードは必ず一致する。

出典: 国土交通省 国土数値情報 行政区域データ (N03)  データ基準日 2026-01-01
利用規約: https://nlftp.mlit.go.jp/ksj/other/agreement.html

使い方:
  python scripts/prepare_municipalities.py                # 全国 (01〜47)
  python scripts/prepare_municipalities.py --prefectures 13,27,47
  python scripts/prepare_municipalities.py --keep-raw     # ダウンロード zip を残す

※ 出力ファイルは自動生成物。手編集しないこと。
"""

from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import httpx
import pandas as pd

from municipalities_lib import municipality_name, parse_prefectures

N03_YEAR = "2026"
N03_BASE_DATE = "20260101"
N03_URL_TEMPLATE = (
    "https://nlftp.mlit.go.jp/ksj/gml/data/N03/"
    f"N03-{N03_YEAR}/N03-{N03_BASE_DATE}_{{pref:02d}}_GML.zip"
)

SOURCE_LABEL = "国土交通省 国土数値情報 行政区域データ (N03)"
BASE_DATE_LABEL = "2026-01-01"

# 表示用の簡略化トレランス（度）。約 0.003 度 ≒ 250m 相当。
# preserve_topology=True で自己交差・境界消失・離島消失を避ける。
# --tolerance で上書き可能。最終値は README に記録する。
DEFAULT_SIMPLIFY_TOLERANCE = 0.003
# 座標小数桁。4 桁 ≒ 11m。全国表示・クリック判定には十分。
COORD_DECIMALS = 4

_SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = _SCRIPTS_DIR.parent
RAW_DIR = _SCRIPTS_DIR / "data" / "raw"
GEOJSON_OUT = ROOT / "frontend" / "public" / "data" / "municipalities.geojson"
JSON_OUT = ROOT / "backend" / "app" / "data" / "municipalities.json"


def download_prefecture(pref: int) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / f"N03-{N03_BASE_DATE}_{pref:02d}_GML.zip"
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    url = N03_URL_TEMPLATE.format(pref=pref)
    tmp = dest.with_suffix(".part")
    print(f"  download {url}")
    with httpx.stream("GET", url, timeout=180.0, follow_redirects=True) as response:
        response.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in response.iter_bytes(1 << 20):
                fh.write(chunk)
    tmp.rename(dest)
    return dest


def read_prefecture(zip_path: Path) -> gpd.GeoDataFrame:
    """zip 内の GeoJSON（無ければ Shapefile）を読み込む。"""
    with zipfile.ZipFile(zip_path) as zf, tempfile.TemporaryDirectory() as tmp:
        names = zf.namelist()
        geojson = next((n for n in names if n.lower().endswith(".geojson")), None)
        if geojson is not None:
            zf.extract(geojson, tmp)
            return gpd.read_file(Path(tmp) / geojson)
        members = [
            n
            for n in names
            if n.lower().endswith((".shp", ".shx", ".dbf", ".prj", ".cpg"))
        ]
        zf.extractall(tmp, members)
        shp = next(p for p in Path(tmp).glob("*.shp"))
        return gpd.read_file(shp)


def build_prefecture_records(
    gdf: gpd.GeoDataFrame, tolerance: float
) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        gdf = gdf.set_crs(6668)  # JGD2011 地理座標
    gdf = gdf.to_crs(4326)  # WGS84 / GeoJSON 標準

    gdf = gdf.rename(
        columns={
            "N03_001": "prefectureName",
            "N03_004": "_name",
            "N03_005": "_ward",
            "N03_007": "municipalityCode",
        }
    )
    if "_ward" not in gdf.columns:
        gdf["_ward"] = None
    gdf = gdf[gdf["municipalityCode"].notna()].copy()
    gdf["municipalityCode"] = (
        gdf["municipalityCode"].astype(str).str.strip().str.zfill(5)
    )
    # 「所属未定地」などの都道府県レベル擬似コード（末尾 000）は除外
    gdf = gdf[~gdf["municipalityCode"].str.endswith("000")]

    gdf["prefectureCode"] = gdf["municipalityCode"].str[:2]
    gdf["municipalityName"] = [
        municipality_name(n, w) for n, w in zip(gdf["_name"], gdf["_ward"])
    ]
    gdf = gdf[
        [
            "municipalityCode",
            "prefectureCode",
            "prefectureName",
            "municipalityName",
            "geometry",
        ]
    ]

    # 同一コードの離島・飛び地・複数ポリゴンを 1 Feature(MultiPolygon) へ統合
    dissolved = gdf.dissolve(by="municipalityCode", as_index=False, aggfunc="first")
    dissolved["geometry"] = dissolved["geometry"].simplify(
        tolerance, preserve_topology=True
    )
    dissolved["geometry"] = dissolved["geometry"].make_valid()
    return dissolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prefectures",
        default="1-47",
        help="対象の都道府県コード。例: 1-47 / 13,27,47",
    )
    parser.add_argument(
        "--keep-raw", action="store_true", help="ダウンロードした zip を削除しない"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_SIMPLIFY_TOLERANCE,
        help=f"簡略化トレランス（度）。既定 {DEFAULT_SIMPLIFY_TOLERANCE}",
    )
    args = parser.parse_args()

    prefectures = parse_prefectures(args.prefectures)
    print(f"target prefectures: {prefectures}  tolerance={args.tolerance}")

    parts: list[gpd.GeoDataFrame] = []
    for pref in prefectures:
        print(f"[{pref:02d}]")
        zip_path = download_prefecture(pref)
        records = build_prefecture_records(read_prefecture(zip_path), args.tolerance)
        print(f"  -> {len(records)} municipalities")
        parts.append(records)
        if not args.keep_raw:
            zip_path.unlink(missing_ok=True)

    combined = gpd.GeoDataFrame(
        pd.concat(parts, ignore_index=True), geometry="geometry", crs=4326
    )
    combined = combined.sort_values("municipalityCode").reset_index(drop=True)

    unique_codes = combined["municipalityCode"].nunique()
    if len(combined) != unique_codes:
        raise SystemExit(
            f"duplicate municipalityCode after dissolve: "
            f"{len(combined)} features / {unique_codes} codes"
        )

    GEOJSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    if GEOJSON_OUT.exists():
        GEOJSON_OUT.unlink()
    combined.to_file(
        GEOJSON_OUT, driver="GeoJSON", COORDINATE_PRECISION=COORD_DECIMALS
    )

    mapping = {
        row.municipalityCode: {
            "prefecture": row.prefectureName,
            "city": row.municipalityName,
        }
        for row in combined.itertuples()
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    size_mb = GEOJSON_OUT.stat().st_size / 1_000_000
    print(
        f"\n{SOURCE_LABEL}  基準日 {BASE_DATE_LABEL}\n"
        f"simplify tolerance : {args.tolerance} deg\n"
        f"municipalities.geojson : {size_mb:.1f} MB / {len(combined)} features\n"
        f"municipalities.json    : {len(mapping)} entries\n"
        f"unique municipalityCode: {unique_codes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
