from math import inf

import numpy as np
import pytest

from pfdf.errors import (
    GeometryError,
    MissingCRSError,
    MissingTransformError,
    PointError,
    PolygonError,
    ShapeError,
)
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster, RasterMetadata
from pfdf.raster._features import _validate

#####
# Groups
#####


class TestFieldOptions:
    def test_valid(_):
        def testop():
            pass

        testop()

        dtype, casting, nodata = _validate.field_options(
            "test", int, "SAFE", 5.1, "unsafe", testop
        )
        assert dtype == np.dtype(int)
        assert casting == "safe"
        assert nodata == 5

    def test_invalid_field(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.field_options(5, None, None, None, None, None)
        assert_contains(error, "field must be a str")

    def test_invalid_dtype(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.field_options("test", "invalid", None, None, None, None)
        assert_contains(error, 'Could not convert the "dtype" input to a numpy dtype')

    def test_invalid_field_casting(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.field_options("test", None, "invalid", None, None, None)
        assert_contains(error, "field_casting (invalid) is not a recognized option")

    def test_invalid_nodata(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.field_options("test", None, "safe", "invalid", "safe", None)
        assert_contains(error, "The dtype of nodata", "is not an allowed dtype")

    def test_invalid_casting_option(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.field_options("test", int, "safe", 5, "invalid", None)
        assert_contains(error, "casting (invalid) is not a recognized option")

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.field_options("test", int, "safe", 2.2, "safe", None)
        assert_contains(
            error,
            "Cannot cast the NoData value (value = 2.2) to the raster dtype",
        )

    def test_invalid_operation(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.field_options("test", None, "safe", None, None, 5)
        assert_contains(error, 'The "operation" input must be a callable object')


class TestSpatial:
    def test_valid(_):
        bounds, resolution, units = _validate.spatial((1, 2, 3, 4), 10, "BASE")
        assert bounds == BoundingBox(1, 2, 3, 4)
        assert resolution == [10, 10]
        assert units == "base"

    def test_invalid_bounds(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.spatial("invalid", 10, "base")
        assert_contains(
            error,
            "bounds must be a BoundingBox, Raster, RasterMetadata, dict, list, or tuple",
        )

    def test_invalid_resolution(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.spatial(None, "invalid", "base")
        assert_contains(error, "The dtype of resolution", "is not an allowed dtype")

    def test_invalid_units(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.spatial(None, 10, "invalid")
        assert_contains(error, "units (invalid) is not a recognized option")


class TestFileIO:
    def test_valid(_, fraster):
        path, layer, driver, encoding = _validate.file_io(
            fraster, "test layer", "test driver", "test encoding"
        )
        assert path == fraster
        assert layer == "test layer"
        assert driver == "test driver"
        assert encoding == "test encoding"

    def test_layer(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.file_io(fraster, 2.2, None, None)
        assert_contains(error, "layer must be a int or string")

    def test_driver(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.file_io(fraster, None, 2.2, None)
        assert_contains(error, "driver must be a string")

    def test_encoding(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.file_io(fraster, None, None, 2.2)
        assert_contains(error, "encoding must be a string")

    def test_path(_):
        with pytest.raises(FileNotFoundError):
            _validate.file_io("invalid", None, None, None)


#####
# Specific inputs
#####


class TestResolution:
    def test_valid_raster(_, araster):
        input = Raster.from_array(araster, transform=(10, -10, 0, 0))
        output = _validate.resolution(input)
        assert output == (10, 10)

    def test_invalid_raster(_, araster, assert_contains):
        input = Raster.from_array(araster)
        with pytest.raises(MissingTransformError) as error:
            _validate.resolution(input)
        assert_contains(error, "does not have an affine transform")

    def test_valid_metadata(_, araster):
        input = RasterMetadata(araster.shape, transform=(10, -10, 0, 0))
        output = _validate.resolution(input)
        assert output == (10, 10)

    def test_invalid_metadata(_, araster, assert_contains):
        input = RasterMetadata(araster.shape)
        with pytest.raises(MissingTransformError) as error:
            _validate.resolution(input)
        assert_contains(error, "does not have an affine transform")

    def test_transform_no_crs(_):
        res = Transform(10, -10, 0, 0)
        assert _validate.resolution(res) == (10, 10)

    def test_transform_with_crs(_):
        res = Transform(10, -10, 0, 0, 4326)
        assert _validate.resolution(res) == res

    def test_scalar(_):
        output = _validate.resolution(5)
        assert np.array_equal(output, (5, 5))

    def test_vector(_):
        output = _validate.resolution((1, 2))
        assert np.array_equal(output, (1, 2))

    def test_too_long(_, assert_contains):
        with pytest.raises(ShapeError) as error:
            _validate.resolution((1, 2, 3, 4))
        assert_contains(error, "resolution may have either 1 or 2 elements")

    @pytest.mark.parametrize("bad", (-5, np.nan, np.inf))
    def test_invalid(_, bad, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.resolution(bad)
        assert_contains(error, "resolution")


class TestField:
    def properties(cls):
        return {"test": "int:32", "KFFACT": "float", "invalid": "str"}

    @pytest.mark.parametrize("input", (None, "test", "KFFACT"))
    def test_valid(self, input):
        _validate.field(input, self.properties())

    def test_missing(self, assert_contains):
        with pytest.raises(KeyError) as error:
            _validate.field("missing", self.properties())
        assert_contains(error, "not the name of a feature data field")

    def test_bad_type(self, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.field("invalid", self.properties())
        assert_contains(error, "must be an int or float", "has a 'str' type instead")


class TestUnits:
    def test_base(_):
        _validate.units("base", None, (10, 10), "polygon", "a/file/path")

    def test_units_transform(_):
        resolution = Transform(1, 2, 3, 4, 26911)
        _validate.units("meters", None, resolution, "polygon", "a/file/path")

    def test_units_crs(_):
        crs = CRS(26911)
        _validate.units("meters", crs, (5, 5), "polygon", "a/file/path")

    def test_units_invalid(_, assert_contains):
        with pytest.raises(MissingCRSError) as error:
            _validate.units("meters", None, (5, 5), "polygon", "a/file/path")
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
            _validate.geometry(5, None, None)
        assert_contains(error, "Feature[5] does not have a geometry")

    def test_unrecognized(_, assert_contains):
        allowed = ["Point", "MultiPoint"]
        geometry = {"type": "Polygon"}
        with pytest.raises(GeometryError) as error:
            _validate.geometry(5, geometry, allowed)
        assert_contains(
            error,
            "Each feature in the input file must have a Point or MultiPoint geometry",
            "feature[5] has a Polygon geometry instead",
        )

    def test_coordinate(_):
        allowed = ["Point", "MultiPoint"]
        geometry = {"type": "Point", "coordinates": (1, 2)}
        coords = _validate.geometry(5, geometry, allowed)
        assert coords == [(1, 2)]

    def test_multicoordinate(_):
        allowed = ["Point", "MultiPoint"]
        geometry = {"type": "MultiPoint", "coordinates": [(1, 2), (3, 4), (5, 6)]}
        coords = _validate.geometry(5, geometry, allowed)
        assert coords == [(1, 2), (3, 4), (5, 6)]


class TestPoint:
    def test_not_tuple(_, assert_contains):
        with pytest.raises(PointError) as error:
            _validate.point(0, 0, 5)
        assert_contains(
            error, "feature[0]", "point[0]", "is neither a list nor a tuple"
        )

    def test_wrong_length(_, assert_contains):
        with pytest.raises(PointError) as error:
            _validate.point(1, 2, [1, 2, 3, 4])
        assert_contains(error, "feature[1]", "point[2]", "has 4 elements")

    def test_valid(_):
        _validate.point(0, 0, [1, 2])

    def test_not_finite(_, assert_contains):
        with pytest.raises(PointError) as error:
            _validate.point(0, 0, [inf, 2])
        assert_contains(error, "has nan or infinite elements")

    def test_wrong_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.point(1, 2, ["a", "b"])
        assert_contains(
            error,
            "must have an int or float type",
            "feature[1]",
            "the x coordinate for point[2]",
        )


class TestPolygon:
    def test_not_list(_, assert_contains):
        with pytest.raises(PolygonError) as error:
            _validate.polygon(4, 5, "invalid")
        assert_contains(error, "feature[4]", "polygon[5] is not a list")

    def test_ring_not_list(_, assert_contains):
        coords = [
            [(1, 2), (3, 4), (5, 6), (1, 2)],
            (1, 2),
        ]
        with pytest.raises(PolygonError) as error:
            _validate.polygon(4, 5, coords)
        assert_contains(error, "feature[4]", "polygon[5].coordinates[1]", "not a list")

    def test_too_short(_, assert_contains):
        coords = [[(1, 2), (2, 3), (1, 2)]]
        with pytest.raises(PolygonError) as error:
            _validate.polygon(4, 5, coords)
        assert_contains(
            error, "ring[0]", "feature[4]", "polygon[5]", "does not have 4 positions"
        )

    def test_bad_end(_, assert_contains):
        coords = [[(1, 2), (2, 3), (4, 5), (6, 7)]]
        with pytest.raises(PolygonError) as error:
            _validate.polygon(4, 5, coords)
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
        _validate.polygon(1, 2, coords)

    def test_with_holes(_):
        coords = [
            [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (1, 2)],
            [(1, 2), (3, 4), (2, 2), (1, 2)],
            [(1, 2), (5, 6), (2, 2), (1, 2)],
        ]
        _validate.polygon(1, 2, coords)

    def test_not_finite(_, assert_contains):
        coords = [
            [(1, 2), (3, 4), (5, inf), (1, 2)],
        ]
        with pytest.raises(PolygonError) as error:
            _validate.polygon(1, 2, coords)
        assert_contains(error, "contains nan or infinite elements")
