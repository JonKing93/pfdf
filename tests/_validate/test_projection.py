import pytest
from affine import Affine

import pfdf._validate.projection as validate
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster, RasterMetadata


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

    def test_missing_raster(_, araster, assert_contains):
        raster = Raster(araster)
        with pytest.raises(MissingTransformError) as error:
            validate.bounds(raster)
        assert_contains(error, "does not have an affine Transform")

    def test_missing_metadata(_, araster, assert_contains):
        raster = RasterMetadata(araster.shape)
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
        assert_contains(
            error, "must be a BoundingBox, Raster, RasterMetadata, dict, list, or tuple"
        )


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
            error,
            "must be a Transform, Raster, RasterMetadata, dict, list, tuple, or affine.Affine",
        )
