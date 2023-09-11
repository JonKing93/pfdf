from math import sqrt

import numpy as np
import pytest
from affine import Affine
from geojson import FeatureCollection
from numpy import isnan, nan
from pysheds.grid import Grid
from rasterio.crs import CRS
from shapely import LineString

from pfdf import watershed
from pfdf.raster import Raster, pysheds_raster

#####
# Testing fixtures
#####


@pytest.fixture
def network_flow():
    flow = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 3, 3, 7, 3, 0],
            [0, 8, 3, 3, 7, 5, 0],
            [0, 5, 7, 3, 6, 5, 0],
            [0, 5, 1, 7, 1, 1, 0],
            [0, 5, 5, 7, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(flow, nodata=0)


@pytest.fixture
def network_mask():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 0, 1, 0, 1, 1, 0],
            [0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )


@pytest.fixture
def segments():
    segments = [
        [[1, 1], [1, 2], [2, 3], [2, 4], [3, 4]],
        [[4, 1], [4, 2]],
        [[5, 1], [5, 0]],
        [[2, 2], [2, 1], [2, 0]],
        [[5, 2], [4, 2]],
        [[4, 2], [4, 3]],
        [[1, 3], [0, 3]],
        [[3, 3], [3, 2], [3, 1], [3, 0]],
        [[5, 3], [4, 3]],
        [[4, 3], [3, 4]],
        [[3, 4], [3, 5], [3, 6]],
        [[1, 4], [0, 4]],
        [[4, 4], [5, 4], [6, 4]],
        [[2, 5], [1, 5], [0, 5]],
        [[4, 5], [5, 5], [6, 5]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def masked_segments(segments):
    return [
        segment for s, segment in enumerate(segments) if s in [0, 1, 2, 4, 5, 8, 9, 10]
    ]


# @pytest.fixture
# def split_segments(masked_segments):


#####
# Internal functions
#####


def test_to_pysheds():
    a = np.arange(10).reshape(2, 5)
    crs = CRS.from_epsg(4000)
    transform = Affine(0.03, 0, -4, 0, 0.03, -3)
    raster = Raster.from_array(a, nodata=-999, crs=crs, transform=transform)
    raster, metadata = watershed._to_pysheds(raster)

    assert isinstance(raster, pysheds_raster)
    assert raster.affine == transform
    assert raster.crs == crs
    assert raster.nodata == -999
    assert np.array_equal(raster, a)

    assert isinstance(metadata, dict)
    assert list(metadata.keys()) == ["transform", "crs"]
    assert metadata["transform"] == transform
    assert metadata["crs"] == crs


def test_geojson_to_shapely(network_flow, segments):
    flow = network_flow.as_pysheds()
    mask = np.ones(flow.shape, dtype=bool)
    mask = Raster(mask).as_pysheds()
    grid = Grid.from_raster(flow)
    network = grid.extract_river_network(flow, mask, **watershed._FLOW_OPTIONS)
    assert isinstance(network, FeatureCollection)
    output = watershed._geojson_to_shapely(network)
    print(output)
    print(segments)
    assert output == segments


class TestSplit:
    def test_short(_):
        aline = LineString([[0, 0], [0, 1], [0, 2]])
        output = watershed._split(aline, max_length=10)
        assert output == [aline]

    def test_long(_):
        aline = LineString([[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6]])
        expected = [
            LineString([[0, 0], [0, 1], [0, 2]]),
            LineString([[0, 2], [0, 3], [0, 4]]),
            LineString([[0, 4], [0, 5], [0, 6]]),
        ]
        output = watershed._split(aline, max_length=2)
        assert output == expected


def test_split_segments():
    segments = [
        LineString([[0, 0], [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6]]),
        LineString([[1, 0], [1, 1], [1, 2], [1, 3], [1, 4]]),
        LineString([[0, 0], [0, 1]]),
    ]
    output = watershed._split_segments(segments, max_length=2)
    expected = [
        LineString([[0, 0], [0, 1], [0, 2]]),
        LineString([[0, 2], [0, 3], [0, 4]]),
        LineString([[0, 4], [0, 5], [0, 6]]),
        LineString([[1, 0], [1, 1], [1, 2]]),
        LineString([[1, 2], [1, 3], [1, 4]]),
        LineString([[0, 0], [0, 1]]),
    ]
    print(output)
    print(expected)
    assert output == expected


#####
# User Functions
#####


class TestFlow:
    def test(_):
        dem = np.array(
            [
                [1, 1, 1, 4, 5],
                [1, 1, 1, 0, 0],
                [1, 1, 1, 0, 0],
                [1, 1, 0, 4, 5],
                [1, 2, 3, 4, -999],
            ]
        )
        expected = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 3, 1, 1, 0],
                [0, 8, 1, 1, 0],
                [0, 1, 2, 3, 0],
                [0, 0, 0, 0, 0],
            ]
        )
        dem = Raster.from_array(dem, nodata=-999)
        flow = watershed.flow(dem)
        assert isinstance(flow, Raster)
        assert np.array_equal(flow.values, expected)
        assert flow.nodata == 0
        assert flow.crs is None
        assert flow.transform is None


