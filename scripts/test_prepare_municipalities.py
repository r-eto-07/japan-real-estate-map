"""生成スクリプトの純粋関数のテスト。

実行:  python -m pytest scripts/
（geopandas に依存しない municipalities_lib のみを対象にする）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from municipalities_lib import municipality_name, parse_prefectures  # noqa: E402


def test_parse_prefectures_range() -> None:
    assert parse_prefectures("1-3") == [1, 2, 3]


def test_parse_prefectures_mixed_and_dedup() -> None:
    assert parse_prefectures("13, 27 , 13, 5-6") == [5, 6, 13, 27]


def test_parse_prefectures_clamps_out_of_range() -> None:
    assert parse_prefectures("0,48,47") == [47]


def test_municipality_name_tokyo_ward() -> None:
    assert municipality_name("千代田区", None) == "千代田区"


def test_municipality_name_designated_city_ward() -> None:
    assert municipality_name("横浜市", "西区") == "横浜市西区"
    assert municipality_name("堺市", "堺区") == "堺市堺区"


def test_municipality_name_plain_city_town_village() -> None:
    assert municipality_name("八王子市", None) == "八王子市"
    assert municipality_name("檜原村", "") == "檜原村"


def test_municipality_name_handles_nan() -> None:
    assert municipality_name("那覇市", float("nan")) == "那覇市"
