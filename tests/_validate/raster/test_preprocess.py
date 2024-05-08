from math import inf

import numpy as np
import pytest
from affine import Affine
from pyproj import CRS

import pfdf._validate.raster._preprocess as validate
from pfdf.errors import (
    DimensionError,
    MissingCRSError,
    MissingTransformError,
    ShapeError,
)
from pfdf.projection import BoundingBox, Transform
from pfdf.raster import Raster

#####
# Misc
#####


class TestResampling:
    @pytest.mark.parametrize(
        "name, value",
        (
            ("nearest", 0),
            ("bilinear", 1),
            ("cubic", 2),
            ("cubic_spline", 3),
            ("lanczos", 4),
            ("average", 5),
            ("mode", 6),
            ("max", 8),
            ("min", 9),
            ("med", 10),
            ("q1", 11),
            ("q3", 12),
            ("sum", 13),
            ("rms", 14),
        ),
    )
    def test_valid(_, name, value):
        assert validate.resampling(name) == value

    def test_invalid(_):
        with pytest.raises(ValueError):
            validate.resampling("invalid")


class TestDataBound:
    @pytest.mark.parametrize(
        "dtype, edge, expected",
        (
            ("int16", "min", np.iinfo("int16").min),
            ("int16", "max", np.iinfo("int16").max),
            ("uint8", "min", np.iinfo("uint8").min),
            ("uint8", "max", np.iinfo("uint8").max),
            (bool, "min", False),
            (bool, "max", True),
            ("float32", "min", -inf),
            ("float32", "max", inf),
        ),
    )
    def test_default(_, dtype, edge, expected):
        output = validate.data_bound(None, edge, dtype)
        assert output == expected

    def test_valid(_):
        output = validate.data_bound(2.2, min, float)
        assert output == 2.2

    def test_invalid(_):
        with pytest.raises(TypeError):
            validate.data_bound("invalid", "min", float)

    def test_not_scalar(_):
        with pytest.raises(DimensionError):
            validate.data_bound([1, 2, 3], "min", float)

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.data_bound(2.2, "min", int)
        assert_contains(error, "min", "cast", "safe")


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


#####
# NoData
#####


class TestCasting:
    def test_bool(_):
        a = np.array(True).reshape(1)
        assert validate.casting(a, "", bool, "safe") == True

    def test_bool_as_number(_):
        a = np.array(1.00).reshape(1)
        assert validate.casting(a, "", bool, casting="safe") == True

    def test_castable(_):
        a = np.array(2.2).reshape(1)
        assert validate.casting(a, "", int, casting="unsafe") == 2

    def test_not_castable(_, assert_contains):
        a = np.array(2.2).reshape(1)
        with pytest.raises(TypeError) as error:
            validate.casting(a, "test name", int, casting="safe")
        assert_contains(error, "Cannot cast test name")


class TestNodata:
    def test_nodata(_):
        output = validate.nodata(5, "safe")
        assert output == 5

    def test_casting(_):
        output = validate.nodata(2.2, "unsafe", int)
        assert output == 2

    def test_invalid_casting_option(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.nodata(1, "invalid", bool)
        assert_contains(error, "casting")

    def test_invalid_nodata(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.nodata("invalid", "unsafe")
        assert_contains(error, "nodata")

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.nodata(2.2, "safe", int)
        assert_contains(error, "Cannot cast the NoData value")


#####
# Projection
#####


class TestCRS:
    def test_crs(_):
        crs = CRS(4326)
        output = validate.crs(crs)
        assert output == crs

    def test_raster(_, araster):
        crs = CRS(4326)
        raster = Raster.from_array(araster, crs=crs)
        output = validate.crs(raster)
        assert output == crs

    def test_missing(_, araster, assert_contains):
        raster = Raster.from_array(araster)
        with pytest.raises(MissingCRSError) as error:
            validate.crs(raster)
        assert_contains(error, "does not have a CRS")

    def test_valid(_):
        assert validate.crs(4326) == CRS(4326)

    def test_invalid(_):
        with pytest.raises(Exception):
            validate.crs("invalid")


class TestBounds:
    def test_bounds(_):
        bounds = BoundingBox(0, 10, 50, 100)
        output = validate.bounds(bounds)
        assert output == bounds
        assert output is not bounds

    def test_raster(_, araster):
        bounds = BoundingBox(0, 10, 50, 100)
        transform = bounds.transform(*araster.shape)
        raster = Raster.from_array(araster, transform=transform)
        assert validate.bounds(raster) == bounds

    def test_missing(_, araster, assert_contains):
        raster = Raster(araster)
        with pytest.raises(MissingTransformError) as error:
            validate.bounds(raster)
        assert_contains(error, "does not have an affine Transform")

    def test_dict(_):
        a = {"left": 0, "right": 50, "bottom": 10, "top": 100}
        bounds = BoundingBox.from_dict(a)
        assert validate.bounds(a) == bounds

    def test_tuple(_):
        a = (0, 10, 50, 100)
        bounds = BoundingBox.from_list(a)
        assert validate.bounds(a) == bounds

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.bounds("invalid")
        assert_contains(error, "must be a dict, list, tuple, BoundingBox, or Raster")


class TestTransform:
    def test_transform(_):
        t = Transform(1, 2, 3, 4)
        out = validate.transform(t)
        assert out == t
        assert out is not t

    def test_raster(_, araster):
        t = Transform(1, 2, 3, 4)
        raster = Raster.from_array(araster, transform=t)
        assert validate.transform(raster) == t

    def test_missing(_, araster, assert_contains):
        raster = Raster(araster)
        with pytest.raises(MissingTransformError) as error:
            validate.transform(raster)
        assert_contains(error, "does not have an affine Transform")

    def test_dict(_):
        a = {"dx": 1, "dy": 2, "left": 3, "top": 4}
        t = Transform.from_dict(a)
        assert validate.transform(a) == t

    def test_tuple(_):
        a = (1, 2, 3, 4)
        t = Transform.from_list(a)
        assert validate.transform(a) == t

    def test_affine(_):
        a = Affine(1, 0, 3, 0, 2, 4)
        t = Transform(1, 2, 3, 4)
        assert validate.transform(a) == t

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.transform("invalid")
        assert_contains(
            error, "must be a dict, list, tuple, affine.Affine, Transform, or Raster"
        )


class TestFeatureOptions:
    def test_no_bounds(_):
        res, bounds = validate.feature_options(10, None)
        assert res == [10, 10]
        assert bounds is None

    def test_bounds(_):
        bounds = (1, 2, 3, 4)
        out1, out2 = validate.feature_options(10, bounds)
        assert out1 == [10, 10]
        assert out2 == BoundingBox(1, 2, 3, 4)


class TestSpatial:
    def test_none(_):
        assert validate.spatial(None, None) == (None, None)

    def test(_):
        output = validate.spatial(4326, (1, 2, 3, 4))
        assert output == (CRS(4326), Transform(1, 2, 3, 4))


class TestMetadata:
    def test_none(_):
        assert validate.metadata(None, None, None, None, None) == (None, None, None)

    def test(_):
        output = validate.metadata(4326, (1, 2, 3, 4), 5, "safe", int)
        assert output == (CRS(4326), Transform(1, 2, 3, 4), 5)
