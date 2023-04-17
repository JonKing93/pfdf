"""
test_utils  Unit tests for low-level package utilities
"""

import pytest
import numpy as np
import rasterio
from dfha import utils


@pytest.mark.parametrize(
    "input, expected",
    (
        (1, [1]),
        ([1, 2, 3], [1, 2, 3]),
        ("test", ["test"]),
        ({"a": "test"}, [{"a": "test"}]),
        ((1, 2, 3), [1, 2, 3]),
    ),
)
def test_aslist(input, expected):
    assert utils.aslist(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    (
        (1, (1,)),
        ([1, 2, 3], (1, 2, 3)),
        ("test", ("test",)),
        ({"a": "test"}, ({"a": "test"},)),
        ((1, 2, 3), (1, 2, 3)),
    ),
)
def test_astuple(input, expected):
    assert utils.astuple(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    (
        ((1, 2, 3), True),
        ((True,), True),
        ((False,), True),
        ((1, None, "test"), True),
        ((None, None, False), True),
        ((None,), False),
        ((None, None, None), False),
    ),
)
def test_any_defined(input, expected):
    assert utils.any_defined(*input) == expected


@pytest.fixture
def band1():
    return np.ndarray([1,2,3,4,5,6,7,8]).reshape(2,4)

@pytest.fixture
def band2(band1):
    return band1 * 10

@pytest.fixture
def raster_path(tmp_path, band1, band2):
    raster = tmp_path / "raster.tif"
    with rasterio.open(
        raster, 
        'w', 
        driver='GTiff',
        height = band1.shape[0],
        width = band1.shape[1],
        count = 2,
        dtype = band1.dtype,
    ) as file:
        file.write(band1, 1)
        file.write(band2, 2)
    return raster


class TestLoadRaster:

    @pytest.parametrize('array', (band1, band2))
    def test_array(array):
        assert array == utils.load_raster(array)

    # Band should be ignored when given an ndarray as input
    @pytest.parametrize('band', (1,2,3))
    def test_array_band(band1, band):
        assert utils.load_raster(band1, band) == band1

    def test_path(raster_path, band1):
        assert utils.load_raster(raster_path) == band1

    @pytest.parametrize('band, array', (1, band1), (2, band2))
    def test_path_band(raster_path, band, array):
        assert utils.load_raster(raster_path, band) == array

