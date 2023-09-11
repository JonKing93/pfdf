"""
test_utils  Unit tests for low-level package utilities

Requirements:
    * pytest, numpy, rasterio
"""


import numpy as np
import pytest

from pfdf import _utils


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


class TestClassify:
    def test_default(_):
        a = np.array([1, 2, 3, 4, np.nan, 5, 6, 7, np.nan, 8, 9, 10])
        thresholds = [3, 7]
        output = _utils.classify(a, thresholds)
        expected = np.array([1, 1, 1, 2, np.nan, 2, 2, 2, np.nan, 3, 3, 3])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nan(_):
        a = np.array([1, 2, 3, 4, 5, 6, 7])
        thresholds = [3.5]
        output = _utils.classify(a, thresholds, nodata=4)
        expected = np.array([1, 1, 1, np.nan, 2, 2, 2])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nan_to(_):
        a = np.array([1, 2, 3, 4, 5, 6, 7])
        thresholds = [3.5]
        output = _utils.classify(a, thresholds, nodata=4, nodata_to=-999)
        expected = np.array([1, 1, 1, -999, 2, 2, 2])
        assert np.array_equal(output, expected)
