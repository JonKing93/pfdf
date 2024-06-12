import os
from math import isnan, nan
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder

from pfdf.errors import (
    CRSError,
    DimensionError,
    MissingCRSError,
    MissingNoDataError,
    MissingTransformError,
    RasterCRSError,
    RasterShapeError,
    RasterTransformError,
    TransformError,
)
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster, RasterInput
from pfdf.typing import MatrixArray

#####
# Testing utilities
#####


@pytest.fixture
def bounds(transform, araster):
    return transform.bounds(*araster.shape)


def check(output, name, araster, transform, crs):
    "Checks a raster object's properties match expected values"

    assert isinstance(output, Raster)
    assert output.name == name

    assert np.array_equal(output.values, araster)
    assert output.values is not output._values
    assert output._values is not araster
    assert output._values.flags.writeable == False

    assert output.dtype == araster.dtype
    assert output.nodata == -999
    assert output.nodata.dtype == output.dtype

    assert output.shape == araster.shape
    assert output.size == araster.size
    assert output.height == araster.shape[0]
    assert output.width == araster.shape[1]

    assert output.crs == crs
    transform = transform.todict()
    transform["crs"] = crs
    transform = Transform.from_dict(transform)
    assert output.transform == transform
    left, top = transform.affine * (0, 0)
    right, bottom = transform.affine * (araster.shape[1], araster.shape[0])
    assert output.bounds == BoundingBox(left, bottom, right, top, crs)


#####
# Low level Init
#####


def test_raster_input():
    assert RasterInput == (
        str | Path | rasterio.DatasetReader | MatrixArray | Raster | PyshedsRaster
    )


class TestInitEmpty:
    def test(_):
        a = Raster()
        assert isinstance(a, Raster)
        assert a._values is None
        assert a._nodata is None
        assert a._crs is None
        assert a._transform is None
        assert a.name == "raster"

    def test_with_name(_):
        a = Raster(None, "test name")
        assert isinstance(a, Raster)
        assert a._values is None
        assert a._nodata is None
        assert a._crs is None
        assert a._transform is None
        assert a.name == "test name"

    def test_invalid_name(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster(None, 5)
        assert_contains(error, "name")


class TestInitUser:
    def test_file(_, fraster, araster, transform, crs):
        raster = Raster(fraster, "test")
        check(raster, "test", araster, transform, crs)

    def test_rasterio(_, fraster, araster, transform, crs):
        with rasterio.open(fraster) as reader:
            pass
        output = Raster(reader, "test")
        check(output, "test", araster, transform, crs)

    def test_pysheds(_, araster, transform, crs):
        view = ViewFinder(
            affine=transform.affine, crs=crs, nodata=-999, shape=araster.shape
        )
        input = PyshedsRaster(araster, view)
        output = Raster(input, "test")
        check(output, "test", araster, transform, crs)
        assert output._values is not input

    def test_array(_, araster):
        output = Raster(araster, "test")
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output._values is not araster
        assert output.name == "test"
        assert np.isnan(output.nodata)
        assert output.transform is None
        assert output.crs is None

    def test_raster(self, fraster, araster, transform, crs):
        input = Raster(fraster, "a different name")
        output = Raster(input, "test")
        check(output, "test", araster, transform, crs)

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster(5, "test name")
        assert_contains(error, "test name")


#####
# Low level Factories
#####


class TestMatch:
    def test(_):
        raster1 = Raster()
        raster1._values = 1
        raster1._crs = 2
        raster1._transform = 3
        raster1._nodata = 4

        raster2 = Raster()
        raster2._match(raster1)
        assert raster2._values == 1
        assert raster2._crs == 2
        assert raster2._transform == 3
        assert raster2._nodata == 4


class TestCreate:
    def test(_, araster, crs, transform):
        output = Raster._create("test", araster, crs, transform, -999, "unsafe", False)
        assert isinstance(output, Raster)
        assert output._name == "test"
        assert np.array_equal(output._values, araster)
        assert output._nodata == -999
        assert output._crs == crs
        assert output._transform == transform


class TestFinalize:
    def test_no_metadata(_, araster):
        raster = Raster()
        raster._finalize(araster, None, None, None, "safe", False)

        assert raster._nodata is None
        assert raster._transform is None
        assert raster._crs is None
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False

    def test_with_metadata(_, araster, crs, transform):
        raster = Raster()
        raster._finalize(araster, crs, transform, -999, "unsafe", False)

        assert raster._nodata == -999
        assert raster._nodata.dtype == raster.dtype
        assert raster._transform == transform
        assert isinstance(raster._transform, Transform)
        assert raster._crs == crs
        assert isinstance(raster._crs, CRS)
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False

    def test_nodata_casting(_, araster, crs, transform):
        raster = Raster()
        araster = araster.astype(int)
        raster._finalize(araster, crs, transform, -2.2, "unsafe", False)

        assert raster._nodata == -2
        assert raster._nodata.dtype == raster.dtype
        assert raster._transform == transform
        assert raster._crs == crs
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False

    def test_invalid_crs(_, araster):
        raster = Raster()
        with pytest.raises(CRSError):
            raster._finalize(araster, "invalid", None, None, "safe", False)

    def test_invalid_transform(_, araster, assert_contains):
        raster = Raster()
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, "invalid", None, "safe", False)
        assert_contains(
            error,
            "transform must be a dict, list, tuple, affine.Affine, Transform, or Raster",
        )

    def test_invalid_shear(_, araster, assert_contains):
        raster = Raster()
        transform = Affine(1, 2, 3, 4, 5, 6)
        with pytest.raises(TransformError) as error:
            raster._finalize(araster, None, transform, None, "unsafe", False)
        assert_contains(
            error, "The affine transform must only support scaling and translation."
        )

    def test_invalid_nodata(_, araster, assert_contains):
        raster = Raster()
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, None, "invalid", "safe", False)
        assert_contains(error, "nodata")

    def test_invalid_casting_option(_, araster, assert_contains):
        raster = Raster()
        with pytest.raises(ValueError) as error:
            raster._finalize(araster, None, None, 2, "invalid", False)
        assert_contains(error, "casting")

    def test_invalid_casting(_, araster, assert_contains):
        raster = Raster()
        araster = araster.astype(int)
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, None, -2.2, "safe", False)
        assert_contains(error, "Cannot cast the NoData value")

    def test_invalid_values(_, assert_contains):
        raster = Raster(None, "test name")
        with pytest.raises(TypeError) as error:
            raster._finalize("invalid", None, None, None, "unsafe", False)
        assert_contains(error, "test name")

    def test_invalid_dtype(_, araster, assert_contains):
        raster = Raster(None, "test name")
        araster = araster.astype("complex")
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, None, None, "unsafe", False)
        assert_contains(error, "test name")

    def test_invalid_shape(_, araster, assert_contains):
        raster = Raster(None, "test name")
        araster = araster.reshape(2, 2, 2)
        with pytest.raises(DimensionError) as error:
            raster._finalize(araster, None, None, None, "unsafe", False)
        assert_contains(error, "test name")

    def test_bool(_):
        raster = Raster()
        araster = np.array([[1, 0, -9, 1], [0, -9, 0, 1]])
        expected = np.array([[1, 0, 0, 1], [0, 0, 0, 1]]).astype(bool)
        raster._finalize(araster, None, None, -9, "unsafe", isbool=True)

        assert raster._nodata == False
        assert raster._nodata.dtype == bool
        assert raster._values.dtype == bool
        assert np.array_equal(raster._values, expected)
        assert raster._values.flags.writeable == False

    def test_bool_no_nodata(_):
        raster = Raster()
        araster = np.array([[1, 0, 0, 1], [0, 0, 0, 1]]).astype(bool)
        raster._finalize(araster, None, None, None, "safe", isbool=True)

        assert raster._nodata == False
        assert raster._nodata.dtype == bool
        assert np.array_equal(raster._values, araster)
        assert raster._values.dtype == bool
        assert raster._values.flags.writeable == False

    def test_invalid_bool(_, assert_contains):
        raster = Raster()
        araster = np.array([0, 1, 2])
        with pytest.raises(ValueError) as error:
            raster._finalize(araster, None, None, None, "unsafe", isbool=True)
        assert_contains(error, "a boolean raster", "0 or 1")

    def test_strip_transform(_, araster, crs, transform):
        raster = Raster()
        transform = transform.todict()
        transform["crs"] = None
        raster._finalize(araster, crs, transform, -999, "unsafe", False)

        assert raster._nodata == -999
        assert raster._nodata.dtype == raster.dtype
        assert raster._transform == Transform.from_dict(transform)
        assert isinstance(raster._transform, Transform)
        assert raster._crs == crs
        assert isinstance(raster._crs, CRS)
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False


class TestSetMetadata:
    def test(_):
        raster = Raster()
        raster._set_metadata(1, 2, 3)
        assert raster._crs == 1
        assert raster._transform == 2
        assert raster._nodata == 3


#####
# Factories
#####


