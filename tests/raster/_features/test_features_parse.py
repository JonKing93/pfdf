from math import isnan

import numpy as np
import pytest

from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster._features import _parse


class TestDtype:
    def test_no_field(_):
        output = _parse.dtype(None, None, None)
        assert output == np.dtype(bool)

    def test_user(_):
        dtype = np.dtype("uint16")
        output = _parse.dtype("test", {}, dtype)
        assert output == np.dtype("uint16")

    def test_int_schema(_):
        props = {"test": "int32"}
        output = _parse.dtype("test", props, None)
        assert output == np.dtype(int)

    def test_float_schema(_):
        props = {"test": "float32"}
        output = _parse.dtype("test", props, None)
        assert output == np.dtype(float)


class TestNodata:
    def test_bool(_):
        assert _parse.nodata(None, "safe", bool) == False

    def test_default(_):
        output = _parse.nodata(None, "safe", float)
        assert isnan(output)

    def test_user(_):
        assert _parse.nodata(5, "safe", float) == 5

    def test_invalid_user(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _parse.nodata(2.2, "safe", int)
        assert_contains(error, "Cannot cast the NoData value")


class TestResolution:
    @pytest.mark.parametrize("units", ("meters", "base"))
    def test_transform(_, units):
        crs = CRS(4326)
        res = Transform(1, 2, 3, 4, crs)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        out1, out2 = _parse.resolution(res, units, crs, bounds)
        assert out1 == (1, 2)
        assert out2 == crs

    def test_reproject_transform(_):
        crs = CRS(26910)
        res = Transform(1, 2, 3, 4, 26911)
        bounds = BoundingBox(0, 100, 500, 1000, crs)
        out1, out2 = _parse.resolution(res, "base", crs, bounds)
        expected = (0.997261140611954, 1.9945226908862739)
        assert np.allclose(out1, expected)
        assert out2 == crs

    def test_inherit_crs(_):
        crs = CRS(4326)
        res = Transform(1, 2, 3, 4, crs)
        bounds = BoundingBox(1, 2, 3, 4, None)
        output = _parse.resolution(res, "base", None, bounds)
        assert output == ((1, 2), crs)

    def test_meters(_):
        crs = CRS(4326)
        res = (10, 10)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        out1, out2 = _parse.resolution(res, "meters", crs, bounds)
        assert out1 == (9.005557863254549e-05, 8.993216059187306e-05)
        assert out2 == crs

    def test_base(_):
        crs = CRS(4326)
        res = (10, 10)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        output = _parse.resolution(res, "base", crs, bounds)
        assert output == ((10, 10), crs)


class TestExtent:
    def test(_):
        bounds = BoundingBox(0, 0, 10, 200)
        resolution = (5, 10)
        out1, out2 = _parse.extent(bounds, resolution)
        assert out1 == Transform(5, -10, 0, 200)
        assert out2 == (20, 2)
