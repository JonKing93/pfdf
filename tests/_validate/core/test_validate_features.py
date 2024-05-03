from math import inf, isnan

import pytest

import pfdf._validate.core._features as validate
from pfdf.errors import PointError, PolygonError


class TestPoint:
    def test_not_tuple(_, assert_contains):
        with pytest.raises(PointError) as error:
            validate.point(0, 0, 5)
        assert_contains(
            error, "feature[0]", "point[0]", "is neither a list nor a tuple"
        )

    def test_wrong_length(_, assert_contains):
        with pytest.raises(PointError) as error:
            validate.point(1, 2, [1, 2, 3, 4])
        assert_contains(error, "feature[1]", "point[2]", "has 4 elements")

    def test_valid(_):
        validate.point(0, 0, [1, 2])

    def test_not_finite(_, assert_contains):
        with pytest.raises(PointError) as error:
            validate.point(0, 0, [inf, 2])
        assert_contains(error, "has nan or infinite elements")

    def test_wrong_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.point(1, 2, ["a", "b"])
        assert_contains(
            error,
            "must have an int or float type",
            "feature[1]",
            "the x coordinate for point[2]",
        )


class TestPolygon:
    def test_not_list(_, assert_contains):
        with pytest.raises(PolygonError) as error:
            validate.polygon(4, 5, "invalid")
        assert_contains(error, "feature[4]", "polygon[5] is not a list")

    def test_ring_not_list(_, assert_contains):
        coords = [
            [(1, 2), (3, 4), (5, 6), (1, 2)],
            (1, 2),
        ]
        with pytest.raises(PolygonError) as error:
            validate.polygon(4, 5, coords)
        assert_contains(error, "feature[4]", "polygon[5].coordinates[1]", "not a list")

    def test_too_short(_, assert_contains):
        coords = [[(1, 2), (2, 3), (1, 2)]]
        with pytest.raises(PolygonError) as error:
            validate.polygon(4, 5, coords)
        assert_contains(
            error, "ring[0]", "feature[4]", "polygon[5]", "does not have 4 positions"
        )

    def test_bad_end(_, assert_contains):
        coords = [[(1, 2), (2, 3), (4, 5), (6, 7)]]
        with pytest.raises(PolygonError) as error:
            validate.polygon(4, 5, coords)
        assert_contains(
            error,
            "ring[0]",
            "feature[4]",
            "polygon[5]",
            "must match the first position",
        )

    def test_shell_only(_):
        coords = [
            [(1, 2), (3, 4), (5, 6), (1, 2)],
        ]
        validate.polygon(1, 2, coords)

    def test_with_holes(_):
        coords = [
            [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (1, 2)],
            [(1, 2), (3, 4), (2, 2), (1, 2)],
            [(1, 2), (5, 6), (2, 2), (1, 2)],
        ]
        validate.polygon(1, 2, coords)

    def test_not_finite(_, assert_contains):
        coords = [
            [(1, 2), (3, 4), (5, inf), (1, 2)],
        ]
        with pytest.raises(PolygonError) as error:
            validate.polygon(1, 2, coords)
        assert_contains(error, "contains nan or infinite elements")


@pytest.fixture
def properties():
    return {"test": "float", "KFFACT": "float", "invalid": "str"}


class TestField:
    def test_none(_):
        output = validate.field({}, None, None)
        assert output == (bool, False, False)

    def test_default_fill(_, properties):
        dtype, nodata, fill = validate.field(properties, "test", fill=None)
        assert dtype == float
        assert isnan(nodata)
        assert isnan(fill)

    def test_user_fill(_, properties):
        output = validate.field(properties, "test", fill=5)
        assert output[0] == float
        assert isnan(output[1])
        assert output[2] == 5

    def test_missing(_, properties, assert_contains):
        with pytest.raises(KeyError) as error:
            validate.field(properties, "missing", None)
        assert_contains(error, "not the name of a feature data field")

    def test_bad_type(_, properties, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.field(properties, "invalid", None)
        assert_contains(error, "must be an int or float", "has a 'str' type instead")

    def test_invalid_fill(_, properties, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.field(properties, "test", "invalid")
        assert_contains(error, "fill")