class TestSlopes:
    def test(_):
        dem = np.array(
            [
                [1, 1, 1, 1, 1],
                [1, 4, 3, 2, 1],
                [1, 6, 20, 100, 1],
                [1, 8, 50, 10, 1],
                [1, 1, 1, 1, 1],
            ]
        )
        flow = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0],
                [0, 3, 8, 6, 0],
                [0, 3, 3, 1, 0],
                [0, 0, 0, 0, 0],
            ]
        )
        flow = Raster.from_array(flow, nodata=0)
        expected = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0],
                [0, 2, 10 / sqrt(2), 50 / sqrt(2), 0],
                [0, 2, 30, 9, 0],
                [0, 0, 0, 0, 0],
            ]
        )
        slopes = watershed.slopes(dem, flow)
        assert isinstance(slopes, Raster)
        assert np.array_equal(slopes.values, expected)
        assert np.isnan(slopes.nodata)
        assert flow.crs is None
        assert flow.transform is None


class TestRelief:
    def test(_):
        dem = np.array(
            [
                [0.0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 470, 480, 490, 500, 490, 480, 470, 0],
                [0, 599, 600, 650, 700, 650, 600, 599, 0],
                [0, 750, 900, 940, 950, 940, 900, 750, 0],
                [0, 800, 990, 998, 999, 998, 990, 800, 0],
                [0, 751, 901, 941, 951, 941, 901, 751, 0],
                [0, 599, 600, 650, 700, 650, 600, 599, 0],
                [0, 470, 480, 490, 500, 490, 480, 470, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
            ]
        )
        dem = Raster.from_array(dem, nodata=nan)
        expected = np.array(
            [
                [nan, nan, nan, nan, nan, nan, nan, nan, nan],
                [nan, 0.0, 518.0, 450.0, 499.0, 450.0, 518.0, 0.0, nan],
                [nan, 0.0, 398.0, 290.0, 299.0, 290.0, 398.0, 0.0, nan],
                [nan, 0.0, 98.0, 0.0, 49.0, 0.0, 98.0, 0.0, nan],
                [nan, 190.0, 0.0, 0.0, 0.0, 0.0, 0.0, 190.0, nan],
                [nan, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, nan],
                [nan, 0.0, 301.0, 291.0, 251.0, 291.0, 301.0, 0.0, nan],
                [nan, 0.0, 421.0, 451.0, 451.0, 451.0, 421.0, 0.0, nan],
                [nan, nan, nan, nan, nan, nan, nan, nan, nan],
            ]
        )
        flow = watershed.flow(dem)
        print(flow.values)
        relief = watershed.relief(dem, flow)

        print(relief.values)
        print(expected)

        assert isinstance(relief, Raster)
        assert np.array_equal(relief.values, expected, equal_nan=True)
        assert isnan(relief.nodata)
        assert relief.crs is None
        assert relief.transform is None


class TestAccumulation:
    flow = np.array(
        [
            [7, 1, 3, 0],
            [7, 3, 7, 7],
            [7, 3, 7, 0],
        ]
    )
    weights = np.array(
        [
            [1, 6, 7, 2],
            [2, 5, 8, -999],
            [3, 4, 9, -999],
        ]
    )
    mask = np.array(
        [
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 0, 0, 1],
        ]
    )

    flow = Raster.from_array(flow, nodata=0)
    weights = Raster.from_array(weights, nodata=-999)
    mask = Raster(mask)

    def check(_, acc, expected):
        assert isinstance(acc, Raster)
        assert np.array_equal(acc.values, expected, equal_nan=True)
        assert isnan(acc.nodata)
        assert acc.crs is None
        assert acc.transform is None

    def test_basic(self):
        acc = watershed.accumulation(self.flow)
        expected = np.array(
            [
                [1, 3, 4, nan],
                [2, 2, 1, 1],
                [3, 1, 2, nan],
            ]
        )
        self.check(acc, expected)

    def test_weighted(self):
        acc = watershed.accumulation(self.flow, self.weights)
        expected = np.array(
            [
                [1, 15, 22, nan],
                [3, 9, 8, nan],
                [6, 4, 17, nan],
            ]
        )
        self.check(acc, expected)

    def test_masked(self):
        acc = watershed.accumulation(self.flow, mask=self.mask)
        expected = np.array(
            [
                [0, 1, 2, nan],
                [1, 0, 1, 1],
                [2, 0, 1, nan],
            ]
        )
        self.check(acc, expected)

    def test_weighted_mask(self):
        acc = watershed.accumulation(self.flow, self.weights, self.mask)
        expected = np.array(
            [
                [0, 6, 13, nan],
                [2, 0, 8, nan],
                [5, 0, 8, nan],
            ]
        )
        self.check(acc, expected)


