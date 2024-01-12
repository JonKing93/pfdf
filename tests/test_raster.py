import os
from math import inf, isnan, nan, sqrt
from pathlib import Path

import fiona
import numpy as np
import pytest
import rasterio
from affine import Affine
from geojson import Feature, MultiPolygon, Polygon
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder
from rasterio.coords import BoundingBox
from rasterio.crs import CRS

from pfdf._utils.transform import Transform
from pfdf.errors import (
    CrsError,
    DimensionError,
    RasterCrsError,
    RasterShapeError,
    RasterTransformError,
    ShapeError,
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
    assert output.transform == transform
    left, top = transform * (0, 0)
    right, bottom = transform * (araster.shape[1], araster.shape[0])
    assert output.bounds == BoundingBox(left, bottom, right, top)

    assert output.resolution == (transform[0], transform[4])
    assert output.pixel_area == transform[0] * transform[4]
    assert output.pixel_diagonal == sqrt(transform[0] ** 2 + transform[4] ** 2)


def assert_contains(error, *strings):
    "Check exception message contains specific strings"
    message = error.value.args[0]
    for string in strings:
        assert string in message


@pytest.fixture
def polygon_coords():
    return [
        (
            [(2, 2), (2, 7), (6, 7), (6, 2), (2, 2)],
            [(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)],  # hole in upper-left
        ),
        ([(4, 6), (4, 9), (9, 9), (9, 6), (4, 6)],),
    ]


@pytest.fixture
def polygons(polygon_coords, tmp_path, crs):
    file = Path(tmp_path) / "test.geojson"
    values = range(len(polygon_coords))
    polygons = [
        Feature(geometry=Polygon(coords), properties={"test": value})
        for coords, value in zip(polygon_coords, values)
    ]
    save_features(file, polygons, crs)
    return file


@pytest.fixture
def multipolygons(tmp_path, crs):
    coords = [
        [  # Multipolygon A
            [  # Polygon A1
                [(2, 2), (2, 7), (6, 7), (6, 2), (2, 2)],
                [(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)],
            ],
            [[(4, 6), (4, 9), (9, 9), (9, 6), (4, 6)]],  # Polygon A2
        ],
        [[[(5, 3), (5, 4), (6, 4), (6, 3), (5, 3)]]],  # Multipolygon B
    ]
    values = range(len(coords))
    multis = [
        Feature(geometry=MultiPolygon(coords), properties={"test": value})
        for coords, value in zip(coords, values)
    ]
    file = Path(tmp_path) / "multitest.geojson"
    save_features(file, multis, crs)
    return file


def save_features(path, features, crs):
    schema = {"geometry": features[0].geometry.type, "properties": {"test": "int"}}
    with fiona.open(
        path,
        "w",
        driver="GeoJSON",
        schema=schema,
        crs=crs,
    ) as file:
        file.writerecords(features)


#####
# Init
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
        assert isinstance(a._transform, Transform)
        assert a._transform.affine is None
        assert a.name == "raster"

    def test_with_name(_):
        a = Raster(None, "test name")
        assert isinstance(a, Raster)
        assert a._values is None
        assert a._nodata is None
        assert a._crs is None
        assert isinstance(a._transform, Transform)
        assert a._transform.affine is None
        assert a.name == "test name"

    def test_invalid_name(_):
        with pytest.raises(TypeError) as error:
            Raster(None, 5)
        assert_contains(error, "name")


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
        view = ViewFinder(affine=transform, crs=crs, nodata=-999, shape=araster.shape)
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
        assert output.nodata is None
        assert output.transform is None
        assert output.crs is None

    def test_raster(self, fraster, araster, transform, crs):
        input = Raster(fraster, "a different name")
        output = Raster(input, "test")
        check(output, "test", araster, transform, crs)

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            Raster(5, "test name")
        assert_contains(error, "test name")


#####
# Factories
#####


class TestFinalize:
    def test_no_metadata(_, araster):
        raster = Raster()
        raster._finalize(araster, None, None, None, "safe")

        assert raster._nodata is None
        assert isinstance(raster._transform, Transform)
        assert raster._transform.affine is None
        assert raster._crs is None
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False

    def test_with_metadata(_, araster, crs, transform):
        raster = Raster()
        raster._finalize(araster, crs, transform, -999, casting="unsafe")

        assert raster._nodata == -999
        assert raster._nodata.dtype == raster.dtype
        assert isinstance(raster._transform, Transform)
        assert raster._transform.affine == transform
        assert raster._crs == crs
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False

    def test_nodata_casting(_, araster, crs, transform):
        raster = Raster()
        araster = araster.astype(int)
        raster._finalize(araster, crs, transform, -2.2, casting="unsafe")

        assert raster._nodata == -2
        assert raster._nodata.dtype == raster.dtype
        assert isinstance(raster._transform, Transform)
        assert raster._transform.affine == transform
        assert raster._crs == crs
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False

    def test_invalid_crs(_, araster):
        raster = Raster()
        with pytest.raises(CrsError):
            raster._finalize(araster, "invalid", None, None, "safe")

    def test_invalid_transform(_, araster):
        raster = Raster()
        with pytest.raises(TransformError):
            raster._finalize(araster, None, "invalid", None, "safe")

    def test_invalid_shear(_, araster):
        raster = Raster()
        transform = Affine(1, 2, 3, 4, 5, 6)
        with pytest.raises(TransformError) as error:
            raster._finalize(araster, None, transform, None, "unsafe")
        assert_contains(
            error, "The raster transform must only support scaling and translation."
        )

    def test_invalid_nodata(_, araster):
        raster = Raster()
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, None, "invalid", "safe")
        assert_contains(error, "nodata")

    def test_invalid_casting_option(_, araster):
        raster = Raster()
        with pytest.raises(ValueError) as error:
            raster._finalize(araster, None, None, None, "invalid")
        assert_contains(error, "casting")

    def test_invalid_casting(_, araster):
        raster = Raster()
        araster = araster.astype(int)
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, None, nodata=-2.2, casting="safe")
        assert_contains(error, "Cannot cast the NoData value")

    def test_invalid_values(_):
        raster = Raster(None, "test name")
        with pytest.raises(TypeError) as error:
            raster._finalize("invalid", None, None, None, "unsafe")
        assert_contains(error, "test name")

    def test_invalid_dtype(_, araster):
        raster = Raster(None, "test name")
        araster = araster.astype("complex")
        with pytest.raises(TypeError) as error:
            raster._finalize(araster, None, None, None, "unsafe")
        assert_contains(error, "test name")

    def test_invalid_shape(_, araster):
        raster = Raster(None, "test name")
        araster = araster.reshape(2, 2, 2)
        with pytest.raises(DimensionError) as error:
            raster._finalize(araster, None, None, None, "unsafe")
        assert_contains(error, "test name")


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
            transform=transform,
            crs=crs,
        ) as writer:
            writer.write(araster, 1)
            writer.write(zeros, 2)

        raster = Raster.from_file(file, band=2)
        check(raster, "raster", zeros, transform, crs)

    def test_bool(_, araster, transform, crs, tmp_path):
        araster = np.array([[0, 1, 1, 0], [1, 1, 0, 0]]).astype(float)
        file = Path(tmp_path) / "test.tif"
        with rasterio.open(
            file,
            "w",
            driver="GTiff",
            width=araster.shape[1],
            height=araster.shape[0],
            count=1,
            crs=crs,
            transform=transform,
            dtype=araster.dtype,
        ) as writer:
            writer.write(araster, 1)

        raster = Raster.from_file(file, isbool=True)
        assert np.array_equal(raster.values, araster.astype(bool))
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == transform


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
            transform=transform,
            crs=crs,
        ) as writer:
            writer.write(araster, 1)
            writer.write(zeros, 2)

        with rasterio.open(file) as reader:
            pass
        raster = Raster.from_rasterio(reader, band=2)

    def test_old_reader(_, fraster):
        with rasterio.open(fraster) as reader:
            pass
        fraster.unlink()
        with pytest.raises(FileNotFoundError) as error:
            Raster.from_rasterio(reader, "")
        assert_contains(error, "rasterio.DatasetReader", "no longer exists")

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            Raster.from_rasterio("invalid")
        assert_contains(error, "rasterio.DatasetReader")


