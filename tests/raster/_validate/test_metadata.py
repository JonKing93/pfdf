import numpy as np
import pytest
from affine import Affine

import pfdf.raster._validate._metadata as validate
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster

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


#####
# Multiple Metadatas
#####


class TestSpatial:
    def test_none(_):
        assert validate.spatial(None, None) == (None, None)

    def test(_):
        output = validate.spatial(4326, (1, 2, 3, 4))
        assert output == (CRS(4326), Transform(1, 2, 3, 4))


class TestMetadata:
    def test_none(_):
        assert validate.metadata(None, None, None, None, None, None) == (
            None,
            None,
            None,
        )

    def test(_):
        output = validate.metadata(4326, (1, 2, 3, 4), None, 5, "safe", int)
        assert output == (CRS(4326), Transform(1, 2, 3, 4), 5)

    def test_bounds_transform(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.metadata(None, (1, 2, 3, 4), (10, 20, 30, 40), None, "safe")
        assert_contains(
            error,
            'You cannot specify both "transform" and "bounds" metadata.',
            "The two inputs are mutually exclusive.",
        )

    def test_bounds(_):
        crs, bounds, nodata = validate.metadata(
            None, None, (10, 20, 30, 40), None, "safe"
        )
        assert crs is None
        assert bounds == BoundingBox(10, 20, 30, 40)
        assert nodata is None
