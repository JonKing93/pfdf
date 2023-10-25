import numpy as np
import pytest

from pfdf._utils import aslist, astuple, clean_dims, real

#####
# Misc
#####


def test_real():
    assert real == [np.integer, np.floating, np.bool_]


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


class TestCleanDims:
    def test_clean(_):
        a = np.ones((4, 4, 1))
        output = clean_dims(a, keepdims=False)
        assert output.shape == (4, 4)
        assert np.array_equal(output, np.ones((4, 4)))

    def test_no_clean(_):
        a = np.ones((4, 4, 1))
        output = clean_dims(a, keepdims=True)
        assert output.shape == (4, 4, 1)
        assert np.array_equal(a, output)
