import fiona
import numpy as np
import pytest

from pfdf.errors import DimensionError, GeometryError, NoFeaturesError, PointError
from pfdf.projection import BoundingBox
from pfdf.raster._features import _features
from pfdf.raster._features._ffile import FeatureFile


class TestParse:
    def test_invalid_geometry(_, polygons, assert_contains):
        with FeatureFile(polygons, None, None, None) as ffile:
            with pytest.raises(GeometryError) as error:
                _features.parse("point", ffile, None, None, None, None, None, None)
            assert_contains(
                error,
                "must have a Point or MultiPoint geometry",
                "feature[0] has a Polygon geometry",
            )

    def test_invalid_coordinates(_, invalid_points):
        with FeatureFile(invalid_points, None, None, None) as ffile:
            with pytest.raises(PointError):
                _features.parse("point", ffile, None, None, None, None, None, None)

    def test_points(_, points, crs):
        with FeatureFile(points, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "point", ffile, None, None, None, None, crs, None
            )
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(10, 20, 50, 60, crs)

    def test_multipoints(_, multipoints, crs):
        with FeatureFile(multipoints, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "point", ffile, None, None, None, None, crs, None
            )
        with fiona.open(multipoints) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(10, 20, 80, 90, crs)

    def test_polygons(_, polygons, crs):
        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "polygon", ffile, None, None, None, None, crs, None
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(20, 20, 90, 90, crs)

    def test_multipolygons(_, multipolygons, crs):
        with FeatureFile(multipolygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "polygon", ffile, None, None, None, None, crs, None
            )
        with fiona.open(multipolygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert bounds == BoundingBox(20, 20, 90, 90, crs)

    def test_field(_, polygons):
        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "polygon", ffile, "test", None, None, None, None, None
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
            geomvals, bounds = _features.parse(
                "polygon", ffile, None, None, None, None, crs, window
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(features[0]["geometry"], True)]
        assert bounds == window

    def test_point_window(_, points, crs):
        window = BoundingBox(0, 0, 45, 45, crs)
        with FeatureFile(points, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "point", ffile, None, None, None, None, crs, window
            )
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [
            (features[0]["geometry"], True),
            (features[1]["geometry"], True),
        ]
        assert bounds == window

    def test_no_features(_, polygons, crs, assert_contains):
        window = BoundingBox(1000, 1000, 2000, 2000, crs)
        with FeatureFile(polygons, None, None, None) as ffile:
            with pytest.raises(NoFeaturesError) as error:
                _features.parse("polygon", ffile, None, None, None, None, crs, window)
            assert_contains(
                error, "None of the polygon features intersect the input bounds"
            )

    def test_cast_dtype(_, polygons):
        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "polygon", ffile, "test", np.dtype(int), "unsafe", None, None, None
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], int(f)) for f, feature in enumerate(features)
        ]
        assert bounds == BoundingBox(20, 20, 90, 90)

    def test_operation(_, polygons):
        def plus_one(value):
            return value + 1

        with FeatureFile(polygons, None, None, None) as ffile:
            geomvals, bounds = _features.parse(
                "polygon", ffile, "test", None, None, plus_one, None, None
            )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [
            (feature["geometry"], f + 1) for f, feature in enumerate(features)
        ]
        assert bounds == BoundingBox(20, 20, 90, 90)


class TestParseValue:
    def feature(cls):
        return {"properties": {"test": 5}}

    def test_no_field(_):
        output = _features._parse_value(5, {}, None, None, None, None)
        assert output == True

    def test_bad_operation(self, assert_contains):
        def bad():
            raise Exception("The operation failed")

        try:
            bad()
        except Exception:
            "Ensuring the function fails"

        dtype = np.dtype(int)

        with pytest.raises(RuntimeError) as error:
            _features._parse_value(
                5, self.feature(), "test", dtype, "safe", operation=bad
            )
        assert_contains(error, 'The "operation" function caused an error')

    def test_bad_operation_output(self, assert_contains):
        def bad(value):
            return [1, 2, 3, 4, 5]

        dtype = np.dtype(int)

        with pytest.raises(DimensionError) as error:
            _features._parse_value(
                5, self.feature(), "test", dtype, "safe", operation=bad
            )
        assert_contains(
            error,
            'the value for feature 5 output by "operation" must have exactly 1 element',
        )

    def test_field_no_operation(self):
        output = _features._parse_value(
            5, self.feature(), "test", np.dtype(int), "safe", None
        )
        assert output == 5

    def test_field_operation(self):
        def plus_one(value):
            return value + 1

        output = _features._parse_value(
            5, self.feature(), "test", np.dtype(int), "safe", plus_one
        )
        assert output == 6


class TestRequireFeatures:
    def test_have_features(_):
        features = [1, 2, 3]
        _features._require_features("", features, None, None)

    def test_empty(_, assert_contains):
        with pytest.raises(NoFeaturesError) as error:
            _features._require_features("polygon", [], None, "a/file/path")
        assert_contains(
            error,
            "The polygon feature file is empty and does not have any polygon features",
            "File: a/file/path",
        )

    def test_none_in_bounds(_, assert_contains):
        with pytest.raises(NoFeaturesError) as error:
            _features._require_features(
                "polygon", [], BoundingBox(1, 2, 3, 4), "a/file/path"
            )
        assert_contains(
            error,
            "None of the polygon features intersect the input bounds",
            "File: a/file/path",
        )
