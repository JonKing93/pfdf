"""
test_severity  Unit tests for the severity module
"""

from pathlib import Path

import numpy as np
import pytest

from dfha import severity
from dfha.errors import ShapeError
from dfha.utils import load_raster

#####
# Testing utilities
#####


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


# A severity raster
@pytest.fixture
def rseverity():
    severity = np.array(
        [
            [-1, -1, 2, 4],
            [3, 2, 4, 2],
            [3, -1, -1, 1],
        ]
    )
    return severity


# A dnbr raster
@pytest.fixture
def dnbr():
    return np.array(
        [
            [-1, 100, 300, 250],
            [-22, 1000, -1, 200],
            [600, 700, -1, 800],
        ]
    )


# The expected severity estimate
@pytest.fixture
def estimate():
    return np.array([[1, 1, 3, 3], [1, 4, 1, 2], [4, 4, 1, 4]]).astype("int8")


@pytest.fixture
def thresholds():
    return [0, 300, 700]


# The expected estimate for thresholds [0, 300, 700]
@pytest.fixture
def estimate_thresh():
    return np.array([[1, 2, 3, 2], [1, 4, 1, 2], [3, 4, 1, 4]]).astype("int8")


# The expected severity estimate when -1 is NoData
@pytest.fixture
def estimate_nodata():
    return np.array([[0, 1, 3, 3], [1, 4, 0, 2], [4, 4, 0, 4]]).astype("int8")


#####
# Module Utilities
#####


class TestValidateDescriptions:
    def test_string(_):
        output = severity._validate_descriptions("moderate")
        assert output == set(["moderate"])

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            severity._validate_descriptions(5)
        assert_contains(error, "not a string")

    def test_sequence(_):
        input = ["moderate", "high"]
        output = severity._validate_descriptions(input)
        assert output == set(input)

    def test_recognized(_):
        input = ["moderate", "high"]
        output = severity._validate_descriptions(input)
        assert output == set(input)

    def test_unrecognized(_):
        input = ["moderate", "valid"]
        with pytest.raises(ValueError) as error:
            severity._validate_descriptions(input)
        assert_contains(error, "unburned", "low", "moderate", "high")

    def test_repeat(_):
        input = ["moderate", "high", "high", "high"]
        output = severity._validate_descriptions(input)
        assert output == set(input)


class TestValidateThresholds:
    def test_sequence(_):
        values = [1, 2, 3]
        output = severity._validate_thresholds(values)
        expected = np.array(values).reshape(-1)
        assert np.array_equal(output, expected)

    def test_numpy(_):
        values = np.array([1, 2, 3])
        output = severity._validate_thresholds(values)
        assert np.array_equal(output, values)

    @pytest.mark.parametrize("values", ([1, 2], [1, 2, 3, 4]))
    def test_not_3(_, values):
        with pytest.raises(ShapeError):
            severity._validate_thresholds(values)

    def test_invalid(_):
        with pytest.raises(TypeError):
            severity._validate_thresholds("invalid")

    def test_unsorted(_):
        values = [2, 1, 3]
        with pytest.raises(ValueError) as error:
            severity._validate_thresholds(values)
        assert_contains(error, "unburned-low", "low-moderate")

    def test_nan(_):
        values = np.full((3,), np.nan)
        with pytest.raises(ValueError):
            severity._validate_thresholds(values)


class TestCompare:
    def test_valid(_):
        values = np.array([1, 2])
        names = ["test1", "test2"]
        severity._compare(values, names)

    def test_invalid(_):
        values = np.array([2, 1])
        names = ["test1", "test2"]
        with pytest.raises(ValueError) as error:
            severity._compare(values, names)
        assert_contains(error, "test1", "test2")


class TestClassify:
    def test(_, rseverity, dnbr):
        expected = np.zeros(rseverity.shape, dtype=float)
        thresholds = [200, 700]
        mask = (dnbr >= thresholds[0]) & (dnbr < thresholds[1])
        expected[mask] = 4

        array = np.zeros(rseverity.shape, dtype=float)
        severity._classify(array, dnbr, thresholds, 4)
        assert np.array_equal(array, expected)


#####
# User Functions
#####


class TestClassification:
    def test(_):
        output = severity.classification()
        assert output == {1: "unburned", 2: "low", 3: "moderate", 4: "high"}


class TestMask:
    def test_single(_, rseverity):
        output = severity.mask(rseverity, "moderate")
        expected = rseverity == 3
        assert np.array_equal(output, expected)

    def test_multiple(_, rseverity):
        levels = ["high", "moderate"]
        output = severity.mask(rseverity, levels)
        expected = (rseverity == 3) | (rseverity == 4)
        assert np.array_equal(output, expected)

    def test_save(_, rseverity, tmp_path):
        path = Path(tmp_path) / "output.tif"
        levels = ["high", "moderate"]
        output = severity.mask(rseverity, levels, path=path)

        assert path.is_file()
        assert output == path
        output = load_raster(path)
        expected = (rseverity == 3) | (rseverity == 4)
        expected = expected.astype("int8")
        assert np.array_equal(output, expected)


class TestEstimate:
    def test(_, dnbr, estimate):
        output = severity.estimate(dnbr)
        assert np.array_equal(output, estimate)

    def test_thresholds(_, dnbr, thresholds, estimate_thresh):
        output = severity.estimate(dnbr, thresholds)
        assert np.array_equal(output, estimate_thresh)

    def test_nodata(_, dnbr, estimate_nodata):
        output = severity.estimate(dnbr, nodata=-1)
        assert np.array_equal(output, estimate_nodata)

    def test_save(_, dnbr, estimate, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output = severity.estimate(dnbr, path=path)

        assert path.is_file()
        assert output == path
        output = load_raster(path)
        assert np.array_equal(output, estimate)