class TestFromPysheds:
    def test(_, araster, transform, crs):
        view = ViewFinder(affine=transform, crs=crs, nodata=-999, shape=araster.shape)
        input = PyshedsRaster(araster, view)
        araster = araster.astype(input.dtype)
        output = Raster.from_pysheds(input, "test")
        check(output, "test", araster, transform, crs)
        assert output._values is not input

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            Raster.from_pysheds("invalid")
        assert_contains(error, "pysheds.sview.Raster")


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
        assert output.nodata is None
        assert output.transform == transform
        assert output.crs == crs

    def test_spatial_override(_, araster, fraster, transform):
        template = Raster(fraster)
        crs = CRS.from_epsg(4000)
        output = Raster.from_array(araster, spatial=template, crs=crs)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, araster)
        assert output.name == "raster"
        assert output.nodata is None
        assert output.transform == transform
        assert output.crs == crs

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
        assert_contains(error, "Cannot cast the NoData value")

    def test_invalid_transform(_, araster):
        with pytest.raises(TransformError) as error:
            Raster.from_array(araster, transform="invalid")
        assert_contains(error, "transform", "affine.Affine")

    def test_invalid_crs(_, araster):
        with pytest.raises(CrsError) as error:
            Raster.from_array(araster, crs="invalid")
        assert_contains(error, "crs", "rasterio.crs.CRS")

    def test_invalid_spatial(_, araster):
        with pytest.raises(TypeError) as error:
            Raster.from_array(araster, spatial=5)
        assert_contains(error, "spatial template must be a pfdf.raster.Raster object")


class Test_FromArray:
    def test(_, araster):
        raster = Raster._from_array(araster, crs=None, transform=None, nodata=None)
        assert raster._values.base is araster
        assert raster._values.flags.writeable == False


#####
# From Polygons
#####


class TestValidateField:
    schema = {"test": "int:2", "test2": "float:5.5", "bad": "str:47"}

    def test_none(self):
        Raster._validate_field(None, self.schema)

    def test_not_str(self):
        with pytest.raises(TypeError) as error:
            Raster._validate_field(5, self.schema)
        assert_contains(error, "field", "str")

    def test_missing(self):
        with pytest.raises(KeyError) as error:
            Raster._validate_field("missing", self.schema)
        assert_contains(
            error,
            "'missing' is not the name of a polygon data field",
            "Allowed field names are: test, test2",
        )

    def test_invalid_type(self):
        with pytest.raises(TypeError) as error:
            Raster._validate_field("bad", self.schema)
        assert_contains(
            error,
            "The 'bad' field is not an int or float. Instead, it has a 'str' type.",
        )

    def test_invalid_casting(self):
        with pytest.raises(KeyError) as error:
            Raster._validate_field("TeSt", self.schema)
        assert_contains(error, "'TeSt' is not the name of a polygon data field")

    @pytest.mark.parametrize("field", ("test", "test2"))
    def test_valid(self, field):
        Raster._validate_field(field, self.schema)


class TestValidatePolygon:
    def test_not_list(_):
        with pytest.raises(ValueError) as error:
            Raster._validate_polygon(4, 5, "invalid")
        assert_contains(error, "feature[4]", "polygon[5] is not a list")

    def test_ring_not_list(_):
        coords = [
            [(1, 2), (3, 4), (5, 6), (1, 2)],
            (1, 2),
        ]
        with pytest.raises(ValueError) as error:
            Raster._validate_polygon(4, 5, coords)
        assert_contains(error, "feature[4]", "polygon[5].coordinates[1]", "not a list")

    def test_too_short(_):
        coords = [[(1, 2), (2, 3), (1, 2)]]
        with pytest.raises(ValueError) as error:
            Raster._validate_polygon(4, 5, coords)
        assert_contains(
            error, "ring[0]", "feature[4]", "polygon[5]", "does not have 4 positions"
        )

    def test_bad_end(_):
        coords = [[(1, 2), (2, 3), (4, 5), (6, 7)]]
        with pytest.raises(ValueError) as error:
            Raster._validate_polygon(4, 5, coords)
        assert_contains(
            error,
            "ring[0]",
            "feature[4]",
            "polygon[5]",
            "must match the first position",
        )

    def test_shell_only(_):
        coords = [
            [(1, 2), (3, 4), (5, 6), (1, 2)],
        ]
        Raster._validate_polygon(1, 2, coords)

    def test_with_holes(_):
        coords = [
            [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (1, 2)],
            [(1, 2), (3, 4), (2, 2), (1, 2)],
            [(1, 2), (5, 6), (2, 2), (1, 2)],
        ]
        Raster._validate_polygon(1, 2, coords)


class TestUpdateBounds:
    def test_no_updates(_):
        coords = [[(1, 2), (3, 4), (5, 6), (1, 2)]]
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        Raster._update_bounds(coords, bounds)
        assert bounds["left"] == -10
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 10

    def test_all_update(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        Raster._update_bounds(coords, bounds)
        assert bounds["left"] == -10
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 10

    def test_mixed(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        bounds = {
            "left": -20,
            "right": 0,
            "bottom": 0,
            "top": 20,
        }
        Raster._update_bounds(coords, bounds)
        assert bounds["left"] == -20
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 20


class TestValidateFeature:
    def test_no_geometry(_):
        feature = {"geometry": None}
        with pytest.raises(ValueError) as error:
            Raster._validate_feature(5, feature, None, None)
        assert_contains(error, "Feature[5] does not have a geometry")

    def test_not_polygon(_):
        feature = {
            "geometry": {
                "type": "Point",
                "coordinates": (1, 2),
            }
        }
        with pytest.raises(ValueError) as error:
            Raster._validate_feature(5, feature, None, None)
        assert_contains(
            error,
            "must have a Polygon or MultiPolygon geometry",
            "feature[5] has a Point geometry",
        )

    def test_polygon(_):
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [(1, 2), (3, 4), (5, 6), (7, 8), (1, 2)],
                [(1, 2), (2, 2), (2, 1), (1, 2)],
            ],
        }
        feature = {"properties": None, "id": 5, "geometry": geometry}
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        initial_bounds = bounds.copy()
        output = Raster._validate_feature(5, feature, bounds, None)
        assert output == (geometry, True)
        assert bounds == initial_bounds

    def test_multipolygon(_):
        geometry = {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [(1, 2), (3, 4), (5, 6), (7, 8), (1, 2)],
                    [(1, 2), (2, 2), (2, 1), (1, 2)],
                ],
                [[(10, -10), (-10, -10), (-10, 10), (10, 10), (10, -10)]],
            ],
        }
        feature = {"properties": None, "id": 5, "geometry": geometry}
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        initial_bounds = bounds.copy()
        output = Raster._validate_feature(5, feature, bounds, None)
        assert output == (geometry, True)
        assert bounds == initial_bounds

    def test_invalid_polygon(_):
        geometry = {
            "type": "Polygon",
            "coordinates": [[(1, 2), (3, 4)], [(1, 2), (2, 2), (2, 1), (1, 2)]],
        }
        feature = {"properties": None, "id": 5, "geometry": geometry}
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        with pytest.raises(ValueError) as error:
            Raster._validate_feature(5, feature, bounds, None)
        assert_contains(error, "4 positions")

    def test_update_bounds(_):
        geometry = {
            "type": "MultiPolygon",
            "coordinates": [[[(10, -10), (-10, -10), (-10, 10), (10, 10), (10, -10)]]],
        }
        feature = {"properties": None, "id": 5, "geometry": geometry}
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        expected = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        output = Raster._validate_feature(5, feature, bounds, None)
        assert output == (geometry, True)
        assert bounds == expected

    def test_field(_):
        geometry = {
            "type": "Polygon",
            "coordinates": [
                [(1, 2), (3, 4), (5, 6), (7, 8), (1, 2)],
                [(1, 2), (2, 2), (2, 1), (1, 2)],
            ],
        }
        field = 17
        feature = {"properties": {"test": field}, "id": 5, "geometry": geometry}
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        initial_bounds = bounds.copy()
        output = Raster._validate_feature(5, feature, bounds, "test")
        assert output == (geometry, field)
        assert bounds == initial_bounds


