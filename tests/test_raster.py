from math import isnan, nan, sqrt
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from pysheds.sview import Raster as pysheds_raster
from pysheds.sview import ViewFinder
from rasterio.coords import BoundingBox
from rasterio.crs import CRS

from pfdf.errors import (
    CrsError,
    DimensionError,
    RasterCrsError,
    RasterShapeError,
    RasterTransformError,
    TransformError,
)
from pfdf.raster import Raster, RasterInput
from pfdf.typing import MatrixArray


#####
# Testing utilities and fixtures
#####
@pytest.fixture
def araster():
    "A numpy array raster"
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


@pytest.fixture
def crs():
    return CRS.from_epsg(4326)


@pytest.fixture
def transform():
    return Affine(0.03, 0, -4, 0, 0.03, -3)


@pytest.fixture
def fraster(tmp_path, araster, transform, crs):
    "A file-based raster"
    path = tmp_path / "raster.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=araster.shape[0],
        width=araster.shape[1],
        count=1,
        dtype=araster.dtype,
        nodata=-999,
        transform=transform,
        crs=crs,
    ) as file:
        file.write(araster, 1)
    return path


def check(output, name, araster, transform, crs):
    "Checks a raster object's properties match expected values"

    assert isinstance(output, Raster)
    assert output.name == name
    assert np.array_equal(output.values, araster)
    assert output.dtype == araster.dtype
    assert output.nodata == -999

    assert output.shape == araster.shape
    assert output.size == araster.size
    assert output.height == araster.shape[0]
    assert output.width == araster.shape[1]

    assert output.crs == crs
    assert output.transform == transform
    left, top = transform * (0, 0)
    right, bottom = transform * araster.shape
    assert output.bounds == BoundingBox(left, bottom, right, top)

    assert output.resolution == (transform[0], transform[4])
    assert output.pixel_area == transform[0] * transform[4]
    assert output.pixel_diagonal == sqrt(transform[0] ** 2 + transform[4] ** 2)


def assert_contains(error, *strings):
    "Check exception message contains specific strings"
    message = error.value.args[0]
    for string in strings:
        assert string in message


#####
# Object Creation
#####


def test_raster_input():
    assert RasterInput == (
        str | Path | rasterio.DatasetReader | MatrixArray | Raster | pysheds_raster
    )


class TestRasterInit:
    #####
    # Valid inputs
    #####
    def test_string(self, fraster, araster, transform, crs):
        output = Raster(str(fraster), "test")
        check(output, "test", araster, transform, crs)

    def test_default_name(self, fraster):
        output = Raster(fraster)
        assert output.name == "raster"

    def test_path(self, fraster, araster, transform, crs):
        output = Raster(fraster, "test")
        check(output, "test", araster, transform, crs)

    def test_dataset_reader(self, fraster, araster, transform, crs):
        with rasterio.open(fraster) as reader:
            pass
        output = Raster(reader, "test")
        check(output, "test", araster, transform, crs)

    def test_array(self, araster):
        output = Raster(araster, "test")
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.name == "test"
        assert output.nodata is None
        assert output.transform is None
        assert output.crs is None

    def test_raster(self, fraster, araster, transform, crs):
        input = Raster(fraster, "a different name")
        output = Raster(input, "test")
        check(output, "test", araster, transform, crs)

    def test_pysheds(self, araster, transform, crs):
        view = ViewFinder(affine=transform, crs=crs, nodata=-999, shape=araster.shape)
        input = pysheds_raster(araster, view)
        output = Raster(input, "test")
        check(output, "test", araster, transform, crs)

    #####
    # Invalid inputs
    #####
    def test_bad_string(_):
        input = "not-a-file"
        with pytest.raises(FileNotFoundError):
            Raster(input, "")

    def test_missing_file(_, fraster):
        fraster.unlink()
        with pytest.raises(FileNotFoundError):
            Raster(fraster, "")

    def test_old_reader(_, fraster):
        with rasterio.open(fraster) as reader:
            pass
        fraster.unlink()
        with pytest.raises(FileNotFoundError) as error:
            Raster(reader, "")
        assert_contains(error, "rasterio.DatasetReader", "no longer exists")

    def test_invalid_type(_):
        with pytest.raises(TypeError) as error:
            Raster(5, "test name")
        assert_contains(error, "test name")

    def test_invalid_dtype(_, araster):
        araster = araster.astype("complex")
        with pytest.raises(TypeError) as error:
            Raster(araster, "test name")
        assert_contains(error, "test name")

    def test_not_matrix(_, araster):
        araster = np.stack((araster, araster), axis=1)
        with pytest.raises(DimensionError) as error:
            Raster(araster, "test name")
        assert_contains(error, "test name")

    def test_bad_affine(_, araster):
        raster = Raster(araster)
        raster._transform = Affine(1, 2, 3, 4, 5, 6)
        with pytest.raises(TransformError) as error:
            Raster(raster, "test name")
        assert_contains(
            error, "The raster transform must only support scaling and translation."
        )


