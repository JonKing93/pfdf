from math import isnan

import fiona
import numpy as np
import pytest

from pfdf.projection import Transform
from pfdf.raster._features import _main


class TestParseFile:
    def test_invalid_resolution(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _main.parse_file(
                # General
                "polygon",
                polygons,
                None,
                # Field
                None,
                None,
                None,
                None,
                None,
                # Spatial
                None,
                "invalid",
                "base",
                # File IO
                None,
                None,
                None,
            )
        assert_contains(error, "resolution")

    def test_invalid_bounds(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _main.parse_file(
                # Generla
                "polygon",
                polygons,
                None,
                # Field
                None,
                None,
                None,
                None,
                None,
                # Spatial
                "invalid",
                10,
                "meters",
                # File IO
                None,
                None,
                None,
            )
        assert_contains(error, "bounds")

    def test_invalid_field(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _main.parse_file(
                # General
                "polygon",
                polygons,
                5,
                # Field
                None,
                None,
                None,
                None,
                None,
                # Spatial
                None,
                10,
                "meters",
                # File IO
                None,
                None,
                None,
            )
        assert_contains(error, "field")

    def test_invalid_nodata(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _main.parse_file(
                # General
                "polygon",
                polygons,
                "test",
                # Field
                None,
                "safe",
                "invalid",
                "safe",
                None,
                # Spatial
                None,
                10,
                "meters",
                # File IO
                None,
                None,
                None,
            )
        assert_contains(error, "nodata", "not an allowed dtype")

    def test_polygons(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            None,
            # Field
            None,
            None,
            None,
            None,
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == bool
        assert nodata == False

    def test_multipolygons(_, multipolygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            multipolygons,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(multipolygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == bool
        assert nodata == False

    def test_points(_, points, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "point",
            points,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert outcrs == crs
        assert transform == Transform(10, -10, 10, 60)
        assert shape == (4, 4)
        assert dtype == bool
        assert nodata == False

    def test_multipoints(_, multipoints, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "point",
            multipoints,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(multipoints) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert outcrs == crs
        assert transform == Transform(10, -10, 10, 90)
        assert shape == (7, 7)
        assert dtype == bool
        assert nodata == False

    def test_windowed(_, polygons, crs):
        window = (0, 0, 30, 30, crs)
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            window,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(features[0]["geometry"], True)]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 70)
        assert shape == (5, 4)
        assert dtype == bool
        assert nodata == False

    def test_int_field(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            "test",
            # Field
            None,
            "safe",
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f) for f, feature in enumerate(features)
        ]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == int
        assert nodata == np.iinfo(int).min

    def test_float_field(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            "test-float",
            # Field
            None,
            "safe",
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f + 1.2) for f, feature in enumerate(features)
        ]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == float
        assert isnan(nodata)

    def test_nodata(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            "test",
            # Spatial
            None,
            "safe",
            5,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f) for f, feature in enumerate(features)
        ]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == int
        assert nodata == 5

    def test_nodata_casting(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            "test",
            # Field
            None,
            "safe",
            5.2,
            "unsafe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f) for f, feature in enumerate(features)
        ]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == int
        assert nodata == 5

    def test_dtype_casting(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            "test-float",
            # Field
            "int32",
            "unsafe",
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        print(geomvals)
        assert geomvals == [
            (feature["geometry"], int(f + 1.2)) for f, feature in enumerate(features)
        ]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == np.dtype("int32")
        assert nodata == np.iinfo("int32").min

    def test_operation(_, polygons, crs):
        def plus_one(value):
            return value + 1

        geomvals, outcrs, transform, shape, dtype, nodata = _main.parse_file(
            # General
            "polygon",
            polygons,
            "test-float",
            # Field
            None,
            "safe",
            None,
            "safe",
            plus_one,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f + 1.2 + 1) for f, feature in enumerate(features)
        ]
        assert outcrs == crs
        assert transform == Transform(10, -10, 20, 90)
        assert shape == (7, 7)
        assert dtype == float
        assert isnan(nodata)
