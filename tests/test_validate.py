"""
test_validate  Unit tests for user-input validation functions
"""

from pathlib import Path

import numpy as np
import pytest
import rasterio

from pfdf import _validate
from pfdf.errors import DimensionError, ShapeError

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
def band2(band1):
    return band1 * 10


@pytest.fixture
def raster(tmp_path, band1, band2):
    raster = tmp_path / "raster.tif"
    with rasterio.open(
        raster,
        "w",
        driver="GTiff",
        height=band1.shape[0],
        width=band1.shape[1],
        count=2,
        nodata=4,
        dtype=band1.dtype,
        crs="+proj=latlong",
        transform=rasterio.transform.Affine(300, 0, 101985, 0, -300, 2826915),
    ) as file:
        file.write(band1, 1)
        file.write(band2, 2)
    return raster


# A complex-valued raster
@pytest.fixture
def craster(tmp_path, band1):
    band1 = band1.astype(np.csingle)
    raster = tmp_path / "raster.tif"
    with rasterio.open(
        raster,
        "w",
        driver="GTiff",
        height=band1.shape[0],
        width=band1.shape[1],
        count=2,
        nodata=4,
        dtype=band1.dtype,
        crs="+proj=latlong",
        transform=rasterio.transform.Affine(300, 0, 101985, 0, -300, 2826915),
    ) as file:
        file.write(band1, 1)
    return raster


def check_equal(array1, array2):
    assert np.array_equal(array1, array2)


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
        with pytest.raises(_validate.ShapeError) as error:
            _validate.shape_(self.name, self.axes, required, self.shape)
        assert_contains(error, self.name, axis)

    def test_none(self):
        _validate.shape_(self.name, self.axes, None, self.shape)

    def test_pass(self):
        _validate.shape_(self.name, self.axes, self.shape, self.shape)

    def test_skip(self):
        required = (-1, self.shape[1])
        _validate.shape_(self.name, self.axes, required, self.shape)


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
            _validate.dtype_(self.name, allowed, self.dtype)
        assert_contains(error, self.name, string, self.string)

    def test_none(self):
        _validate.dtype_(self.name, None, self.dtype)

    @pytest.mark.parametrize("allowed", [(np.integer), ([np.floating, np.integer])])
    def test_pass(self, allowed):
        _validate.dtype_(self.name, allowed, self.dtype)


class TestNonsingleton:
    def test(_):
        array = np.arange(0, 36).reshape(2, 1, 1, 3, 1, 6)
        tf = [True, False, False, True, False, True]
        assert _validate.nonsingleton(array) == tf


#####
# Shape and Type
#####