def test_from_file(fraster, araster, transform, crs):
    raster = Raster(araster)
    raster._from_file(fraster)
    assert np.array_equal(raster._values, araster)
    assert raster._nodata == -999
    assert raster._transform == transform
    assert raster._crs == crs


def test_from_pysheds(araster, transform, crs):
    raster = Raster(araster)
    view = ViewFinder(affine=transform, crs=crs, nodata=-999, shape=araster.shape)
    input = pysheds_raster(araster, view)
    raster._from_pysheds(input)
    assert np.array_equal(raster._values, araster)
    assert raster._nodata == -999
    assert raster._transform == transform
    assert raster._crs == crs


def test_from_raster(fraster, araster, transform, crs):
    raster = Raster(araster)
    input = Raster(fraster)
    raster._from_raster(input)
    assert np.array_equal(raster._values, araster)
    assert raster._nodata == -999
    assert raster._transform == transform
    assert raster._crs == crs


class TestFromArray:
    def test_without_metadata(_, araster):
        output = Raster.from_array(araster)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.name == "raster"
        assert output.nodata is None
        assert output.transform is None
        assert output.crs is None

    def test_with_metadata(_, araster, transform, crs):
        output = Raster.from_array(
            araster, name="test", nodata=-999, transform=transform, crs=crs
        )
        check(output, "test", araster, transform, crs)

    def test_nodata_casting(_, araster):
        araster = araster.astype("float64")
        nodata = np.array(-999).astype("float32")
        output = Raster.from_array(araster, nodata=nodata)
        assert output.dtype == "float64"
        assert output.nodata == -999
        assert output.nodata.dtype == "float64"

    def test_nodata_not_scalar(_, araster):
        nodata = [1, 2]
        with pytest.raises(DimensionError) as error:
            Raster.from_array(araster, nodata=nodata)
        assert_contains(error, "nodata")

    def test_nodata_invalid_type(_, araster):
        nodata = "invalid"
        with pytest.raises(TypeError):
            Raster.from_array(araster, nodata=nodata)

    def test_invalid_nodata_casting(_, araster):
        nodata = -1.2
        araster = araster.astype(int)
        with pytest.raises(TypeError) as error:
            Raster.from_array(araster, nodata=nodata)
        assert_contains(error, "Cannot safely cast the NoData value")

    def test_invalid_transform(_, araster):
        with pytest.raises(TransformError) as error:
            Raster.from_array(araster, transform="invalid")
        assert_contains(error, "transform", "affine.Affine")

    def test_invalid_crs(_, araster):
        with pytest.raises(CrsError) as error:
            Raster.from_array(araster, crs="invalid")
        assert_contains(error, "crs", "rasterio.crs.CRS")


#####
# Misc Properties
#####


class TestSetName:
    def test_string(_, araster):
        output = Raster(araster, "test")
        output.name = "different name"
        assert output.name == "different name"

    def test_not_string(_, araster):
        output = Raster(araster, "test")
        with pytest.raises(TypeError) as error:
            output.name = 5
        assert_contains(error, "raster name must be a string")


class TestBounds:
    def test_exists(_, fraster, transform):
        raster = Raster(fraster)
        left, top = transform * (0, 0)
        right, bottom = transform * raster.shape
        expected = BoundingBox(left, bottom, right, top)
        assert raster.bounds == expected

    def test_missing(_, araster):
        raster = Raster(araster)
        expected = BoundingBox(nan, nan, nan, nan)
        assert raster.bounds == expected