class TestFromPolygons:
    def test_invalid_path(_):
        with pytest.raises(FileNotFoundError):
            Raster.from_polygons("not-a-file")

    def test_invalid_resolution(_, polygons):
        with pytest.raises(ValueError) as error:
            Raster.from_polygons(polygons, resolution=-5)
        assert_contains(error, "resolution")

    def test_missing_resolution(_, polygons, araster):
        raster = Raster.from_array(araster)
        with pytest.raises(ValueError) as error:
            Raster.from_polygons(polygons, resolution=raster)
        assert_contains(error, "raster does not have an affine transform")

    def test_polygons(_, polygons, crs):
        raster = Raster.from_polygons(polygons)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Affine(1, 0, 2, 0, -1, 9)

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

    def test_multipolygons(_, multipolygons, crs):
        raster = Raster.from_polygons(multipolygons)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Affine(1, 0, 2, 0, -1, 9)

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
        raster = Raster.from_polygons(polygons, resolution=3)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Affine(3, 0, 2, 0, -3, 9)

        expected = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
        assert np.array_equal(raster.values, expected)

    def test_mixed_res(_, polygons, crs):
        raster = Raster.from_polygons(polygons, resolution=[3, 1])
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Affine(3, 0, 2, 0, -1, 9)

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
        raster = Raster.from_array(araster, transform=Affine(3, 0, -9, 0, -1, -9))
        raster = Raster.from_polygons(polygons, resolution=raster)
        assert raster.dtype == bool
        assert raster.nodata == False
        assert raster.crs == crs
        assert raster.transform == Affine(3, 0, 2, 0, -1, 9)

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
        assert raster.transform == Affine(1, 0, 2, 0, -1, 9)

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
        assert raster.transform == Affine(1, 0, 2, 0, -1, 9)

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

        print(raster.values)
        assert np.array_equal(raster.values, expected, equal_nan=True)

    def test_invalid_field(_, polygons):
        with pytest.raises(KeyError):
            Raster.from_polygons(polygons, field="missing")

    def test_fill(_, polygons, crs):
        raster = Raster.from_polygons(polygons, field="test", fill=-9)
        assert raster.dtype == float
        assert isnan(raster.nodata)
        assert raster.crs == crs
        assert raster.transform == Affine(1, 0, 2, 0, -1, 9)

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

    def test_invalid_fill(_, polygons):
        with pytest.raises(TypeError) as error:
            Raster.from_polygons(polygons, field="test", fill="invalid")
        assert_contains(error, "fill")


#####
# Metadata
#####


class TestValidateShape:
    def test_none(_):
        output = Raster._validate_shape(None)
        assert output is None

    def test_valid(_):
        output = Raster._validate_shape([1, 2])
        assert np.array_equal(output, [1, 2])

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            Raster._validate_shape("invalid")
        assert_contains(error, "shape")

    def test_invalid_dtype(_):
        shape = np.array([1, 2]).astype("complex")
        with pytest.raises(TypeError) as error:
            Raster._validate_shape(shape)
        assert_contains(error, "shape")

    def test_not_vector(_, araster):
        with pytest.raises(DimensionError):
            Raster._validate_shape(araster)

    def test_wrong_length(_):
        with pytest.raises(ShapeError):
            Raster._validate_shape([1, 2, 3])

    @pytest.mark.parametrize("bad", (0, -1))
    def test_negative(_, bad):
        with pytest.raises(ValueError):
            Raster._validate_shape([bad, bad])

    def test_float(_):
        with pytest.raises(ValueError):
            Raster._validate_shape([1.2, 2.3])


class TestValidateSpatial:
    def test_none(_):
        output = Raster._validate_spatial(None, None)
        assert output == (None, None)

    def test_valid(_, crs, transform):
        out1, out2 = Raster._validate_spatial(crs, transform)
        assert out1 == crs
        assert out2 == transform

    def test_invalid_crs(_):
        with pytest.raises(CrsError):
            Raster._validate_spatial("invalid", None)

    def test_invalid_transform(_):
        with pytest.raises(TransformError):
            Raster._validate_spatial(None, "invalid")


class TestValidateNodata:
    def test_none(_):
        output = Raster._validate_nodata(None, "unsafe")
        assert output is None

    def test_nodata(_):
        output = Raster._validate_nodata(5, "safe")
        assert output == 5

    def test_casting(_):
        output = Raster._validate_nodata(2.2, "unsafe", int)
        assert output == 2

    def test_invalid_casting_option(_):
        with pytest.raises(ValueError) as error:
            Raster._validate_nodata(None, "invalid")
        assert_contains(error, "casting")

    def test_invalid_nodata(_):
        with pytest.raises(TypeError) as error:
            Raster._validate_nodata("invalid", "unsafe")
        assert_contains(error, "nodata")

    def test_invalid_casting(_):
        with pytest.raises(TypeError) as error:
            Raster._validate_nodata(2.2, "safe", int)
        assert_contains(error, "Cannot cast the NoData value")


class TestValidateMetadata:
    def test_none(_):
        crs, transform, nodata = Raster._validate_metadata(None, None, None, "safe")
        assert crs is None
        assert transform is None
        assert nodata is None

    def test_valid(_, crs, transform):
        crs, transform, nodata = Raster._validate_metadata(crs, transform, -999, "safe")
        assert crs == crs
        assert transform == transform
        assert nodata == -999

    def test_valid_casting(_, crs, transform):
        crs, transform, nodata = Raster._validate_metadata(
            crs, transform, -2.2, "unsafe", int
        )
        assert crs == crs
        assert transform == transform
        assert nodata == -2

    def test_invalid_spatial(_):
        with pytest.raises(CrsError):
            Raster._validate_metadata("invalid", None, None, "unsafe")

    def test_invalid_nodata(_):
        with pytest.raises(TypeError) as error:
            Raster._validate_metadata(None, None, "invalid", "unsafe")
        assert_contains(error, "nodata")


class TestParseTemplate:
    def test_no_template(_):
        keywords = {"a": 1, "b": 2}
        options = Raster._parse_template(None, "template", keywords)
        assert options == {"a": 1, "b": 2}

    def test_no_keywords(_):
        template = Raster()
        template._set_metadata(1, 2, 3)
        keywords = {"crs": None, "nodata": None}
        metadata = Raster._parse_template(template, "template", keywords)
        assert metadata == {"crs": 1, "nodata": 3}

    def test_mixed(_):
        template = Raster()
        template._set_metadata(1, 2, 3)
        keywords = {"crs": None, "nodata": 4}
        metadata = Raster._parse_template(template, "template", keywords)
        assert metadata == {"crs": 1, "nodata": 4}

    def test_invalid_template(_):
        keywords = {"a": 1, "b": 2}
        with pytest.raises(TypeError) as error:
            Raster._parse_template("invalid", "template name", keywords)
        assert_contains(error, "pfdf.raster.Raster")