class TestScalar:
    name = "test name"

    def test_int(_):
        a = 4
        assert _validate.scalar(a, "") == np.array(a)

    def test_float(_):
        a = 5.5
        assert _validate.scalar(a, "") == np.array(5.5)

    def test_1D(_):
        a = np.array(2.2)
        assert _validate.scalar(a, "") == a

    def test_ND(_):
        a = np.array(2.2).reshape(1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
        assert _validate.scalar(a, "") == a.reshape(1)

    def test_dtype(_):
        a = np.array(2.2, dtype=float)
        assert _validate.scalar(a, "", dtype=np.floating) == a

    def test_empty(self):
        with pytest.raises(_validate.DimensionError) as error:
            _validate.scalar([], self.name)
        assert_contains(error, self.name, "0 elements")

    def test_failed_list(self):
        a = [1, 2, 3, 4]
        with pytest.raises(_validate.DimensionError) as error:
            _validate.scalar(a, self.name)
        assert_contains(error, self.name, f"{len(a)} elements")

    def test_failed_numpy(self):
        a = np.array([1, 2, 3, 4])
        with pytest.raises(_validate.DimensionError) as error:
            _validate.scalar(a, self.name)
        assert_contains(error, self.name, f"{a.size} elements")

    def test_dtype_failed(self):
        a = np.array(4, dtype=int)
        allowed = np.bool_
        string = "numpy.bool_"
        with pytest.raises(TypeError) as error:
            _validate.scalar(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)


class TestVector:
    name = "test name"

    def test_list(_):
        a = [1, 2, 3, 4, 5]
        output = _validate.vector(a, "")
        check_equal(output, np.array(a))

    def test_tuple(_):
        a = (1, 2, 3, 4, 5)
        output = _validate.vector(a, "")
        check_equal(output, np.array(a))

    def test_1D(_):
        a = np.array([1, 2, 3, 4, 5])
        output = _validate.vector(a, "")
        check_equal(output, a)

    @pytest.mark.parametrize("shape", [(1, 5), (1, 1, 1, 1, 5), (1, 1, 5, 1, 1)])
    def test_ND(_, shape):
        a = np.array([1, 2, 3, 4, 5]).reshape(*shape)
        output = _validate.vector(a, "")
        check_equal(output, a.reshape(5))

    @pytest.mark.parametrize("types", [(np.integer), ([np.integer, np.floating])])
    def test_dtype(_, types):
        a = np.array([1, 2, 3, 4, 5])
        output = _validate.vector(a, "", dtype=types)
        check_equal(output, a)

    def test_length(_):
        a = np.arange(1, 6)
        output = _validate.vector(a, "", length=5)
        check_equal(output, a)

    def test_scalar(self):
        a = 2.2
        output = _validate.vector(a, "")
        check_equal(output, np.array(a).reshape(1))

    def test_dtype_failed(self):
        a = np.arange(0, 5, dtype=int)
        allowed = np.bool_
        string = "numpy.bool_"
        with pytest.raises(TypeError) as error:
            _validate.vector(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)

    def test_empty(self):
        with pytest.raises(_validate.DimensionError) as error:
            _validate.vector([], self.name)
        assert_contains(error, self.name)

    def test_ND_failed(self):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(_validate.DimensionError) as error:
            _validate.vector(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("length", [(1), (2), (3)])
    def test_length_failed(self, length):
        a = np.arange(0, 10)
        with pytest.raises(_validate.ShapeError) as error:
            _validate.vector(a, self.name, length=length)
        assert_contains(error, self.name, f"{len(a)} element(s)")


class TestMatrix:
    name = "test name"

    def test_list(_):
        a = [1, 2, 3, 4]
        output = _validate.matrix(a, "")
        check_equal(output, np.array(a).reshape(1, 4))

    def test_tuple(_):
        a = (1, 2, 3, 4)
        output = _validate.matrix(a, "")
        check_equal(output, np.array(a).reshape(1, 4))

    def test_2D(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = _validate.matrix(a, "")
        check_equal(output, a)

    def test_trailing(_):
        a = np.arange(0, 10).reshape(2, 5, 1, 1, 1)
        output = _validate.matrix(a, "")
        check_equal(output, a.reshape(2, 5))

    def test_dtype(_):
        a = np.arange(0, 10, dtype=int).reshape(2, 5)
        output = _validate.matrix(a, "", dtype=np.integer)
        check_equal(output, a)

    def test_shape(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = _validate.matrix(a, "", shape=(2, 5))
        check_equal(output, a)

    def test_skip_shape(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = _validate.matrix(a, "", shape=(-1, 5))
        check_equal(output, a)
        output = _validate.matrix(a, "", shape=(2, -1))
        check_equal(output, a)
        output = _validate.matrix(a, "", shape=(-1, -1))
        check_equal(output, a)

    def test_scalar(_):
        a = 5
        output = _validate.matrix(a, "")
        check_equal(output, np.array(a).reshape(1, 1))

    def test_vector(_):
        a = np.arange(0, 10)
        output = _validate.matrix(a, "")
        check_equal(output, a.reshape(1, -1))

    def test_dtype_failed(self):
        a = np.arange(0, 10, dtype=int)
        allowed = np.bool_
        string = "numpy.bool_"
        with pytest.raises(TypeError) as error:
            _validate.matrix(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)

    def test_empty(self):
        with pytest.raises(_validate.DimensionError) as error:
            _validate.matrix([], self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize(
        "array",
        [(np.arange(0, 27).reshape(3, 3, 3)), (np.arange(0, 10).reshape(1, 2, 5))],
    )
    def test_ND(self, array):
        with pytest.raises(_validate.DimensionError) as error:
            _validate.matrix(array, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize(
        "shape, axis", [((3, 5), "3 row(s)"), ((2, 7), "7 column(s)")]
    )
    def test_shape_failed(self, shape, axis):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(_validate.ShapeError) as error:
            _validate.matrix(a, self.name, shape=shape)
        assert_contains(error, self.name, axis)


#####
# Rasters
#####


class TestRasterType:
    name = "test name"

    def test_string(self, raster, band1):
        output, isfile = _validate._raster_type(str(raster), "")
        assert output == raster
        assert isfile == True

    def test_path(_, raster, band1):
        output, isfile = _validate._raster_type(raster, "")
        assert output == raster
        assert isfile == True

    def test_reader(_, raster, band1):
        with rasterio.open(raster) as reader:
            output, isfile = _validate._raster_type(reader, "")
        assert output == raster
        assert isfile == True

    def test_array(_, band1):
        output, isfile = _validate._raster_type(band1, "")
        check_equal(output, band1)
        assert isfile == False

    def test_bad_string(self):
        raster = "not a file"
        with pytest.raises(FileNotFoundError):
            _validate._raster_type(raster, self.name)

    def test_missing(self, raster):
        raster.unlink()
        raster = str(raster)
        with pytest.raises(FileNotFoundError):
            _validate._raster_type(raster, self.name)

    def test_old_reader(self, raster):
        with rasterio.open(raster) as reader:
            reader.close()
            raster.unlink()
            with pytest.raises(FileNotFoundError) as error:
                _validate._raster_type(reader, self.name)
            assert_contains(error, "no longer exists", str(raster))

    def test_other(self):
        with pytest.raises(TypeError) as error:
            _validate._raster_type(np, self.name)
        assert_contains(
            error,
            self.name,
            "str, pathlib.Path, rasterio.DatasetReader, or 2D numpy.ndarray",
        )


class TestRasterFile:
    name = "test name"

    def test_shape(self, raster, band1):
        output, nodata = _validate._raster_file(raster, "", shape=band1.shape, load=True)
        check_equal(output, band1)
        assert nodata == 4

    def test_invalid_shape(self, raster):
        with pytest.raises(ShapeError) as error:
            _validate._raster_file(raster, self.name, shape=(1000, 1000), load=True)
        assert_contains(error, self.name)

    def test_noload(self, raster):
        output, nodata = _validate._raster_file(raster, "", shape=None, load=False)
        assert output == raster
        assert nodata == 4

    def test_invalid_dtype(self, craster):
        with pytest.raises(TypeError) as error:
            _validate._raster_file(craster, "", shape=None, load=False)
        assert_contains(error, "floating", "integer", "bool")


class TestRasterArray:
    name = "test name"

    def test_invalid_dtype(self, band1):
        band1 = band1.astype(np.csingle)
        with pytest.raises(TypeError) as error:
            _validate._raster_array(
                band1, self.name, shape=None, nodata=None, nodata_name=""
            )
        assert_contains(error, "integer", "floating", "bool")

    def test_shape(self):
        raster = np.arange(0, 10).reshape(2, 5)
        output, nodata = _validate._raster_array(
            raster, "", shape=(2, 5), nodata=None, nodata_name=""
        )
        check_equal(raster, output)
        assert nodata is None

    def test_invalid_shape(self):
        raster = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(ShapeError) as error:
            _validate._raster_array(
                raster, self.name, shape=(3, 6), nodata=None, nodata_name=""
            )
        assert_contains(error, self.name)

    def test_nodata(self, band1):
        output, nodata = _validate._raster_array(
            band1, "", shape=None, nodata=-999, nodata_name=""
        )
        check_equal(band1, output)
        assert nodata == -999

    def test_invalid_nodata(self, band1):
        with pytest.raises(TypeError) as error:
            _validate._raster_array(
                band1,
                "test name",
                shape=None,
                nodata="invalid",
                nodata_name="some nodata name",
            )
        assert_contains(error, "some nodata name")

    def test_not_matrix(self, band1):
        band1 = np.stack((band1, band1), axis=-1)
        with pytest.raises(DimensionError) as error:
            _validate._raster_array(
                band1, "test name", shape=None, nodata=None, nodata_name=""
            )
        assert_contains(error, "test name")


# Most functionality is tested via the tests of the private raster validaters.
# Only need to check the intersection of file-based and numpy options here
class TestRaster:
    @pytest.mark.parametrize("numpy_nodata", (-999, "invalid"))
    def test_file_numpy_nodata(self, raster, band1, numpy_nodata):
        output, nodata = _validate.raster(
            raster, "test name", shape=None, numpy_nodata=numpy_nodata
        )
        check_equal(output, band1)
        assert nodata == 4

    def test_file_noload(self, raster):
        output, nodata = _validate.raster(raster, "", shape=None, load=False)
        assert output == raster
        assert nodata == 4

    def test_numpy_noload(self, band1):
        output, nodata = _validate.raster(band1, "", numpy_nodata=-999, load=False)
        check_equal(output, band1)
        assert nodata == -999


class TestOutputPath:
    @pytest.mark.parametrize("input", (True, 5, np.arange(0, 100)))
    def test_invalid(_, input):
        with pytest.raises(TypeError):
            _validate.output_path(input, True)

    def test_invalid_overwrite(_, raster):
        with pytest.raises(FileExistsError):
            _validate.output_path(raster, overwrite=False)

    @pytest.mark.parametrize("overwrite", (True, False))
    def test_none(_, overwrite):
        path, save = _validate.output_path(None, overwrite)
        assert path is None
        assert save == False

    @pytest.mark.parametrize(
        "path", ("some-file", "some-file.tif", "some-file.tiff", "some-file.TiFf")
    )
    def test_valid(_, path):
        output, save = _validate.output_path(path, True)
        assert output == Path("some-file.tif").resolve()
        assert save == True

    def test_valid_overwrite(_, raster):
        output, save = _validate.output_path(raster, True)
        assert output == raster.resolve()
        assert save == True


#####
# Loaded Array Utilities
#####


class TestIsData:
    def test_neither(_, band1):
        assert _validate._isdata(band1, None, None) is None

    def test_both(_, band1):
        isdata = band1 > 6
        output = _validate._isdata(band1, isdata, 4)
        check_equal(output, isdata)

    def test_isdata(_, band1):
        isdata = band1 > 6
        output = _validate._isdata(band1, isdata, None)
        check_equal(output, isdata)

    def test_nodata(_, band1):
        expected = band1 != 4
        output = _validate._isdata(band1, None, nodata=4)
        check_equal(output, expected)


class TestDataElements:
    def test(_, band1):
        isdata = band1 > 6
        output = _validate._data_elements(band1, isdata)
        check_equal(output, band1[isdata])

    def test_none(_, band1):
        output = _validate._data_elements(band1, None)
        check_equal(output, band1)


class TestFirstFailure:
    def test(_, band1):
        isdata = band1 <= 6
        data = band1[isdata]
        passed = np.full(data.shape, True)
        passed[-1] = False
        index, value = _validate._first_failure(band1, isdata, passed)
        assert np.array_equal(index, [1, 1])
        assert value == 6


class TestCheck:
    def test_passed(_, band1):
        isdata = band1 > 6
        data = band1[isdata]
        passed = np.full(data.shape, True)
        _validate._check(passed, "test description", band1, "test name", isdata)

    def test_failed(_, band1):
        isdata = band1 <= 6
        data = band1[isdata]
        passed = np.full(data.shape, True)
        passed[-1] = False
        with pytest.raises(ValueError) as error:
            _validate._check(passed, "test description", band1, "test name", isdata)
        assert_contains(error, "test description", "test name", "6", "1, 1")


#####
# Loaded Arrays
#####


class TestCheckBound:
    def test_pass(_, array):
        min = np.amin(array)
        max = np.amax(array)
        _validate._check_bound(array, "", None, "<", max + 1)
        _validate._check_bound(array, "", None, "<=", max)
        _validate._check_bound(array, "", None, ">=", min)
        _validate._check_bound(array, "", None, ">", min - 1)

    def test_fail(_, array):
        min = np.amin(array)
        max = np.amax(array)
        name = "test name"

        with pytest.raises(ValueError) as error:
            _validate._check_bound(array, name, None, "<", max)
            assert_contains(error, name, "less than")

        with pytest.raises(ValueError) as error:
            _validate._check_bound(array, name, None, "<=", max - 1)
            assert_contains(error, name, "less than or equal to")

        with pytest.raises(ValueError) as error:
            _validate._check_bound(array, name, None, ">=", min + 1)
            assert_contains(error, name, "greater than or equal to")

        with pytest.raises(ValueError) as error:
            _validate._check_bound(array, name, None, ">", min)
            assert_contains(error, name, "greater than")


class TestPositive:
    name = "test name"

    def test_pass(self):
        array = np.arange(1, 11).reshape(2, 5)
        _validate.positive(array, self.name)

    def test_fail(self):
        array = np.arange(-11, -1).reshape(2, 5)
        with pytest.raises(ValueError) as error:
            _validate.positive(array, self.name)
        assert_contains(error, self.name)

    def test_pass_0(self):
        array = np.arange(0, 10).reshape(2, 5)
        _validate.positive(array, self.name, allow_zero=True)

    def test_fail_0(self):
        array = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(ValueError) as error:
            _validate.positive(array, self.name)
        assert_contains(error, self.name)

    def test_nan(self):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            _validate.positive(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        _validate.positive(a, "", nodata=nodata)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        _validate.positive(a, "", isdata=isdata)


class TestIntegers:
    name = "test name"

    def test_pass(self):
        array = np.array([-4.0, -3.0, 1.0, 2.0, 3.0, 100.000], dtype=float)
        _validate.integers(array, self.name)

    def test_fail(self):
        array = np.array([1.2, 2.0, 3.0, 4.222])
        with pytest.raises(ValueError) as error:
            _validate.integers(array, self.name)
        assert_contains(error, self.name)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:dfha.validate")
    def test_nan(self):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            _validate.integers(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (3.3, np.nan))
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        _validate.integers(a, "", nodata=nodata)

    def test_isdata(_):
        a = np.array([-3.2, -2.4, -1.9, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        _validate.positive(a, "", isdata=isdata)


class TestInRange:
    name = "test name"

    @staticmethod
    def bounds(array):
        return (np.amin(array), np.amax(array))

    def test_pass(self, array):
        min, max = self.bounds(array)
        _validate.inrange(array, self.name, min - 1, max + 1)

    def test_includes_bound(self, array):
        min, max = self.bounds(array)
        _validate.inrange(array, self.name, min, max)

    def test_too_high(self, array):
        min, max = self.bounds(array)
        with pytest.raises(ValueError) as error:
            _validate.inrange(array, self.name, min, max - 1)
        assert_contains(error, self.name, str(max - 1))

    def test_too_low(self, array):
        min, max = self.bounds(array)
        with pytest.raises(ValueError) as error:
            _validate.inrange(array, self.name, min + 1, max)
        assert_contains(error, self.name, str(min + 1))

    def test_only_upper(self, array):
        _, max = self.bounds(array)
        _validate.inrange(array, self.name, max=max)

    def test_only_lower(self, array):
        min, _ = self.bounds(array)
        _validate.inrange(array, self.name, min=min)

    def test_nan(self):
        a = np.array([np.nan, np.nan])
        with pytest.raises(ValueError) as error:
            _validate.inrange(a, self.name, min=-np.inf, max=np.inf)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        _validate.inrange(a, "", min=1, max=4, nodata=nodata)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        _validate.inrange(a, "", min=1, max=4, isdata=isdata)


class TestMask:
    @pytest.mark.parametrize("type", (bool, int, float))
    def test_valid(_, mask, type):
        input = mask.astype(type)
        output = _validate.mask(input, "test name")
        assert np.array_equal(output, mask)

    @pytest.mark.parametrize("value", (np.nan, np.inf, -999, 3))
    def test_invalid(_, mask, value):
        mask = mask.astype(float)
        mask[0, 0] = value
        with pytest.raises(ValueError) as error:
            _validate.mask(mask, "test name")
        assert_contains(error, "test name")

    def test_nan(_, mask):
        mask = mask.astype(float)
        mask[0, 0] = np.nan
        with pytest.raises(ValueError) as error:
            _validate.mask(mask, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 1, 0])
        output = _validate.mask(a, "", nodata=nodata)
        expected = np.array([False, False, True, True, False])
        check_equal(output, expected)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 1, 0, 0])
        isdata = np.array([False] * 4 + [True] * 4)
        output = _validate.mask(a, "", isdata=isdata)
        expected = np.array([False] * 4 + [True, True, False, False])
        check_equal(output, expected)


class TestFlow:
    @pytest.mark.parametrize("type", (int, float))
    def test_valid(_, type):
        a = np.array([1, 2, 5, 4, 8, 6, 7, 2, 4, 3, 5, 4, 6, 7, 8]).astype(type)
        _validate.flow(a, "test name")

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:pfdf.validate")
    @pytest.mark.parametrize("value", (np.nan, np.inf, -np.inf, 0, 1.1, 6.7, 9, -900))
    def test_invalid(_, value):
        a = np.array([1, 2, 5, 4, 8, 6, 7, 2, 4, 3, 5, 4, 6, 7, 8]).astype(type)
        a[5] = value
        with pytest.raises(ValueError) as error:
            _validate.flow(a, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize("nodata", (-999, np.nan))
    def test_nodata(_, nodata):
        a = np.array([nodata, nodata, 1, 2, 3])
        _validate.flow(a, "", nodata=nodata)

    def test_isdata(_):
        a = np.array([-3, -2, -1, 0, 1, 2, 3, 4])
        isdata = np.array([False] * 4 + [True] * 4)
        _validate.flow(a, "", isdata=isdata)
