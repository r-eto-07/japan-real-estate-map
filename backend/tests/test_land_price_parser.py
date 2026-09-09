from app.parsers.land_price_parser import extract_land_points

GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.97, 35.86]},
            "properties": {
                "city_code": "12217",
                "u_current_years_price_ja": "165,000(円/㎡)",
                "use_category_name_ja": "住宅地",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.98, 35.87]},
            "properties": {
                "city_code": "12217",
                "u_current_years_price_ja": "3,100,000(円/㎡)",
                "land_price_type": "商業地",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.7, 35.69]},
            "properties": {
                "city_code": "13104",
                "u_current_years_price_ja": "900,000(円/㎡)",
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [139.99, 35.88]},
            "properties": {"city_code": "12217", "u_current_years_price_ja": ""},
        },
    ],
}


def test_extracts_points_for_target_municipality_only() -> None:
    points = extract_land_points(GEOJSON, "12217")

    assert [p.price_per_sqm for p in points] == [165000, 3100000]
    assert points[0].latitude == 35.86
    assert points[0].longitude == 139.97
    assert points[0].land_price_type == "住宅地"
    assert points[1].land_price_type == "商業地"


def test_empty_when_no_match() -> None:
    assert extract_land_points(GEOJSON, "99999") == []
    assert extract_land_points({}, "12217") == []