class TestSetMetadata:
    def test(_):
        raster = Raster()
        raster._set_metadata(1, 2, 3)
        assert raster._crs == 1
        assert raster._transform == 2
        assert raster._nodata == 3


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
        other._crs = CRS.from_epsg(4000)
        assert raster != other

    def test_other_transform(_, fraster):
        raster = Raster(fraster)
        other = Raster(fraster)
        other._transform = Transform(Transform.build(1, 2, 3, 4))
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

    def test_bad_shape(_, fraster, transform, crs):
        raster = Raster(fraster, "self name")
        height = raster.shape[0] + 1
        width = raster.shape[1] + 1
        araster = np.ones((height, width))
        input = Raster.from_array(araster, transform=transform, crs=crs)
        with pytest.raises(RasterShapeError) as error:
            raster.validate(input, "test name")
        assert_contains(error, "test name", "self name")

    def test_bad_transform(_, fraster, araster, crs):
        transform = Affine(9, 0, 0, 0, 9, 0)
        raster = Raster(fraster, "self name")
        input = Raster.from_array(araster, crs=crs, transform=transform)
        with pytest.raises(RasterTransformError) as error:
            raster.validate(input, "test name")
        assert_contains(error, "test name", "self name")

    def test_bad_crs(_, fraster, araster, transform):
        crs = CRS.from_epsg(4000)
        raster = Raster(fraster, "self name")
        input = Raster.from_array(araster, crs=crs, transform=transform)
        with pytest.raises(RasterCrsError) as error:
            raster.validate(input, "test name")
        assert_contains(error, "test name", "self name")

    @pytest.mark.parametrize(
        "input, error, message",
        (
            (5, TypeError, "test name"),
            (np.ones((3, 3, 3)), DimensionError, "test name"),
        ),
    )
    def test_invalid_raster(_, input, error, message, fraster):
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
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.affine == transform
        assert output.crs == crs

    def test_no_metadata(_, araster):
        raster = Raster(araster)
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
        assert output.affine == transform
        assert output.crs == crs

    def test_bool_without_nodata(_, araster, transform, crs):
        araster = araster.astype(bool)
        raster = Raster.from_array(araster, transform=transform, crs=crs)
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == False
        assert output.affine == transform
        assert output.crs == crs

    def test_int8_with_nodata(_, araster, transform, crs):
        araster = araster.astype("int8")
        raster = Raster.from_array(araster, nodata=5, crs=crs, transform=transform)
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == 5
        assert output.affine == transform
        assert output.crs == crs

    def test_int8_without_nodata(_, araster, transform, crs):
        araster = araster.astype("int8")
        raster = Raster.from_array(araster, crs=crs, transform=transform)
        output = raster.as_pysheds()
        assert isinstance(output, PyshedsRaster)
        assert np.array_equal(output, araster)
        assert output.nodata == 0
        assert output.affine == transform
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
# GIS Metadata
#####


class TestEdgeDict:
    def test(_):
        output = Raster._edge_dict(1, 2, 3, 4, 10, 20)
        assert output == {
            "left": (1, 10),
            "right": (2, 10),
            "top": (3, 20),
            "bottom": (4, 20),
        }


class TestParseMetadatas:
    def test_no_nones(_):
        assert Raster._parse_metadatas(1, 2, 3) == {"source": 1, "template": 2}

    def test_both_nones(_):
        assert Raster._parse_metadatas(None, None, 3) == {"source": 3, "template": 3}

    def test_source_only(_):
        assert Raster._parse_metadatas(1, None, 3) == {"source": 1, "template": 1}

    def test_template_only(_):
        assert Raster._parse_metadatas(None, 2, 3) == {"source": 2, "template": 2}


class TestParseNodata:
    def test_none(_, araster):
        raster = Raster.from_array(araster)
        with pytest.raises(ValueError) as error:
            raster._parse_nodata(None, "unsafe")
        assert_contains(error, "raster does not have a NoData value")

    def test_both(_, araster):
        raster = Raster.from_array(araster, nodata=5)
        with pytest.raises(ValueError) as error:
            raster._parse_nodata(6, "unsafe")
        assert_contains(error, "the raster already has a NoData value")

    def test_self(_, araster):
        raster = Raster.from_array(araster, nodata=5)
        assert raster._parse_nodata(None, "unsafe") == 5

    def test_user(_, araster):
        raster = Raster.from_array(araster)
        assert raster._parse_nodata(6, "unsafe") == 6

    def test_invalid_user(_, araster):
        raster = Raster.from_array(araster)
        with pytest.raises(TypeError):
            assert raster._parse_nodata("invalid", "unsafe")

    def test_invalid_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster.from_array(araster)
        with pytest.raises(TypeError):
            assert raster._parse_nodata(2.2, "safe")


#####
# Numeric Preprocessing
#####


class TestFill:
    def test_none(_, araster):
        raster = Raster(araster)
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

    def test_invalid_value(_, araster):
        raster = Raster.from_array(araster, nodata=0)
        with pytest.raises(TypeError) as error:
            raster.fill("invalid")
        assert_contains(error, "fill value")

    def test_invalid_casting(_, araster):
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
        raster = Raster(araster)
        raster.set_range(min=3)
        expected = araster.copy()
        expected[expected < 3] = 3
        assert np.array_equal(raster.values, expected)
        assert raster.nodata is None

    def test_max(_, araster):
        raster = Raster(araster)
        raster.set_range(max=3)
        expected = araster.copy()
        expected[expected > 3] = 3
        assert np.array_equal(raster.values, expected)
        assert raster.nodata is None

    def test_both(_, araster):
        raster = Raster(araster)
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
        raster = Raster(araster)
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

    def test_missing_nodata(_, araster):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster.set_range(min=3, max=6, fill=True)
        assert_contains(error, "raster does not have a NoData value")

    def test_extra_nodata(_, araster):
        raster = Raster.from_array(araster, nodata=-999)
        with pytest.raises(ValueError) as error:
            raster.set_range(min=3, max=6, fill=True, nodata=0)
        assert_contains(error, "raster already has a NoData value")

    def test_set_nodata(_, araster):
        raster = Raster(araster)
        raster.set_range(min=3, max=6, fill=True, nodata=-999)
        expected = araster.copy()
        expected[expected < 3] = -999
        expected[expected > 6] = -999
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == -999

    def test_invalid_nodata(_, araster):
        raster = Raster(araster)
        with pytest.raises(TypeError) as error:
            raster.set_range(min=3, fill=True, nodata="invalid")
        assert_contains(error, "nodata")

    def test_invalid_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster(araster)
        with pytest.raises(TypeError) as error:
            raster.set_range(min=3, max=6, fill=True, nodata=2.2)
        assert_contains(error, "NoData value", "cast", "safe")

    def test_cast_nodata(_, araster):
        araster = araster.astype(int)
        raster = Raster(araster)
        raster.set_range(min=3, max=6, fill=True, nodata=-999.1, casting="unsafe")
        expected = araster.copy()
        expected[expected < 3] = -999
        expected[expected > 6] = -999
        assert np.array_equal(raster.values, expected)
        assert raster.nodata == -999


class TestValidateBound:
    @pytest.mark.parametrize(
        "dtype, edge, expected",
        (
            ("int16", "min", np.iinfo("int16").min),
            ("int16", "max", np.iinfo("int16").max),
            ("uint8", "min", np.iinfo("uint8").min),
            ("uint8", "max", np.iinfo("uint8").max),
            (bool, "min", False),
            (bool, "max", True),
            ("float32", "min", -inf),
            ("float32", "max", inf),
        ),
    )
    def test_default(_, araster, dtype, edge, expected):
        araster = araster.astype(dtype)
        raster = Raster(araster)
        output = raster._validate_bound(None, edge)
        assert output == expected

    def test_valid(_, araster):
        araster = araster.astype(float)
        raster = Raster(araster)
        output = raster._validate_bound(2.2, min)
        assert output == 2.2

    def test_invalid(_, araster):
        raster = Raster(araster)
        with pytest.raises(TypeError):
            raster._validate_bound("invalid", "min")

    def test_not_scalar(_, araster):
        raster = Raster(araster)
        with pytest.raises(DimensionError):
            raster._validate_bound([1, 2, 3], "min")

    def test_invalid_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster(araster)
        with pytest.raises(TypeError) as error:
            raster._validate_bound(2.2, "min")
        assert_contains(error, "min", "cast", "safe")


