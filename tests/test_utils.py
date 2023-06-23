"""
test_utils  Unit tests for low-level package utilities

Requirements:
    * pytest, numpy, rasterio
"""


import numpy as np
import pytest

from dfha import _utils


#####
# Fixtures
#####
@pytest.fixture
def band1():
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


#####
# Misc
#####


def test_real():
    assert _utils.real == [np.integer, np.floating, np.bool_]


@pytest.mark.parametrize(
    "input, expected",
    (
        ((1, 2, 3), True),
        ((True,), True),
        ((False,), True),
        ((1, None, "test"), True),
        ((None, None, False), True),
        ((None,), False),
        ((None, None, None), False),
    ),
)
def test_any_defined(input, expected):
    assert _utils.any_defined(*input) == expected


#####
# Sequences
#####


@pytest.mark.parametrize(
    "input, expected",
    (
        (1, [1]),
        ([1, 2, 3], [1, 2, 3]),
        ("test", ["test"]),
        ({"a": "test"}, [{"a": "test"}]),
        ((1, 2, 3), [1, 2, 3]),
    ),
)
def test_aslist(input, expected):
    assert _utils.aslist(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    (
        (1, (1,)),
        ([1, 2, 3], (1, 2, 3)),
        ("test", ("test",)),
        ({"a": "test"}, ({"a": "test"},)),
        ((1, 2, 3), (1, 2, 3)),
    ),
)
def test_astuple(input, expected):
    assert _utils.astuple(input) == expected


#####
# NoData
#####


@pytest.mark.parametrize("function", (_utils.data_mask, _utils.isdata))
class TestDataMask:
    def test_none(_, function, band1):
        output = function(band1, None)
        assert output is None

    def test_number(_, function, band1):
        band1[band1 >= 6] = -999
        output = function(band1, -999)
        assert np.array_equal(output, band1 != -999)

    def test_nan(_, function, band1):
        band1 = band1.astype(float)
        band1[band1 >= 6] = np.nan
        output = function(band1, np.nan)
        assert np.array_equal(output, ~np.isnan(band1))


@pytest.mark.parametrize("function", (_utils.nodata_mask, _utils.isnodata))
class TestNodataMask:
    def test_none(_, function, band1):
        output = function(band1, None)
        assert output is None

    def test_number(_, function, band1):
        band1[band1 >= 6] = -999
        output = function(band1, -999)
        assert np.array_equal(output, band1 == -999)

    def test_nan(_, function, band1):
        band1 = band1.astype(float)
        band1[band1 >= 6] = np.nan
        output = function(band1, np.nan)
        assert np.array_equal(output, np.isnan(band1))


class TestHasNodata:
    def test_none(_, band1):
        assert _utils.has_nodata(band1, None) == False

    def test_nan(_, band1):
        assert _utils.has_nodata(band1, np.nan) == False
        band1[0, 0] = np.nan
        assert _utils.has_nodata(band1, np.nan) == True

    def test_number(_, band1):
        assert _utils.has_nodata(band1, 5) == True
        assert _utils.has_nodata(band1, -999) == False
