from math import inf, nan
from pathlib import Path

import numpy as np
import pytest
from affine import Affine
from rasterio.crs import CRS

from pfdf._utils import validate
from pfdf._utils.nodata import NodataMask
from pfdf.errors import (
    CrsError,
    DimensionError,
    EmptyArrayError,
    ShapeError,
    TransformError,
)

#####
# Fixtures and testing utilities
#####


@pytest.fixture
def array():
    return np.arange(1, 51).reshape(10, 5)


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


@pytest.fixture
def band1():
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4)


@pytest.fixture
def mask():
    return np.array([True, False, False, True]).reshape(2, 2)


###
# Low-level
###


class TestShape:
    name = "test name"
    axes = ["rows", "columns"]
    shape = (10, 5)

    @pytest.mark.parametrize("required, axis", [((2, 5), "rows"), ((10, 2), "columns")])
    def test_failed(self, required, axis):
        with pytest.raises(ShapeError) as error:
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
    name = "test name"
    dtype = np.integer
    string = "numpy.integer"

    @pytest.mark.parametrize(
        "allowed, string",
        [(np.bool_, "numpy.bool_"), ([np.floating, np.bool_], "numpy.floating")],
    )
    def test_failed(self, allowed, string):
        with pytest.raises(TypeError) as error:
            validate.dtype_(self.name, allowed, self.dtype)
        assert_contains(error, self.name, string, self.string)

    def test_none(self):
        validate.dtype_(self.name, None, self.dtype)

    @pytest.mark.parametrize("allowed", [(np.integer), ([np.floating, np.integer])])
    def test_pass(self, allowed):
        validate.dtype_(self.name, allowed, self.dtype)


class TestNonsingleton:
    def test(_):
        array = np.arange(0, 36).reshape(2, 1, 1, 3, 1, 6)
        tf = [True, False, False, True, False, True]
        assert validate.nonsingleton(array) == tf


#####
# Shape and Type
#####


class TestArray:
    def test_scalar(_):
        a = 1
        expected = np.atleast_1d(np.array(a))
        output = validate.array(a, "")
        assert np.array_equal(output, expected)

    def test_ND(_):
        a = np.arange(0, 27).reshape(3, 3, 3)
        output = validate.array(a, "")
        assert np.array_equal(a, output)

    def test_empty(_):
        a = np.array([])
        with pytest.raises(EmptyArrayError) as error:
            validate.array(a, "test name")
        assert_contains(error, "test name")

    def test_dtype(_):
        a = np.arange(0, 10, dtype=float)
        output = validate.array(a, "", dtype=float)
        assert np.array_equal(a, output)

    def test_dtype_failed(_):
        a = np.arange(0, 10, dtype=float)
        with pytest.raises(TypeError) as error:
            validate.array(a, "test name", dtype=int)
        assert_contains(error, "test name")