class TestFromFile:
    def test_string(_, fraster, araster, transform, crs):
        output = Raster.from_file(str(fraster), "test")
        check(output, "test", araster, transform, crs)

    def test_path(_, fraster, araster, transform, crs):
        output = Raster.from_file(fraster, "test")
        check(output, "test", araster, transform, crs)

    def test_bad_string(_):
        input = "not-a-file"
        with pytest.raises(FileNotFoundError):
            Raster.from_file(input, "")

    def test_missing_file(_, fraster):
        fraster.unlink()
        with pytest.raises(FileNotFoundError):
            Raster.from_file(fraster, "")

    def test_driver(_, fraster, araster, transform, crs, tmp_path):
        raster = Raster.from_file(fraster)
        file = Path(tmp_path) / "test.unknown_extension"
        raster.save(file, driver="GTiff")
        raster = Raster.from_file(file, driver="GTiff")
        check(raster, "raster", araster, transform, crs)

    def test_band(_, araster, affine, crs, tmp_path):
        zeros = np.zeros(araster.shape, araster.dtype)
        file = Path(tmp_path) / "test.tif"
        with rasterio.open(
            file,
            "w",
            dtype=araster.dtype,
            driver="GTiff",
            width=araster.shape[1],
            height=araster.shape[0],
            count=2,
            nodata=-999,
            transform=affine,
            crs=crs,
        ) as writer:
            writer.write(araster, 1)
            writer.write(zeros, 2)

        raster = Raster.from_file(file, band=2)
        check(raster, "raster", zeros, Transform.from_affine(affine), crs)

    def test_isbool(_, araster, affine, crs, tmp_path):
        araster = np.array([[1, 0, -9, 1], [0, -9, 0, 1]])
        file = Path(tmp_path) / "test.tif"
        with rasterio.open(
            file,
            "w",
            driver="GTiff",
            width=araster.shape[1],
            height=araster.shape[0],
            count=1,
            crs=crs,
            transform=affine,
            dtype=araster.dtype,
            nodata=-9,
        ) as writer:
            writer.write(araster, 1)

        raster = Raster.from_file(file, isbool=True)
        expected = np.array([[1, 0, 0, 1], [0, 0, 0, 1]]).astype(bool)
        assert raster.dtype == bool
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == False

    def test_bounded_exact(_, fraster, araster, crs):
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97, crs)
        raster = Raster.from_file(fraster, bounds=bounds)
        expected = araster[1:2, 1:3]
        assert np.array_equal(raster.values, expected)
        assert raster.crs == crs
        assert raster.transform == Transform(0.03, 0.03, -3.97, -2.97, crs)

    def test_bounded_clipped(_, fraster, araster, crs):
        bounds = BoundingBox(-3.97, 0, 0, -2.97, crs)
        raster = Raster.from_file(fraster, bounds=bounds)
        expected = araster[1:, 1:]
        assert np.array_equal(raster.values, expected)
        assert raster.crs == crs
        assert raster.transform == Transform(0.03, 0.03, -3.97, -2.97, crs)

    def test_automatic_nodata(_, fraster):
        raster = Raster(fraster)
        raster.fill(0)
        assert raster.nodata is None
        raster.save(fraster, overwrite=True)
        raster = Raster.from_file(fraster)
        assert np.isnan(raster.nodata)

    def test_default_nodata(_, fraster):
        raster = Raster(fraster)
        raster.fill(0)
        assert raster.nodata is None
        raster.save(fraster, overwrite=True)
        raster = Raster.from_file(fraster, default_nodata=5)
        assert raster.nodata == 5

    def test_disable_nodata(_, fraster):
        raster = Raster(fraster)
        raster.fill(0)
        assert raster.nodata is None
        raster.save(fraster, overwrite=True)
        raster = Raster.from_file(fraster, ensure_nodata=False)
        assert raster.nodata is None


class TestFromRasterio:
    def test(_, fraster, araster, transform, crs):
        with rasterio.open(fraster) as reader:
            pass
        output = Raster.from_rasterio(reader, "test")
        check(output, "test", araster, transform, crs)

    def test_band(_, araster, transform, crs, tmp_path):
        zeros = np.zeros(araster.shape, araster.dtype)
        file = Path(tmp_path) / "test.tif"
        with rasterio.open(
            file,
            "w",
            dtype=araster.dtype,
            driver="GTiff",
            width=araster.shape[1],
            height=araster.shape[0],
            count=2,
            nodata=-999,
            transform=transform.affine,
            crs=crs,
        ) as writer:
            writer.write(araster, 1)
            writer.write(zeros, 2)

        with rasterio.open(file) as reader:
            pass
        raster = Raster.from_rasterio(reader, band=2)
        check(raster, "raster", zeros, transform, crs)

    def test_old_reader(_, fraster, assert_contains):
        with rasterio.open(fraster) as reader:
            pass
        fraster.unlink()
        with pytest.raises(FileNotFoundError) as error:
            Raster.from_rasterio(reader, "")
        assert_contains(error, "rasterio.DatasetReader", "no longer exists")

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster.from_rasterio("invalid")
        assert_contains(error, "rasterio.DatasetReader")

    def test_isbool(_, araster, transform, crs, tmp_path):
        araster = np.array([[1, 0, -9, 1], [0, -9, 0, 1]])
        file = Path(tmp_path) / "test.tif"
        with rasterio.open(
            file,
            "w",
            driver="GTiff",
            width=araster.shape[1],
            height=araster.shape[0],
            count=1,
            crs=crs,
            transform=transform.affine,
            dtype=araster.dtype,
            nodata=-9,
        ) as writer:
            writer.write(araster, 1)

        with rasterio.open(file) as reader:
            pass

        raster = Raster.from_rasterio(reader, isbool=True)
        expected = np.array([[1, 0, 0, 1], [0, 0, 0, 1]]).astype(bool)
        assert raster.dtype == bool
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == False

    def test_bounded_exact(_, fraster, araster, crs):
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97, crs)
        with rasterio.open(fraster) as reader:
            pass
        raster = Raster.from_rasterio(reader, bounds=bounds)
        expected = araster[1:2, 1:3]
        assert np.array_equal(raster.values, expected)
        assert raster.crs == crs
        assert raster.transform == Transform(0.03, 0.03, -3.97, -2.97, crs)

    def test_bounded_clipped(_, fraster, araster, crs):
        bounds = BoundingBox(-3.97, 0, 0, -2.97, crs)
        with rasterio.open(fraster) as reader:
            pass
        raster = Raster.from_rasterio(reader, bounds=bounds)
        expected = araster[1:, 1:]
        assert np.array_equal(raster.values, expected)
        assert raster.crs == crs
        assert raster.transform == Transform(0.03, 0.03, -3.97, -2.97, crs)

    def test_automatic_nodata(_, fraster):
        raster = Raster(fraster)
        raster.fill(0)
        assert raster.nodata is None
        raster.save(fraster, overwrite=True)
        with rasterio.open(fraster) as reader:
            pass
        raster = Raster.from_rasterio(reader)
        assert np.isnan(raster.nodata)

    def test_default_nodata(_, fraster):
        raster = Raster(fraster)
        raster.fill(0)
        assert raster.nodata is None
        raster.save(fraster, overwrite=True)
        with rasterio.open(fraster) as reader:
            pass
        raster = Raster.from_rasterio(reader, default_nodata=5)
        assert raster.nodata == 5

    def test_disable_nodata(_, fraster):
        raster = Raster(fraster)
        raster.fill(0)
        assert raster.nodata is None
        raster.save(fraster, overwrite=True)
        with rasterio.open(fraster) as reader:
            pass
        raster = Raster.from_rasterio(reader, ensure_nodata=False)
        assert raster.nodata is None


class TestFromPysheds:
    def test(_, araster, transform, crs):
        view = ViewFinder(
            affine=transform.affine, crs=crs, nodata=-999, shape=araster.shape
        )
        input = PyshedsRaster(araster, view)
        araster = araster.astype(input.dtype)
        output = Raster.from_pysheds(input, "test")
        check(output, "test", araster, transform, crs)
        assert output._values is not input

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster.from_pysheds("invalid")
        assert_contains(error, "pysheds.sview.Raster")

    def test_isbool(_, transform, crs):
        araster = np.array([[1, 0, -9, 1], [0, -9, 0, 1]])
        view = ViewFinder(
            affine=transform.affine, crs=crs, nodata=-9, shape=araster.shape
        )
        input = PyshedsRaster(araster, view)
        raster = Raster.from_pysheds(input, isbool=True)

        expected = np.array([[1, 0, 0, 1], [0, 0, 0, 1]]).astype(bool)
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == False
        assert raster.dtype == bool


