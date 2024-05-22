import numpy as np
import pytest

from pfdf.utils import nodata


class TestDefault:
    def test_float(_):
        output = nodata.default(float)
        assert np.isnan(output)

    def test_int(_):
        assert nodata.default("int16") == np.iinfo("int16").min

    def test_uint(_):
        assert nodata.default("uint16") == np.iinfo("uint16").max

    def test_bool(_):
        assert nodata.default(bool) == False

    def test_other(_):
        assert nodata.default(str) is None


class TestMask:
    def test_number(_, araster):
        araster[araster >= 6] = -999
        output = nodata.mask(araster, -999)
        assert np.array_equal(output, araster == -999)

    def test_nan(_, araster):
        araster = araster.astype(float)
        araster[araster >= 6] = np.nan
        output = nodata.mask(araster, np.nan)
        assert np.array_equal(output, np.isnan(araster))

    def test_none(_, araster):
        output = nodata.mask(araster, None)
        expected = np.zeros(araster.shape, bool)
        assert np.array_equal(output, expected)

    def test_invert(_, araster):
        output = nodata.mask(araster, None, invert=True)
        expected = np.ones(araster.shape, bool)
        assert np.array_equal(output, expected)

    def test_invalid(_, araster, assert_contains):
        with pytest.raises(TypeError) as error:
            nodata.mask(araster, "invalid")
        assert_contains(error, "nodata")
