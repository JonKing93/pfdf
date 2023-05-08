"""
test_utils  Unit tests for low-level package utilities

Requirements:
    * pytest, numpy, rasterio
"""

import pytest
import numpy as np
import rasterio
from dfha import utils


#####
# Fixtures
#####
@pytest.fixture
def band1():
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


@pytest.fixture
def band2(band1):
    return band1 * 10


@pytest.fixture
def fraster(tmp_path, band1, band2):
    raster = tmp_path / "raster.tif"
    with rasterio.open(
        raster,
        "w",
        driver="GTiff",
        height=band1.shape[0],
        width=band1.shape[1],
        count=2,
        dtype=band1.dtype,
        crs="+proj=latlong",
        transform=rasterio.transform.Affine(300, 0, 101985, 0, -300, 2826915),
    ) as file:
        file.write(band1, 1)
        file.write(band2, 2)
    return raster


@pytest.fixture
def output_path(tmp_path):
    return tmp_path / "output.tif"


#####
# Tests
#####
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


class TestLoadRaster:
    def test_array(_, band1):
        output = utils.load_raster(band1)
        assert np.array_equal(output, band1)

    # Band should be ignored when given an ndarray as input
    @pytest.mark.parametrize("band", [(1), (2), (3)])
    def test_array_band(_, band1, band):
        output = utils.load_raster(band1, band)
        assert np.array_equal(output, band1)

    def test_path(_, fraster, band1):
        output = utils.load_raster(fraster)
        assert np.array_equal(output, band1)

    def test_path_band2(_, fraster, band2):
        output = utils.load_raster(fraster, band=2)
        assert np.array_equal(output, band2)


class TestWriteRaster:
    def test(_, band1, output_path):
        utils.write_raster(band1, output_path)
        with rasterio.open(output_path) as file:
            assert file.count == 1
            raster = file.read(1)
            assert np.array_equal(raster, band1)

    @pytest.mark.parametrize("nodata", (np.nan, 0, -999))
    def test_nodata(_, band1, output_path, nodata):
        utils.write_raster(band1, output_path, nodata)
        with rasterio.open(output_path) as file:
            assert file.count == 1
            assert np.array_equal(file.nodata, nodata, equal_nan=True)
            raster = file.read(1)
            assert np.array_equal(raster, band1)
