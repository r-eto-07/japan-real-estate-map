"""scripts/prepare_municipalities.py が生成したデータの検証。

生成物（自動生成・手編集しない）:
  backend/app/data/municipalities.json
  frontend/public/data/municipalities.geojson
"""

import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
MUNI_JSON = _ROOT / "backend" / "app" / "data" / "municipalities.json"
MUNI_GEOJSON = _ROOT / "frontend" / "public" / "data" / "municipalities.geojson"

pytestmark = pytest.mark.skipif(
    not MUNI_JSON.exists() or not MUNI_GEOJSON.exists(),
    reason="municipalities データ未生成（python scripts/prepare_municipalities.py）",
)


@pytest.fixture(scope="module")
def municipalities() -> dict:
    return json.loads(MUNI_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def geojson() -> dict:
    return json.loads(MUNI_GEOJSON.read_text(encoding="utf-8"))


def test_json_lookup_known_code(municipalities: dict) -> None:
    assert municipalities["12217"] == {"prefecture": "千葉県", "city": "柏市"}


def test_json_has_no_bogus_code(municipalities: dict) -> None:
    assert "99999" not in municipalities


@pytest.mark.parametrize(
    "code",
    ["01101", "13104", "14101", "12217", "27127", "40131", "47201"],
)
def test_representative_municipalities_exist(municipalities: dict, code: str) -> None:
    # 政令市の区 / 東京23区 / 通常市 / 郡部の町村 を横断的に確認（データ検証）
    assert code in municipalities
    assert municipalities[code]["prefecture"]
    assert municipalities[code]["city"]


def test_every_feature_has_required_properties(geojson: dict) -> None:
    for feature in geojson["features"]:
        props = feature["properties"]
        for key in (
            "municipalityCode",
            "prefectureCode",
            "prefectureName",
            "municipalityName",
        ):
            assert props.get(key), f"{key} missing in {props}"
        assert feature["geometry"] is not None
        assert feature["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_no_duplicate_municipality_code(geojson: dict) -> None:
    codes = [f["properties"]["municipalityCode"] for f in geojson["features"]]
    assert len(codes) == len(set(codes))


def test_geojson_and_json_codes_match(municipalities: dict, geojson: dict) -> None:
    geo_codes = {f["properties"]["municipalityCode"] for f in geojson["features"]}
    assert geo_codes == set(municipalities)
