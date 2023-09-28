from math import nan

import numpy as np
import pytest

from pfdf._utils import nodata_


@pytest.fixture
def araster():
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


class TestDefault:
    @pytest.mark.parametrize("dtype", ("float32", "float64"))
    def test_float(_, dtype):
        output = nodata_.default(dtype)
        assert np.isnan(output)

    @pytest.mark.parametrize(
        "dtype, expected",
        (("uint16", 0), ("uint32", 0), ("int16", -32768), ("int32", -2147483648)),
    )
    def test_int(_, dtype, expected):
        output = nodata_.default(dtype)
        assert output == expected

    def test_bool(_):
        output = nodata_.default(bool)
        assert output == False


class TestEqual:
    @pytest.mark.parametrize("value", (-999, None, nan))
    def test_equal(_, value):
        assert nodata_.equal(value, value)

    def test_mixed_none(_):
        assert not nodata_.equal(-999, None)

    def test_mixed_nan(_):
        assert not nodata_.equal(-999, nan)

    def test_nan_none(_):
        assert not nodata_.equal(nan, None)


class TestIsIn:
    def test_none(_, araster):
        assert nodata_.isin(araster, None) == False

    def test_nan(_, araster):
        assert nodata_.isin(araster, np.nan) == False
        araster[0, 0] = np.nan
        assert nodata_.isin(araster, np.nan) == True

    def test_number(_, araster):
        assert nodata_.isin(araster, 5) == True
        assert nodata_.isin(araster, -999) == False


class TestMask:
    def test_none(_, araster):
        output = nodata_.mask(araster, None)
        assert output is None

    def test_number(_, araster):
        araster[araster >= 6] = -999
        output = nodata_.mask(araster, -999)
        assert np.array_equal(output, araster == -999)

    def test_nan(_, araster):
        araster = araster.astype(float)
        araster[araster >= 6] = np.nan
        output = nodata_.mask(araster, np.nan)
        assert np.array_equal(output, np.isnan(araster))

    def test_number_invert(_, araster):
        araster[araster >= 6] = -999
        output = nodata_.mask(araster, -999, invert=True)
        assert np.array_equal(output, araster != -999)

    def test_nan_invert(_, araster):
        araster = araster.astype(float)
        araster[araster >= 6] = np.nan
        output = nodata_.mask(araster, np.nan, invert=True)
        assert np.array_equal(output, ~np.isnan(araster))


class TestFill:
    def test_all_none(_):
        a = np.arange(10).reshape(2, 5)
        masks = (None, None, None)
        output = nodata_.fill(a, masks, 0)
        assert np.array_equal(a, output)

    def test_all_masks(_):
        a = np.arange(10).reshape(2, 5)
        mask1 = np.array([[0, 0, 0, 1, 1], [0, 0, 0, 1, 1]], dtype=bool)
        mask2 = np.array([[1, 1, 0, 0, 0], [0, 0, 0, 1, 1]], dtype=bool)
        expected = np.array([[0, 0, 2, 0, 0], [5, 6, 7, 0, 0]])
        output = nodata_.fill(a, (mask1, mask2), 0)
        assert np.array_equal(output, expected)

    def test_mixed(_):
        a = np.arange(10).reshape(2, 5)
        mask1 = np.array([[0, 0, 0, 1, 1], [0, 0, 0, 1, 1]], dtype=bool)
        expected = np.array([[0, 1, 2, 0, 0], [5, 6, 7, 0, 0]])
        output = nodata_.fill(a, (mask1, None), 0)
        assert np.array_equal(output, expected)
