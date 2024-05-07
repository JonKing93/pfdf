import os
from math import inf, isnan
from pathlib import Path

import fiona
import fiona.model
import numpy as np
import pytest
from fiona.collection import Collection

from pfdf._utils import features
from pfdf._utils.features import FeatureFile
from pfdf.errors import (
    FeatureFileError,
    GeometryError,
    MissingCRSError,
    PointError,
    PolygonError,
)
from pfdf.projection import CRS, BoundingBox, Transform

#####
# Feature parsing
#####


class TestUnbounded:
    def test(_):
        assert features._unbounded() == {
            "left": inf,
            "bottom": inf,
            "right": -inf,
            "top": -inf,
        }


class TestUpdateBounds:
    def test_mins(_):
        bounds = {"left": -100, "right": 100, "bottom": -100, "top": 100}
        features._update_bounds(bounds, 200, 200, 200, 200)
        assert bounds == {"left": -100, "right": 200, "bottom": -100, "top": 200}

    def test_maxs(_):
        bounds = {"left": -100, "right": 100, "bottom": -100, "top": 100}
        features._update_bounds(bounds, -200, -200, -200, -200)
        assert bounds == {"left": -200, "right": 100, "bottom": -200, "top": 100}


class TestAddCoords:
    def test_no_updates(_):
        coords = [[(1, 2), (3, 4), (5, 6), (1, 2)]]
        bounds = {
            "left": -10,
            "right": 10,
            "bottom": -10,
            "top": 10,
        }
        features._add_coords(bounds, coords, False)
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
        features._add_coords(bounds, coords, False)
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
        features._add_coords(bounds, coords, False)
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
        features._add_coords(bounds, coords, ispoint=False)
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
        features._add_coords(bounds, coords, ispoint=True)
        assert bounds["left"] == 0
        assert bounds["right"] == 10
        assert bounds["bottom"] == 0
        assert bounds["top"] == 10


