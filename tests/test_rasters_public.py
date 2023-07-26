import numpy as np
import pytest
import rasterio

from pfdf.rasters import Raster


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


class TestRaster:
    def test_standard(_):
        a = np.arange(0, 10).reshape(2, 5)
        npr = Raster(a, nodata=-999)
        assert np.array_equal(npr.array, a)
        assert npr.shape == (2, 5)
        assert npr.dtype == a.dtype
        assert npr.nodata == -999

    def test_invalid_nodata(_):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(TypeError) as error:
            Raster(a, nodata="invalid")
        assert_contains(error, "nodata")

    def test_invalid_array(_):
        with pytest.raises(TypeError) as error:
            Raster("invalid")
        assert_contains(error, "input raster")

    def test_nodata_cast_dtype(_):
        a = np.arange(0, 10).reshape(2, 5).astype(int)
        npr = Raster(a, nodata=2.2)
        assert npr.nodata == 2