class TestFromArray:
    def test_without_metadata(_, araster):
        output = Raster.from_array(araster)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.name == "raster"
        assert np.isnan(output.nodata)
        assert output.transform is None
        assert output.crs is None

    def test_copy(_, araster):
        output = Raster.from_array(araster)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.values.base is not araster

    def test_no_copy(_, araster):
        output = Raster.from_array(araster, copy=False)
        assert isinstance(output, Raster)
        assert output.values.base is araster

    def test_with_metadata(_, araster, transform, crs):
        output = Raster.from_array(
            araster, name="test", nodata=-999, transform=transform, crs=crs
        )
        check(output, "test", araster, transform, crs)

    def test_safe_nodata_casting(_, araster):
        araster = araster.astype("float64")
        nodata = np.array(-999).astype("float32")
        output = Raster.from_array(araster, nodata=nodata)
        assert output.dtype == "float64"
        assert output.nodata == -999
        assert output.nodata.dtype == "float64"

    def test_unsafe_nodata_casting(_, araster):
        araster = araster.astype(int)
        nodata = 1.2
        output = Raster.from_array(araster, nodata=nodata, casting="unsafe")
        assert output.dtype == int
        assert output.nodata == 1
        assert output.nodata.dtype == int

    def test_spatial(_, araster, fraster, crs, transform):
        template = Raster(fraster)
        output = Raster.from_array(araster, spatial=template)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.name == "raster"
        assert np.isnan(output.nodata)
        assert output.transform.affine == transform.affine
        assert output.crs == crs

    def test_spatial_override(_, araster, fraster):
        template = Raster(fraster)
        transform = Transform(1, 2, 3, 4)
        output = Raster.from_array(araster, spatial=template, transform=transform)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.name == "raster"
        assert np.isnan(output.nodata)
        assert output.transform.affine == transform.affine
        assert output.crs == template.crs

    def test_nodata_not_scalar(_, araster, assert_contains):
        nodata = [1, 2]
        with pytest.raises(DimensionError) as error:
            Raster.from_array(araster, nodata=nodata)
        assert_contains(error, "nodata")

    def test_nodata_invalid_type(_, araster):
        nodata = "invalid"
        with pytest.raises(TypeError):
            Raster.from_array(araster, nodata=nodata)

    def test_invalid_nodata_casting(_, araster, assert_contains):
        nodata = -1.2
        araster = araster.astype(int)
        with pytest.raises(TypeError) as error:
            Raster.from_array(araster, nodata=nodata)
        assert_contains(error, "Cannot cast the NoData value")

    def test_invalid_transform(_, araster, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster.from_array(araster, transform="invalid")
        assert_contains(error, "transform", "affine.Affine")

    def test_invalid_crs(_, araster, assert_contains):
        with pytest.raises(CRSError) as error:
            Raster.from_array(araster, crs="invalid")
        assert_contains(error, "must be convertible to a pyproj.CRS")

    def test_invalid_spatial(_, araster, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster.from_array(araster, spatial=5)
        assert_contains(error, "spatial template must be a Raster object")

    def test_isbool(_):
        araster = np.array([[1, 0, -9, 1], [0, -9, 0, 1]])
        raster = Raster.from_array(araster, nodata=-9, isbool=True)

        expected = np.array([[1, 0, 0, 1], [0, 0, 0, 1]]).astype(bool)
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == False
        assert raster.dtype == bool

    def test_disable_nodata(_, araster):
        raster = Raster.from_array(araster, ensure_nodata=False)
        assert raster.nodata is None

    def test_bounds_and_transform(_, araster, assert_contains):
        with pytest.raises(ValueError) as error:
            Raster.from_array(araster, transform=1, bounds=2)
        assert_contains(
            error,
            'You cannot specify both "transform" and "bounds" metadata. The two inputs are mutually exclusive.',
        )

    def test_bounds(_, araster, transform):
        bounds = transform.bounds(*araster.shape)
        raster = Raster.from_array(araster, bounds=bounds)
        assert transform.isclose(raster.transform)
        assert raster.bounds == bounds
        assert np.array_equal(raster.values, araster)

    def test_inherit_crs(_, araster):
        transform = Transform(1, 2, 3, 4, 26911)
        raster = Raster.from_array(araster, transform=transform)
        assert raster.crs == CRS(26911)
        bounds = BoundingBox(1, 2, 3, 4, 26911)
        raster = Raster.from_array(araster, bounds=bounds)
        assert raster.crs == CRS(26911)

    def test_reproject_transform(_, araster):
        transform = Transform(1, 1, 0, 0, 26911)
        raster = Raster.from_array(araster, crs=4326, transform=transform)
        assert raster.crs == CRS(4326)
        expected = Transform(
            dx=8.958996673413822e-06,
            dy=9.019375921135681e-06,
            left=-121.48874388438703,
            top=0.0,
            crs=4326,
        )
        assert raster.transform.isclose(expected)

    def test_reproject_bounds(_, araster):
        bounds = BoundingBox(0, 0, 100, 100, 26911)
        raster = Raster.from_array(araster, crs=4326, bounds=bounds)
        expected = BoundingBox(
            left=-121.48874388494063,
            bottom=2.786575690246623e-10,
            right=-121.4878479834734,
            top=0.0009019375809660552,
            crs=4326,
        )
        assert raster.bounds.isclose(expected)


#####
# From vector features
#####


class TestFromPoints:
    def test_invalid_path(_):
        with pytest.raises(FileNotFoundError):
            Raster.from_points("not-a-file")

    def test_points(_, points, crs):
        raster = Raster.from_points(points)
        assert raster.dtype == bool
        assert raster.crs == crs
        assert raster.nodata == False
        assert raster.transform.affine == Transform(10, -10, 10, 60).affine

        expected = np.array(
            [
                [0, 0, 0, 0, 1],
                [0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_memory(_, points, assert_contains):
        with pytest.raises(MemoryError) as error:
            Raster.from_points(points, resolution=1e-20)
        assert_contains(
            error,
            "requested array is too large",
            'Try increasing the "resolution" input',
        )

    def test_multipoints(_, multipoints, crs):
        raster = Raster.from_points(multipoints)
        assert raster.dtype == bool
        assert raster.crs == crs
        assert raster.nodata == False
        assert raster.transform.affine == Transform(10, -10, 10, 90).affine

        expected = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_fixed_res(_, points, crs):
        raster = Raster.from_points(points, resolution=20)
        assert raster.dtype == bool
        assert raster.crs == crs
        assert raster.nodata == False
        assert raster.transform.affine == Transform(20, -20, 10, 60).affine

        expected = np.array(
            [
                [0, 1, 1],
                [0, 0, 0],
                [1, 0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_mixed_res(_, points, crs):
        raster = Raster.from_points(points, resolution=(20, 10))
        assert raster.dtype == bool
        assert raster.crs == crs
        assert raster.nodata == False
        assert raster.transform.affine == Transform(20, -10, 10, 60).affine

        expected = np.array(
            [
                [0, 0, 1],
                [0, 1, 0],
                [0, 0, 0],
                [0, 0, 0],
                [1, 0, 0],
            ]
        )

        print(raster.values)
        print(expected)
        assert np.array_equal(raster.values, expected)

    def test_driver(_, points, crs):
        newfile = points.parent / "test.shp"
        os.rename(points, newfile)
        raster = Raster.from_points(newfile, driver="GeoJSON")

        assert raster.dtype == bool
        assert raster.crs == crs
        assert raster.nodata == False
        assert raster.transform.affine == Transform(10, -10, 10, 60).affine

        expected = np.array(
            [
                [0, 0, 0, 0, 1],
                [0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_field(_, points, crs):
        raster = Raster.from_points(points, field="test")
        assert raster.dtype == float
        assert raster.crs == crs
        assert isnan(raster.nodata)
        assert raster.transform.affine == Transform(10, -10, 10, 60).affine

        expected = np.array(
            [
                [nan, nan, nan, nan, 2],
                [nan, nan, 1, nan, nan],
                [nan, nan, nan, nan, nan],
                [nan, nan, nan, nan, nan],
                [0, nan, nan, nan, nan],
            ]
        )
        assert np.array_equal(raster.values, expected, equal_nan=True)

    def test_invalid_field(_, points):
        with pytest.raises(KeyError):
            Raster.from_points(points, field="missing")

    def test_fill(_, points, crs):
        raster = Raster.from_points(points, field="test", fill=5)
        assert raster.dtype == float
        assert raster.crs == crs
        assert isnan(raster.nodata)
        assert raster.transform.affine == Transform(10, -10, 10, 60).affine

        expected = np.array(
            [
                [5, 5, 5, 5, 2],
                [5, 5, 1, 5, 5],
                [5, 5, 5, 5, 5],
                [5, 5, 5, 5, 5],
                [0, 5, 5, 5, 5],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_invalid_fill(_, points, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster.from_points(points, field="test", fill="invalid")
        assert_contains(error, "fill")

    def test_windowed(_, points, crs):
        bounds = BoundingBox(10, 0, 30, 30, crs)
        raster = Raster.from_points(points, bounds=bounds)
        assert raster.dtype == bool
        assert raster.crs == crs
        assert raster.nodata == False
        assert raster.transform == Transform(10, -10, 10, 30, crs)

        expected = np.array(
            [
                [0, 0],
                [1, 0],
                [0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)


class TestFromPolygons:
    def test_invalid_path(_):
        with pytest.raises(FileNotFoundError):
            Raster.from_polygons("not-a-file")

    def test_polygons(_, polygons, crs):
        raster = Raster.from_polygons(polygons)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Transform(10, -10, 20, 90, crs)

        expected = np.array(
            [
                [0, 0, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 0, 0, 0],
                [1, 1, 1, 1, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0],
            ],
        )
        assert np.array_equal(raster.values, expected)

    def test_memory(_, polygons, assert_contains):
        with pytest.raises(MemoryError) as error:
            Raster.from_polygons(polygons, resolution=1e-20)
        assert_contains(
            error,
            "requested array is too large",
            'Try increasing the "resolution" input',
        )

    def test_multipolygons(_, multipolygons, crs):
        raster = Raster.from_polygons(multipolygons)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform.affine == Affine(10, 0, 20, 0, -10, 90)

        expected = np.array(
            [
                [0, 0, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 0, 0, 0],
                [1, 1, 1, 1, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0],
            ],
        )
        assert np.array_equal(raster.values, expected)

    def test_fixed_res(_, polygons, crs):
        raster = Raster.from_polygons(polygons, resolution=30)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform.affine == Affine(30, 0, 20, 0, -30, 90)

        expected = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
        assert np.array_equal(raster.values, expected)

    def test_mixed_res(_, polygons, crs):
        raster = Raster.from_polygons(polygons, resolution=[30, 10])
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform.affine == Affine(30, 0, 20, 0, -10, 90)

        expected = np.array(
            [
                [0, 1, 0],
                [0, 1, 0],
                [1, 1, 0],
                [1, 0, 0],
                [1, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_raster_res(_, polygons, crs, araster):
        raster = Raster.from_array(araster, transform=Affine(30, 0, -90, 0, -10, -90))
        raster = Raster.from_polygons(polygons, resolution=raster)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform.affine == Affine(30, 0, 20, 0, -10, 90)

        expected = np.array(
            [
                [0, 1, 0],
                [0, 1, 0],
                [1, 1, 0],
                [1, 0, 0],
                [1, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ]
        )
        assert np.array_equal(raster.values, expected)

    def test_driver(_, polygons, crs):
        newfile = polygons.parent / "test.shp"
        os.rename(polygons, polygons.parent / "test.shp")
        raster = Raster.from_polygons(newfile, driver="GeoJSON")
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform.affine == Affine(10, 0, 20, 0, -10, 90)

        expected = np.array(
            [
                [0, 0, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
                [1, 1, 1, 1, 0, 0, 0],
                [1, 1, 1, 1, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0],
            ],
        )
        assert np.array_equal(raster.values, expected)

    def test_field(_, polygons, crs):
        raster = Raster.from_polygons(polygons, field="test")
        assert raster.dtype == float
        assert isnan(raster.nodata)
        assert raster.crs == crs
        assert raster.transform.affine == Affine(10, 0, 20, 0, -10, 90)

        expected = np.array(
            [
                [nan, nan, 1, 1, 1, 1, 1],
                [nan, nan, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, nan, nan, nan],
                [0, 0, 0, 0, nan, nan, nan],
                [nan, nan, 0, 0, nan, nan, nan],
                [nan, nan, 0, 0, nan, nan, nan],
            ],
        )
        assert np.array_equal(raster.values, expected, equal_nan=True)

    def test_invalid_field(_, polygons):
        with pytest.raises(KeyError):
            Raster.from_polygons(polygons, field="missing")

    def test_fill(_, polygons, crs):
        raster = Raster.from_polygons(polygons, field="test", fill=-9)
        assert raster.dtype == float
        assert isnan(raster.nodata)
        assert raster.crs == crs
        assert raster.transform.affine == Affine(10, 0, 20, 0, -10, 90)

        expected = np.array(
            [
                [-9, -9, 1, 1, 1, 1, 1],
                [-9, -9, 1, 1, 1, 1, 1],
                [0, 0, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, -9, -9, -9],
                [0, 0, 0, 0, -9, -9, -9],
                [-9, -9, 0, 0, -9, -9, -9],
                [-9, -9, 0, 0, -9, -9, -9],
            ],
        )

        print(raster.values)
        assert np.array_equal(raster.values, expected)

    def test_invalid_fill(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster.from_polygons(polygons, field="test", fill="invalid")
        assert_contains(error, "fill")

    def test_windowed(_, polygons, crs):
        bounds = BoundingBox(50, 0, 70, 40, crs)
        raster = Raster.from_polygons(polygons, bounds=bounds)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Transform(10, -10, 50, 40, crs)

        print(raster.values)
        expected = np.array(
            [
                [1, 0],
                [1, 0],
                [0, 0],
                [0, 0],
            ],
        )
        assert np.array_equal(raster.values, expected)


#####
# Metadata Attributes
#####


class TestEnsureNodata:
    def test_has_nodata(_, araster):
        raster = Raster.from_array(araster, nodata=5)
        raster.ensure_nodata()
        assert raster.nodata == 5

    def test_auto_nodata(_, araster):
        raster = Raster.from_array(araster, ensure_nodata=False)
        assert raster.nodata is None
        raster.ensure_nodata()
        assert np.isnan(raster.nodata)

    def test_default_nodata(_, araster):
        raster = Raster.from_array(araster, ensure_nodata=False)
        assert raster.nodata is None
        raster.ensure_nodata(default=15)
        assert raster.nodata == 15

    def test_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster.from_array(araster, ensure_nodata=False)
        assert raster.nodata is None
        raster.ensure_nodata(default=2.2, casting="unsafe")
        assert raster.nodata == 2

    def test_invalid_nodata(_, araster, assert_contains):
        raster = Raster.from_array(araster, ensure_nodata=False)
        with pytest.raises(TypeError) as error:
            raster.ensure_nodata("invalid")
        assert_contains(error, "nodata")

    def test_invalid_casting(_, araster, assert_contains):
        araster = araster.astype(int)
        raster = Raster.from_array(araster, ensure_nodata=False)
        with pytest.raises(TypeError) as error:
            raster.ensure_nodata(2.2)
        assert_contains(error, "casting")


class TestOverride:
    def test_crs(_, fraster):
        raster = Raster(fraster)
        raster.override(crs=4326)
        assert raster.crs == 4326

    def test_transform(_, fraster, crs):
        raster = Raster(fraster)
        raster.override(transform=(1, 2, 3, 4))
        assert raster.transform == Transform(1, 2, 3, 4, crs)

    def test_bounds(_, fraster, crs):
        raster = Raster(fraster)
        raster.override(bounds=(0, 0, 100, 100))
        assert raster.bounds == BoundingBox(0, 0, 100, 100, crs)

    def test_nodata(_, fraster):
        raster = Raster(fraster)
        assert raster.nodata != 5
        raster.override(nodata=5)
        assert raster.nodata == 5

    def test_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster.from_array(araster, nodata=0)
        raster.override(nodata=2.2, casting="unsafe")
        assert raster.nodata == 2

    def test_invalid_casting(_, araster, assert_contains):
        araster = araster.astype(int)
        raster = Raster.from_array(araster, nodata=0)
        with pytest.raises(TypeError) as error:
            raster.override(nodata=2.2)
        assert_contains(error, "cast")

    def test_invalid_casting_option(_, fraster, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.override(nodata=2.2, casting="invalid")
        assert_contains(error, "casting (invalid) is not a recognized option")


#####
# Metadata Parsing
#####


class TestParseProjection:
    def test_none(_):
        crs = CRS(4326)
        projection = None
        assert Raster._parse_projection(crs, projection, (3, 4)) == (crs, None)

    def test_bounds(_):
        crs = CRS(26911)
        bounds = BoundingBox(0, 1, 100, 501, 26911)
        outcrs, transform = Raster._parse_projection(crs, bounds, (10, 100))
        assert outcrs == crs
        assert transform == Transform(1, -50, 0, 501, 26911)

    def test_transform(_):
        crs = CRS(26911)
        transform = Transform(10, 5, 0, 1)
        outcrs, outtransform = Raster._parse_projection(crs, transform, (10, 100))
        assert outcrs == crs
        assert outtransform == transform

    def test_inherit(_):
        crs = None
        transform = Transform(1, 2, 3, 4, 26911)
        outcrs, outtransform = Raster._parse_projection(crs, transform, (10, 11))
        assert outcrs == CRS(26911)
        assert outtransform == transform

    def test_reproject_from_transform(_):
        crs = CRS(4326)
        transform = Transform(1, 2, 3, 4, 26911)
        outcrs, outtra = Raster._parse_projection(crs, transform, (10, 5))
        expected = Transform(
            dx=8.958995962871086e-06,
            dy=1.8038752956919747e-05,
            left=-121.4887170073974,
            top=3.607750457626307e-05,
            crs=crs,
        )
        assert outcrs == crs
        assert outtra.isclose(expected)

    def test_reproject_from_bounds(_):
        crs = CRS(4326)
        bounds = BoundingBox(0, 0, 100, 500, 26911)
        outcrs, outtra = Raster._parse_projection(crs, bounds, (10, 5))
        expected = Transform(
            dx=0.00017918258576798962,
            dy=-0.0004509677872809176,
            left=-121.48874389822696,
            top=0.004509687904713325,
            crs=crs,
        )
        assert outcrs == crs
        assert outtra.isclose(expected)


class TestParseTemplate:
    def test_no_template(_):
        output = Raster._parse_template(None, "template", 1, 2)
        assert output == (1, 2)

    def test_no_keywords(_):
        template = Raster()
        template._set_metadata(1, 2, 3)
        crs, transform = Raster._parse_template(template, "template", 1, 2)
        assert crs == 1
        assert transform == 2

    def test_mixed(_):
        template = Raster()
        template._set_metadata(1, 2, 3)
        output = Raster._parse_template(template, "template", None, 4)
        assert output == (1, 4)

    def test_invalid_template(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Raster._parse_template("invalid", "template name", 1, 2)
        assert_contains(error, "Raster object")


class TestParseSrcDst:
    def test(_):
        assert Raster._parse_src_dst(1, 2, 3) == (1, 2)
        assert Raster._parse_src_dst(None, 2, 3) == (2, 2)
        assert Raster._parse_src_dst(1, None, 3) == (1, 1)
        assert Raster._parse_src_dst(None, None, 3) == (3, 3)


#####
# Comparisons
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
        other._crs = CRS.from_epsg(4326)
        assert raster != other

    def test_other_transform(_, fraster):
        raster = Raster(fraster)
        other = Raster(fraster)
        other._transform = Transform(1, 2, 3, 4)
        assert raster != other


class TestValidate:
    def test_valid_raster(_, fraster, araster, transform, crs):
        raster = Raster(fraster, "a different name")
        output = raster.validate(fraster, "test")
        check(output, "test", araster, transform, crs)

    def test_default_spatial(_, fraster, araster):
        raster = Raster(fraster)
        output = raster.validate(araster, "test")
        assert output.crs == raster.crs
        assert output.transform == raster.transform

    def test_bad_shape(_, fraster, transform, crs, assert_contains):
        raster = Raster(fraster, "self name")
        height = raster.shape[0] + 1
        width = raster.shape[1] + 1
        araster = np.ones((height, width))
        input = Raster.from_array(araster, transform=transform, crs=crs)
        with pytest.raises(RasterShapeError) as error:
            raster.validate(input, "test name")
        assert_contains(error, "test name", "self name")

    def test_bad_transform(_, fraster, araster, crs, assert_contains):
        transform = Affine(9, 0, 0, 0, 9, 0)
        raster = Raster(fraster, "self name")
        input = Raster.from_array(araster, crs=crs, transform=transform)
        with pytest.raises(RasterTransformError) as error:
            raster.validate(input, "test name")
        assert_contains(error, "test name", "self name")

    def test_bad_crs(_, fraster, araster, transform, assert_contains):
        crs = CRS.from_epsg(4326)
        raster = Raster(fraster, "self name")
        input = Raster.from_array(araster, crs=crs, transform=transform)
        with pytest.raises(RasterCRSError) as error:
            raster.validate(input, "test name")
        assert_contains(error, "test name", "self name")

    @pytest.mark.parametrize(
        "input, error, message",
        (
            (5, TypeError, "test name"),
            (np.ones((3, 3, 3)), DimensionError, "test name"),
        ),
    )
    def test_invalid_raster(_, input, error, message, fraster, assert_contains):
        raster = Raster(fraster, "test name")
        with pytest.raises(error) as e:
            raster.validate(input, "test name")
        assert_contains(e, message)


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
        assert file.transform == transform.affine
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
        assert file.nodata == False
        assert file.transform == transform.affine
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
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.affine == transform.affine
        assert output.crs == crs

    def test_no_metadata(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == 0
        assert output.affine == Affine(1, 0, 0, 0, 1, 0)
        assert output.crs == CRS.from_epsg(4326)

    def test_bool_with_nodata(_, araster, transform, crs):
        araster = araster.astype(bool)
        raster = Raster.from_array(araster, nodata=True, transform=transform, crs=crs)
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == True
        assert output.affine == transform.affine
        assert output.crs == crs

    def test_bool_without_nodata(_, araster, transform, crs):
        araster = araster.astype(bool)
        raster = Raster.from_array(
            araster, transform=transform, crs=crs, ensure_nodata=False
        )
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == False
        assert output.affine == transform.affine
        assert output.crs == crs

    def test_int8_with_nodata(_, araster, transform, crs):
        araster = araster.astype("int8")
        raster = Raster.from_array(araster, nodata=5, crs=crs, transform=transform)
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == 5
        assert output.affine == transform.affine
        assert output.crs == crs

    def test_int8_without_nodata(_, araster, transform, crs):
        araster = araster.astype("int8")
        raster = Raster.from_array(
            araster, crs=crs, transform=transform, ensure_nodata=False
        )
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == 0
        assert output.affine == transform.affine
        assert output.crs == crs


class TestCopy:
    def test(_, fraster):
        raster = Raster(fraster)
        copy = raster.copy()
        assert copy._name is raster._name
        copy.name = "different"
        assert copy.name != raster.name
        assert copy._values is raster._values
        assert copy._nodata is raster._nodata
        assert copy._crs is raster._crs
        assert copy._transform is raster._transform

        del raster
        assert copy._name is not None
        assert copy._values is not None
        assert copy._nodata is not None
        assert copy._crs is not None
        assert copy._transform is not None


#####
# Numeric Preprocessing
#####


class TestFill:
    def test_none(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        base = raster.values.base
        raster.fill(value=50)

        assert raster.values.base is base
        assert raster.nodata is None

    def test_numeric_nodata(_, araster):
        araster[0, :] = 3
        raster = Raster.from_array(araster, nodata=3)
        copy = raster.copy()
        raster.fill(value=100)

        expected = araster.copy()
        expected[0, :] = 100
        assert raster.nodata is None
        assert np.array_equal(raster.values, expected)
        assert np.array_equal(copy.values, araster)

    def test_nan_nodata(_, araster):
        araster = araster.astype(float)
        araster[0, :] = nan
        raster = Raster.from_array(araster, nodata=nan)
        copy = raster.copy()
        raster.fill(value=100)

        expected = araster.copy()
        expected[0, :] = 100
        assert raster.nodata is None
        assert np.array_equal(raster.values, expected)
        assert np.array_equal(copy.values, araster, equal_nan=True)

    def test_invalid_value(_, araster, assert_contains):
        raster = Raster.from_array(araster, nodata=0)
        with pytest.raises(TypeError) as error:
            raster.fill("invalid")
        assert_contains(error, "fill value")

    def test_invalid_casting(_, araster, assert_contains):
        araster = araster.astype(int)
        raster = Raster.from_array(araster, nodata=0)
        with pytest.raises(TypeError) as error:
            raster.fill(value=2.2)
        assert_contains(error, "fill value", "cast", "safe")


class TestFind:
    def test_numeric(_, fraster, araster):
        raster = Raster(fraster)
        output = raster.find(values=[3, 7])
        assert isinstance(output, Raster)
        assert np.array_equal(raster.values, araster)
        assert output.crs == raster.crs
        assert output.transform == raster.transform
        expected = np.array([[0, 0, 1, 0], [0, 0, 1, 0]]).astype(bool)
        assert np.array_equal(output.values, expected)
        assert output.nodata == False

    def test_nan_and_nodata(_, araster, transform, crs):
        araster[0, 0] = nan
        raster = Raster.from_array(araster, transform=transform, crs=crs, nodata=3)
        output = raster.find([nan, 3])
        assert isinstance(output, Raster)
        assert np.array_equal(raster.values, araster, equal_nan=True)
        assert output.crs == raster.crs
        assert output.transform == raster.transform
        expected = np.array([[1, 0, 1, 0], [0, 0, 0, 0]]).astype(bool)
        assert np.array_equal(output.values, expected)
        assert output.nodata == False


class TestSetRange:
    def test_min(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        raster.set_range(min=3)
        expected = araster.copy()
        expected[expected < 3] = 3
        assert np.array_equal(raster.values, expected)
        assert raster.nodata is None

    def test_max(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        raster.set_range(max=3)
        expected = araster.copy()
        expected[expected > 3] = 3
        assert np.array_equal(raster.values, expected)
        assert raster.nodata is None

    def test_both(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        raster.set_range(min=3, max=6)
        expected = araster.copy()
        expected[expected < 3] = 3
        expected[expected > 6] = 6
        assert np.array_equal(raster.values, expected)
        assert raster.nodata is None

    def test_fill(_, araster):
        raster = Raster.from_array(araster, nodata=-999)
        raster.set_range(min=3, max=6, fill=True)
        expected = araster.copy()
        expected[expected < 3] = -999
        expected[expected > 6] = -999
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == -999

    def test_clip(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        raster.set_range(min=3, max=6)
        expected = araster.copy()
        expected[expected < 3] = 3
        expected[expected > 6] = 6
        assert np.array_equal(raster.values, expected)
        assert raster.nodata is None

    def test_nodata_pixels(_, araster):
        raster = Raster.from_array(araster, nodata=0)
        raster.set_range(min=3)
        expected = araster.copy()
        expected[(expected != 0) & (expected < 3)] = 3
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == 0

    def test_missing_nodata(_, araster, assert_contains):
        raster = Raster(araster, ensure_nodata=False)
        with pytest.raises(MissingNoDataError) as error:
            raster.set_range(min=3, max=6, fill=True)
        assert_contains(error, "raster does not have a NoData value")

    def test_invalid_exclusive(_, araster, assert_contains):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster.set_range(min=0, exclusive=True)
        assert_contains(error, "You can only set exclusive=True when fill=True.")

    def test_exclusive(_, araster):
        raster = Raster.from_array(araster, nodata=-999)
        raster.set_range(min=3, max=6, fill=True, exclusive=True)
        expected = araster.copy()
        expected[expected <= 3] = -999
        expected[expected >= 6] = -999
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == -999


#####
# Spatial Preprocessing
#####


class TestBuffer:
    def test_all_default(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(distance=0.09)

        values = np.full(
            (araster.shape[0] + 6, araster.shape[1] + 6), -999, dtype=raster.dtype
        )
        values[3:5, 3:7] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3.09)
        assert raster.transform.affine == transform

    def test_memory(_, fraster, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(MemoryError) as error:
            raster.buffer(1e200)
        assert_contains(
            error,
            "buffered array is too large for memory. Try decreasing the buffering distance.",
        )

    def test_left(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(left=0.09)

        values = np.full(
            (araster.shape[0], araster.shape[1] + 3), -999, dtype=raster.dtype
        )
        values[:, 3:] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3)
        assert raster.transform.affine == transform

    def test_right(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(right=0.09)

        values = np.full(
            (araster.shape[0], araster.shape[1] + 3), -999, dtype=raster.dtype
        )
        values[:, 0:4] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4, 0, 0.03, -3)
        assert raster.transform.affine == transform

    def test_top(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(top=0.09)

        values = np.full(
            (araster.shape[0] + 3, araster.shape[1]), -999, dtype=raster.dtype
        )
        values[3:, :] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4, 0, 0.03, -3.09)
        assert raster.transform.affine == transform

    def test_bottom(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(bottom=0.09)

        values = np.full(
            (araster.shape[0] + 3, araster.shape[1]), -999, dtype=raster.dtype
        )
        values[0:2, :] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4, 0, 0.03, -3)
        assert raster.transform.affine == transform

    def test_mixed(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(distance=0.09, left=0.06, top=0.03)

        values = np.full(
            (araster.shape[0] + 4, araster.shape[1] + 5), -999, dtype=raster.dtype
        )
        values[1:3, 2:6] = araster

        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.06, 0, 0.03, -3.03)
        assert raster.transform.affine == transform

    def test_inexact_buffer(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(distance=0.08)

        values = np.full(
            (araster.shape[0] + 6, araster.shape[1] + 6), -999, dtype=raster.dtype
        )
        values[3:5, 3:7] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3.09)

        assert raster.transform.affine == transform

    def test_invert_transform(_, araster):
        transform = Affine(-0.03, 0, -4, 0, -0.03, -3)
        raster = Raster.from_array(araster, transform=transform, nodata=-999)
        raster.buffer(distance=0.09, units="base")

        values = np.full(
            (araster.shape[0] + 6, araster.shape[1] + 6), -999, dtype=raster.dtype
        )
        values[3:5, 3:7] = araster

        transform = Affine(-0.03, 0, -3.91, 0, -0.03, -2.91)
        assert raster.transform.affine == transform

    def test_pixels(_, araster):
        raster = Raster.from_array(araster, nodata=-999)
        raster.buffer(distance=2, units="pixels")

        values = np.full((6, 8), -999, dtype=raster.dtype)
        values[2:4, 2:6] = araster
        assert np.array_equal(values, raster.values)
        assert raster.transform is None

    def test_meters(_, araster, fraster):
        raster = Raster(fraster)
        raster.buffer(distance=0.09, units="meters")

        values = np.full(
            (araster.shape[0] + 6, araster.shape[1] + 6), -999, dtype=raster.dtype
        )
        values[3:5, 3:7] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3.09)
        print(raster.transform)
        print(transform)
        assert raster.transform.affine == transform

    def test_meters_no_transform(_, araster, assert_contains):
        raster = Raster.from_array(araster, transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            raster.buffer(1, units="meters")
        assert_contains(error, "Cannot convert buffering distances from meters")

    def test_no_buffer(_, fraster, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.buffer()
        assert_contains(error, "must specify at least one buffer")

    def test_no_transform(_, araster, assert_contains):
        raster = Raster.from_array(araster, nodata=-999)
        with pytest.raises(MissingTransformError) as error:
            raster.buffer(distance=10)
        assert_contains(error, "does not have an affine transform")

    def test_missing_nodata(_, araster, transform, assert_contains):
        raster = Raster.from_array(araster, transform=transform, ensure_nodata=False)
        with pytest.raises(MissingNoDataError) as error:
            raster.buffer(distance=3, units="base")
        assert_contains(error, "does not have a NoData value")

    def test_0_buffer(_, fraster, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.buffer(distance=0)
        assert_contains(error, "Buffering distances cannot all be 0")


class TestClip:
    def test_different_crs(_, crs):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(
            araster, crs=crs, transform=Affine.identity(), ensure_nodata=False
        )
        bounds = BoundingBox(2, 8, 8, 3, crs).reproject(4326)
        raster.clip(bounds)
        assert raster.crs == crs
        assert raster.transform.isclose(Transform(1, 1, 2, 3))
        assert raster.nodata is None
        assert np.array_equal(raster.values, araster[3:8, 2:8])

    def test_no_transform(_, araster, assert_contains):
        raster = Raster(araster)
        bounds = BoundingBox(1, 2, 3, 4)
        with pytest.raises(MissingTransformError) as error:
            raster.clip(bounds)
        assert_contains(error, "does not have an affine Transform")

    def test_interior(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(
            araster, transform=Affine.identity(), ensure_nodata=False
        )
        bounds = BoundingBox(2, 8, 8, 3)
        raster.clip(bounds)
        assert raster.crs is None
        assert raster.transform == Transform(1, 1, 2, 3)
        assert raster.nodata is None
        assert np.array_equal(raster.values, araster[3:8, 2:8])

    def test_exterior(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(araster, transform=Affine.identity(), nodata=0)
        bounds = BoundingBox(-5, 15, 8, 3)
        raster.clip(bounds)

        assert raster.crs is None
        assert raster.nodata == 0
        assert raster.transform == Transform(1, 1, -5, 3)

        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]
        assert np.array_equal(raster.values, expected)

    def test_set_crs(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(
            araster, transform=Affine.identity(), ensure_nodata=False
        )
        bounds = BoundingBox(2, 8, 8, 3, 4326)
        raster.clip(bounds)
        assert raster.crs == 4326
        assert raster.transform.affine == Transform(1, 1, 2, 3).affine
        assert raster.nodata is None
        assert np.array_equal(raster.values, araster[3:8, 2:8])


class TestReproject:
    def test_no_parameters(_, araster, assert_contains):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster.reproject()
        assert_contains(error, "cannot all be None")

    def test_missing_transform(_, araster, assert_contains):
        raster = Raster(araster)
        with pytest.raises(MissingTransformError) as error:
            raster.reproject(crs=4326)
        assert_contains(error, "does not have an affine Transform")

    def test_invalid_crs(_, araster, transform):
        raster = Raster.from_array(araster, transform=transform, nodata=-999)
        with pytest.raises(CRSError):
            raster.reproject(crs="invalid")

    def test_invalid_transform(_, araster, transform, assert_contains):
        raster = Raster.from_array(araster, transform=transform, nodata=-999)
        with pytest.raises(TypeError) as error:
            raster.reproject(transform="invalid")
        assert_contains(
            error,
            "transform must be a dict, list, tuple, affine.Affine, Transform, or Raster",
        )

    def test_invalid_nodata(_, araster, assert_contains):
        raster = Raster.from_array(
            araster,
            crs=CRS.from_epsg(26911),
            transform=Affine.identity(),
            ensure_nodata=False,
        )
        with pytest.raises(TypeError) as error:
            raster.reproject(crs=CRS.from_epsg(26910), nodata="invalid")
        assert_contains(error, "nodata")

    def test_missing_nodata(_, araster, assert_contains):
        raster = Raster.from_array(
            araster,
            crs=CRS.from_epsg(26911),
            transform=Affine.identity(),
            ensure_nodata=False,
        )
        with pytest.raises(MissingNoDataError) as error:
            raster.reproject(crs=CRS.from_epsg(26910))
        assert_contains(error, "does not have a NoData value")

    def test_invalid_resampling(_, araster, assert_contains):
        raster = Raster.from_array(
            araster, crs=CRS.from_epsg(26911), transform=Affine.identity(), nodata=0
        )
        with pytest.raises(ValueError) as error:
            raster.reproject(crs=CRS.from_epsg(26910), resampling="invalid")
        assert_contains(error, "resampling")

    def test_crs(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(crs=CRS.from_epsg(26910))

        assert raster.crs == CRS.from_epsg(26910)
        expected = Transform(
            10.611506455694325,
            -9.427027871832252,
            1045837.212456758,
            3802906.8102235873,
        )
        assert raster.transform.isclose(expected)
        assert raster.nodata == -999

        expected = np.array(
            [
                [
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    8,
                    -999,
                    -999,
                ],
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 19, -999],
                [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, -999],
                [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, -999],
                [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, -999],
                [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, -999],
                [50, 51, 52, 53, 54, 55, 56, 57, 58, 59, -999],
                [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, -999],
                [70, 71, 72, 73, 74, 75, 76, 77, 78, 79, -999],
                [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, -999],
                [80, 91, 92, 93, 94, 95, 96, 97, 98, 99, -999],
                [
                    -999,
                    91,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                    -999,
                ],
            ]
        )
        assert np.allclose(raster.values, expected)

    def test_transform(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(transform=Transform(20, -20, 1045830, 3802910))

        assert raster.crs == CRS.from_epsg(26911)
        assert raster.nodata == -999
        assert raster.transform.isclose(Transform(20, -20, 492850, 3787010))

        expected = np.array(
            [
                [1.0, 3.0, 5.0, 7.0, 9.0],
                [21.0, 23.0, 25.0, 27.0, 29.0],
                [41.0, 43.0, 45.0, 47.0, 49.0],
                [61.0, 63.0, 65.0, 67.0, 69.0],
                [81.0, 83.0, 85.0, 87.0, 89.0],
                [-999.0, -999.0, -999.0, -999.0, -999.0],
            ]
        )
        assert np.allclose(raster.values, expected)

    def test_memory(_, fraster, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(MemoryError) as error:
            raster.reproject(transform=(1e-200, 1e-200, 0, 0))
        assert_contains(error, "reprojected raster is too large for memory")

    def test_reproject(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(transform=Transform(20, -20, 0, 0), crs=CRS.from_epsg(26910))

        assert raster.crs == CRS.from_epsg(26910)
        assert raster.nodata == -999
        assert raster.transform.isclose(Transform(20, -20, 1045820, 3802920))

        expected = np.array(
            [
                [-999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0],
                [-999.0, 1.0, 3.0, 15.0, 17.0, 19.0, -999.0],
                [-999.0, 21.0, 23.0, 35.0, 37.0, 39.0, -999.0],
                [-999.0, 40.0, 42.0, 54.0, 56.0, 58.0, -999.0],
                [-999.0, 60.0, 62.0, 74.0, 76.0, 78.0, -999.0],
                [-999.0, 80.0, 82.0, 94.0, 96.0, 98.0, -999.0],
                [-999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0],
            ]
        )
        assert np.allclose(raster.values, expected)

    def test_template(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )

        template = np.arange(10).reshape(5, 2)
        template = Raster.from_array(
            template, crs=CRS.from_epsg(26910), transform=Transform(20, -20, 0, 0)
        )
        raster.reproject(template)

        assert raster.crs == CRS.from_epsg(26910)
        assert raster.nodata == -999
        assert raster.transform.isclose(Transform(20, -20, 1045820, 3802920))

        expected = np.array(
            [
                [-999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0],
                [-999.0, 1.0, 3.0, 15.0, 17.0, 19.0, -999.0],
                [-999.0, 21.0, 23.0, 35.0, 37.0, 39.0, -999.0],
                [-999.0, 40.0, 42.0, 54.0, 56.0, 58.0, -999.0],
                [-999.0, 60.0, 62.0, 74.0, 76.0, 78.0, -999.0],
                [-999.0, 80.0, 82.0, 94.0, 96.0, 98.0, -999.0],
                [-999.0, -999.0, -999.0, -999.0, -999.0, -999.0, -999.0],
            ]
        )
        assert np.allclose(raster.values, expected)

    def test_template_override(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )

        template = np.arange(10).reshape(5, 2)
        template = Raster.from_array(
            template, crs=CRS.from_epsg(4396), transform=Transform(20, -20, 0, 0)
        )
        raster.reproject(template, crs=CRS.from_epsg(26910))

        assert raster.crs == CRS.from_epsg(26910)
        assert raster.nodata == -999
        assert raster.transform.isclose(
            Transform(
                -30.172586417756975,
                24.700681280344725,
                1045956.3935164977,
                3802791.929956563,
            )
        )

        expected = np.array(
            [
                [99, 96, 93, 90],
                [79, 76, 73, 60],
                [-999, 47, 44, 41],
                [-999, 27, 24, 11],
                [-999, -999, -999, -999],
            ]
        )
        print(raster.values)
        assert np.allclose(raster.values, expected)

    def test_bilinear(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(
            transform=Transform(20, -20, 1045830, 3802910), resampling="bilinear"
        )

        assert raster.crs == CRS.from_epsg(26911)
        assert raster.nodata == -999
        assert raster.transform.isclose(Transform(20, -20, 492850, 3787010))

        expected = np.array(
            [
                [1.96428571, 3.75, 5.75, 7.75, 9.53571429],
                [15.71428571, 17.5, 19.5, 21.5, 23.28571429],
                [35.71428571, 37.5, 39.5, 41.5, 43.28571429],
                [55.71428571, 57.5, 59.5, 61.5, 63.28571429],
                [75.71428571, 77.5, 79.5, 81.5, 83.28571429],
                [-999.0, -999.0, -999.0, -999.0, -999.0],
            ]
        )
        assert np.allclose(raster.values, expected)

    def test_bool(_):
        araster = np.arange(100).reshape(10, 10).astype(bool)
        transform = Transform(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=0, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(transform=Transform(20, -20, 1045830, 3802910))

        assert raster.crs == CRS.from_epsg(26911)
        assert raster.nodata == False
        assert raster.transform.isclose(Transform(20, -20, 492850, 3787010))

        assert raster.dtype == bool
        expected = np.array(
            [
                [True, True, True, True, True],
                [True, True, True, True, True],
                [True, True, True, True, True],
                [True, True, True, True, True],
                [True, True, True, True, True],
                [False, False, False, False, False],
            ]
        )
        assert np.allclose(raster.values, expected)


#####
# Data Properties
#####


class TestName:
    def test_set_string(_, araster):
        output = Raster(araster, "test")
        output.name = "different name"
        assert output.name == "different name"

    def test_set_not_string(_, araster, assert_contains):
        output = Raster(araster, "test")
        with pytest.raises(TypeError) as error:
            output.name = 5
        assert_contains(error, "raster name must be a string")


class TestValues:
    def test_values(_, araster):
        raster = Raster(araster)
        output = raster.values
        assert np.array_equal(output, araster)
        assert output.base is not araster
        assert output.base is not None
        assert output.flags.writeable == False

    def test_none(_):
        raster = Raster()
        assert raster.values is None


class TestDtype:
    def test_dtype(_, araster):
        raster = Raster(araster)
        assert raster.dtype == araster.dtype

    def test_none(_):
        raster = Raster()
        assert raster.dtype is None


class TestNodata:
    def test_get(_, fraster):
        raster = Raster(fraster)
        assert raster.nodata == -999

    def test_set(_, araster):
        raster = Raster(araster, ensure_nodata=False)
        raster.nodata = 5
        assert raster.nodata == 5

    def test_already_set(_, fraster, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.nodata = 5
        assert_contains(error, "already has a NoData")

    def test_invalid(_, araster, assert_contains):
        raster = Raster(araster, ensure_nodata=False)
        with pytest.raises(TypeError) as error:
            raster.nodata = "invalid"
        assert_contains(error, "dtype of nodata")


class TestNodataMask:
    def test(_, fraster, araster):
        raster = Raster(fraster)
        output = raster.nodata_mask
        expected = araster == -999
        assert np.array_equal(output, expected)


class TestDataMask:
    def test(_, fraster, araster):
        raster = Raster(fraster)
        output = raster.data_mask
        expected = araster != -999
        assert np.array_equal(output, expected)


#####
# Shape properties
#####


class TestShape:
    def test_shape(_, araster):
        raster = Raster(araster)
        assert raster.shape == araster.shape

    def test_none(_):
        raster = Raster()
        assert raster.shape == (0, 0)


class TestHeight:
    def test_height(_, araster):
        assert Raster(araster).height == araster.shape[0]

    def test_none(_):
        raster = Raster()
        assert raster.height == 0


class TestWidth:
    def test_width(_, araster):
        assert Raster(araster).width == araster.shape[1]

    def test_none(_):
        raster = Raster()
        assert raster.width == 0


class TestSize:
    def test_size(_, araster):
        assert Raster(araster).size == araster.size

    def test_none(_):
        raster = Raster()
        assert raster.size == 0


#####
# CRS Properties
#####


class TestCRS:
    def test_crs(_, fraster, crs):
        assert Raster(fraster).crs == crs

    def test_set(_, crs):
        raster = Raster()
        raster.crs = crs
        assert raster.crs == crs

    def test_already_set(_, fraster, crs, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.crs = crs
        assert_contains(error, "raster already has a CRS")

    def test_invalid(_):
        raster = Raster()
        with pytest.raises(CRSError):
            raster.crs = "invalid"


class TestCrsUnits:
    def test_none(_, araster):
        raster = Raster(araster)
        assert raster.crs_units == (None, None)

    def test_linear(_, araster):
        raster = Raster.from_array(araster, crs=26911)
        assert raster.crs_units == ("metre", "metre")

    def test_angular(_, araster):
        raster = Raster.from_array(araster, crs=4326)
        assert raster.crs_units == ("degree", "degree")


class TestCrsUnitsPerM:
    def test_none(_, araster):
        raster = Raster(araster)
        assert raster.crs_units_per_m == (None, None)

    def test_linear(_, araster):
        raster = Raster.from_array(araster, crs=26911)
        assert raster.crs_units_per_m == (1, 1)

    def test_angular_default(_, araster):
        raster = Raster.from_array(araster, crs=4326)
        output = raster.crs_units_per_m
        expected = (8.993216059187306e-06, 8.993216059187306e-06)
        assert np.allclose(output, expected)

    def test_angular_y(_, araster):
        raster = Raster.from_array(araster, crs=4326)
        raster.bounds = (0, 29, 10, 31)
        output = raster.crs_units_per_m
        expected = (1.0384471425304483e-05, 8.993216059187306e-06)
        assert np.allclose(output, expected)


class TestUtmZone:
    def test_no_crs(_, araster):
        raster = Raster.from_array(araster, bounds=(1, 2, 3, 4))
        assert raster.utm_zone is None

    def test_no_bounds(_, araster):
        raster = Raster.from_array(araster, crs=4326)
        assert raster.utm_zone is None

    def test(_, araster):
        raster = Raster.from_array(
            araster, crs=4326, bounds=BoundingBox(-119, 30, -115, 50)
        )
        assert raster.utm_zone == CRS(32611)


#####
# Transform Properties
#####


class TestTransform:
    def test_transform(_, fraster, transform, crs):
        expected = transform.todict()
        expected["crs"] = crs
        expected = Transform.from_dict(expected)
        assert Raster(fraster).transform == expected

    def test_set(_, araster, transform):
        raster = Raster(araster)
        raster.transform = transform
        assert raster.transform == transform

    def test_already_set(_, fraster, transform, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.transform = transform
        assert_contains(error, "raster already has a transform")

    def test_invalid(_):
        raster = Raster()
        with pytest.raises(TypeError):
            raster.transform = "invalid"

    def test_inherit_crs(_, araster):
        raster = Raster(araster)
        crs = CRS(4326)
        transform = Transform(1, 2, 3, 4, crs)
        raster.transform = transform
        assert raster.crs == crs
        assert raster.transform == transform

    def test_reproject(_, araster):
        raster = Raster.from_array(araster, crs=4326)
        raster.transform = Transform(1, 2, 3, 4, 26911)
        expected = Transform(
            dx=8.958995962871086e-06,
            dy=1.8038752956919747e-05,
            left=-121.4887170073974,
            top=3.607750457626307e-05,
            crs=4326,
        )
        assert raster.transform.isclose(expected)
        assert raster.crs == CRS(4326)


class TestPixel:
    def test_none(_, araster):
        raster = Raster(araster)
        assert raster._pixel(None, None, None) is None


class TestDx:
    def test_none(_, araster):
        raster = Raster(araster)
        assert raster.dx() is None

    def test(_, fraster):
        raster = Raster(fraster)
        transform = raster.transform
        _, y = raster.center
        assert raster.dx() == transform.dx(meters=True, y=y)
        assert raster.dx(base_unit=True) == transform.dx(meters=False, y=y)

    def test_invalid_meters(_, araster, assert_contains):
        raster = Raster(araster)
        raster.transform = (1, 1, 0, 0)
        with pytest.raises(RuntimeError) as error:
            raster.dx()
        assert_contains(
            error, "Cannot convert raster dx to meters", "does not have a CRS"
        )


class TestDy:
    def test_none(_, araster):
        assert Raster(araster).dy() is None

    def test(_, fraster, transform):
        raster = Raster(fraster)
        transform = raster.transform
        assert raster.dy() == transform.dy(meters=True)
        assert raster.dy(base_unit=True) == transform.dy(meters=False)

    def test_invalid_meters(_, araster, assert_contains):
        raster = Raster(araster)
        raster.transform = (1, 1, 0, 0)
        with pytest.raises(RuntimeError) as error:
            raster.dy()
        assert_contains(
            error, "Cannot convert raster dy to meters", "does not have a CRS"
        )


class TestResolution:
    def test_none(_, araster):
        assert Raster(araster).resolution() is None

    def test(_, fraster):
        raster = Raster(fraster)
        transform = raster.transform
        _, y = raster.center
        assert raster.resolution() == transform.resolution(meters=False, y=y)
        assert raster.resolution(True) == transform.resolution(meters=False, y=y)

    def test_invalid_meters(_, araster, assert_contains):
        raster = Raster(araster)
        raster.transform = (1, 1, 0, 0)
        with pytest.raises(RuntimeError) as error:
            raster.resolution()
        assert_contains(
            error, "Cannot convert raster resolution to meters", "does not have a CRS"
        )


class TestPixelArea:
    def test_none(_, araster):
        assert Raster(araster).pixel_area() is None

    def test(_, fraster):
        raster = Raster(fraster)
        transform = raster.transform
        _, y = raster.center
        assert raster.pixel_area() == transform.pixel_area(meters=True, y=y)
        assert raster.pixel_area(True) == transform.pixel_area(meters=False, y=y)

    def test_invalid_meters(_, araster, assert_contains):
        raster = Raster(araster)
        raster.transform = (1, 1, 0, 0)
        with pytest.raises(RuntimeError) as error:
            raster.pixel_area()
        assert_contains(
            error, "Cannot convert raster pixel_area to meters", "does not have a CRS"
        )


class TestPixelDiagonal:
    def test_none(_, araster):
        assert Raster(araster).pixel_diagonal() is None

    def test(_, fraster):
        raster = Raster(fraster)
        transform = raster.transform
        _, y = raster.center
        assert raster.pixel_diagonal() == transform.pixel_diagonal(meters=True, y=y)
        assert raster.pixel_diagonal(True) == transform.pixel_diagonal(
            meters=False, y=y
        )

    def test_invalid_meters(_, araster, assert_contains):
        raster = Raster(araster)
        raster.transform = (1, 1, 0, 0)
        with pytest.raises(RuntimeError) as error:
            raster.pixel_diagonal()
        assert_contains(
            error,
            "Cannot convert raster pixel_diagonal to meters",
            "does not have a CRS",
        )


class TestAffine:
    def test_none(_, araster):
        assert Raster(araster).affine is None

    def test(_, fraster):
        raster = Raster(fraster)
        transform = raster.transform
        assert raster.affine == transform.affine


#####
# Bounds Properties
#####


class TestBounds:
    def test_get(_, fraster, bounds, crs):
        expected = bounds.todict()
        expected["crs"] = crs
        expected = BoundingBox.from_dict(expected)
        assert Raster(fraster).bounds == expected

    def test_no_transform(_, araster):
        raster = Raster(araster)
        assert raster.bounds is None

    def test_set(_, araster, bounds):
        raster = Raster(araster)
        raster.bounds = bounds
        assert raster.bounds == bounds

    def test_already_set(_, fraster, bounds, assert_contains):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.bounds = bounds
        assert_contains(error, "already has bounds")

    def test_inherit_crs(_, araster):
        raster = Raster.from_array(araster)
        bounds = BoundingBox(1, 2, 3, 4, 4326)
        raster.bounds = bounds
        assert raster.bounds == bounds
        assert raster.crs == bounds.crs

    def test_reproject(_, araster):
        raster = Raster.from_array(araster, crs=4326)
        bounds = BoundingBox(0, 0, 100, 100, 26911)
        raster.bounds = bounds
        expected = BoundingBox(
            left=-121.48874388494063,
            bottom=2.786575690246623e-10,
            right=-121.4878479834734,
            top=0.0009019375809660552,
            crs=4326,
        )
        assert raster.bounds.isclose(expected)


class TestLeft:
    def test_none(_, araster):
        assert Raster(araster).left is None

    def test(_, fraster):
        raster = Raster(fraster)
        bounds = raster.bounds
        assert raster.left == bounds.left


class TestRight:
    def test_none(_, araster):
        assert Raster(araster).right is None

    def test(_, fraster):
        raster = Raster(fraster)
        bounds = raster.bounds
        assert raster.right == bounds.right


class TestBottom:
    def test_none(_, araster):
        assert Raster(araster).bottom is None

    def test(_, fraster):
        raster = Raster(fraster)
        bounds = raster.bounds
        assert raster.bottom == bounds.bottom


class TestTop:
    def test_none(_, araster):
        assert Raster(araster).top is None

    def test(_, fraster):
        raster = Raster(fraster)
        bounds = raster.bounds
        assert raster.top == bounds.top


class TestCenter:
    def test_none(_, araster):
        assert Raster(araster).center is None

    def test(_, fraster):
        raster = Raster(fraster)
        bounds = raster.bounds
        assert raster.center == bounds.center


class TestCenterX:
    def test_none(_, araster):
        assert Raster(araster).center_x is None

    def test(_, araster):
        raster = Raster(araster)
        raster.bounds = (0, 20, 100, 40)
        assert raster.center_x == 50


class TestCenterY:
    def test_none(_, araster):
        assert Raster(araster).center_y is None

    def test(_, araster):
        raster = Raster(araster)
        raster.bounds = (0, 20, 100, 40)
        assert raster.center_y == 30


class TestOrientation:
    def test_none(_, araster):
        assert Raster(araster).orientation is None

    def test(_, fraster):
        raster = Raster(fraster)
        bounds = raster.bounds
        assert raster.orientation == bounds.orientation