class TestParseFeatures:
    def test_no_geometry(_, assert_contains):
        records = [{"geometry": None}]
        with pytest.raises(GeometryError) as error:
            features.parse_features(records, None, ["Polygon"], None, None)
        assert_contains(error, "Feature[0] does not have a geometry")

    def test_wrong_type(_, assert_contains):
        records = [
            {
                "geometry": {
                    "type": "Point",
                    "coordinates": (1, 2),
                }
            }
        ]
        with pytest.raises(GeometryError) as error:
            features.parse_features(
                records,
                field=None,
                geometries=["Polygon", "MultiPolygon"],
                crs=None,
                window=None,
            )
        assert_contains(
            error,
            "must have a Polygon or MultiPolygon geometry",
            "feature[0] has a Point geometry",
        )

    def test_invalid_polygon(_):
        records = [
            {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [1, 2],
                }
            }
        ]
        with pytest.raises(PolygonError):
            features.parse_features(
                records, field=None, geometries=["Polygon"], crs=None, window=None
            )

    def test_invalid_point(_):
        records = [{"geometry": {"type": "Point", "coordinates": [1, 2, 3]}}]
        with pytest.raises(PointError):
            features.parse_features(
                records, field=None, geometries=["Point"], crs=None, window=None
            )

    def test_points(_):
        geom1 = {"type": "Point", "coordinates": [0, 0]}
        geom2 = {"type": "Point", "coordinates": [10, 20]}
        records = [{"geometry": geom1}, {"geometry": geom2}]
        output, bounds = features.parse_features(
            records, None, ["Point"], crs=None, window=None
        )
        assert output == [(geom1, True), (geom2, True)]
        assert bounds == BoundingBox.from_dict(
            {"left": 0, "right": 10, "top": 20, "bottom": 0}
        )

    def test_multipoints(_):
        geom1 = {"type": "MultiPoint", "coordinates": [[0, 0], [1, 2]]}
        geom2 = {"type": "MultiPoint", "coordinates": [[5, 10], [10, 20]]}
        records = [{"geometry": geom1}, {"geometry": geom2}]
        output, bounds = features.parse_features(
            records, None, ["MultiPoint"], crs=None, window=None
        )
        assert output == [(geom1, True), (geom2, True)]
        assert bounds == BoundingBox.from_dict(
            {"left": 0, "right": 10, "top": 20, "bottom": 0}
        )

    def test_polygons(_):
        geom1 = {
            "type": "Polygon",
            "coordinates": [
                [(1, 2), (3, 4), (5, 6), (7, 8), (1, 2)],
                [(1, 2), (2, 2), (2, 1), (1, 2)],
            ],
        }
        geom2 = {"type": "Polygon", "coordinates": [[(1, 2), (3, 4), (5, 6), (1, 2)]]}
        records = [{"geometry": geom1}, {"geometry": geom2}]
        output, bounds = features.parse_features(records, None, ["Polygon"], None, None)
        assert output == [(geom1, True), (geom2, True)]
        assert bounds == BoundingBox.from_dict(
            {"left": 1, "right": 7, "top": 8, "bottom": 2}
        )

    def test_multipolygons(_):
        geom1 = {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [(1, 2), (3, 4), (5, 6), (7, 8), (1, 2)],
                    [(1, 2), (2, 2), (2, 1), (1, 2)],
                ]
            ],
        }
        records = [{"geometry": geom1}, {"geometry": geom1}]
        output, bounds = features.parse_features(
            records, None, ["MultiPolygon"], None, None
        )
        assert output == [(geom1, True), (geom1, True)]
        assert bounds == BoundingBox.from_dict(
            {"left": 1, "right": 7, "top": 8, "bottom": 2}
        )

    def test_field(_):
        geom1 = {"type": "Point", "coordinates": [0, 0]}
        geom2 = {"type": "Point", "coordinates": [10, 20]}
        records = [
            {"geometry": geom1, "properties": {"test": 5}},
            {"geometry": geom2, "properties": {"test": 19}},
        ]
        output, bounds = features.parse_features(records, "test", ["Point"], None, None)
        assert output == [(geom1, 5), (geom2, 19)]
        assert bounds == BoundingBox.from_dict(
            {"left": 0, "right": 10, "top": 20, "bottom": 0}
        )

    def test_polygon_window(_):
        geom1 = {
            "type": "Polygon",
            "coordinates": [
                [(2, 2), (2, 7), (6, 7), (6, 2), (2, 2)],
                [(2, 2), (2, 4), (4, 4), (4, 2), (2, 2)],  # hole in upper-left
            ],
        }
        geom2 = {
            "type": "Polygon",
            "coordinates": [[(4, 6), (4, 9), (9, 9), (9, 6), (4, 6)]],
        }
        records = [{"geometry": geom1}, {"geometry": geom2}]
        crs = CRS(4326)
        window = BoundingBox(5, 1, 7, 4, crs)
        output, bounds = features.parse_features(
            records, None, ["Polygon"], crs, window
        )
        assert output == [(geom1, True)]
        assert bounds == BoundingBox.from_dict(
            {"left": 2, "right": 6, "top": 7, "bottom": 2, "crs": crs}
        )

    def test_point_window(_):
        geom1 = {"type": "Point", "coordinates": [2, 3]}
        geom2 = {"type": "Point", "coordinates": [9, 9]}
        geom3 = {"type": "Point", "coordinates": [4, 4]}
        records = [{"geometry": geom1}, {"geometry": geom2}, {"geometry": geom3}]
        crs = CRS(4326)
        window = BoundingBox(0, 0, 4, 4, crs)
        output, bounds = features.parse_features(records, None, ["Point"], crs, window)
        assert output == [(geom1, True), (geom3, True)]
        assert bounds == BoundingBox.from_dict(
            {"left": 2, "right": 4, "top": 4, "bottom": 3, "crs": crs}
        )


