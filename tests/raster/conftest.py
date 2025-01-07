from pathlib import Path

import fiona
import numpy as np
import pytest
import rasterio
from geojson import Feature, MultiPoint, MultiPolygon, Point, Polygon

from pfdf.raster import RasterMetadata

#####
# File-based raster
#####


@pytest.fixture
def MockReader():
    class MockReader:
        def __init__(self):
            self.height = 4
            self.width = 5
            self.dtypes = ["int16"]
            self.nodata = -1
            self.crs = 26911
            self.transform = (10, -10, 0, 0)

        def __enter__(self):
            return self

        def __exit__(self, *args, **kwargs):
            pass

        def read(*args, **kwargs):
            return np.array(
                [
                    [1, 1, 1, 1, 1],
                    [2, 2, 2, 2, 2],
                    [3, 3, 3, 3, 3],
                    [4, 4, 4, 4, 4],
                ],
                "int16",
            )

    return MockReader()


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


@pytest.fixture
def fmetadata():
    return RasterMetadata(
        (2, 4), dtype=float, nodata=-999, crs=26911, transform=(0.03, 0.03, -4, -3)
    )


#####
# Vector features
#####


@pytest.fixture
def points(tmp_path, crs):
    points = [[10, 20], [33, 44], [50, 60]]
    values = range(len(points))

    records = [
        Feature(
            geometry=Point(coords),
            properties={"test": value, "test-float": value + 1.2, "invalid": "invalid"},
        )
        for coords, value in zip(points, values)
    ]
    file = Path(tmp_path) / "test.geojson"
    save_features(file, records, crs)
    return file


@pytest.fixture
def multipoints(tmp_path, crs):
    points = [
        [[10, 20], [30, 40], [55, 66]],
        [[80, 90], [20, 70]],
    ]
    values = range(len(points))

    records = [
        Feature(
            geometry=MultiPoint(coords),
            properties={"test": value, "test-float": value + 1.2, "invalid": "invalid"},
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
            [(20, 20), (20, 70), (60, 70), (60, 20), (20, 20)],
            [(20, 20), (20, 40), (40, 40), (40, 20), (20, 20)],  # hole in upper-left
        ),
        ([(40, 60), (40, 90), (90, 90), (90, 60), (40, 60)],),
    ]


@pytest.fixture
def polygons(polygon_coords, tmp_path, crs):
    file = Path(tmp_path) / "test.geojson"
    values = range(len(polygon_coords))
    polygons = [
        Feature(
            geometry=Polygon(coords),
            properties={"test": value, "test-float": value + 1.2, "invalid": "invalid"},
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
                [(20, 20), (20, 70), (60, 70), (60, 20), (20, 20)],
                [(20, 20), (20, 40), (40, 40), (40, 20), (20, 20)],
            ],
            [[(40, 60), (40, 90), (90, 90), (90, 60), (40, 60)]],  # Polygon A2
        ],
        [[[(50, 30), (50, 40), (60, 40), (60, 30), (50, 30)]]],  # Multipolygon B
    ]
    values = range(len(coords))
    multis = [
        Feature(
            geometry=MultiPolygon(coords),
            properties={"test": value, "test-float": value + 1.2, "invalid": "invalid"},
        )
        for coords, value in zip(coords, values)
    ]
    file = Path(tmp_path) / "multitest.geojson"
    save_features(file, multis, crs)
    return file


@pytest.fixture
def invalid_points(tmp_path, crs):
    path = Path(tmp_path) / "invalid-points.geojson"
    feature = [
        {
            "geometry": {"type": "Point", "coordinates": (1, 2, 3, 4)},
            "properties": {"test": 1, "test-float": 2.2, "invalid": "a string"},
        }
    ]
    save_features(path, feature, crs)
    return path


def save_features(path, features, crs):
    schema = {
        "geometry": features[0]["geometry"]["type"],
        "properties": {"test": "int", "test-float": "float", "invalid": "str"},
    }
    with fiona.open(
        path,
        "w",
        driver="GeoJSON",
        schema=schema,
        crs=crs,
    ) as file:
        file.writerecords(features)