#####
# Buffering
#####


class TestValidateDistance:
    def test_valid(_):
        assert Raster._validate_distance(5, "distance") == 5

    def test_negative(_):
        with pytest.raises(ValueError) as error:
            Raster._validate_distance(-5, "distance")
        assert_contains(error, "distance")

    def test_vector(_):
        with pytest.raises(DimensionError) as error:
            Raster._validate_distance([1, 2, 3], "distance")
        assert_contains(error, "distance")


class TestValidateBuffer:
    def test_none(_):
        assert Raster._validate_buffer(None, "left", default=5) == 5

    def test_valid(_):
        assert Raster._validate_buffer(5, "left", 6) == 5

    def test_negative(_):
        with pytest.raises(ValueError) as error:
            Raster._validate_buffer(-5, "left", 6)
        assert_contains(error, "left")


class Test_Buffer:
    def test_with_transform(_, fraster, araster):
        buffers = {"left": 3, "top": 4, "right": 1, "bottom": 2}
        raster = Raster(fraster)
        raster._buffer(buffers, -999)

        values = np.full((8, 8), -999, dtype=raster.dtype)
        values[4:6, 3:7] = araster
        assert np.array_equal(values, raster.values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3.12)
        assert raster.transform == transform

    def test_without_transform(_, araster):
        buffers = {"left": 3, "top": 4, "right": 1, "bottom": 2}
        raster = Raster(araster)
        raster._buffer(buffers, -999)

        values = np.full((8, 8), -999, dtype=raster.dtype)
        values[4:6, 3:7] = araster
        assert np.array_equal(values, raster.values)
        assert raster.transform is None


class TestComputeBuffers:
    def test_all_default(_, fraster):
        raster = Raster(fraster)
        buffers = raster._compute_buffers(
            distance=5, left=None, right=None, top=None, bottom=None, pixels=True
        )
        assert buffers == {"left": 5, "right": 5, "top": 5, "bottom": 5}

    def test_no_default(_, fraster):
        raster = Raster(fraster)
        buffers = raster._compute_buffers(
            distance=None, left=1, right=2, top=3, bottom=4, pixels=True
        )
        assert buffers == {"left": 1, "right": 2, "top": 3, "bottom": 4}

    def test_mixed(_, fraster):
        raster = Raster(fraster)
        buffers = raster._compute_buffers(
            distance=5, left=None, right=2, top=3, bottom=None, pixels=True
        )
        assert buffers == {"left": 5, "right": 2, "top": 3, "bottom": 5}

    def test_pixels(_, araster):
        raster = Raster(araster)
        buffers = raster._compute_buffers(
            distance=None, left=1, right=2, top=3, bottom=4, pixels=True
        )
        assert buffers == {"left": 1, "right": 2, "top": 3, "bottom": 4}

    def test_not_pixels(_, fraster):
        raster = Raster(fraster)
        buffers = raster._compute_buffers(
            distance=None, left=0.03, right=0.06, top=0.09, bottom=0.12, pixels=False
        )
        assert buffers == {"left": 1, "right": 2, "top": 3, "bottom": 4}

    def test_inexact_pixels(_, araster):
        raster = Raster(araster)
        buffers = raster._compute_buffers(
            distance=None, left=0.9, right=1.1, top=2.5, bottom=3.999, pixels=True
        )
        assert buffers == {"left": 1, "right": 2, "top": 3, "bottom": 4}

    def test_inexact_transform(_, fraster):
        raster = Raster(fraster)
        buffers = raster._compute_buffers(
            distance=None,
            left=0.02,
            right=0.05,
            top=0.0600001,
            bottom=0.1199999,
            pixels=False,
        )
        assert buffers == {"left": 1, "right": 2, "top": 3, "bottom": 4}

    def test_unbuffered(_, araster):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster._compute_buffers(
                distance=0, left=None, right=None, top=None, bottom=None, pixels=True
            )
        assert_contains(error, "must have a non-zero buffer")

    def test_negative_buffer(_, araster):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster._compute_buffers(
                distance=5, left=-1, right=None, top=None, bottom=None, pixels=True
            )
        assert_contains(error, "left")


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
        print(raster.transform)
        print(transform)
        assert raster.transform == transform

    def test_left(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(left=0.09)

        values = np.full(
            (araster.shape[0], araster.shape[1] + 3), -999, dtype=raster.dtype
        )
        values[:, 3:] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3)
        print(raster.transform)
        print(transform)
        assert raster.transform == transform

    def test_right(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(right=0.09)

        values = np.full(
            (araster.shape[0], araster.shape[1] + 3), -999, dtype=raster.dtype
        )
        values[:, 0:4] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4, 0, 0.03, -3)
        print(raster.transform)
        print(transform)
        assert raster.transform == transform

    def test_top(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(top=0.09)

        values = np.full(
            (araster.shape[0] + 3, araster.shape[1]), -999, dtype=raster.dtype
        )
        values[3:, :] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4, 0, 0.03, -3.09)
        print(raster.transform)
        print(transform)
        assert raster.transform == transform

    def test_bottom(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(bottom=0.09)

        values = np.full(
            (araster.shape[0] + 3, araster.shape[1]), -999, dtype=raster.dtype
        )
        values[0:2, :] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4, 0, 0.03, -3)
        print(raster.transform)
        print(transform)
        assert raster.transform == transform

    def test_mixed(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(distance=0.09, left=0.06, top=0.03)

        values = np.full(
            (araster.shape[0] + 4, araster.shape[1] + 5), -999, dtype=raster.dtype
        )
        values[1:3, 2:6] = araster

        print(values)
        print(raster.values)
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.06, 0, 0.03, -3.03)
        print(raster.transform)
        print(transform)
        assert raster.transform == transform

    def test_inexact_buffer(_, fraster, araster):
        raster = Raster(fraster)
        raster.buffer(distance=0.08)

        values = np.full(
            (araster.shape[0] + 6, araster.shape[1] + 6), -999, dtype=raster.dtype
        )
        values[3:5, 3:7] = araster
        assert np.array_equal(raster.values, values)

        transform = Affine(0.03, 0, -4.09, 0, 0.03, -3.09)

        assert raster.transform == transform

    def test_invert_transform(_, araster):
        transform = Affine(-0.03, 0, -4, 0, -0.03, -3)
        raster = Raster.from_array(araster, transform=transform, nodata=-999)
        raster.buffer(distance=0.09)

        values = np.full(
            (araster.shape[0] + 6, araster.shape[1] + 6), -999, dtype=raster.dtype
        )
        values[3:5, 3:7] = araster

        transform = Affine(-0.03, 0, -3.91, 0, -0.03, -2.91)
        assert raster.transform == transform

    def test_pixels(_, araster):
        raster = Raster.from_array(araster, nodata=-999)
        raster.buffer(distance=2, pixels=True)

        values = np.full((6, 8), -999, dtype=raster.dtype)
        values[2:4, 2:6] = araster
        assert np.array_equal(values, raster.values)
        assert raster.transform is None

    def test_no_buffer(_, fraster):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.buffer()
        assert_contains(error, "must specify at least 1 buffering distance")

    def test_no_transform(_, araster):
        raster = Raster.from_array(araster, nodata=-999)
        with pytest.raises(RasterTransformError) as error:
            raster.buffer(distance=10)
        assert_contains(error, "does not have an affine transformation")

    def test_missing_nodata(_, araster, transform):
        raster = Raster.from_array(araster, transform=transform)
        with pytest.raises(ValueError) as error:
            raster.buffer(distance=3)
        assert_contains(error, "does not have a NoData value")

    def test_extra_nodata(_, fraster):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.buffer(distance=3, nodata=0)
        assert_contains(error, "raster already has a NoData value")

    def test_nodata(_, araster):
        raster = Raster(araster)
        raster.buffer(distance=2, pixels=True, nodata=-999)
        values = np.full((6, 8), -999, dtype=raster.dtype)
        values[2:4, 2:6] = araster
        assert np.array_equal(values, raster.values)

    def test_invalid_nodata(_, araster):
        raster = Raster(araster)
        with pytest.raises(TypeError) as error:
            raster.buffer(distance=2, nodata="invalid", pixels=True)
        assert_contains(error, "nodata")

    def test_invalid_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster(araster)
        with pytest.raises(TypeError) as error:
            raster.buffer(distance=2, nodata=1.2, pixels=True)
        assert_contains(error, "casting")

    def test_invalid_casting_option(_, araster):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster.buffer(distance=2, nodata=1.2, casting="invalid", pixels=True)
        assert_contains(error, "casting", "safe", "unsafe", "no")

    def test_change_casting(_, araster):
        araster = araster.astype(int)
        raster = Raster(araster)
        raster.buffer(distance=2, pixels=True, nodata=-999.2, casting="unsafe")
        values = np.full((6, 8), -999, dtype=raster.dtype)
        values[2:4, 2:6] = araster
        assert np.array_equal(values, raster.values)

    def test_0_buffer(_, fraster):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.buffer(distance=0)
        assert_contains(error, "must have a non-zero buffer")


