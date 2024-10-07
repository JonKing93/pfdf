import numpy as np
import pytest

import pfdf._validate.core._elements as validate
from pfdf._utils.nodata import NodataMask

#####
# Fixtures
#####


@pytest.fixture
def array():
    return np.arange(1, 51).reshape(10, 5)


@pytest.fixture
def mask():
    return np.array([True, False, False, True]).reshape(2, 2)


#####
# Element Utilities
#####


class TestGetData:
    def test_none(_, array):
        output, mask = validate._get_data(array, None)
        assert np.array_equal(output, array)
        assert isinstance(mask, NodataMask)
        assert mask.mask is None
        assert mask.size == array.size

    def test_nodata(_, array):
        output, mask = validate._get_data(array, 10)
        expected_mask = array != 10
        expected = array[expected_mask]
        assert np.array_equal(output, expected)
        assert isinstance(mask, NodataMask)
        assert np.array_equal(mask.mask, expected_mask)
        assert mask.size == array.size

    def test_multiple_nodata(_, array):
        output, mask = validate._get_data(array, [None, 10, 11, np.nan])
        expected_mask = ~np.isin(array, [10, 11])
        expected = array[expected_mask]
        assert np.array_equal(output, expected)
        assert isinstance(mask, NodataMask)
        assert np.array_equal(mask.mask, expected_mask)
        assert mask.size == array.size


class TestCheckIntegers:
    def test_pass(_, array):
        array = array.astype(float)
        data, mask = validate._get_data(array, 10)
        validate._check_integers(data, "", array, mask)

    def test_fail(_, array, assert_contains):
        array = array.astype(float)
        array[0, 1] = 5.5
        data, mask = validate._get_data(array, 1)
        print(data)
        with pytest.raises(ValueError) as error:
            validate._check_integers(data, "test name", array, mask)
        assert_contains(error, "test name", "element [0, 1] (value=5.5)")


class TestCheckBound:
    def test_pass(_, array):
        data, mask = validate._get_data(array, 10)
        min = np.amin(array)
        max = np.amax(array)
        validate._check_bound(data, "", "<", max + 1, array, mask)
        validate._check_bound(data, "", "<=", max, array, mask)
        validate._check_bound(data, "", ">=", min, array, mask)
        validate._check_bound(data, "", ">", min - 1, array, mask)

    def test_fail(_, array, assert_contains):
        data, mask = validate._get_data(array, 10)
        min = np.amin(array)
        max = np.amax(array)
        name = "test name"

        with pytest.raises(ValueError) as error:
            validate._check_bound(data, name, "<", max, array, mask)
        assert_contains(error, name, "less than", f"value={max}")

        with pytest.raises(ValueError) as error:
            validate._check_bound(data, name, "<=", max - 1, array, mask)
        assert_contains(error, name, "less than or equal to", f"value={max}")

        with pytest.raises(ValueError) as error:
            validate._check_bound(data, name, ">=", min + 1, array, mask)
        assert_contains(error, name, "greater than or equal to", f"value={min}")

        with pytest.raises(ValueError) as error:
            validate._check_bound(data, name, ">", min, array, mask)
        assert_contains(error, name, "greater than", f"value={min}")


class TestCheck:
    def test_passed(_, araster):
        data, mask = validate._get_data(araster, 4)
        passed = np.full(data.shape, True)
        validate._check(passed, "", araster, "", mask)

    def test_failed(_, araster, assert_contains):
        data, mask = validate._get_data(araster, 4)
        passed = np.full(data.shape, True)
        passed[-1] = False
        with pytest.raises(ValueError) as error:
            validate._check(passed, "test description", araster, "test name", mask)
        assert_contains(
            error, "test description", "test name", "element [1, 3] (value=8.0)"
        )


class TestFirstFailure:
    def test(_, araster):
        data, mask = validate._get_data(araster, 4)
        passed = np.full(data.shape, True)
        passed[-1] = False
        index, value = validate._first_failure(passed, araster, mask)
        assert np.array_equal(index, [1, 3])
        assert value == 8


#####
# Generic Elements
#####


class TestDefined:
    def test_pass(_):
        a = np.arange(100)
        validate.defined(a, "")

    def test_fail(_, assert_contains):
        a = np.array([1, 2, np.nan, 4])
        with pytest.raises(ValueError) as error:
            validate.defined(a, "test name")
        assert_contains(error, "test name")


class TestFinite:
    def test_pass(_):
        a = np.arange(100)
        validate.finite(a, "")

    @pytest.mark.parametrize("bad", (np.nan, np.inf, -np.inf))
    def test_fail(_, bad, assert_contains):
        a = np.array([1, 2, bad, 4])
        with pytest.raises(ValueError) as error:
            validate.finite(a, "test name")
        assert_contains(error, "test name")


