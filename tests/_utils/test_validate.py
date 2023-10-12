from pathlib import Path

import numpy as np
import pytest
from affine import Affine
from rasterio.crs import CRS

from pfdf._utils import validate
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


class TestCheckBound:
    def test_pass(_, array):
        min = np.amin(array)
        max = np.amax(array)
        validate._check_bound(array, "", None, "<", max + 1)
        validate._check_bound(array, "", None, "<=", max)
        validate._check_bound(array, "", None, ">=", min)
        validate._check_bound(array, "", None, ">", min - 1)

    def test_fail(_, array):
        min = np.amin(array)
        max = np.amax(array)
        name = "test name"

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, name, None, "<", max)
        assert_contains(error, name, "less than")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, name, None, "<=", max - 1)
        assert_contains(error, name, "less than or equal to")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, name, None, ">=", min + 1)
        assert_contains(error, name, "greater than or equal to")

        with pytest.raises(ValueError) as error:
            validate._check_bound(array, name, None, ">", min)
        assert_contains(error, name, "greater than")


class TestIsData:
    def test_neither(_, band1):
        assert validate._isdata(band1, None, None) is None

    def test_both(_, band1):
        isdata = band1 > 6
        output = validate._isdata(band1, isdata, 4)
        np.array_equal(output, isdata)

    def test_isdata(_, band1):
        isdata = band1 > 6
        output = validate._isdata(band1, isdata, None)
        np.array_equal(output, isdata)

    def test_nodata(_, band1):
        expected = band1 != 4
        output = validate._isdata(band1, None, nodata=4)
        np.array_equal(output, expected)


class TestDataElements:
    def test(_, band1):
        isdata = band1 > 6
        output = validate._data_elements(band1, isdata)
        np.array_equal(output, band1[isdata])

    def test_none(_, band1):
        output = validate._data_elements(band1, None)
        np.array_equal(output, band1)


class TestCheck:
    def test_passed(_, band1):
        isdata = band1 > 6
        data = band1[isdata]
        passed = np.full(data.shape, True)
        validate._check(passed, "test description", band1, "test name", isdata)

    def test_failed(_, band1):
        isdata = band1 <= 6
        data = band1[isdata]
        passed = np.full(data.shape, True)
        passed[-1] = False
        with pytest.raises(ValueError) as error:
            validate._check(passed, "test description", band1, "test name", isdata)
        assert_contains(error, "test description", "test name", "6", "1, 1")


class TestFirstFailure:
    def test(_, band1):
        isdata = band1 <= 6
        data = band1[isdata]
        passed = np.full(data.shape, True)
        passed[-1] = False
        index, value = validate._first_failure(band1, isdata, passed)
        assert np.array_equal(index, [1, 1])
        assert value == 6


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
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 1, 0])
        output = validate.boolean(a, "", nodata=nodata)
        expected = np.array([False, False, True, True, False])
        np.array_equal(output, expected)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 1, 0, 0])
        isdata = np.array([False] * 4 + [True] * 4)
        output = validate.boolean(a, "", isdata=isdata)
        expected = np.array([False] * 4 + [True, True, False, False])
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
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.integers(a, "", nodata=nodata)

    def test_isdata(_):
        a = np.array([-3.2, -2.4, -1.9, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        validate.positive(a, "", isdata=isdata)


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
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.positive(a, "", nodata=nodata)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        validate.positive(a, "", isdata=isdata)


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
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.inrange(a, "", min=1, max=4, nodata=nodata)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        validate.inrange(a, "", min=1, max=4, isdata=isdata)


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
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        validate.flow(a, "", nodata=nodata)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        validate.flow(a, "", isdata=isdata)


#####
# Raster Metadata
#####


class TestNoData:
    @pytest.mark.parametrize("value, dtype", ((-999, int), (-999, float), (2.2, float)))
    def test_numeric(_, value, dtype):
        nodata = validate.nodata(value, dtype=dtype, casting="safe")
        assert nodata == value
        assert nodata.dtype == dtype

    def test_nan(_):
        nodata = validate.nodata(np.nan, float, casting="safe")
        assert np.isnan(nodata)

    def test_safe_casting(_):
        nodata = np.array(-999).astype("float32")
        nodata = validate.nodata(nodata, "float64", casting="safe")
        assert nodata.dtype == "float64"

    def test_unsafe_casting(_):
        nodata = 1.2
        nodata = validate.nodata(nodata, int, casting="unsafe")
        assert nodata.dtype == int

    @pytest.mark.parametrize("input, expected", ((0.0, False), (1.0, True)))
    def test_bool_casting(_, input, expected):
        nodata = validate.nodata(input, bool, casting="safe")
        assert nodata.dtype == bool
        assert nodata == expected

    def test_not_scalar(_):
        nodata = [1, 2]
        with pytest.raises(DimensionError) as error:
            validate.nodata(nodata, dtype=int, casting="safe")
        assert_contains(error, "nodata")

    def test_invalid_type(_):
        nodata = "invalid"
        with pytest.raises(TypeError) as error:
            validate.nodata(nodata, int, casting="safe")
        assert_contains(error, "nodata")

    def test_invalid_casting(_):
        nodata = -1.2
        with pytest.raises(TypeError) as error:
            validate.nodata(nodata, int, casting="safe")
        assert_contains(error, "Cannot cast the NoData value")


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
    def test_bad_matrix(_, affine):
        with pytest.raises(TransformError) as error:
            validate.transform(affine)
        assert_contains(error, "scaling and translation")


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