class TestCatchment:
    flow = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 3, 3, 7, 3, 0],
            [0, 8, 3, 3, 7, 5, 0],
            [0, 5, 7, 3, 6, 5, 0],
            [0, 5, 1, 7, 1, 1, 0],
            [0, 5, 5, 7, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    flow = Raster.from_array(flow, nodata=0)

    @pytest.mark.parametrize(
        "row,column,expected",
        (
            (
                5,
                3,
                np.array(
                    [
                        [0, 0, 0, 0, 0, 0, 0],
                        [0, 1, 0, 0, 1, 0, 0],
                        [0, 1, 0, 0, 1, 1, 0],
                        [0, 0, 1, 0, 1, 1, 0],
                        [0, 0, 1, 1, 0, 0, 0],
                        [0, 0, 0, 1, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0],
                    ]
                ).astype(bool),
            ),
            (
                3,
                4,
                np.array(
                    [
                        [0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 1, 1, 0],
                        [0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0, 0, 0],
                    ]
                ).astype(bool),
            ),
        ),
    )
    def test(self, row, column, expected):
        output = watershed.catchment(self.flow, row, column)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, expected)
        assert output.dtype == bool
        assert output.nodata is None
        assert output.crs is None
        assert output.transform is None


class TestNetwork:
    def test_all(_, network_flow, segments):
        mask = np.ones(network_flow.shape, dtype=bool)
        output = watershed.network(network_flow, mask)
        assert output == segments

    def test_masked(_, network_flow, network_mask, masked_segments):
        output = watershed.network(network_flow, network_mask)
        assert output == masked_segments

    def test_split(self):
        flow = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0],
            ]
        )
        flow = Raster.from_array(flow, nodata=0)
        mask = np.ones(flow.shape, bool)

        output = watershed.network(flow, mask, max_length=2)
        expected = [
            LineString([[1, 1], [2, 1], [3, 1]]),
            LineString([[3, 1], [4, 1], [5, 1]]),
            LineString([[5, 1], [6, 1], [7, 1]]),
            LineString([[1, 2], [2, 2], [3, 2]]),
            LineString([[3, 2], [4, 2], [5, 2]]),
            LineString([[5, 2], [6, 2], [7, 2]]),
        ]
        assert output == expected
