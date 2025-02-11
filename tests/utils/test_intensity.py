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
    def test_scalar_R(_):
        R15 = 5
        output = intensity.from_accumulation(R15, 15)
        assert output == 20

    def test_vector_R(_):
        R15 = np.array([5, 6, 7, 10]).reshape(-1)
        output = intensity.from_accumulation(R15, 15)
        expected = np.array([20, 24, 28, 40]).reshape(4)
        assert np.array_equal(output, expected)

    def test_array_R(_):
        R = np.array(
            [
                [1, 1, 1],
                [2, 2, 2],
            ]
        ).reshape((1, 2, 3))
        durations = [15, 30, 60]
        output = intensity.from_accumulation(R, durations)
        expected = np.array(
            [
                [4, 2, 1],
                [8, 4, 2],
            ]
        ).reshape((1, 2, 3))
        assert np.array_equal(output, expected)

    def test_invalid_R(_, assert_contains):
        with pytest.raises(TypeError) as error:
            intensity.from_accumulation("invalid", 15)
        assert_contains(
            error, "dtype of rainfall accumulations (R)", "not an allowed dtype"
        )

    def test_dim(_):
        R = np.array(
            [
                [1, 2],
                [1, 2],
                [1, 2],
            ]
        ).reshape(1, 3, 2)
        durations = [15, 30, 60]
        output = intensity.from_accumulation(R, durations, dim=1)
        expected = np.array(
            [
                [4, 8],
                [2, 4],
                [1, 2],
            ]
        ).reshape((1, 3, 2))
        assert np.array_equal(output, expected)

    def test_dim_small_ndim(_):
        R = np.array(
            [
                [1, 1, 1],
                [2, 2, 2],
            ]
        )
        output = intensity.from_accumulation(R, durations=15, dim=5)
        expected = np.array(
            [
                [4, 4, 4],
                [8, 8, 8],
            ]
        ).reshape((2, 3, 1, 1, 1, 1))
        assert np.array_equal(output, expected)

    def test_scalar_durations(_):
        R = np.array(
            [
                [1, 1, 1],
                [2, 2, 2],
            ]
        ).reshape((1, 2, 3))
        durations = 15
        output = intensity.from_accumulation(R, durations)
        expected = np.array(
            [
                [4, 4, 4],
                [8, 8, 8],
            ]
        ).reshape((1, 2, 3))
        assert np.array_equal(output, expected)

    def test_vector_durations(_):
        R = np.array(
            [
                [1, 1, 1],
                [2, 2, 2],
            ]
        ).reshape((1, 2, 3))
        durations = [15, 30, 60]
        output = intensity.from_accumulation(R, durations)
        expected = np.array(
            [
                [4, 2, 1],
                [8, 4, 2],
            ]
        ).reshape((1, 2, 3))
        assert np.array_equal(output, expected)

    def test_durations_invalid_length(_, assert_contains):
        R = np.array(
            [
                [1, 1, 1],
                [2, 2, 2],
            ]
        )
        durations = [15, 30]
        with pytest.raises(ShapeError) as error:
            intensity.from_accumulation(R, durations)
        assert_contains(
            error,
            "The length of the durations vector must either be 1 or 3 (scalar or R.shape[-1])",
        )
