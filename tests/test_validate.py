"""
test_validate  Unit tests for user-input validation functions
"""

import pytest
import numpy as np
from dfha import validate

#####
# Fixtures and testing utilities
#####


@pytest.fixture
def array():
    return np.arange(1, 51).reshape(10, 5)

def assert_contains(error, *strings):
    message = error.value.args[0]
    print(repr(message))
    for string in strings:
        assert string in message

###
# Low-level
###


class TestCheckBound:

    def test_pass(_, array):
        min = np.amin(array)
        max = np.amax(array)
        validate._check_bound(array, "", "<", max + 1)
        validate._check_bound(array, "", "<=", max)
        validate._check_bound(array, "", ">=", min)
        validate._check_bound(array, "", ">", min - 1)

    def test_fail(_, array):
        min = np.amin(array)
        max = np.amax(array)
        name = "test name"

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", "<", max)
            assert_contains(error, name, "less than")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", "<=", max - 1)
            assert_contains(error, name, "less than or equal to")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", ">=", min + 1)
            assert_contains(error, name, "greater than or equal to")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, "test name", ">", min)
            assert_contains(error, name, "greater than")


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


class TestShape:
    name = 'test name'
    axes = ['rows', 'columns']
    shape = (10,5)

    @pytest.mark.parametrize('required, axis', [((2,5), 'rows'), ((10,2), 'columns')])
    def test_failed(self, required, axis):
        with pytest.raises(validate.ShapeError) as error:
            validate.shape_(self.name, self.axes, required, self.shape)
        assert_contains(error, self.name, axis)


    def test_none(self):
        validate.shape_(self.name, self.axes, None, self.shape)
        
    def test_pass(self):
        validate.shape_(self.name, self.axes, self.shape, self.shape)

    def test_skip(self):
        required = (-1, self.shape[1])
        validate.shape_(self.name, self.axes, required, self.shape)


class TestDtype:
    name = 'test name'
    dtype = np.integer
    string = 'numpy.integer'

    @pytest.mark.parametrize('allowed, string', [(np.bool_, 'numpy.bool_'), ([np.floating, np.bool_], 'numpy.floating')])
    def test_failed(self, allowed, string):
        with pytest.raises(TypeError) as error:
            validate.dtype_(self.name, allowed, self.dtype)
        assert_contains(error, self.name, string, self.string)

    def test_none(self):
        validate.dtype_(self.name, None, self.dtype)

    @pytest.mark.parametrize('allowed', [(np.integer), ([np.floating, np.integer])])
    def test_pass(self, allowed):
        validate.dtype_(self.name, allowed, self.dtype)


