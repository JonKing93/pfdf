"""
test_nodata  Unit tests for the nodata module
"""

import numpy as np
import pytest

from pfdf import _nodata as nodata


@pytest.fixture
def araster():
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


class TestDefault:
    @pytest.mark.parametrize("dtype", ("float32", "float64"))
    def test_float(_, dtype):
        output = nodata.default(dtype)
        assert np.isnan(output)

    @pytest.mark.parametrize(
        "dtype, expected",
        (("uint16", 0), ("uint32", 0), ("int16", -32768), ("int32", -2147483648)),
    )
    def test_int(_, dtype, expected):
        output = nodata.default(dtype)
        assert output == expected

    def test_bool(_):
        output = nodata.default(bool)
        assert output == False


class TestIsIn:
    def test_none(_, araster):
        assert nodata.isin(araster, None) == False

    def test_nan(_, araster):
        assert nodata.isin(araster, np.nan) == False
        araster[0, 0] = np.nan
        assert nodata.isin(araster, np.nan) == True

    def test_number(_, araster):
        assert nodata.isin(araster, 5) == True
        assert nodata.isin(araster, -999) == False


class TestMask:
    def test_none(_, araster):
        output = nodata.mask(araster, None)
        assert output is None

    def test_number(_, araster):
        araster[araster >= 6] = -999
        output = nodata.mask(araster, -999)
        assert np.array_equal(output, araster == -999)

    def test_nan(_, araster):
        araster = araster.astype(float)
        araster[araster >= 6] = np.nan
        output = nodata.mask(araster, np.nan)
        assert np.array_equal(output, np.isnan(araster))

    def test_number_invert(_, araster):
        araster[araster >= 6] = -999
        output = nodata.mask(araster, -999, invert=True)
        assert np.array_equal(output, araster != -999)

    def test_nan_invert(_, araster):
        araster = araster.astype(float)
        araster[araster >= 6] = np.nan
        output = nodata.mask(araster, np.nan, invert=True)
        assert np.array_equal(output, ~np.isnan(araster))