#####
# Reprojection
#####


class TestValidateResampling:
    @pytest.mark.parametrize(
        "name, value",
        (
            ("nearest", 0),
            ("bilinear", 1),
            ("cubic", 2),
            ("cubic_spline", 3),
            ("lanczos", 4),
            ("average", 5),
            ("mode", 6),
            ("max", 8),
            ("min", 9),
            ("med", 10),
            ("q1", 11),
            ("q3", 12),
            ("sum", 13),
            ("rms", 14),
        ),
    )
    def test_valid(_, name, value):
        assert Raster._validate_resampling(name) == value

    def test_invalid(_):
        with pytest.raises(ValueError):
            Raster._validate_resampling("invalid")


class TestAxisLength:
    def test_oriented(_):
        assert Raster._axis_length(10, 4, 2) == 3

    def test_flipped(_):
        assert Raster._axis_length(4, 10, 2) == 3

    def test_partial(_):
        assert Raster._axis_length(10, 5, 2) == 3


class TestAlignEdge:
    @pytest.mark.parametrize(
        "dx, redge, expected",
        (
            (2, 27, 27),
            (2, 2.9, 1),
            (2, 5.1, 5),
            (-2, 3.1, 5),
            (-2, 0.9, 1),
        ),
    )
    def test(_, dx, redge, expected):
        assert Raster._align_edge(dx, 3, redge) == expected


class TestAlignment:
    def test_resolution_overlapping(_, crs):
        shape = (10, 10)
        stransform = Transform.build(1, 1, 0, 0)
        ttransform = Transform.build(2, 2, 0, 0)

        shape, transform = Raster._alignment(crs, crs, shape, stransform, ttransform)
        assert shape == (5, 5)
        assert transform == ttransform

    def test_resolution_no_overlap(_, crs):
        shape = (10, 10)
        stransform = Transform.build(1, 1, 0, 0)
        ttransform = Transform.build(2, 2, 100, 50)

        shape, transform = Raster._alignment(crs, crs, shape, stransform, ttransform)
        assert shape == (5, 5)
        assert transform == Transform.build(2, 2, 0, 0)

    def test_alignment(_, crs):
        shape = (10, 10)
        stransform = Transform.build(1, 1, 0, 0)
        ttransform = Transform.build(1, 1, 0.1, 0.1)

        shape, transform = Raster._alignment(crs, crs, shape, stransform, ttransform)
        assert shape == (11, 11)
        assert transform == Transform.build(1, 1, -0.9, -0.9)

    def test_resolution_alignment(_, crs):
        shape = (10, 10)
        stransform = Transform.build(1, 1, 5, 6)
        ttransform = Transform.build(2, 3, 20.1, 10)

        shape, transform = Raster._alignment(crs, crs, shape, stransform, ttransform)
        assert shape == (4, 6)
        expected = Transform.build(2, 3, 4.1, 4)
        assert np.allclose(transform, expected)

    def test_invert_orientation(_, crs):
        shape = (10, 10)
        stransform = Transform.build(1, 1, 0, 0)
        ttransform = Transform.build(-1, -1, 0, 0)

        shape, transform = Raster._alignment(crs, crs, shape, stransform, ttransform)
        assert shape == (10, 10)
        assert transform == Transform.build(-1, -1, 10, 10)

    def test_negative_orientation(_, crs):
        shape = (10, 10)
        stransform = Transform.build(-1, -1, 10, 10)
        ttransform = Transform.build(-2, -2, 6, 6)

        shape, transform = Raster._alignment(crs, crs, shape, stransform, ttransform)
        assert shape == (5, 5)
        assert transform == Transform.build(-2, -2, 10, 10)

    def test_reproject(_):
        icrs = CRS.from_epsg(26911)
        fcrs = CRS.from_epsg(26910)
        transform = Transform.build(10, -10, 492850, 3787000)
        shape = (10, 10)

        shape, transform = Raster._alignment(icrs, fcrs, shape, transform, transform)
        assert shape == (12, 12)
        expected = Transform.build(10, -10, 1045830, 3802910)
        assert np.allclose(transform, expected)


class TestReproject:
    def test_no_parameters(_, araster):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster.reproject()
        assert_contains(error, "cannot all be None")

    def test_invalid_crs(_, araster):
        raster = Raster(araster)
        with pytest.raises(CrsError):
            raster.reproject(crs="invalid")

    def test_invalid_transform(_, araster):
        raster = Raster(araster)
        with pytest.raises(TransformError):
            raster.reproject(transform="invalid")

    def test_invalid_nodata(_, araster):
        raster = Raster.from_array(
            araster, crs=CRS.from_epsg(26911), transform=Affine.identity()
        )
        with pytest.raises(TypeError) as error:
            raster.reproject(crs=CRS.from_epsg(26910), nodata="invalid")
        assert_contains(error, "nodata")

    def test_missing_nodata(_, araster):
        raster = Raster.from_array(
            araster, crs=CRS.from_epsg(26911), transform=Affine.identity()
        )
        with pytest.raises(ValueError) as error:
            raster.reproject(crs=CRS.from_epsg(26910))
        assert_contains(error, "raster does not have a NoData value")

    def test_invalid_resampling(_, araster):
        raster = Raster.from_array(
            araster, crs=CRS.from_epsg(26911), transform=Affine.identity(), nodata=0
        )
        with pytest.raises(ValueError) as error:
            raster.reproject(crs=CRS.from_epsg(26910), resampling="invalid")
        assert_contains(error, "resampling")

    def test_crs(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(crs=CRS.from_epsg(26910))

        assert raster.crs == CRS.from_epsg(26910)
        assert np.allclose(raster.transform, Transform.build(10, -10, 1045830, 3802910))
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
                    -999,
                    -999,
                    -999,
                    -999,
                ],
                [-999, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, -999],
                [-999, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, -999],
                [-999, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, -999],
                [-999, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, -999],
                [-999, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, -999],
                [-999, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, -999],
                [-999, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, -999],
                [-999, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, -999],
                [-999, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, -999],
                [-999, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, -999],
                [
                    -999,
                    -999,
                    -999,
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
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(transform=Transform.build(20, -20, 1045830, 3802910))

        assert raster.crs == CRS.from_epsg(26911)
        assert raster.nodata == -999
        assert np.allclose(raster.transform, Transform.build(20, -20, 492850, 3787010))

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

    def test_reproject(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(
            transform=Transform.build(20, -20, 0, 0), crs=CRS.from_epsg(26910)
        )

        assert raster.crs == CRS.from_epsg(26910)
        assert raster.nodata == -999
        assert np.allclose(raster.transform, Transform.build(20, -20, 1045820, 3802920))

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
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )

        template = np.arange(10).reshape(5, 2)
        template = Raster.from_array(
            template, crs=CRS.from_epsg(26910), transform=Transform.build(20, -20, 0, 0)
        )
        raster.reproject(template)

        assert raster.crs == CRS.from_epsg(26910)
        assert raster.nodata == -999
        assert np.allclose(raster.transform, Transform.build(20, -20, 1045820, 3802920))

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
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )

        template = np.arange(10).reshape(5, 2)
        template = Raster.from_array(
            template, crs=CRS.from_epsg(4396), transform=Transform.build(20, -20, 0, 0)
        )
        raster.reproject(template, crs=CRS.from_epsg(26910))

        assert raster.crs == CRS.from_epsg(26910)
        assert raster.nodata == -999
        assert np.allclose(raster.transform, Transform.build(20, -20, 1045820, 3802920))

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

    def test_bilinear(_):
        araster = np.arange(100).reshape(10, 10).astype(float)
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=-999, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(
            transform=Transform.build(20, -20, 1045830, 3802910), resampling="bilinear"
        )

        assert raster.crs == CRS.from_epsg(26911)
        assert raster.nodata == -999
        assert np.allclose(raster.transform, Transform.build(20, -20, 492850, 3787010))

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
        transform = Transform.build(10, -10, 492850, 3787000)
        raster = Raster.from_array(
            araster, nodata=0, crs=CRS.from_epsg(26911), transform=transform
        )
        raster.reproject(transform=Transform.build(20, -20, 1045830, 3802910))

        assert raster.crs == CRS.from_epsg(26911)
        assert raster.nodata == False
        assert np.allclose(raster.transform, Transform.build(20, -20, 492850, 3787010))

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
# Clipping
#####


