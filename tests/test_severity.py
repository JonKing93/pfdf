"""
test_severity  Unit tests for the severity module
"""

from pathlib import Path

import numpy as np
import pytest

from pfdf import severity
from pfdf._rasters import Raster as _Raster
from pfdf.errors import ShapeError
from pfdf.rasters import Raster

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
    return np.array([[1, 1, 3, 2], [1, 4, 1, 2], [4, 4, 1, 4]]).astype("int64")


@pytest.fixture
def thresholds():
    return [0, 300, 700]


# The expected estimate for thresholds [0, 300, 700]
@pytest.fixture
def estimate_thresh():
    return np.array([[1, 2, 2, 2], [1, 4, 1, 2], [3, 3, 1, 4]]).astype("int64")


# The expected severity estimate when -1 is NoData
@pytest.fixture
def estimate_nodata():
    return np.array([[0, 1, 3, 2], [1, 4, 0, 2], [4, 4, 0, 4]]).astype("int64")


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
        assert np.array_equal(output.array, expected)

    def test_multiple(_, rseverity):
        levels = ["high", "moderate"]
        output = severity.mask(rseverity, levels)
        expected = (rseverity == 3) | (rseverity == 4)
        assert np.array_equal(output.array, expected)

    def test_save(_, rseverity, tmp_path):
        path = Path(tmp_path) / "output.tif"
        levels = ["high", "moderate"]
        output = severity.mask(rseverity, levels, path=path)

        assert path.is_file()
        assert output == path
        output = _Raster(path)
        expected = (rseverity == 3) | (rseverity == 4)
        expected = expected.astype("int8")
        assert np.array_equal(output.values, expected)


class TestEstimate:
    def test(_, dnbr, estimate):
        output = severity.estimate(dnbr)
        assert np.array_equal(output.array, estimate)

    def test_thresholds(_, dnbr, thresholds, estimate_thresh):
        output = severity.estimate(dnbr, thresholds)
        assert np.array_equal(output.array, estimate_thresh)

    def test_nodata(_, dnbr, estimate_nodata):
        dnbr = Raster(dnbr, nodata=-1)
        output = severity.estimate(dnbr)
        assert np.array_equal(output.array, estimate_nodata)

    def test_save(_, dnbr, estimate, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output = severity.estimate(dnbr, path=path)

        assert path.is_file()
        assert output == path
        output = _Raster(path)
        assert np.array_equal(output.values, estimate)
