import operator
from math import nan

import numpy as np
import pytest

from pfdf._utils import nodata
from pfdf._utils.nodata import NodataMask

#####
# Functions
#####


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


class TestEqual:
    @pytest.mark.parametrize("value", (-999, None, nan))
    def test_equal(_, value):
        assert nodata.equal(value, value)

    def test_mixed_none(_):
        assert not nodata.equal(-999, None)

    def test_mixed_nan(_):
        assert not nodata.equal(-999, nan)

    def test_nan_none(_):
        assert not nodata.equal(nan, None)


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


#####
# NodataMask Init
#####


class TestInit:
    def test_none(_, araster):
        output = NodataMask(araster, None)
        assert isinstance(output, NodataMask)
        assert output.mask is None
        assert output.size == araster.size

    def test_invert_none(_, araster):
        output = NodataMask(araster, None, invert=True)
        assert isinstance(output, NodataMask)
        assert output.mask is None
        assert output.size == araster.size

    def test_nodata(_, araster):
        output = NodataMask(araster, nodata=8)
        expected = araster == 8
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == araster.size

    def test_invert_nodata(_, araster):
        output = NodataMask(araster, nodata=8, invert=True)
        expected = araster != 8
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == araster.size

    def test_multiple_nodata(_, araster):
        output = NodataMask(araster, nodata=[3, 8, 9])
        expected = (araster == 3) | (araster == 8)
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == araster.size

    def test_invert_multiple_nodata(_, araster):
        output = NodataMask(araster, nodata=[3, 8, 9], invert=True)
        expected = ~np.isin(araster, [3, 8])
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == araster.size


#####
# Logical operators
#####


class TestLogical:
    def test_object(_, araster):
        mask = NodataMask(araster, 8)
        other = NodataMask(araster, 7)
        expected = (araster == 8) | (araster == 7)
        output = mask._logical(operator.or_, other)
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == mask.size

    def test_both_none(_, araster):
        mask = NodataMask(araster, None)
        output = mask._logical(operator.or_, None)
        assert isinstance(output, NodataMask)
        assert output.mask is None
        assert output.size == mask.size

    def test_self_none(_, araster):
        mask = NodataMask(araster, None)
        other = araster == 8
        output = mask._logical(operator.or_, other)
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, other)
        assert output.size == mask.size

    def test_other_none(_, araster):
        mask = NodataMask(araster, 8)
        other = None
        output = mask._logical(operator.or_, other)
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, araster == 8)
        assert output.size == mask.size

    def test_neither_none(_, araster):
        mask = NodataMask(araster, 8)
        other = araster == 7
        expected = (araster == 8) | (araster == 7)
        output = mask._logical(operator.or_, other)
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == mask.size


class TestOr:
    def test_object(_, araster):
        mask = NodataMask(araster, 8)
        other = NodataMask(araster, 7)
        expected = (araster == 8) | (araster == 7)
        output = mask | other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == mask.size

    def test_both_none(_, araster):
        mask = NodataMask(araster, None)
        output = mask | None
        assert isinstance(output, NodataMask)
        assert output.mask is None
        assert output.size == mask.size

    def test_self_none(_, araster):
        mask = NodataMask(araster, None)
        other = araster == 8
        output = mask | other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, other)
        assert output.size == mask.size

    def test_other_none(_, araster):
        mask = NodataMask(araster, 8)
        other = None
        output = mask | other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, araster == 8)
        assert output.size == mask.size

    def test_neither_none(_, araster):
        mask = NodataMask(araster, 8)
        other = araster == 7
        expected = (araster == 8) | (araster == 7)
        output = mask | other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == mask.size


class TestAnd:
    def test_object(_):
        araster = np.array([1, 2, 3, 4, 7, 7, 7, 7])
        braster = np.array([1, 2, 3, 4, 7, 8, 8, 8])
        mask = NodataMask(araster, 7)
        other = NodataMask(braster, 8)
        expected = (araster == 7) & (braster == 8)
        output = mask & other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == mask.size

    def test_both_none(_, araster):
        mask = NodataMask(araster, None)
        output = mask & None
        assert isinstance(output, NodataMask)
        assert output.mask is None
        assert output.size == mask.size

    def test_self_none(_, araster):
        mask = NodataMask(araster, None)
        other = araster == 8
        output = mask & other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, other)
        assert output.size == mask.size

    def test_other_none(_, araster):
        mask = NodataMask(araster, 8)
        other = None
        output = mask & other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, araster == 8)
        assert output.size == mask.size

    def test_neither_none(_):
        araster = np.array([1, 2, 3, 4, 7, 7, 7, 7])
        braster = np.array([1, 2, 3, 4, 7, 8, 8, 8])
        mask = NodataMask(araster, 7)
        other = braster == 8
        expected = (araster == 7) & (braster == 8)
        output = mask & other
        assert isinstance(output, NodataMask)
        assert np.array_equal(output.mask, expected)
        assert output.size == mask.size


#####
# Workflow methods
#####


class TestFill:
    def test_none(_, araster):
        mask = NodataMask(araster, None)
        output = mask.fill(araster, 0)
        assert np.array_equal(output, araster)

    def test_invert_none(_, araster):
        mask = NodataMask(araster, None)
        output = mask.fill(araster, 0, invert=True)
        expected = np.empty((0, 0), dtype=araster.dtype)
        assert np.array_equal(output, expected)

    def test_to_float(_, araster):
        araster = araster.astype(int)
        mask = NodataMask(araster, 8)
        output = mask.fill(araster, nan)
        assert output.dtype == float
        expected = np.array([1, 2, 3, 4, 5, 6, 7, nan]).reshape(2, 4).astype(float)
        assert np.array_equal(output, expected, equal_nan=True)

    def test_fill(_, araster):
        araster[0, 0:3] = 3
        mask = NodataMask(araster, 3)
        output = mask.fill(araster, 0)
        expected = np.array([0, 0, 0, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)
        assert np.array_equal(output, expected)

    def test_invert_fill(_, araster):
        araster[0, 0:3] = 3
        mask = NodataMask(araster, 3)
        output = mask.fill(araster, 0, invert=True)
        expected = np.array([3, 3, 3, 0, 0, 0, 0, 0]).reshape(2, 4).astype(float)
        assert np.array_equal(output, expected)

    def test_preserve_float32(_, araster):
        araster = araster.astype("float32")
        mask = NodataMask(araster, 8)
        output = mask.fill(araster, nan)
        assert output.dtype == "float32"
        assert output is araster
        expected = np.array([1, 2, 3, 4, 5, 6, 7, nan]).reshape(2, 4).astype("float32")
        assert np.array_equal(output, expected, equal_nan=True)


class TestIsnan:
    def test_none(_):
        assert NodataMask.isnan(None) == False

    def test_numeric(_):
        assert NodataMask.isnan(5.2) == False

    def test_nan(_):
        assert NodataMask.isnan(nan) == True


class TestIndices:
    def test_none(_, araster):
        mask = NodataMask(araster, None, invert=True)
        output = mask.indices()
        expected = np.arange(araster.size)
        assert np.array_equal(output, expected)

    def test_mask(_, araster):
        mask = NodataMask(araster, 8, invert=True)
        output = mask.indices()
        assert np.array_equal(output, range(7))


class TestValues:
    def test_none(_, araster):
        mask = NodataMask(araster, None, invert=True)
        output = mask.values(araster)
        assert output is araster

    def test_mask(_, araster):
        mask = NodataMask(araster, 8, invert=True)
        output = mask.values(araster)
        expected = np.array([1, 2, 3, 4, 5, 6, 7])
        assert np.array_equal(output, expected)