class TestValidateOrientation:
    def test_valid(_):
        clipped = {"left": 0, "bottom": 0, "right": 10, "top": 10}
        source = BoundingBox(-1, -1, 11, 11)
        Raster._validate_orientation(clipped, source, "left", "right")

    def test_equal(_):
        clipped = {"left": 0, "bottom": 0, "right": 0, "top": 10}
        source = BoundingBox(-1, -1, 11, 11)
        with pytest.raises(ValueError) as error:
            Raster._validate_orientation(clipped, source, "left", "right")
        assert_contains(error, "left and right clipping bounds are equal (value = 0)")

    def test_invalid_orientation(_):
        clipped = {"left": 0, "bottom": 0, "right": 10, "top": 10}
        source = BoundingBox(10, 0, 0, 10)
        with pytest.raises(ValueError) as error:
            Raster._validate_orientation(clipped, source, "left", "right")
        assert_contains(
            error,
            "The orientation of the left and right clipping bounds "
            "(left = 0 < 10 = right) "
            "does not match the orientation of the current raster "
            "(left = 10 > 0 = right). "
            "Try swapping the left and right clipping bounds.",
        )


class TestParseBounds:
    def test_template(_):
        clipped = Raster._edge_dict(None, None, None, None, 1, 1)
        source = BoundingBox(0, 0, 10, 10)
        ttransform = Transform(Transform.build(1, -1, 2, 8))
        template = np.empty(shape=(5, 5))

        Raster._parse_bounds(clipped, source, ttransform, template)
        assert clipped == {"left": 2, "right": 7, "top": 8, "bottom": 3}

    def test_unoriented_template(_):
        clipped = Raster._edge_dict(None, None, None, None, 1, 1)
        source = BoundingBox(0, 0, 10, 10)
        ttransform = Transform(Transform.build(1, 1, 2, 3))
        template = np.empty(shape=(5, 5))

        Raster._parse_bounds(clipped, source, ttransform, template)
        assert clipped == {"left": 2, "right": 7, "top": 8, "bottom": 3}

    def test_keyword(_):
        clipped = Raster._edge_dict(2, None, None, None, 1, 1)
        source = BoundingBox(0, 0, 10, 10)
        Raster._parse_bounds(clipped, source, None, None)
        assert clipped == {"left": 2, "right": 10, "bottom": 0, "top": 10}

    def test_keyword_and_template(_):
        clipped = Raster._edge_dict(3, None, 5, None, 1, 1)
        source = BoundingBox(0, 0, 10, 10)
        ttransform = Transform(Transform.build(1, -1, 2, 8))
        template = np.empty(shape=(5, 5))

        Raster._parse_bounds(clipped, source, ttransform, template)
        assert clipped == {"left": 3, "right": 7, "top": 5, "bottom": 3}

    def test_invalid_keyword(_):
        clipped = Raster._edge_dict("invalid", None, None, None, 1, 1)
        source = BoundingBox(0, 0, 10, 10)
        with pytest.raises(TypeError) as error:
            Raster._parse_bounds(clipped, source, None, None)
        assert_contains(error, "The left clipping bound")

    def test_not_oriented(_):
        clipped = Raster._edge_dict(9, 0, 1, 10, 1, 1)
        source = BoundingBox(0, 0, 10, 10)
        with pytest.raises(ValueError) as error:
            Raster._parse_bounds(clipped, source, None, None)
        assert_contains(
            error,
            "The orientation of the left and right clipping bounds "
            "(left = 9.0 > 0.0 = right) "
            "does not match the orientation of the current raster "
            "(left = 0 < 10 = right). "
            "Try swapping the left and right clipping bounds.",
        )


class TestClipIndices:
    def test_mins(_):
        current = np.arange(-5, 5)
        clipped = np.arange(0, 10)
        sout, cout = Raster._clip_indices(current, clipped, 20)

        assert sout == slice(0, 5)
        assert cout == slice(5, 10)

    def test_maxs(_):
        current = np.arange(5, 15)
        clipped = np.arange(0, 10)
        sout, cout = Raster._clip_indices(current, clipped, 10)

        assert sout == slice(5, 10)
        assert cout == slice(0, 5)

    def test_both(_):
        current = np.arange(-5, 20)
        clipped = np.arange(0, 25)
        length = 10
        sout, cout = Raster._clip_indices(current, clipped, length)

        assert sout == slice(0, 10)
        assert cout == slice(5, 15)

    def test_empty(_):
        current = np.arange(1000, 1020)
        clipped = np.arange(0, 20)
        length = 20
        sout, cout = Raster._clip_indices(current, clipped, length)

        assert sout == slice(0, 0)
        assert cout == slice(0, 0)


class TestClipExterior:
    def test_keyword_nodata(_):
        rows = [-5, 15]
        cols = [-2, 13]
        nodata = -999

        araster = np.arange(100).reshape(10, 10) + 1
        raster = Raster(araster)
        values, nodata = raster._clip_exterior(rows, cols, nodata=0, casting="safe")

        assert nodata == 0
        expected = np.full((20, 15), 0)
        expected[5:15, 2:12] = araster
        assert np.array_equal(values, expected)

    def test_self_nodata(_):
        rows = [-5, 15]
        cols = [-2, 13]
        nodata = -999

        araster = np.arange(100).reshape(10, 10) + 1
        raster = Raster.from_array(araster, nodata=0)
        values, nodata = raster._clip_exterior(rows, cols, nodata=None, casting="safe")

        assert nodata == 0
        expected = np.full((20, 15), 0)
        expected[5:15, 2:12] = araster
        assert np.array_equal(values, expected)

    def test_partial(_):
        rows = [-5, 15]
        cols = [3, 8]
        nodata = -999

        araster = np.arange(100).reshape(10, 10) + 1
        raster = Raster(araster)
        values, nodata = raster._clip_exterior(rows, cols, nodata=0, casting="safe")

        assert nodata == 0
        expected = np.full((20, 5), 0)
        expected[5:15, :] = araster[:, 3:8]
        assert np.array_equal(values, expected)


