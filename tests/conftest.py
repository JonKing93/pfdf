from pathlib import Path

import fiona
import numpy as np
import pytest
import rasterio
from affine import Affine
from geojson import Feature, MultiPoint, MultiPolygon, Point, Polygon
from pyproj import CRS

from pfdf.projection import Transform


def _assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


@pytest.fixture
def assert_contains():
    return _assert_contains


@pytest.fixture
def crs():
    return CRS(26911)


@pytest.fixture
def affine():
    return Affine(0.03, 0, -4, 0, 0.03, -3)


@pytest.fixture
def transform(affine):
    return Transform.from_affine(affine)


@pytest.fixture
def araster():
    "A numpy array raster"
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


@pytest.fixture
def points(tmp_path, crs):
    points = [[1, 2], [3.3, 4.4], [5, 6]]
    values = range(len(points))

    records = [
        Feature(
            geometry=Point(coords), properties={"test": value, "invalid": "invalid"}
        )
        for coords, value in zip(points, values)
    ]
    file = Path(tmp_path) / "test.geojson"
    save_features(file, records, crs)
    return file


@pytest.fixture
def multipoints(tmp_path, crs):
    points = [
        [[1, 2], [3, 4], [5.5, 6.6]],
        [[8, 9], [2, 7]],
    ]
    values = range(len(points))

    records = [
        Feature(
            geometry=MultiPoint(coords),
            properties={"test": value, "invalid": "invalid"},
        )
        for coords, value in zip(points, values)
    ]
    file = Path(tmp_path) / "test.geojson"
    save_features(file, records, crs)
    return file


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
        Feature(
            geometry=Polygon(coords), properties={"test": value, "invalid": "invalid"}
        )
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
        Feature(
            geometry=MultiPolygon(coords),
            properties={"test": value, "invalid": "invalid"},
        )
        for coords, value in zip(coords, values)
    ]
    file = Path(tmp_path) / "multitest.geojson"
    save_features(file, multis, crs)
    return file


def save_features(path, features, crs):
    schema = {
        "geometry": features[0].geometry.type,
        "properties": {"test": "int", "invalid": "str"},
    }
    with fiona.open(
        path,
        "w",
        driver="GeoJSON",
        schema=schema,
        crs=crs,
    ) as file:
        file.writerecords(features)


@pytest.fixture
def fraster(tmp_path, araster, affine, crs):
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
        transform=affine,
        crs=crs,
    ) as file:
        file.write(araster, 1)
    return path
