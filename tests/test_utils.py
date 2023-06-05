"""
test_utils  Unit tests for low-level package utilities

Requirements:
    * pytest, numpy, rasterio
"""

import pytest
import numpy as np
import rasterio
import warnings
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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        with rasterio.open(
            raster,
            "w",
            driver="GTiff",
            height=band1.shape[0],
            width=band1.shape[1],
            count=2,
            dtype=band1.dtype,
            nodata=1,
        ) as file:
            file.write(band1, 1)
            file.write(band2, 2)
    return raster


@pytest.fixture
def output_path(tmp_path):
    return tmp_path / "output.tif"


#####
# Misc
#####

def test_real():
    assert utils.real == [np.integer, np.floating, np.bool_]


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


#####
# Sequences
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


#####
# Rasters
#####


class TestLoadRaster:
    def test_array(_, band1):
        output = utils.load_raster(band1)
        assert np.array_equal(output, band1)

    # Band should be ignored when given an ndarray as input
    @pytest.mark.parametrize("band", [(1), (2), (3)])
    def test_array_band(_, band1, band):
        output = utils.load_raster(band1, band=band)
        assert np.array_equal(output, band1)

    def test_path(_, fraster, band1):
        output = utils.load_raster(fraster)
        assert np.array_equal(output, band1)

    def test_path_band2(_, fraster, band2):
        output = utils.load_raster(fraster, band=2)
        assert np.array_equal(output, band2)


@pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
class TestSaveRaster:
    def test(_, band1, output_path):
        utils.save_raster(band1, output_path)
        with rasterio.open(output_path) as file:
            assert file.count == 1
            raster = file.read(1)
            assert np.array_equal(raster, band1)

    @pytest.mark.parametrize("nodata", (np.nan, 0, -999))
    def test_nodata(_, band1, output_path, nodata):
        utils.save_raster(band1, output_path, nodata)
        with rasterio.open(output_path) as file:
            assert file.count == 1
            assert np.array_equal(file.nodata, nodata, equal_nan=True)
            raster = file.read(1)
            assert np.array_equal(raster, band1)

    def test_bool(_, band1, output_path):
        band1 = band1.astype(bool)
        utils.save_raster(band1, output_path)
        with rasterio.open(output_path) as file:
            assert file.count == 1
            raster = file.read(1)
            assert np.array_equal(raster, band1)


class TestRasterShape:
    def test_array(_, band1):
        assert utils.raster_shape(band1) == band1.shape

    def test_file(_, fraster, band1):
        assert utils.raster_shape(fraster) == band1.shape


#####
# NoData
#####

@pytest.mark.parametrize('function', (utils.data_mask, utils.isdata))
class TestDataMask:
    def test_none(_, function, band1):
        output = function(band1, None)
        assert output is None
        
    def test_number(_, function, band1):
        band1[band1>=6] = -999
        output = function(band1, -999)
        assert np.array_equal(output, band1!=-999)
        
    def test_nan(_, function, band1):
        band1 = band1.astype(float)
        band1[band1>=6] = np.nan
        output = function(band1, np.nan)
        assert np.array_equal(output, ~np.isnan(band1))

@pytest.mark.parametrize('function', (utils.nodata_mask, utils.isnodata))
class TestNodataMask:
    def test_none(_, function, band1):
        output = function(band1, None)
        assert output is None
        
    def test_number(_, function, band1):
        band1[band1>=6] = -999
        output = function(band1, -999)
        assert np.array_equal(output, band1==-999)
        
    def test_nan(_, function, band1):
        band1 = band1.astype(float)
        band1[band1>=6] = np.nan
        output = function(band1, np.nan)
        assert np.array_equal(output, np.isnan(band1))



