from pathlib import Path
from warnings import catch_warnings, simplefilter

import numpy as np
import pytest
import rasterio

from pfdf._rasters import Raster as _Raster
from pfdf.errors import DimensionError, ShapeError
from pfdf.rasters import NumpyRaster


#####
# Testing Utilities and fixtures
#####
@pytest.fixture
def araster():
    "A numpy array raster"
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


@pytest.fixture
def fraster(tmp_path, araster):
    "A file-based raster"
    path = tmp_path / "raster.tif"
    raster = _Raster(araster)
    raster.nodata = 1
    raster.save(path)
    return path


def assert_contains(error, *strings):
    "Check exception message contains specific strings"
    message = error.value.args[0]
    for string in strings:
        assert string in message


#####
# Tests
#####


class TestRasterInit:
    def test_array(_, araster):
        raster = _Raster(araster)
        assert raster.path is None
        assert np.array_equal(raster.values, araster)
        assert raster.shape == araster.shape
        assert raster.dtype == araster.dtype
        assert raster.nodata is None

    def test_npr(_, araster):
        npr = NumpyRaster(araster, nodata=-999)
        raster = _Raster(npr)
        assert raster.path is None
        assert np.array_equal(raster.values, araster)
        assert raster.shape == araster.shape
        assert raster.dtype == araster.dtype
        assert raster.nodata == -999

    def test_file_noload(_, fraster, araster):
        raster = _Raster(fraster, load=False)
        assert raster.path == fraster
        assert raster.values is None
        assert raster.shape == araster.shape
        assert raster.dtype == araster.dtype
        assert raster.nodata == 1

    def test_file_load(_, fraster, araster):
        raster = _Raster(fraster, load=True)
        assert raster.path == fraster
        assert np.array_equal(raster.values, araster)
        assert raster.shape == araster.shape
        assert raster.dtype == araster.dtype
        assert raster.nodata == 1


class TestSetValues:
    def test_valid(_, fraster):
        raster = _Raster(fraster, load=False)
        new = np.arange(0, 100).reshape(10, 10).astype(float)
        raster.values = new
        assert raster.path is None
        assert np.array_equal(raster.values, new)
        assert raster.shape == new.shape

    def test_invalid(_, araster):
        raster = _Raster(araster)
        new = araster.astype(bool)
        with pytest.raises(RuntimeError) as error:
            raster.values = new
        assert_contains(error, "would change the dtype")


class TestLoad:
    def test_array(_, araster):
        raster = _Raster(araster, load=False)
        assert raster.path is None
        assert np.array_equal(raster.values, araster)

        raster.load()
        assert raster.path is None
        assert np.array_equal(raster.values, araster)

    def test_path(_, fraster, araster):
        raster = _Raster(fraster, load=False)
        assert raster.path == fraster
        assert raster.values is None

        raster.load()
        assert raster.path == fraster
        assert np.array_equal(raster.values, araster)


class TestSave:
    def test(_, araster, tmp_path):
        path = Path(tmp_path) / "output.tif"
        raster = _Raster(araster)
        raster.save(path)
        assert path.is_file()
        output = _Raster(path)
        assert np.array_equal(output.values, araster)

    def test_not_loaded(_, fraster, tmp_path):
        path = Path(tmp_path) / "output.tif"
        raster = _Raster(fraster, load=False)
        with pytest.raises(RuntimeError) as error:
            raster.save(path)
        assert_contains(error, "raster values have not been loaded")

    def test_bool(_, araster, tmp_path):
        path = Path(tmp_path) / "output.tif"
        araster = araster.astype(bool)
        raster = _Raster(araster)
        raster.save(path)
        assert path.is_file()
        output = _Raster(path)
        assert output.dtype == "int8"
        assert np.array_equal(output.values, araster.astype("int8"))
        assert raster.dtype == bool
        assert np.array_equal(raster.values, araster.astype("int8"))