class TestResolution:
    def test_exists(_, fraster, transform):
        raster = Raster(fraster)
        assert raster.resolution == (transform[0], transform[4])

    def test_missing(_, araster):
        raster = Raster(araster)
        dx, dy = raster.resolution
        assert isnan(dx)
        assert isnan(dy)

    def test_negative_scale(_, araster):
        transform = Affine(-10, 0, 0, 0, -10, 0)
        raster = Raster.from_array(araster, transform=transform)
        dx, dy = raster.resolution
        assert dx == 10
        assert dy == 10


class TestPixelArea:
    def test_exists(_, fraster, transform):
        raster = Raster(fraster)
        assert raster.pixel_area == transform[0] * transform[4]

    def test_missing(_, araster):
        raster = Raster(araster)
        assert isnan(raster.pixel_area)

    def test_negative_scale(_, araster):
        transform = Affine(10, 0, 0, 0, -10, 0)
        raster = Raster.from_array(araster, transform=transform)
        assert raster.pixel_area == 100


class TestPixelDiagonal:
    def test_exists(_, fraster, transform):
        raster = Raster(fraster)
        assert raster.pixel_diagonal == sqrt(transform[0] ** 2 + transform[4] ** 2)

    def test_missing(_, araster):
        raster = Raster(araster)
        assert isnan(raster.pixel_diagonal)


#####
# Dunders
#####


class TestEq:
    def test_same(_, fraster, araster, crs, transform):
        raster = Raster(fraster)
        other = Raster.from_array(araster, crs=crs, transform=transform, nodata=-999)
        assert raster == other

    def test_same_nan_nodata(_, araster):
        araster[0, 0] = np.nan
        raster = Raster.from_array(araster, nodata=np.nan)
        other = araster.copy()
        other = Raster.from_array(other, nodata=np.nan)
        assert raster == other

    def test_both_none_nodata(_, araster):
        raster1 = Raster.from_array(araster)
        raster2 = Raster.from_array(araster)
        assert raster1 == raster2

    def test_single_none_nodata(_, araster):
        raster1 = Raster.from_array(araster)
        raster2 = Raster.from_array(araster, nodata=-999)
        assert raster1 != raster2

    def test_other_type(_, fraster):
        raster = Raster(fraster)
        assert raster != 5

    def test_other_nodata(_, fraster):
        raster = Raster(fraster)
        other = Raster(fraster)
        other._nodata = 5
        assert raster != other

    def test_other_crs(_, fraster):
        raster = Raster(fraster)
        other = Raster(fraster)
        other._crs = CRS.from_epsg(4000)
        assert raster != other

    def test_other_transform(_, fraster):
        raster = Raster(fraster)
        other = Raster(fraster)
        other._transform = Affine(1, 2, 3, 4, 5, 6)
        assert raster != other


#####
# IO
#####


class TestSave:
    def test_standard(_, fraster, tmp_path, araster, transform, crs):
        path = Path(tmp_path) / "output.tif"
        raster = Raster(fraster)
        raster.save(path)
        assert path.is_file()
        with rasterio.open(path) as file:
            values = file.read(1)
        assert np.array_equal(values, araster)
        assert file.nodata == -999
        assert file.transform == transform
        assert file.crs == crs

    def test_boolean(_, tmp_path, araster, transform, crs):
        path = Path(tmp_path) / "output.tif"
        araster = araster.astype(bool)
        raster = Raster.from_array(araster, transform=transform, crs=crs)
        raster.save(path)
        assert path.is_file()
        with rasterio.open(path) as file:
            values = file.read(1)
        assert values.dtype == "int8"
        assert np.array_equal(values, araster.astype("int8"))
        assert file.nodata is None
        assert file.transform == transform
        assert file.crs == crs

    def test_overwrite(_, fraster, tmp_path, araster, transform, crs):
        path = Path(tmp_path) / "output.tif"
        raster = Raster(fraster)
        raster.save(path)
        assert path.is_file()

        araster = araster + 1
        raster = Raster.from_array(araster, transform=transform, crs=crs)
        raster.save(path, overwrite=True)
        assert path.is_file()
        with rasterio.open(path) as file:
            values = file.read(1)
        assert np.array_equal(values, araster)

    def test_invalid_overwrite(_, fraster, tmp_path):
        path = Path(tmp_path) / "output.tif"
        raster = Raster(fraster)
        raster.save(path)
        with pytest.raises(FileExistsError):
            raster.save(path)


