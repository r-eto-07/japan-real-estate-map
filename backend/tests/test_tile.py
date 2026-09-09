from app.utils.tile import latlon_to_tile

ZOOM = 13


def test_is_deterministic() -> None:
    assert latlon_to_tile(35.86, 139.97, ZOOM) == latlon_to_tile(35.86, 139.97, ZOOM)


def test_within_tile_grid_bounds() -> None:
    n = 2**ZOOM
    x, y = latlon_to_tile(35.86, 139.97, ZOOM)
    assert 0 <= x < n
    assert 0 <= y < n


def test_origin_tiles() -> None:
    assert latlon_to_tile(0.0, 0.0, 0) == (0, 0)
    assert latlon_to_tile(0.0, 0.0, 1) == (1, 1)


def test_x_increases_eastward() -> None:
    west = latlon_to_tile(35.0, 139.0, ZOOM)[0]
    east = latlon_to_tile(35.0, 141.0, ZOOM)[0]
    assert west < east


def test_y_increases_southward() -> None:
    north = latlon_to_tile(36.0, 139.0, ZOOM)[1]
    south = latlon_to_tile(34.0, 139.0, ZOOM)[1]
    assert north < south


def test_extreme_values_are_clamped() -> None:
    n = 2**ZOOM
    for lat, lon in [(89.0, 200.0), (-89.0, -200.0), (95.0, 0.0)]:
        x, y = latlon_to_tile(lat, lon, ZOOM)
        assert 0 <= x < n
        assert 0 <= y < n