class TestClipInterior:
    def test(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster(araster)
        rows = [2, 7]
        cols = [3, 6]
        values, nodata = raster._clip_interior(rows, cols)

        expected = araster[2:7, 3:6]
        assert np.array_equal(values, expected)
        assert values.base is raster._values.base
        assert nodata is None


class TestClippedValues:
    def test_interior(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster(araster)
        stransform = Transform(Affine.identity())
        clipped = {
            "left": 2,
            "right": 8,
            "bottom": 8,
            "top": 3,
        }
        values, nodata = raster._clipped_values(
            stransform, clipped, nodata=-9, casting="unsafe"
        )
        assert nodata is None
        assert np.array_equal(values, araster[3:8, 2:8])
        assert values.base is raster._values.base

    def test_exterior(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster(araster)
        stransform = Transform(Affine.identity())
        clipped = {"left": -5, "right": 8, "bottom": 15, "top": 3}
        values, nodata = raster._clipped_values(
            stransform, clipped, nodata=0, casting="safe"
        )

        assert nodata == 0
        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]
        assert np.array_equal(values, expected)

    @pytest.mark.parametrize(
        "clipped",
        (
            {"left": 1.9, "right": 7.9, "bottom": 7.9, "top": 2.9},
            {"left": 2.2, "right": 8.2, "bottom": 8.2, "top": 3.2},
        ),
    )
    def test_inexact(_, clipped):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster(araster)
        stransform = Transform(Affine.identity())
        values, nodata = raster._clipped_values(
            stransform, clipped, nodata=-9, casting="unsafe"
        )
        assert nodata is None
        assert np.array_equal(values, araster[3:8, 2:8])
        assert values.base is raster._values.base


class TestClip:
    def test_no_bounds(_, araster):
        raster = Raster(araster)
        with pytest.raises(ValueError) as error:
            raster.clip()
        assert_contains(error, "cannot all be None")

    def test_different_crs(_, araster, crs):
        raster = Raster.from_array(araster, crs=crs)
        bounds = Raster.from_array(araster, crs=CRS.from_epsg(4000))
        with pytest.raises(RasterCrsError):
            raster.clip(bounds)

    def test_no_transform(_, araster):
        raster = Raster(araster)
        with pytest.raises(RasterTransformError) as error:
            raster.clip(left=0)
        assert_contains(
            error, "raster does not have a transform and there is no bounding raster"
        )

    def test_no_transform_2(_, araster):
        raster = Raster(araster)
        bounds = Raster(araster)
        with pytest.raises(RasterTransformError) as error:
            raster.clip(bounds)
        assert_contains(
            error, "neither the raster nor the bounding raster has a transform"
        )

    def test_interior(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(araster, transform=Affine.identity())
        raster.clip(left=2, right=8, bottom=8, top=3)
        assert raster.crs is None
        assert raster.transform == Transform.build(1, 1, 2, 3)
        assert raster.nodata is None
        assert np.array_equal(raster.values, araster[3:8, 2:8])

    def test_exterior(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(araster, transform=Affine.identity())
        raster.clip(left=-5, right=8, bottom=15, top=3, nodata=0)

        assert raster.crs is None
        assert raster.nodata == 0
        assert raster.transform == Transform.build(1, 1, -5, 3)

        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]
        assert np.array_equal(raster.values, expected)

    def test_template(_, crs):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(araster, transform=Affine.identity(), nodata=0)

        bounds = np.zeros((12, 13))
        tbounds = Transform.build(1, 1, -5, 3)
        bounds = Raster.from_array(bounds, crs=crs, transform=tbounds)

        raster.clip(bounds)
        assert raster.crs is crs
        assert raster.nodata == 0
        assert raster.transform == Transform.build(1, 1, -5, 3)

        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]

        print(raster.values)
        print(expected)

        assert np.array_equal(raster.values, expected)

    def test_keyword(_):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(araster, transform=Affine.identity())
        raster.clip(left=2, right=8)
        assert raster.crs is None
        assert raster.transform == Transform.build(1, 1, 2, 0)
        assert raster.nodata is None
        assert np.array_equal(raster.values, araster[:, 2:8])

    def test_template_keyword(_, crs):
        araster = np.arange(100).reshape(10, 10)
        raster = Raster.from_array(araster, transform=Affine.identity(), nodata=0)

        bounds = np.zeros((20, 13))
        tbounds = Transform.build(1, 1, -5, 3)
        bounds = Raster.from_array(bounds, crs=crs, transform=tbounds)

        raster.clip(bounds, bottom=15)
        assert raster.crs == crs
        assert raster.nodata == 0
        assert raster.transform == Transform.build(1, 1, -5, 3)

        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]
        assert np.array_equal(raster.values, expected)


#####
# Properties
#####


class TestName:
    def test_set_string(_, araster):
        output = Raster(araster, "test")
        output.name = "different name"
        assert output.name == "different name"

    def test_set_not_string(_, araster):
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
    def test_nodata(_, fraster):
        raster = Raster(fraster)
        assert raster.nodata == -999


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


class TestWidth:
    def test_width(_, araster):
        assert Raster(araster).width == araster.shape[1]


class TestSize:
    def test_size(_, araster):
        assert Raster(araster).size == araster.size


class TestCrs:
    def test_crs(_, fraster, crs):
        assert Raster(fraster).crs == crs

    def test_set(_, crs):
        raster = Raster()
        raster.crs = crs
        assert raster.crs == crs

    def test_already_set(_, fraster, crs):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.crs = crs
        assert_contains(error, "raster already has a CRS")

    def test_invalid(_):
        raster = Raster()
        with pytest.raises(CrsError):
            raster.crs = "invalid"


class TestTransform:
    def test_transform(_, fraster, transform):
        assert Raster(fraster).transform == transform

    def test_set(_, transform):
        raster = Raster()
        raster.transform = transform
        assert raster.transform == transform

    def test_already_set(_, fraster, transform):
        raster = Raster(fraster)
        with pytest.raises(ValueError) as error:
            raster.transform = transform
        assert_contains(error, "raster already has a transform")

    def test_invalid(_):
        raster = Raster()
        with pytest.raises(TransformError):
            raster.transform = "invalid"


class TestDx:
    def test_dx(_, fraster, transform):
        assert Raster(fraster).dx == transform[0]

    def test_nan(_):
        raster = Raster()
        assert isnan(raster.dx)


class TestDy:
    def test_dy(_, fraster, transform):
        assert Raster(fraster).dy == transform[4]

    def test_nan(_):
        raster = Raster()
        assert isnan(raster.dy)


class TestLeftTop:
    def test_exist(_, fraster, transform):
        raster = Raster(fraster)
        left, top = transform * (0, 0)
        assert raster.left == left
        assert raster.top == top

    def test_missing(_, araster):
        raster = Raster(araster)
        assert isnan(raster.left)
        assert isnan(raster.top)


class TestRightBottom:
    def test_exists(_, fraster, transform):
        raster = Raster(fraster)
        right, bottom = transform * (raster.width, raster.height)
        assert raster.right == right
        assert raster.bottom == bottom

    def test_missing(_, araster):
        raster = Raster(araster)
        assert isnan(raster.right)
        assert isnan(raster.bottom)


class TestBounds:
    def test_exists(_, fraster, transform):
        raster = Raster(fraster)
        left, top = transform * (0, 0)
        right, bottom = transform * (raster.width, raster.height)
        expected = BoundingBox(left, bottom, right, top)
        assert raster.bounds == expected

    def test_missing(_, araster):
        bounds = Raster(araster).bounds
        assert isnan(bounds.left)
        assert isnan(bounds.right)
        assert isnan(bounds.top)
        assert isnan(bounds.bottom)


class TestPixelWidth:
    def test(_, fraster, transform):
        raster = Raster(fraster)
        assert raster.pixel_width == abs(transform[0])

    def test_nan(_):
        raster = Raster()
        assert isnan(raster.pixel_width)


class TestPixelHeight:
    def test(_, fraster, transform):
        raster = Raster(fraster)
        assert raster.pixel_height == abs(transform[4])

    def test_nan(_):
        raster = Raster()
        assert isnan(raster.pixel_height)


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