class TestAsPysheds:
    def test_with_metadata(_, fraster, araster, transform, crs):
        raster = Raster(fraster)
        output = raster.as_pysheds()
        assert isinstance(output, pysheds_raster)
        assert np.array_equal(output, araster)
        assert output.affine == transform
        assert output.crs == crs

    def test_no_metadata(_, araster):
        raster = Raster(araster)
        output = raster.as_pysheds()
        assert isinstance(output, pysheds_raster)
        assert np.array_equal(output, araster)
        assert output.nodata == 0
        assert output.affine == Affine(1, 0, 0, 0, 1, 0)
        assert output.crs == CRS.from_epsg(4326)

    def test_bool_with_nodata(_, araster, transform, crs):
        araster = araster.astype(bool)
        raster = Raster.from_array(araster, nodata=True, transform=transform, crs=crs)
        output = raster.as_pysheds()
        assert isinstance(output, pysheds_raster)
        assert np.array_equal(output, araster)
        assert output.nodata == True
        assert output.affine == transform
        assert output.crs == crs

    def test_bool_without_nodata(_, araster, transform, crs):
        araster = araster.astype(bool)
        raster = Raster.from_array(araster, transform=transform, crs=crs)
        output = raster.as_pysheds()
        assert isinstance(output, pysheds_raster)
        assert np.array_equal(output, araster)
        assert output.nodata == False
        assert output.affine == transform
        assert output.crs == crs

    def test_int8_with_nodata(_, araster, transform, crs):
        araster = araster.astype("int8")
        raster = Raster.from_array(araster, nodata=5, crs=crs, transform=transform)
        output = raster.as_pysheds()
        assert isinstance(output, pysheds_raster)
        assert np.array_equal(output, araster)
        assert output.nodata == 5
        assert output.affine == transform
        assert output.crs == crs

    def test_int8_without_nodata(_, araster, transform, crs):
        araster = araster.astype("int8")
        raster = Raster.from_array(araster, crs=crs, transform=transform)
        output = raster.as_pysheds()
        assert isinstance(output, pysheds_raster)
        assert np.array_equal(output, araster)
        assert output.nodata == 0
        assert output.affine == transform
        assert output.crs == crs


class TestValidate:
    def test_valid_raster(_, fraster, araster, transform, crs):
        raster = Raster(fraster, "a different name")
        output = raster._validate(fraster, "test")
        check(output, "test", araster, transform, crs)

    def test_default_spatial(_, fraster, araster):
        raster = Raster(fraster)
        output = raster._validate(araster, "test")
        assert output.crs == raster.crs
        assert output.transform == raster.transform

    def test_bad_shape(_, fraster, transform, crs):
        raster = Raster(fraster, "self name")
        height = raster.shape[0] + 1
        width = raster.shape[1] + 1
        araster = np.ones((height, width))
        input = Raster.from_array(araster, transform=transform, crs=crs)
        with pytest.raises(RasterShapeError) as error:
            raster._validate(input, "test name")
        assert_contains(error, "test name", "self name")

    def test_bad_transform(_, fraster, araster, crs):
        transform = Affine(9, 0, 0, 0, 9, 0)
        raster = Raster(fraster, "self name")
        input = Raster.from_array(araster, crs=crs, transform=transform)
        with pytest.raises(RasterTransformError) as error:
            raster._validate(input, "test name")
        assert_contains(error, "test name", "self name")

    def test_bad_crs(_, fraster, araster, transform):
        crs = CRS.from_epsg(4000)
        raster = Raster(fraster, "self name")
        input = Raster.from_array(araster, crs=crs, transform=transform)
        with pytest.raises(RasterCrsError) as error:
            raster._validate(input, "test name")
        assert_contains(error, "test name", "self name")

    @pytest.mark.parametrize(
        "input, error, message",
        (
            (5, TypeError, "test name"),
            (np.ones((3, 3, 3)), DimensionError, "test name"),
        ),
    )
    def test_invalid_raster(_, input, error, message, fraster):
        raster = Raster(fraster, "self name")
        with pytest.raises(error) as e:
            raster._validate(input, "test name")
        assert_contains(e, message)
