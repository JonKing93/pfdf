import numpy as np
import pytest

from pfdf._utils import aslist, astuple, classify, real

#####
# Misc
#####


def test_real():
    assert real == [np.integer, np.floating, np.bool_]


class TestClassify:
    def test_default(_):
        a = np.array([1, 2, 3, 4, np.nan, 5, 6, 7, np.nan, 8, 9, 10])
        thresholds = [3, 7]
        output = classify(a, thresholds)
        expected = np.array([1, 1, 1, 2, np.nan, 2, 2, 2, np.nan, 3, 3, 3])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nan(_):
        a = np.array([1, 2, 3, 4, 5, 6, 7])
        thresholds = [3.5]
        output = classify(a, thresholds, nodata=4)
        expected = np.array([1, 1, 1, np.nan, 2, 2, 2])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nan_to(_):
        a = np.array([1, 2, 3, 4, 5, 6, 7])
        thresholds = [3.5]
        output = classify(a, thresholds, nodata=4, nodata_to=-999)
        expected = np.array([1, 1, 1, -999, 2, 2, 2])
        assert np.array_equal(output, expected)


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
    assert aslist(input) == expected


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
    assert astuple(input) == expected
