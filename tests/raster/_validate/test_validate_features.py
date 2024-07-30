from math import inf

import numpy as np
import pytest

import pfdf.raster._validate._features as validate
from pfdf.errors import (
    GeometryError,
    MissingCRSError,
    MissingTransformError,
    PointError,
    PolygonError,
    ShapeError,
)
from pfdf.projection import CRS, Transform
from pfdf.raster import Raster

#####
# User options
#####


class TestResolution:
    def test_valid_raster(_, araster):
        raster = Raster.from_array(araster, transform=(10, 0, 0, 0, -10, 0))
        output = validate.resolution(raster)
        assert output == (10, 10)

    def test_invalid_raster(_, araster, assert_contains):
        raster = Raster.from_array(araster)
        with pytest.raises(MissingTransformError) as error:
            validate.resolution(raster)
        assert_contains(error, "does not have an affine transform")

    def test_transform_no_crs(_):
        res = Transform(10, -10, 0, 0)
        assert validate.resolution(res) == (10, 10)

    def test_transform_with_crs(_):
        res = Transform(10, -10, 0, 0, 4326)
        assert validate.resolution(res) == res

    def test_scalar(_):
        output = validate.resolution(5)
        assert np.array_equal(output, (5, 5))

    def test_vector(_):
        output = validate.resolution((1, 2))
        assert np.array_equal(output, (1, 2))

    def test_too_long(_, assert_contains):
        with pytest.raises(ShapeError) as error:
            validate.resolution((1, 2, 3, 4))
        assert_contains(error, "resolution may have either 1 or 2 elements")

    @pytest.mark.parametrize("bad", (-5, np.nan, np.inf))
    def test_invalid(_, bad, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.resolution(bad)
        assert_contains(error, "resolution")


class TestField:
    def properties(cls):
        return {"test": "int:32", "KFFACT": "float", "invalid": "str"}

    def test_none(_):
        output = validate.field({}, None)
        assert output == bool

    def test_missing(self, assert_contains):
        with pytest.raises(KeyError) as error:
            validate.field(self.properties(), "missing")
        assert_contains(error, "not the name of a feature data field")

    def test_bad_type(self, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.field(self.properties(), "invalid")
        assert_contains(error, "must be an int or float", "has a 'str' type instead")

    def test_int(self):
        assert validate.field(self.properties(), "test") == int

    def test_float(self):
        assert validate.field(self.properties(), "KFFACT") == float


class TestResolutionUnits:
    def test_base(_):
        validate.resolution_units("base", None, (10, 10), "polygon", "a/file/path")

    def test_units_transform(_):
        resolution = Transform(1, 2, 3, 4, 26911)
        validate.resolution_units("meters", None, resolution, "polygon", "a/file/path")

    def test_units_crs(_):
        crs = CRS(26911)
        validate.resolution_units("meters", crs, (5, 5), "polygon", "a/file/path")

    def test_units_invalid(_, assert_contains):
        with pytest.raises(MissingCRSError) as error:
            validate.resolution_units("meters", None, (5, 5), "polygon", "a/file/path")
        assert_contains(
            error,
            "Cannot convert resolution from meters because the polygon feature file does not have a CRS.",
            "File: a/file/path",
        )


#####
# Coordinate Arrays
#####


class TestGeometry:
    def test_none(_, assert_contains):
        with pytest.raises(GeometryError) as error:
            validate.geometry(5, None, None)
        assert_contains(error, "Feature[5] does not have a geometry")

    def test_unrecognized(_, assert_contains):
        allowed = ["Point", "MultiPoint"]
        geometry = {"type": "Polygon"}
        with pytest.raises(GeometryError) as error:
            validate.geometry(5, geometry, allowed)
        assert_contains(
            error,
            "Each feature in the input file must have a Point or MultiPoint geometry",
            "feature[5] has a Polygon geometry instead",
        )

    def test_coordinate(_):
        allowed = ["Point", "MultiPoint"]
        geometry = {"type": "Point", "coordinates": (1, 2)}
        coords = validate.geometry(5, geometry, allowed)
        assert coords == [(1, 2)]

    def test_multicoordinate(_):
        allowed = ["Point", "MultiPoint"]
        geometry = {"type": "MultiPoint", "coordinates": [(1, 2), (3, 4), (5, 6)]}
        coords = validate.geometry(5, geometry, allowed)
        assert coords == [(1, 2), (3, 4), (5, 6)]


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