class TestAsNpr:
    def test_array(_, araster):
        raster = _Raster(araster)
        npr = raster.as_npr()
        assert isinstance(npr, NumpyRaster)
        assert np.array_equal(npr.array, araster)
        assert npr.shape == araster.shape
        assert npr.dtype == araster.dtype
        assert npr.nodata is None

    def test_file(_, fraster, araster):
        raster = _Raster(fraster)
        npr = raster.as_npr()
        assert isinstance(npr, NumpyRaster)
        assert np.array_equal(npr.array, araster)
        assert npr.shape == araster.shape
        assert npr.dtype == araster.dtype
        assert npr.nodata == 1


class TestAsInput:
    def test_npr(_, araster):
        raster = _Raster(araster)
        output = raster.as_input()
        assert isinstance(output, NumpyRaster)
        assert np.array_equal(output.array, araster)

    def test_path(_, fraster):
        raster = _Raster(fraster, load=False)
        output = raster.as_input()
        assert output == fraster


class TestValidated:
    def test_string(_, fraster):
        output = _Raster.validate(str(fraster), "")
        assert isinstance(output, _Raster)

    def test_path(_, fraster):
        output = _Raster.validate(fraster, "")
        assert isinstance(output, _Raster)

    def test_reader(_, fraster):
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
            with rasterio.open(fraster) as input:
                output = _Raster.validate(input, "")
            assert isinstance(output, _Raster)

    def test_array(_, araster):
        output = _Raster.validate(araster, "")
        assert isinstance(output, _Raster)

    def test_npr(_, araster):
        input = NumpyRaster(araster)
        output = _Raster.validate(input, "")
        assert isinstance(output, _Raster)

    def test_bad_string(_):
        input = "not-a-file"
        with pytest.raises(FileNotFoundError):
            _Raster.validate(input, "")

    def test_missing_file(_, fraster):
        fraster.unlink()
        with pytest.raises(FileNotFoundError):
            _Raster.validate(fraster, "")

    def test_old_reader(_, fraster):
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
            with rasterio.open(fraster) as reader:
                reader.close()
                fraster.unlink()
                with pytest.raises(FileNotFoundError) as error:
                    _Raster.validate(reader, "")
                assert_contains(error, "rasterio.DatasetReader", "no longer exists")

    def test_invalid_type(_):
        with pytest.raises(TypeError) as error:
            _Raster.validate(5, "test name")
        assert_contains(error, "test name")

    def test_shape(_, araster):
        output = _Raster.validate(araster, "", shape=(2, 4))
        assert isinstance(output, _Raster)

    def test_invalid_shape(_, araster):
        with pytest.raises(ShapeError) as error:
            _Raster.validate(araster, "test name", shape=(3, 5))
        assert_contains(error, "test name")

    def test_invalid_dtype(_, araster):
        araster = araster.astype("complex")
        with pytest.raises(TypeError) as error:
            _Raster.validate(araster, "test name")
        assert_contains(error, "test name")

    def test_not_matrix(_, araster):
        araster = np.stack((araster, araster), axis=1)
        with pytest.raises(DimensionError) as error:
            _Raster.validate(araster, "test name")
        assert_contains(error, "test name")

    def test_load(_, fraster, araster):
        output = _Raster.validate(fraster, "")
        assert isinstance(output, _Raster)
        assert np.array_equal(output.values, araster)

    def test_noload(_, fraster):
        output = _Raster.validate(fraster, "", load=False)
        assert isinstance(output, _Raster)
        assert output.values is None

    def test_noload_array(_, araster):
        output = _Raster.validate(araster, "", load=False)
        assert isinstance(output, _Raster)
        assert np.array_equal(output.values, araster)


class TestOutput:
    def test_nopath(_):
        a = np.arange(0, 8).reshape(2, 4)
        out = _Raster.output(a, path=None, nodata=0)

        assert isinstance(out, NumpyRaster)
        assert out.nodata == 0
        assert np.array_equal(out.array, a)

    def test_nopath(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        a = np.arange(0, 8).reshape(2, 4)
        out = _Raster.output(a, path, nodata=0)

        assert out == path
        out = _Raster(path)
        assert out.nodata == 0
        assert np.array_equal(out.values, a)