class TestScalar:
    name = "test name"

    def test_int(_):
        a = 4
        assert validate.scalar(a, "") == np.array(a)

    def test_float(_):
        a = 5.5
        assert validate.scalar(a, "") == np.array(5.5)

    def test_1D(_):
        a = np.array(2.2)
        assert validate.scalar(a, "") == a

    def test_ND(_):
        a = np.array(2.2).reshape(1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
        assert validate.scalar(a, "") == a.reshape(1)

    def test_dtype(_):
        a = np.array(2.2, dtype=float)
        assert validate.scalar(a, "", dtype=np.floating) == a

    def test_empty(self):
        with pytest.raises(EmptyArrayError) as error:
            validate.scalar([], self.name)
        assert_contains(error, self.name)

    def test_failed_list(self):
        a = [1, 2, 3, 4]
        with pytest.raises(DimensionError) as error:
            validate.scalar(a, self.name)
        assert_contains(error, self.name, f"{len(a)} elements")

    def test_failed_numpy(self):
        a = np.array([1, 2, 3, 4])
        with pytest.raises(DimensionError) as error:
            validate.scalar(a, self.name)
        assert_contains(error, self.name, f"{a.size} elements")

    def test_dtype_failed(self):
        a = np.array(4, dtype=int)
        allowed = np.bool_
        string = "numpy.bool_"
        with pytest.raises(TypeError) as error:
            validate.scalar(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)


class TestVector:
    name = "test name"

    def test_list(_):
        a = [1, 2, 3, 4, 5]
        output = validate.vector(a, "")
        np.array_equal(output, np.array(a))

    def test_tuple(_):
        a = (1, 2, 3, 4, 5)
        output = validate.vector(a, "")
        np.array_equal(output, np.array(a))

    def test_1D(_):
        a = np.array([1, 2, 3, 4, 5])
        output = validate.vector(a, "")
        np.array_equal(output, a)

    @pytest.mark.parametrize("shape", [(1, 5), (1, 1, 1, 1, 5), (1, 1, 5, 1, 1)])
    def test_ND(_, shape):
        a = np.array([1, 2, 3, 4, 5]).reshape(*shape)
        output = validate.vector(a, "")
        np.array_equal(output, a.reshape(5))

    @pytest.mark.parametrize("types", [(np.integer), ([np.integer, np.floating])])
    def test_dtype(_, types):
        a = np.array([1, 2, 3, 4, 5])
        output = validate.vector(a, "", dtype=types)
        np.array_equal(output, a)

    def test_length(_):
        a = np.arange(1, 6)
        output = validate.vector(a, "", length=5)
        np.array_equal(output, a)

    def test_scalar(self):
        a = 2.2
        output = validate.vector(a, "")
        np.array_equal(output, np.array(a).reshape(1))

    def test_dtype_failed(self):
        a = np.arange(0, 5, dtype=int)
        allowed = np.bool_
        string = "numpy.bool_"
        with pytest.raises(TypeError) as error:
            validate.vector(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)

    def test_empty(self):
        with pytest.raises(EmptyArrayError) as error:
            validate.vector([], self.name)
        assert_contains(error, self.name)

    def test_ND_failed(self):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(DimensionError) as error:
            validate.vector(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("length", [(1), (2), (3)])
    def test_length_failed(self, length):
        a = np.arange(0, 10)
        with pytest.raises(ShapeError) as error:
            validate.vector(a, self.name, length=length)
        assert_contains(error, self.name, f"{len(a)} element(s)")


class TestMatrix:
    name = "test name"

    def test_list(_):
        a = [1, 2, 3, 4]
        output = validate.matrix(a, "")
        np.array_equal(output, np.array(a).reshape(1, 4))

    def test_tuple(_):
        a = (1, 2, 3, 4)
        output = validate.matrix(a, "")
        np.array_equal(output, np.array(a).reshape(1, 4))

    def test_2D(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = validate.matrix(a, "")
        np.array_equal(output, a)

    def test_trailing(_):
        a = np.arange(0, 10).reshape(2, 5, 1, 1, 1)
        output = validate.matrix(a, "")
        np.array_equal(output, a.reshape(2, 5))

    def test_dtype(_):
        a = np.arange(0, 10, dtype=int).reshape(2, 5)
        output = validate.matrix(a, "", dtype=np.integer)
        np.array_equal(output, a)

    def test_shape(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = validate.matrix(a, "", shape=(2, 5))
        np.array_equal(output, a)

    def test_skip_shape(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = validate.matrix(a, "", shape=(-1, 5))
        np.array_equal(output, a)
        output = validate.matrix(a, "", shape=(2, -1))
        np.array_equal(output, a)
        output = validate.matrix(a, "", shape=(-1, -1))
        np.array_equal(output, a)

    def test_scalar(_):
        a = 5
        output = validate.matrix(a, "")
        np.array_equal(output, np.array(a).reshape(1, 1))

    def test_vector(_):
        a = np.arange(0, 10)
        output = validate.matrix(a, "")
        np.array_equal(output, a.reshape(1, -1))

    def test_dtype_failed(self):
        a = np.arange(0, 10, dtype=int)
        allowed = np.bool_
        string = "numpy.bool_"
        with pytest.raises(TypeError) as error:
            validate.matrix(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)

    def test_empty(self):
        with pytest.raises(EmptyArrayError) as error:
            validate.matrix([], self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize(
        "array",
        [(np.arange(0, 27).reshape(3, 3, 3)), (np.arange(0, 10).reshape(1, 2, 5))],
    )
    def test_ND(self, array):
        with pytest.raises(DimensionError) as error:
            validate.matrix(array, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize(
        "shape, axis", [((3, 5), "3 row(s)"), ((2, 7), "7 column(s)")]
    )
    def test_shape_failed(self, shape, axis):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(ShapeError) as error:
            validate.matrix(a, self.name, shape=shape)
        assert_contains(error, self.name, axis)


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
        output, mask = validate._get_data(array, [None, 10, 11, nan])
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

    def test_fail(_, array):
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

    def test_fail(_, array):
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
    def test_passed(_, band1):
        data, mask = validate._get_data(band1, 4)
        passed = np.full(data.shape, True)
        validate._check(passed, "", band1, "", mask)

    def test_failed(_, band1):
        data, mask = validate._get_data(band1, 4)
        passed = np.full(data.shape, True)
        passed[-1] = False
        with pytest.raises(ValueError) as error:
            validate._check(passed, "test description", band1, "test name", mask)
        assert_contains(
            error, "test description", "test name", "element [1, 3] (value=8)"
        )


class TestFirstFailure:
    def test(_, band1):
        data, mask = validate._get_data(band1, 4)
        passed = np.full(data.shape, True)
        passed[-1] = False
        index, value = validate._first_failure(passed, band1, mask)
        assert np.array_equal(index, [1, 3])
        assert value == 8


#####
# Generic Elements
#####


class TestDefined:
    def test_pass(_):
        a = np.arange(100)
        validate.defined(a, "")

    def test_fail(_):
        a = np.array([1, 2, np.nan, 4])
        with pytest.raises(ValueError) as error:
            validate.defined(a, "test name")
        assert_contains(error, "test name")


class TestBoolean:
    @pytest.mark.parametrize("type", (bool, int, float))
    def test_valid(_, mask, type):
        input = mask.astype(type)
        output = validate.boolean(input, "test name")
        assert np.array_equal(output, mask)

    @pytest.mark.parametrize("value", (np.nan, np.inf, -999, 3))
    def test_invalid(_, mask, value):
        mask = mask.astype(float)
        mask[0, 0] = value
        with pytest.raises(ValueError) as error:
            validate.boolean(mask, "test name")
        assert_contains(error, "test name")

    def test_nan(_, mask):
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
        a = np.array([-999, nan, 1, 1, 0])
        output = validate.boolean(a, "", ignore=[-999, nan])
        expected = np.array([False, False, True, True, False])
        np.array_equal(output, expected)


class TestIntegers:
    name = "test name"

    def test_pass(self):
        array = np.array([-4.0, -3.0, 1.0, 2.0, 3.0, 100.000], dtype=float)
        validate.integers(array, self.name)

    def test_fail(self):
        array = np.array([1.2, 2.0, 3.0, 4.222])
        with pytest.raises(ValueError) as error:
            validate.integers(array, self.name)
        assert_contains(error, self.name)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:pfdf._utils.validate")
    def test_nan(self):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            validate.integers(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (3.3, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.integers(a, "", ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([3.3, nan, 1, 2, 3])
        validate.integers(a, "", ignore=[3.3, nan])


class TestPositive:
    name = "test name"

    def test_pass(self):
        array = np.arange(1, 11).reshape(2, 5)
        validate.positive(array, self.name)

    def test_fail(self):
        array = np.arange(-11, -1).reshape(2, 5)
        with pytest.raises(ValueError) as error:
            validate.positive(array, self.name)
        assert_contains(error, self.name)

    def test_pass_0(self):
        array = np.arange(0, 10).reshape(2, 5)
        validate.positive(array, self.name, allow_zero=True)

    def test_fail_0(self):
        array = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(ValueError) as error:
            validate.positive(array, self.name)
        assert_contains(error, self.name)

    def test_nan(self):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            validate.positive(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.positive(a, "", ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([-999, nan, 1, 2, 3])
        validate.positive(a, "", ignore=[-999, nan])


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

    def test_too_high(self, array):
        min, max = self.bounds(array)
        with pytest.raises(ValueError) as error:
            validate.inrange(array, self.name, min, max - 1)
        assert_contains(error, self.name, str(max - 1))

    def test_too_low(self, array):
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

    def test_nan(self):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            validate.inrange(a, self.name, min=-np.inf, max=np.inf)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_ignore(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.inrange(a, "", min=1, max=4, ignore=nodata)

    def test_ignore_multiple(_):
        a = np.array([-999, nan, 1, 2, 3])
        validate.inrange(a, "", min=1, max=4, ignore=[-999, nan])


class TestSorted:
    @pytest.mark.parametrize(
        "a", (np.array([1, 2, 3]), np.array([1, 2, 2, 2, 3]), np.array([1, np.nan, 3]))
    )
    def test_pass(_, a):
        validate.sorted(a, "")

    def test_fail(_):
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
    @pytest.mark.parametrize("value", (np.nan, np.inf, -np.inf, 0, 1.1, 6.7, 9, -900))
    def test_invalid(_, value):
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
        a = np.array([-999, nan, 1, 2, 3])
        validate.flow(a, "", ignore=[-999, nan])


#####
# Raster Metadata
#####


class TestCasting:
    def test_bool(_):
        a = np.array(True).reshape(1)
        assert validate.casting(a, "", bool, "safe") == True

    def test_bool_as_number(_):
        a = np.array(1.00).reshape(1)
        assert validate.casting(a, "", bool, casting="safe") == True

    def test_castable(_):
        a = np.array(2.2).reshape(1)
        assert validate.casting(a, "", int, casting="unsafe") == 2

    def test_not_castable(_):
        a = np.array(2.2).reshape(1)
        with pytest.raises(TypeError) as error:
            validate.casting(a, "test name", int, casting="safe")
        assert_contains(error, "Cannot cast test name")


class TestCheckShear:
    def test_zero(_):
        affine = Affine(0, 0, 0, 0, 0, 0)
        validate._check_shear(affine, "b")

    def test_not_zero(_):
        affine = Affine(1, 1, 1, 1, 1, 1)
        with pytest.raises(TransformError) as error:
            validate._check_shear(affine, "b")
        assert_contains(error, "coefficient 'b' is not 0 (value = 1")


class TestCheckAffine:
    def test_valid(_):
        affine = Affine.identity()
        validate._check_affine(affine, "a")

    def test_not_float(_):
        a = np.array(1).reshape(1)
        affine = Affine(a, a, a, a, a, a)
        with pytest.raises(TransformError) as error:
            validate._check_affine(affine, "a")
        assert_contains(
            error, "coefficients must be floats, but coefficient 'a' is not"
        )

    def test_nan(_):
        affine = Affine(nan, 0, 0, 0, 0, 0)
        with pytest.raises(TransformError) as error:
            validate._check_affine(affine, "a")
        assert_contains(error, "coefficients cannot be NaN, but coefficient 'a' is")

    def test_inf(_):
        affine = Affine(inf, 0, 0, 0, 0, 0)
        with pytest.raises(TransformError) as error:
            validate._check_affine(affine, "a")
        assert_contains(error, "coefficients cannot be Inf, but coefficient 'a' is")


class TestTransform:
    def test_valid(_):
        a = Affine(10, 0, 3, 0, 10, 6)
        output = validate.transform(a)
        assert isinstance(output, Affine)
        assert output == a

    def test_invalid(_):
        with pytest.raises(TransformError) as error:
            validate.transform("invalid")
        assert_contains(error, "transform")

    @pytest.mark.parametrize(
        "affine", (Affine(1, 1, 1, 0, 0, 0), Affine(0, 0, 0, 1, 1, 1))
    )
    def test_bad_shear(_, affine):
        with pytest.raises(TransformError) as error:
            validate.transform(affine)
        assert_contains(error, "scaling and translation")

    def test_bad_coeff(_):
        a = np.array(1).reshape(1)
        affine = Affine(a, a, a, a, a, a)
        with pytest.raises(TransformError) as error:
            validate.transform(affine)
        assert_contains(
            error, "coefficients must be floats, but coefficient 'a' is not"
        )


class TestCrs:
    @pytest.mark.parametrize("input", (CRS.from_epsg(4326), "EPSG:4326"))
    def test_valid(_, input):
        output = validate.crs(input)
        expected = CRS.from_epsg(4326)
        assert isinstance(output, CRS)
        assert output == expected

    def test_invalid(_):
        with pytest.raises(CrsError) as error:
            validate.crs("invalid")
        assert_contains(error, "crs")


class TestResolution:
    def test_invalid_type(_):
        with pytest.raises(TypeError) as error:
            validate.resolution("invalid")
        assert_contains(error, "resolution")

    def test_not_vector(_):
        with pytest.raises(DimensionError):
            validate.resolution(np.array([[1, 2], [3, 4]]))

    def test_too_long(_):
        with pytest.raises(ShapeError):
            validate.resolution([1, 2, 3])

    @pytest.mark.parametrize("value", (0, -2))
    def test_not_positive(_, value):
        with pytest.raises(ValueError) as error:
            validate.resolution(value)

    def test_one_element(_):
        output = validate.resolution(10)
        assert np.array_equal(output, [10, 10])

    def test_two_elements(_):
        output = validate.resolution((5, 6))
        assert np.array_equal(output, (5, 6))


#####
# Paths
#####


class TestInputPath:
    def test_str(_, tmp_path):
        file = Path(tmp_path) / "test.geojson"
        with open(file, "w") as f:
            f.write("test")
        output = validate.input_path(str(file), "")
        assert output == file

    def test_path(_, tmp_path):
        file = Path(tmp_path) / "test.geojson"
        with open(file, "w") as f:
            f.write("test")
        output = validate.input_path(file, "")
        assert output == file

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            validate.input_path(5, "test file")
        assert_contains(error, "test file")

    def test_missing(_, tmp_path):
        file = Path(tmp_path) / "test.geojson"
        with pytest.raises(FileNotFoundError):
            validate.input_path(file, "")


#####
# Misc
#####


class TestBroadcastable:
    def test(_):
        a = (4, 5, 1, 3, 1, 7)
        b = (5, 6, 1, 1, 7)
        output = validate.broadcastable(a, "", b, "")
        expected = (4, 5, 6, 3, 1, 7)
        assert output == expected

    def test_failed(_):
        a = (4, 5)
        b = (5, 6)
        with pytest.raises(ValueError) as error:
            validate.broadcastable(a, "test-name-1", b, "test-name-2")
        assert_contains(error, "test-name-1", "test-name-2")


class TestOption:
    allowed = ["red", "green", "blue"]

    @pytest.mark.parametrize("input", ("red", "GREEN", "BlUe"))
    def test_valid(self, input):
        output = validate.option(input, "", self.allowed)
        assert output == input.lower()

    def test_not_string(self):
        with pytest.raises(TypeError) as error:
            validate.option(5, "test name", self.allowed)
        assert_contains(error, "test name")

    def test_not_recognized(self):
        with pytest.raises(ValueError) as error:
            validate.option("yellow", "test name", self.allowed)
        assert_contains(error, "test name", "yellow", "red, green, blue")


class TestOutputPath:
    def test_valid_string(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output = validate.output_path(str(path), overwrite=False)
        expected = Path(path)
        assert isinstance(output, Path)
        assert output == expected

    def test_valid_path(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output = validate.output_path(path, overwrite=False)
        expected = Path(path)
        assert isinstance(output, Path)
        assert output == expected

    def test_valid_overwrite(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        with open(path, "w") as file:
            file.write("This file already exists")
        assert path.is_file()
        output = validate.output_path(path, overwrite=True)
        assert isinstance(output, Path)
        assert output == path

    def test_invalid(_):
        with pytest.raises(TypeError):
            validate.output_path(5, overwrite=False)

    def test_invalid_overwrite(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        with open(path, "w") as file:
            file.write("This file already exists")
        assert path.is_file()
        with pytest.raises(FileExistsError) as error:
            validate.output_path(path, overwrite=False)
        assert_contains(error, "Output file already exists")
