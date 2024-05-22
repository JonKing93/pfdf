import numpy as np
import pytest

from pfdf.errors import ShapeError
from pfdf.utils import intensity


class TestToAccumulation:
    def test_scalar(_):
        I = [20, 24, 28, 40]
        output = intensity.to_accumulation(I, 15)
        assert np.array_equal(output, [5, 6, 7, 10])

    def test_vector(_):
        I = [20, 30]
        durations = [15, 30]
        output = intensity.to_accumulation(I, durations)
        expected = (5, 15)
        assert np.array_equal(output, expected)

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            intensity.to_accumulation("invalid", 15)
        assert_contains(error, "rainfall intensities (I)")

    def test_invalid_length(_, assert_contains):
        with pytest.raises(ShapeError) as error:
            intensity.to_accumulation([1, 2, 3], [4, 5])
        assert_contains(error, "The length of the durations vector", "3")


class TestFromAccumulation:
    def test_scalar(_):
        R15 = np.array([5, 6, 7, 10]).reshape(-1)
        output = intensity.from_accumulation(R15, 15)
        expected = np.array([20, 24, 28, 40]).reshape(4, 1)
        assert np.array_equal(output, expected)

    def test_vector(_):
        R = np.array([[5, 15], [5.5, 16], [6, 17]])
        durations = [15, 30]
        output = intensity.from_accumulation(R, durations)
        expected = np.array(
            [
                [20, 30],
                [22, 32],
                [24, 34],
            ]
        )
        assert np.array_equal(output, expected)

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            intensity.from_accumulation("invalid", 15)
        assert_contains(error, "rainfall accumulations (R)")

    def test_invalid_length(_, assert_contains):
        R = np.array([[5, 15], [5.5, 16], [6, 17]])
        durations = [1, 2, 3]
        with pytest.raises(ShapeError) as error:
            intensity.from_accumulation(R, durations)
        assert_contains(error, "length of the durations vector", "2")
