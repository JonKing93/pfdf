from pathlib import Path

import numpy as np
import pytest
import rasterio

from pfdf._rasters import Raster as _Raster
from pfdf._rasters import output, validated
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
    raster = tmp_path / "raster.tif"
    with rasterio.open(
        raster,
        "w",
        driver="GTiff",
        height=araster.shape[0],
        width=araster.shape[1],
        count=2,
        dtype=araster.dtype,
        nodata=1,
    ) as file:
        file.write(araster, 1)
    return raster


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
        output = validated(str(fraster), "")
        assert isinstance(output, _Raster)

    def test_path(_, fraster):
        output = validated(fraster, "")
        assert isinstance(output, _Raster)

    def test_reader(_, fraster):
        with rasterio.open(fraster) as input:
            output = validated(input, "")
        assert isinstance(output, _Raster)

    def test_array(_, araster):
        output = validated(araster, "")
        assert isinstance(output, _Raster)

    def test_npr(_, araster):
        input = NumpyRaster(araster)
        output = validated(input, "")
        assert isinstance(output, _Raster)

    def test_bad_string(_):
        input = "not-a-file"
        with pytest.raises(FileNotFoundError):
            validated(input, "")

    def test_missing_file(_, fraster):
        fraster.unlink()
        with pytest.raises(FileNotFoundError):
            validated(fraster, "")

    def test_old_reader(_, fraster):
        with rasterio.open(fraster) as reader:
            reader.close()
            fraster.unlink()
            with pytest.raises(FileNotFoundError):
                validated(fraster, "")

    def test_invalid_type(_):
        with pytest.raises(TypeError) as error:
            validated(5, "test name")
        assert_contains(error, "test name")

    def test_shape(_, araster):
        output = validated(araster, "", shape=(2, 4))
        assert isinstance(output, _Raster)

    def test_invalid_shape(_, araster):
        with pytest.raises(ShapeError) as error:
            validated(araster, "test name", shape=(3, 5))
        assert_contains(error, "test name")

    def test_invalid_dtype(_, araster):
        araster = araster.astype("complex")
        with pytest.raises(TypeError) as error:
            validated(araster, "test name")
        assert_contains(error, "test name")

    def test_not_matrix(_, araster):
        araster = np.stack((araster, araster), axis=1)
        with pytest.raises(DimensionError) as error:
            validated(araster, "test name")
        assert_contains(error, "test name")

    def test_load(_, fraster, araster):
        output = validated(fraster, "")
        assert isinstance(output, _Raster)
        assert np.array_equal(output.values, araster)

    def test_noload(_, fraster):
        output = validated(fraster, "", load=False)
        assert isinstance(output, _Raster)
        assert output.values is None

    def test_noload_array(_, araster):
        output = validated(araster, "", load=False)
        assert isinstance(output, _Raster)
        assert np.array_equal(output.values, araster)


class TestOutput:
    def test_nopath(_):
        a = np.arange(0, 8).reshape(2, 4)
        out = output(a, path=None, nodata=0)

        assert isinstance(out, NumpyRaster)
        assert out.nodata == 0
        assert np.array_equal(out.array, a)

    def test_nopath(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        a = np.arange(0, 8).reshape(2, 4)
        out = output(a, path, nodata=0)

        assert out == path
        out = _Raster(path)
        assert out.nodata == 0
        assert np.array_equal(out.values, a)
