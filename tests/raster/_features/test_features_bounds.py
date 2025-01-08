from math import inf

from pfdf.raster._features import _bounds


class TestUnbounded:
    def test_no_crs(_):
        assert _bounds.unbounded() == {
            "left": inf,
            "bottom": inf,
            "right": -inf,
            "top": -inf,
        }

    def test_crs(_):
        assert _bounds.unbounded(4326) == {
            "left": inf,
            "bottom": inf,
            "right": -inf,
            "top": -inf,
            "crs": 4326,
        }


class TestAddGeometry:
    def test_no_updates(_):
        coords = [[(1, 2), (3, 4), (5, 6), (1, 2)]]
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        _bounds.add_geometry("Polygon", coords, bounds)
        assert bounds["left"] == -10
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 10

    def test_all_update(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        _bounds.add_geometry("Polygon", coords, bounds)
        assert bounds["left"] == -10
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 10

    def test_mixed(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        bounds = {
            "left": -20,
            "right": 0,
            "bottom": 0,
            "top": 20,
        }
        _bounds.add_geometry("Polygon", coords, bounds)
        assert bounds["left"] == -20
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 20

    def test_polygon(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        _bounds.add_geometry("Polygon", coords, bounds)
        assert bounds["left"] == -10
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 10

    def test_point(_):
        coords = [10, 10]
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        _bounds.add_geometry("Point", coords, bounds)
        assert bounds["left"] == 0
        assert bounds["right"] == 10
        assert bounds["bottom"] == 0
        assert bounds["top"] == 10


class TestFromPoint:
    def test(_):
        coords = [10, 10]
        left, bottom, right, top = _bounds._from_point(coords)
        assert left == 10
        assert right == 10
        assert bottom == 10
        assert top == 10


class TestFromPolygon:
    def test(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        left, bottom, right, top = _bounds._from_polygon(coords)
        assert left == -10
        assert right == 10
        assert bottom == -10
        assert top == 10