class TestBoolean:
    @pytest.mark.parametrize("type", (bool, int, float))
    def test_valid(_, mask, type):
        input = mask.astype(type)
        output = validate.boolean(input, "test name")
        assert np.array_equal(output, mask)

    @pytest.mark.parametrize("value", (np.nan, np.inf, -999, 3))
    def test_invalid(_, mask, value, assert_contains):
        mask = mask.astype(float)
        mask[0, 0] = value
        with pytest.raises(ValueError) as error:
            validate.boolean(mask, "test name")
        assert_contains(error, "test name")

    def test_nan(_, mask, assert_contains):
        mask = mask.astype(float)
        mask[0, 0] = np.nan
        with pytest.raises(ValueError) as error:
            validate.boolean(mask, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 1, 0])
        output = validate.boolean(a, "", ignore=nodata)
        expected = np.array([False, False, True, True, False])
        np.array_equal(output, expected)

    def test_ignore_multiple(_):
        a = np.array([-999, np.nan, 1, 1, 0])
        output = validate.boolean(a, "", ignore=[-999, np.nan])
        expected = np.array([False, False, True, True, False])
        np.array_equal(output, expected)


class TestIntegers:
    name = "test name"

    def test_pass(self):
        array = np.array([-4.0, -3.0, 1.0, 2.0, 3.0, 100.000], dtype=float)
        validate.integers(array, self.name)

    def test_fail(self, assert_contains):
        array = np.array([1.2, 2.0, 3.0, 4.222])
        with pytest.raises(ValueError) as error:
            validate.integers(array, self.name)
        assert_contains(error, self.name)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:pfdf._utils.validate")
    def test_nan(self, assert_contains):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            validate.integers(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (3.3, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.integers(a, "", ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([3.3, np.nan, 1, 2, 3])
        validate.integers(a, "", ignore=[3.3, np.nan])


class TestPositive:
    name = "test name"

    def test_pass(self):
        array = np.arange(1, 11).reshape(2, 5)
        validate.positive(array, self.name)

    def test_fail(self, assert_contains):
        array = np.arange(-11, -1).reshape(2, 5)
        with pytest.raises(ValueError) as error:
            validate.positive(array, self.name)
        assert_contains(error, self.name)

    def test_pass_0(self):
        array = np.arange(0, 10).reshape(2, 5)
        validate.positive(array, self.name, allow_zero=True)

    def test_fail_0(self, assert_contains):
        array = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(ValueError) as error:
            validate.positive(array, self.name)
        assert_contains(error, self.name)

    def test_nan(self, assert_contains):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            validate.positive(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.positive(a, "", ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([-999, np.nan, 1, 2, 3])
        validate.positive(a, "", ignore=[-999, np.nan])


class TestInRange:
    name = "test name"

    @staticmethod
    def bounds(array):
        return (np.amin(array), np.amax(array))

    def test_pass(self, array):
        min, max = self.bounds(array)
        validate.inrange(array, self.name, min - 1, max + 1)

    def test_includes_bound(self, array):
        min, max = self.bounds(array)
        validate.inrange(array, self.name, min, max)

    def test_too_high(self, array, assert_contains):
        min, max = self.bounds(array)
        with pytest.raises(ValueError) as error:
            validate.inrange(array, self.name, min, max - 1)
        assert_contains(error, self.name, str(max - 1))

    def test_too_low(self, array, assert_contains):
        min, max = self.bounds(array)
        with pytest.raises(ValueError) as error:
            validate.inrange(array, self.name, min + 1, max)
        assert_contains(error, self.name, str(min + 1))

    def test_only_upper(self, array):
        _, max = self.bounds(array)
        validate.inrange(array, self.name, max=max)

    def test_only_lower(self, array):
        min, _ = self.bounds(array)
        validate.inrange(array, self.name, min=min)

    def test_nan(self, assert_contains):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            validate.inrange(a, self.name, min=-np.inf, max=np.inf)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.inrange(a, "", min=1, max=4, ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([-999, np.nan, 1, 2, 3])
        validate.inrange(a, "", min=1, max=4, ignore=[-999, np.nan])


class TestSorted:
    @pytest.mark.parametrize(
        "a", (np.array([1, 2, 3]), np.array([1, 2, 2, 2, 3]), np.array([1, np.nan, 3]))
    )
    def test_pass(_, a):
        validate.sorted(a, "")

    def test_fail(_, assert_contains):
        a = np.array([1, 4, 3, 5, 6])
        with pytest.raises(ValueError) as error:
            validate.sorted(a, "test name")
        assert_contains(error, "test name")


class TestFlow:
    @pytest.mark.parametrize("type", (int, float))
    def test_valid(_, type):
        a = np.array([1, 2, 5, 4, 8, 6, 7, 2, 4, 3, 5, 4, 6, 7, 8]).astype(type)
        validate.flow(a, "test name")

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:pfdf._utils.validate")
    @pytest.mark.parametrize("value", (np.inf, -np.inf, 0, 1.1, 6.7, 9, -900))
    def test_invalid(_, value, assert_contains):
        a = np.array([1, 2, 5, 4, 8, 6, 7, 2, 4, 3, 5, 4, 6, 7, 8]).astype(type)
        a[5] = value
        with pytest.raises(ValueError) as error:
            validate.flow(a, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.flow(a, "", ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([-999, np.nan, 1, 2, 3])
        validate.flow(a, "", ignore=[-999, np.nan])
