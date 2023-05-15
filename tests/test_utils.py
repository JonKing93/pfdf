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
        nodata=1,
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
        output = utils.load_raster(band1, band=band)
        assert np.array_equal(output, band1)

    def test_path(_, fraster, band1):
        output = utils.load_raster(fraster)
        assert np.array_equal(output, band1)

    def test_path_band2(_, fraster, band2):
        output = utils.load_raster(fraster, band=2)
        assert np.array_equal(output, band2)

    def test_nodata_array(_, band1):
        output = utils.load_raster(band1, numpy_nodata=1, nodata_to=-999)
        band1[0,0] = -999
        assert np.array_equal(output, band1)

    def test_nodata_file(_, fraster, band1):
        output = utils.load_raster(fraster, nodata_to=-999)
        band1[0, 0] = -999
        assert np.array_equal(output, band1)


class TestReplaceNodata:
    def test_number(_, band1):
        expected = band1.copy()
        expected[0, 3] = -999
        output = utils.replace_nodata(band1, 4, -999)
        assert np.array_equal(band1, expected)
        assert output is None

    def test_number_mask(_, band1):
        expected = band1.copy()
        expected[0, 3] = -999
        expected_mask = band1==4
        mask = utils.replace_nodata(band1, 4, -999, return_mask=True)
        assert np.array_equal(band1, expected)
        assert np.array_equal(mask, expected_mask)

    def test_nan(_, band1):
        expected = band1.copy()
        expected[0, 3] = -999
        band1[0, 3] = np.nan
        output = utils.replace_nodata(band1, np.nan, -999)
        assert np.array_equal(band1, expected)
        assert output is None

    def test_nan_mask(_, band1):
        expected = band1.copy()
        expected[0, 3] = -999
        band1[0, 3] = np.nan
        expected_mask = np.isnan(band1)
        mask = utils.replace_nodata(band1, np.nan, -999, return_mask=True)
        assert np.array_equal(band1, expected)
        assert np.array_equal(mask, expected_mask)

    def test_none(_, band1):
        expected = band1.copy()
        output = utils.replace_nodata(band1, None, -999)
        assert output is None
        assert np.array_equal(band1, expected)

    def test_none_mask(_, band1):
        expected = band1.copy()
        mask = utils.replace_nodata(band1, None, -999, return_mask=True)
        assert np.array_equal(mask, np.full(band1.shape, False))
        assert np.array_equal(band1, expected)


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
