"""
test_cannon2010  Unit tests for the cannon2010 module
"""

import numpy as np
import pytest

from pfdf.errors import DimensionError
from pfdf.models import cannon2010 as c10


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


#####
# Validation tests
#####


class TestValidateProbabilities:
    def test_valid(_):
        p = [0, 0.25, np.nan, 0.7, 1]
        output = c10._validate_probabilities(p)
        assert np.array_equal(output, np.array(p), equal_nan=True)

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            c10._validate_probabilities("invalid")
        assert_contains(error, "probabilities")

    @pytest.mark.parametrize("bad", (-1, 2))
    def test_invalid_range(_, bad):
        p = np.array([0.2, bad, 0.6])
        with pytest.raises(ValueError) as error:
            c10._validate_probabilities(p)
        assert_contains(error, "probabilities")


class TestValidateVolumes:
    def test_valid(_):
        v = [0, 1, np.nan, 1e3, 1e5, 1e9]
        output = c10._validate_volumes(v)
        assert np.array_equal(output, np.array(v), equal_nan=True)

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            c10._validate_volumes("invalid")
        assert_contains(error, "volumes")

    def test_negative(_):
        v = [-5, 10, 100]
        with pytest.raises(ValueError) as error:
            c10._validate_volumes(v)
        assert_contains(error, "volumes")


class TestThresholds:
    def test_valid(_):
        # Base case
        t = [0.2, 0.5, 0.7, 0.8]
        output = c10._validate_thresholds(t, "")
        assert np.array_equal(output, np.array(t))

        # Valid within a range
        output = c10._validate_thresholds(t, "", range=[0, 1])
        assert np.array_equal(output, np.array(t))

        # Valid and integers
        t = [1, 2, 3]
        output = c10._validate_thresholds(t, "", integers=True)
        assert np.array_equal(output, np.array(t))

    def test_nan(_):
        t = [0.2, np.nan, 0.7]
        with pytest.raises(ValueError) as error:
            c10._validate_thresholds(t, "test name")
        assert_contains(error, "test name")

    def test_not_vector(_):
        t = np.arange(10).reshape(2, 5)
        with pytest.raises(DimensionError) as error:
            c10._validate_thresholds(t, "test name")
        assert_contains(error, "test name")

    def test_out_of_range(_):
        t = [0.1, 0.2, 3]
        with pytest.raises(ValueError) as error:
            c10._validate_thresholds(t, "test name", range=[0, 1])
        assert_contains(error, "test name")

    def test_not_sorted(_):
        t = [0.2, 0.1, 0.3]
        with pytest.raises(ValueError) as error:
            c10._validate_thresholds(t, "test name")
        assert_contains(error, "test name", "sorted")

    def test_not_integers(_):
        t = [0.1, 0.2, 0.3]
        with pytest.raises(ValueError) as error:
            c10._validate_thresholds(t, "test name", integers=True)
        assert_contains(error, "test name", "integers")


#####
# User Tests
#####


class TestPscore:
    def test_default(_):
        p = [
            0,
            0.1,
            0.2,
            0.25,
            np.nan,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.75,
            np.nan,
            0.8,
            0.9,
            1,
        ]
        output = c10.pscore(p)
        expected = np.array([1, 1, 1, 1, np.nan, 2, 2, 2, 3, 3, 3, np.nan, 4, 4, 4])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_thresholds(_):
        p = [
            0,
            0.1,
            0.2,
            0.25,
            np.nan,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.75,
            np.nan,
            0.8,
            0.9,
            1,
        ]
        thresholds = [0.2, 0.4, 0.6, 0.8]
        output = c10.pscore(p, thresholds)
        expected = [1, 1, 1, 2, np.nan, 2, 2, 3, 3, 4, 4, np.nan, 4, 5, 5]
        assert np.array_equal(output, expected, equal_nan=True)