class TestInit:
    def test_valid(_, fraster):
        a = FeatureFile("polygon", fraster, 1, "ShapeFile", "test")
        assert isinstance(a, FeatureFile)
        assert a.type == "polygon"
        assert a.path == fraster.resolve()
        assert a.layer == 1
        assert a.driver == "ShapeFile"
        assert a.encoding == "test"

    def test_nones(_, fraster):
        a = FeatureFile("polygon", fraster, None, None, None)
        assert a.type == "polygon"
        assert a.path == fraster.resolve()
        assert a.layer is None
        assert a.driver is None
        assert a.encoding is None

    def test_invalid(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            FeatureFile("polygon", fraster, None, 5, None)
        assert_contains(error, "driver")

    def test_missing(_):
        with pytest.raises(FileNotFoundError):
            FeatureFile("polygon", "not-a-file", None, None, None)


class TestEnter:
    def test_invalid(_, fraster, assert_contains):
        with pytest.raises(FeatureFileError) as error:
            FeatureFile("polygon", fraster, None, None, None).__enter__()
        assert_contains(error, "Could not read data from the polygon feature file")

    def test_valid(_, polygons, crs):
        with FeatureFile("polygon", polygons, None, None, None) as file:
            assert isinstance(file.file, Collection)
            assert file.crs == crs
            assert file.file.closed == False


class TestExit:
    def test(_, polygons):
        with FeatureFile("polygon", polygons, None, None, None) as file:
            pass
        assert file.file.closed == True


class TestParseField:
    def test(_, polygons):
        with FeatureFile("polygons", polygons, None, None, None) as file:
            dtype, nodata, fill = file.parse_field("test", 5)
            assert dtype == float
            assert isnan(nodata)
            assert fill == 5


class TestValidateMeters:
    def test_neither(_, polygons):
        with FeatureFile("polygons", polygons, None, None, None) as file:
            file.validate_meters(None, (10, 10), False)

    def test_meters_transform(_, polygons):
        with FeatureFile("polygons", polygons, None, None, None) as file:
            file.validate_meters(None, Transform(1, 2, 3, 4), True)

    def test_meters_valid(_, polygons):
        with FeatureFile("polygons", polygons, None, None, None) as file:
            file.validate_meters(CRS(4326), (10, 10), True)

    def test_meters_invalid(_, polygons, assert_contains):
        with pytest.raises(MissingCRSError) as error:
            with FeatureFile("polygon", polygons, None, None, None) as file:
                file.validate_meters(None, (10, 10), True)
        assert_contains(
            error,
            "Cannot convert resolution from meters because the polygon feature file does not have a CRS",
        )


class TestParseResolution:
    @pytest.mark.parametrize("meters", (True, False))
    def test_transform(_, meters):
        crs = CRS(4326)
        res = Transform(1, 2, 3, 4, crs)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        out1, out2 = FeatureFile.parse_resolution(res, meters, crs, bounds)
        assert out1 == (1, 2)
        assert out2 == crs

    def test_reproject_transform(_):
        crs = CRS(26910)
        res = Transform(1, 2, 3, 4, 26911)
        bounds = BoundingBox(0, 100, 500, 1000, crs)
        out1, out2 = FeatureFile.parse_resolution(res, False, crs, bounds)
        expected = (0.997261140611954, 1.9945226908862739)
        assert np.allclose(out1, expected)
        assert out2 == crs

    def test_inherit_crs(_):
        crs = CRS(4326)
        res = Transform(1, 2, 3, 4, crs)
        bounds = BoundingBox(1, 2, 3, 4, None)
        output = FeatureFile.parse_resolution(res, False, None, bounds)
        assert output == ((1, 2), crs)

    def test_meters(_):
        crs = CRS(4326)
        res = (10, 10)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        out1, out2 = FeatureFile.parse_resolution(res, True, crs, bounds)
        assert out1 == (9.005557863254549e-05, 8.993216059187306e-05)
        assert out2 == crs

    def test_no_meters(_):
        crs = CRS(4326)
        res = (10, 10)
        bounds = BoundingBox(1, 2, 3, 4, crs)
        output = FeatureFile.parse_resolution(res, False, crs, bounds)
        assert output == ((10, 10), crs)


class TestLoad:
    def test(_, polygons):
        with FeatureFile("polygon", polygons, None, None, None) as file:
            output = file.load()
        assert isinstance(output, list)
        print(type(output[0]))
        for elt in output:
            assert isinstance(elt, fiona.model.Feature)


class TestExtent:
    def test(_):
        bounds = BoundingBox(0, 0, 10, 200)
        resolution = (5, 10)
        out1, out2 = FeatureFile.extent(bounds, resolution)
        assert out1 == Transform(5, -10, 0, 200)
        assert out2 == (20, 2)


class TestProcess:
    def test_polygons(_, polygons, crs):
        with FeatureFile("polygon", polygons, None, None, None) as file:
            feats, outcrs, transform, shape, dtype, nodata, fill = file.process(
                "test", 5, (1, 1), False, None
            )
        assert isinstance(feats, list)
        assert len(feats) == 2
        assert outcrs == crs
        assert transform == Transform(1, -1, 2, 9)
        assert shape == (7, 7)
        assert dtype == float
        assert isnan(nodata)
        assert fill == 5

    def test_points(_, points, crs):
        with FeatureFile("point", points, None, None, None) as file:
            feats, outcrs, transform, shape, dtype, nodata, fill = file.process(
                "test", 5, (1, 1), False, None
            )
        assert isinstance(feats, list)
        assert len(feats) == 3
        assert outcrs == crs
        assert transform == Transform(1, -1, 1, 6)
        assert shape == (4, 4)
        assert dtype == float
        assert isnan(nodata)
        assert fill == 5
