from math import inf, isnan

import fiona
import numpy as np
import pytest
from fiona.collection import Collection

from pfdf.errors import FeatureFileError, GeometryError, NoFeaturesError, PointError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import _features
from pfdf.raster._features import FeatureFile

#####
# Main Function
#####


class TestParseFile:
    def test_invalid_resolution(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _features.parse_file(
                "polygon",
                polygons,
                None,
                None,
                None,
                "safe",
                "invalid",
                "base",
                None,
                None,
                None,
            )
        assert_contains(error, "resolution")

    def test_invalid_bounds(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _features.parse_file(
                "polygon",
                polygons,
                None,
                "invalid",
                None,
                "safe",
                10,
                "meters",
                None,
                None,
                None,
            )
        assert_contains(error, "bounds")

    def test_invalid_field(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _features.parse_file(
                "polygon",
                polygons,
                5,
                None,
                None,
                "safe",
                10,
                "meters",
                None,
                None,
                None,
            )
        assert_contains(error, "field")

    def test_invalid_nodata(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            _features.parse_file(
                "polygon",
                polygons,
                "test",
                None,
                "invalid",
                "safe",
                10,
                "meters",
                None,
                None,
                None,
            )
        assert_contains(error, "nodata", "not an allowed dtype")

    def test_polygons(_, polygons, crs):
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon",
            polygons,
            None,
            None,
            None,
            "safe",
            10,
            "meters",
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon",
            multipolygons,
            None,
            None,
            None,
            "safe",
            10,
            "meters",
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "point", points, None, None, None, "safe", 10, "meters", None, None, None
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "point",
            multipoints,
            None,
            None,
            None,
            "safe",
            10,
            "meters",
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon",
            polygons,
            None,
            window,
            None,
            "safe",
            10,
            "meters",
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon",
            polygons,
            "test",
            None,
            None,
            "safe",
            10,
            "meters",
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon",
            polygons,
            "test-float",
            None,
            None,
            "safe",
            10,
            "meters",
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon", polygons, "test", None, 5, "safe", 10, "meters", None, None, None
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
        geomvals, outcrs, transform, shape, dtype, nodata = _features.parse_file(
            "polygon",
            polygons,
            "test",
            None,
            5.2,
            "unsafe",
            10,
            "meters",
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


#####
# Processing Functions
#####


class TestParseNodata:
    def test_bool(_):
        assert _features.parse_nodata(None, "safe", bool) == False

    def test_default(_):
        output = _features.parse_nodata(None, "safe", float)
        assert isnan(output)

    def test_user(_):
        assert _features.parse_nodata(5, "safe", float) == 5

    def test_invalid_user(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _features.parse_nodata(2.2, "safe", int)
        assert_contains(error, "Cannot cast the NoData value")


class TestParseFeatures:
    def test_invalid_geometry(_, polygons, assert_contains):
        with FeatureFile(polygons, None, None, None) as ffile:
            with pytest.raises(GeometryError) as error:
                _features.parse_features("point", ffile, None, None, None)
            assert_contains(
                error,
                "must have a Point or MultiPoint geometry",
                "feature[0] has a Polygon geometry",
            )

    def test_invalid_coordinates(_, invalid_points):
        with FeatureFile(invalid_points, None, None, None) as ffile:
            with pytest.raises(PointError):
                _features.parse_features("point", ffile, None, None, None)

    def test_points(_, points, crs):
        with FeatureFile(points, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features("point", ffile, None, crs, None)
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(10, 20, 50, 60, crs)

    def test_multipoints(_, multipoints, crs):
        with FeatureFile(multipoints, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features("point", ffile, None, crs, None)
        with fiona.open(multipoints) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(10, 20, 80, 90, crs)

    def test_polygons(_, polygons, crs):
        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features(
                "polygon", ffile, None, crs, None
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(20, 20, 90, 90, crs)

    def test_multipolygons(_, multipolygons, crs):
        with FeatureFile(multipolygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features(
                "polygon", ffile, None, crs, None
            )
        with fiona.open(multipolygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(20, 20, 90, 90, crs)

    def test_field(_, polygons):
        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features(
                "polygon", ffile, "test", None, None
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f) for f, feature in enumerate(features)
        ]
        assert bounds == BoundingBox(20, 20, 90, 90)

    def test_polygon_window(_, polygons, crs):
        window = BoundingBox(0, 0, 30, 30, crs)
        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features(
                "polygon", ffile, None, crs, window
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(features[0]["geometry"], True)]
        assert bounds == BoundingBox(20, 20, 60, 70, crs)

    def test_point_window(_, points, crs):
        window = BoundingBox(0, 0, 45, 45, crs)
        with FeatureFile(points, None, None, None) as ffile:
            geomvals, bounds = _features.parse_features(
                "point", ffile, None, crs, window
            )
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [
            (features[0]["geometry"], True),
            (features[1]["geometry"], True),
        ]
        assert bounds == BoundingBox(10, 20, 33, 44, crs)

    def test_no_features(_, polygons, crs, assert_contains):
        window = BoundingBox(1000, 1000, 2000, 2000, crs)
        with FeatureFile(polygons, None, None, None) as ffile:
            with pytest.raises(NoFeaturesError) as error:
                _features.parse_features("polygon", ffile, None, crs, window)
            assert_contains(
                error, "None of the polygon features intersect the input bounds"
            )


class TestParseValue:
    def test_no_field(_):
        assert _features.parse_value({}, None) == True

    def test_field(_):
        feature = {"properties": {"test": 5}}
        assert _features.parse_value(feature, "test") == 5


class TestRequireFeatures:
    def test_have_features(_):
        features = [1, 2, 3]
        _features.require_features("", features, None, None)

    def test_empty(_, assert_contains):
        with pytest.raises(NoFeaturesError) as error:
            _features.require_features("polygon", [], None, "a/file/path")
        assert_contains(
            error,
            "The polygon feature file is empty and does not have any polygon features",
            "File: a/file/path",
        )

    def test_none_in_bounds(_, assert_contains):
        with pytest.raises(NoFeaturesError) as error:
            _features.require_features(
                "polygon", [], BoundingBox(1, 2, 3, 4), "a/file/path"
            )
        assert_contains(
            error,
            "None of the polygon features intersect the input bounds",
            "File: a/file/path",
        )


class TestParseResolution:
    @pytest.mark.parametrize("units", ("meters", "base"))
    def test_transform(_, units):
        crs = CRS(4326)
        res = Transform(1, 2, 3, 4, crs)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        out1, out2 = _features.parse_resolution(res, units, crs, bounds)
        assert out1 == (1, 2)
        assert out2 == crs

    def test_reproject_transform(_):
        crs = CRS(26910)
        res = Transform(1, 2, 3, 4, 26911)
        bounds = BoundingBox(0, 100, 500, 1000, crs)
        out1, out2 = _features.parse_resolution(res, "base", crs, bounds)
        expected = (0.997261140611954, 1.9945226908862739)
        assert np.allclose(out1, expected)
        assert out2 == crs

    def test_inherit_crs(_):
        crs = CRS(4326)
        res = Transform(1, 2, 3, 4, crs)
        bounds = BoundingBox(1, 2, 3, 4, None)
        output = _features.parse_resolution(res, "base", None, bounds)
        assert output == ((1, 2), crs)

    def test_meters(_):
        crs = CRS(4326)
        res = (10, 10)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        out1, out2 = _features.parse_resolution(res, "meters", crs, bounds)
        assert out1 == (9.005557863254549e-05, 8.993216059187306e-05)
        assert out2 == crs

    def test_base(_):
        crs = CRS(4326)
        res = (10, 10)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        output = _features.parse_resolution(res, "base", crs, bounds)
        assert output == ((10, 10), crs)


class TestComputeExtent:
    def test(_):
        bounds = BoundingBox(0, 0, 10, 200)
        resolution = (5, 10)
        out1, out2 = _features.compute_extent(bounds, resolution)
        assert out1 == Transform(5, -10, 0, 200)
        assert out2 == (20, 2)


#####
# BoundingBox Utilities
#####


class TestUnbounded:
    def test_no_crs(_):
        assert _features.unbounded() == {
            "left": inf,
            "bottom": inf,
            "right": -inf,
            "top": -inf,
        }

    def test_crs(_):
        assert _features.unbounded(4326) == {
            "left": inf,
            "bottom": inf,
            "right": -inf,
            "top": -inf,
            "crs": 4326,
        }


class TestPointEdges:
    def test(_):
        coords = [10, 10]
        left, bottom, right, top = _features.point_edges(coords)
        assert left == 10
        assert right == 10
        assert bottom == 10
        assert top == 10


class TestPolygonEdges:
    def test(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        left, bottom, right, top = _features.polygon_edges(coords)
        assert left == -10
        assert right == 10
        assert bottom == -10
        assert top == 10


class TestAddCoords:
    def test_no_updates(_):
        coords = [[(1, 2), (3, 4), (5, 6), (1, 2)]]
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        _features.add_coords("polygon", coords, bounds)
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
        _features.add_coords("polygon", coords, bounds)
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
        _features.add_coords("polygon", coords, bounds)
        assert bounds["left"] == -20
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 20

    def test_polygon(_):
        coords = [[(-10, 10), (10, 10), (10, -10), (-10, -10), (-10, 10)]]
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        _features.add_coords("polygon", coords, bounds)
        assert bounds["left"] == -10
        assert bounds["right"] == 10
        assert bounds["bottom"] == -10
        assert bounds["top"] == 10

    def test_point(_):
        coords = [10, 10]
        bounds = {
            "left": 0,
            "right": 0,
            "bottom": 0,
            "top": 0,
        }
        _features.add_coords("point", coords, bounds)
        assert bounds["left"] == 0
        assert bounds["right"] == 10
        assert bounds["bottom"] == 0
        assert bounds["top"] == 10


class TestUpdateBounds:
    def test_mins(_):
        bounds = {"left": -100, "right": 100, "bottom": -100, "top": 100}
        _features.update_bounds(bounds, 200, 200, 200, 200)
        assert bounds == {"left": -100, "right": 200, "bottom": -100, "top": 200}

    def test_maxs(_):
        bounds = {"left": -100, "right": 100, "bottom": -100, "top": 100}
        _features.update_bounds(bounds, -200, -200, -200, -200)
        assert bounds == {"left": -200, "right": 100, "bottom": -200, "top": 100}


#####
# FeatureFile context manager
#####


class TestInit:
    def test_valid(_, fraster):
        a = FeatureFile(fraster, 1, "ShapeFile", "test")
        assert isinstance(a, FeatureFile)
        assert a.path == fraster.resolve()
        assert a.layer == 1
        assert a.driver == "ShapeFile"
        assert a.encoding == "test"

    def test_nones(_, fraster):
        a = FeatureFile(fraster, None, None, None)
        assert a.path == fraster.resolve()
        assert a.layer is None
        assert a.driver is None
        assert a.encoding is None

    def test_invalid(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            FeatureFile(fraster, None, 5, None)
        assert_contains(error, "driver")

    def test_missing(_):
        with pytest.raises(FileNotFoundError):
            FeatureFile("not-a-file", None, None, None)


class TestEnter:
    def test_invalid(_, fraster, assert_contains):
        with pytest.raises(FeatureFileError) as error:
            FeatureFile(fraster, None, None, None).__enter__()
        assert_contains(error, "Could not read data from the feature file")

    def test_valid(_, polygons, crs):
        with FeatureFile(polygons, None, None, None) as file:
            assert isinstance(file.file, Collection)
            assert file.crs == crs
            assert file.file.closed == False


class TestExit:
    def test(_, polygons):
        with FeatureFile(polygons, None, None, None) as file:
            pass
        assert file.file.closed == True