class TestVscore:
    def test_default(_):
        v = [0, 1, 100, 1e3, np.nan, 2e3, 1e4, 2e4, 1e5, 2e5, np.nan]
        output = c10.vscore(v)
        expected = np.array([1, 1, 1, 1, np.nan, 2, 2, 3, 3, 4, np.nan])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_thresholds(_):
        v = [0, 1, 100, 1e3, np.nan, 2e3, 1e4, 2e4, 1e5, 2e5, np.nan]
        thresholds = [1e2, 1e3, 1e4, 1e5]
        output = c10.vscore(v, thresholds)
        expected = np.array([1, 1, 1, 2, np.nan, 3, 3, 4, 4, 5, np.nan])
        assert np.array_equal(output, expected, equal_nan=True)


class TestHscore:
    def test_default(_):
        h = [1, 2, 3, np.nan, 4, 5, np.nan, 6, 7, 8, 9]
        output = c10.hscore(h)
        expected = np.array([1, 1, 1, np.nan, 2, 2, np.nan, 2, 3, 3, 3])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_thresholds(_):
        h = [1, 2, 3, np.nan, 4, 5, np.nan, 6, 7, 8, 9]
        thresholds = [2, 4, 6, 8]
        output = c10.hscore(h, thresholds)
        expected = np.array([1, 1, 2, np.nan, 2, 3, np.nan, 3, 4, 4, 5])
        assert np.array_equal(output, expected, equal_nan=True)


class TestHazard:
    def test_default(_):
        p = [0.1] * 5 + [0.3] * 5 + [0.7] * 5 + [1] * 5
        v = [np.nan, 0, 2e3, 2e4, 2e5] * 4
        output = c10.hazard(p, v)
        expected = np.array(
            [
                np.nan,
                1,
                1,
                2,
                2,
                np.nan,
                1,
                2,
                2,
                2,
                np.nan,
                2,
                2,
                2,
                3,
                np.nan,
                2,
                2,
                3,
                3,
            ]
        )
        assert np.array_equal(output, expected, equal_nan=True)

    def test_thresholds(_):
        p = [0.1] * 5 + [0.3] * 5 + [0.7] * 5 + [1] * 5
        v = [np.nan, 0, 2e3, 2e4, 2e5] * 4
        p_thresholds = [0.2, 0.4, 0.6, 0.8]
        v_thresholds = [1e2, 1e3, 1e4, 1e5]
        h_thresholds = [2, 4, 6, 8]

        expected = np.array(
            [
                np.nan,
                1,
                2,
                3,
                3,
                np.nan,
                2,
                3,
                3,
                4,
                np.nan,
                3,
                4,
                4,
                5,
                np.nan,
                3,
                4,
                5,
                5,
            ]
        )
        output = c10.hazard(
            p,
            v,
            p_thresholds=p_thresholds,
            v_thresholds=v_thresholds,
            h_thresholds=h_thresholds,
        )
        assert np.array_equal(output, expected, equal_nan=True)

    def test_broadcast(_):
        p = np.arange(0, 1.1, 0.1).reshape(-1, 1)
        v = np.array(
            [10e0, 10e1, 10e2, 20e2, 10e3, 20e3, 10e4, 20e4, 10e5, 20e5]
        ).reshape(1, -1)

        expected = np.array(
            [
                [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0],
                [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0],
                [2.0, 2.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 3.0, 3.0],
                [2.0, 2.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 3.0, 3.0],
                [2.0, 2.0, 2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 3.0, 3.0],
            ]
        )
        output = c10.hazard(p, v)
        assert np.array_equal(output, expected)

    def test_invalid_broadcast(_):
        p = np.arange(0, 1.1, 0.1).reshape(-1)
        v = np.array(
            [10e0, 10e1, 10e2, 20e2, 10e3, 20e3, 10e4, 20e4, 10e5, 20e5]
        ).reshape(-1)
        with pytest.raises(ValueError) as error:
            c10.hazard(p, v)
        assert_contains(error, "probabilities", "volumes", "broadcast")
