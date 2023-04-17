"""
test_validate  Unit tests for user-input validation functions
"""

import pytest
import numpy as np
from dfha import validate

#####
# Fixtures
#####


@pytest.fixture
def array():
    return np.arange(1, 51).reshape(10, 5)


###
# Low-level
###


class TestCheckBound:
    def assert_contains(error, *strings):
        message = error.value.args[0]
        for string in strings:
            assert string in message

    def test_pass(_, array):
        min = np.amin(array)
        max = np.amax(array)
        validate._check_bound(array, "", "<", max + 1)
        validate._check_bound(array, "", "<=", max)
        validate._check_bound(array, "", ">=", min)
        validate._check_bound(array, "", ">", min - 1)

    def test_fail(self, array):
        min = np.amin(array)
        max = np.amax(array)
        name = "test name"

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", "<", max)
            self.assert_contains(error, name, "less than")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", "<=", max - 1)
            self.assert_contains(error, name, "less than or equal to")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", ">=", min + 1)
            self.assert_contains(error, name, "greater than or equal to")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", ">", min)
            self.assert_contains(error, name, "greater than")


class TestShapeError:
    def test(_):
        error = validate.ShapeError("array", "elements", 5, 6)
        assert isinstance(error, Exception)
        assert error.required == 5
        assert error.actual == 6
        assert (
            error.args[0]
            == "array must have 5 elements, but it has 6 elements instead."
        )


class TestDimensionError:
    def test(_):
        message = "test message"
        error = validate.DimensionError(message)
        assert isinstance(error, Exception)
        assert error.args[0] == message


class TestNonsingleton:
    def test(_):
        array = np.arange(0, 36).reshape(2, 1, 1, 3, 1, 6)
        tf = [True, False, False, True, False, True]
        assert validate.nonsingleton(array) == tf
