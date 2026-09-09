"""テスト用の e-Stat getStatsData レスポンス（本物の API は呼ばない）。

分類コード（"10" / "2" / "2023000000" など）はこのモック内で任意に付けた値。
parser は CLASS_INF の「名称」からコードを解決するので、これで
「コードを推測で固定していない」ことも確認できる。
"""

from __future__ import annotations

from typing import Any


def build_rent_response(rents_by_area: dict[str, str]) -> dict[str, Any]:
    """{area_code: 値文字列} から、総数・家賃0円を含まない・2023年の VALUE を組む。"""
    areas = list(rents_by_area)
    values: list[dict[str, Any]] = []
    for area, raw in rents_by_area.items():
        # ノイズ: 家賃0円を含む / 専用住宅 も混ぜておく（parser が正しく絞れるか）
        values.append(_v("10", "1", area, "60000"))
        values.append(_v("20", "2", area, "70000"))
        values.append(_v("10", "2", area, raw))  # 総数・含まない ← これを取る
    return {
        "GET_STATS_DATA": {
            "RESULT": {"STATUS": 0, "ERROR_MSG": "正常に終了しました。"},
            "STATISTICAL_DATA": {
                "CLASS_INF": {
                    "CLASS_OBJ": [
                        {
                            "@id": "tab",
                            "@name": "表章項目",
                            "CLASS": {"@code": "020", "@name": "住宅の１か月当たり家賃"},
                        },
                        {
                            "@id": "cat01",
                            "@name": "住宅の種類",
                            "CLASS": [
                                {"@code": "10", "@name": "総数"},
                                {"@code": "20", "@name": "専用住宅"},
                                {"@code": "30", "@name": "店舗その他の併用住宅"},
                            ],
                        },
                        {
                            "@id": "cat02",
                            "@name": "住宅の家賃の平均",
                            "CLASS": [
                                {"@code": "1", "@name": "家賃０円を含む"},
                                {"@code": "2", "@name": "家賃０円を含まない"},
                            ],
                        },
                        {
                            "@id": "area",
                            "@name": "全国・都道府県・市区町村",
                            "CLASS": [
                                {"@code": a, "@name": f"area-{a}"} for a in areas
                            ]
                            or [{"@code": "00000", "@name": "全国"}],
                        },
                        {
                            "@id": "time",
                            "@name": "時間軸（年次）",
                            "CLASS": {"@code": "2023000000", "@name": "2023年"},
                        },
                    ]
                },
                "DATA_INF": {"VALUE": values},
            },
        }
    }


def _v(cat01: str, cat02: str, area: str, raw: str) -> dict[str, Any]:
    return {
        "@tab": "020",
        "@cat01": cat01,
        "@cat02": cat02,
        "@area": area,
        "@time": "2023000000",
        "$": raw,
    }


# 柏市=68200 / 新宿区=102300 を含む既定レスポンス
RENT_RESPONSE = build_rent_response({"12217": "68200", "13104": "102300"})
