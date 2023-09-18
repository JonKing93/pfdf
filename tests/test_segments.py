from math import isnan, nan
from pathlib import Path

import fiona
import geojson
import numpy as np
import pytest
from affine import Affine
from rasterio.crs import CRS
from shapely import LineString

from pfdf._utils.kernel import Kernel
from pfdf.errors import (
    DimensionError,
    RasterCrsError,
    RasterShapeError,
    RasterTransformError,
    ShapeError,
)
from pfdf.raster import Raster
from pfdf.segments import Segments

#####
# Testing Utilities
#####


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


@pytest.fixture
def transform():
    return Affine(1, 0, 0, 0, 1, 0)


@pytest.fixture
def dem():
    dem = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 61, 10, 10, 50, 10, 0],
            [0, 51, 61, 61, 40, 30, 0],
            [0, 41, 31, 99, 20, 30, 0],
            [0, 19, 21, 10, 22, 20, 0],
            [0, 15, 19, 10, 20, 16, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(dem)


@pytest.fixture
def flow(transform):
    flow = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 3, 3, 7, 3, 0],
            [0, 7, 3, 3, 7, 3, 0],
            [0, 1, 7, 3, 6, 5, 0],
            [0, 5, 1, 7, 1, 1, 0],
            [0, 5, 5, 7, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(flow, nodata=0, transform=transform)


@pytest.fixture
def values(flow):
    values = flow.values
    values[values == 3] = 0
    return Raster.from_array(values, nodata=0)


@pytest.fixture
def mask():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 1, 0, 1, 1, 0],
            [0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype(bool)


@pytest.fixture
def mask2(mask):
    mask[:, 1:4] = False
    return mask


@pytest.fixture
def segments(flow, mask):
    return Segments(flow, mask)


@pytest.fixture
def stream_raster():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 2, 3, 0],
            [0, 1, 0, 0, 2, 3, 0],
            [0, 1, 1, 0, 5, 4, 0],
            [0, 0, 1, 6, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )


@pytest.fixture
def linestrings():
    segments = [
        [[1, 1], [1, 2], [1, 3], [2, 3], [2, 4], [3, 4]],
        [[4, 1], [4, 2], [4, 3]],
        [[5, 2], [5, 1], [5, 0]],
        [[5, 3], [4, 3]],
        [[4, 3], [3, 4]],
        [[3, 4], [3, 5], [3, 6]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def indices():
    return {
        1: ([1, 2, 3, 3, 4], [1, 1, 1, 2, 2]),
        2: ([1, 2], [4, 4]),
        3: ([2, 1], [5, 5]),
        4: ([3], [5]),
        5: ([3], [4]),
        6: ([4, 5], [3, 3]),
    }


@pytest.fixture
def npixels():
    return np.array([5, 2, 2, 1, 4, 11])


@pytest.fixture
def linestrings_split():
    segments = [
        [[1, 1], [1, 2], [1, 3], [1.5, 3]],
        [[1.5, 3], [2, 3], [2, 4], [3, 4]],
        [[4, 1], [4, 2], [4, 3]],
        [[5, 2], [5, 1], [5, 0]],
        [[5, 3], [4, 3]],
        [[4, 3], [3, 4]],
        [[3, 4], [3, 5], [3, 6]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def indices_split():
    return {
        1: ([1, 2, 3], [1, 1, 1]),
        2: ([3, 4], [2, 2]),
        3: ([1, 2], [4, 4]),
        4: ([2, 1], [5, 5]),
        5: ([3], [5]),
        6: ([3], [4]),
        7: ([4, 5], [3, 3]),
    }


@pytest.fixture
def linestrings245(linestrings):
    return [linestrings[1], linestrings[3], linestrings[4]]


@pytest.fixture
def indices245(indices):
    return {key: value for key, value in indices.items() if key in [2, 4, 5]}


@pytest.fixture
def npixels245(npixels):
    return npixels[[1, 3, 4]]


#####
# Dunders
#####


class TestInit:
    def test_any_length(_, flow, mask, linestrings, indices, npixels):
        segments = Segments(flow, mask)
        assert segments._flow == flow
        assert segments._segments == linestrings
        assert np.array_equal(segments._npixels, npixels)
        assert segments._indices == indices

    def test_split_point_upstream(_, flow, mask, linestrings_split, indices_split):
        segments = Segments(flow, mask, 2.5)
        assert segments._flow == flow
        assert segments._segments == linestrings_split
        npixels = np.array([3, 5, 2, 2, 1, 4, 11])
        assert np.array_equal(segments._npixels, npixels)
        assert segments._indices == indices_split

    def test_no_transform(_, flow, mask):
        flow = Raster.from_array(flow.values)
        with pytest.raises(RasterTransformError) as error:
            Segments(flow, mask)
        assert_contains(
            error, "The flow direction raster must have (affine) transform metadata."
        )

    def test_short_maxlength(_, flow, mask):
        with pytest.raises(ValueError) as error:
            Segments(flow, mask, max_length=1)
        assert_contains(error, "max_length", "diagonal")

    def test_split_point_downstream(_, flow, mask, transform):
        # Note that this requires flow to proceed in the opposite direction as
        # the pixel indices

        flow = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 5, 5, 5, 5, 5, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        flow = Raster.from_array(flow, nodata=0, transform=transform)
        mask = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        segments = Segments(flow, mask, max_length=2.5)

        linestrings = [
            LineString([[5, 1], [4, 1], [3, 1], [2.5, 1]]),
            LineString([[2.5, 1], [2, 1], [1, 1], [0, 1]]),
        ]
        indices = {
            1: ([1, 1, 1], [5, 4, 3]),
            2: ([1, 1], [2, 1]),
        }
        npixels = np.array([3, 5])

        assert segments._flow == flow
        assert segments._segments == linestrings
        assert segments._indices == indices
        assert np.array_equal(segments._npixels, npixels)


def test_len(segments):
    assert len(segments) == 6


def test_str(segments):
    assert str(segments) == "A network of 6 stream segments."


#####
# Properties
#####


def test_segments(segments, linestrings):
    assert segments.segments == linestrings


def test_length(segments):
    assert segments.length == 6


def test_indices(segments, indices):
    assert segments.indices == indices


def test_ids(segments, indices):
    expected = np.array(list(indices.keys()))
    assert np.array_equal(segments.ids, expected)


def test_flow(segments, flow):
    assert segments.flow == flow


def test_raster_shape(segments, flow):
    assert segments.raster_shape == flow.shape


def test_crs(segments, flow):
    assert segments.crs == flow.crs


def test_transform(segments, flow):
    assert segments.transform == flow.transform


def test_resolution(segments, flow):
    assert segments.resolution == flow.resolution


def test_pixel_area(segments, flow):
    assert segments.pixel_area == flow.pixel_area


def test_npixels(segments, npixels):
    assert np.array_equal(segments.npixels, npixels)


#####
# Stream Raster
#####


def test_raster(segments, stream_raster):
    output = segments.raster()
    assert isinstance(output, Raster)
    assert output.nodata == 0
    assert output.crs == segments.crs
    assert output.transform == segments.transform
    assert np.array_equal(output.values, stream_raster)


def test_outlets(segments):
    output = segments.outlets()
    expected = [(4, 2), (2, 4), (1, 5), (3, 5), (3, 4), (5, 3)]
    assert output == expected


#####
# Validation
#####


class TestValidate:
    def test_valid_raster(_, segments, flow):
        output = segments._validate(flow, "")
        assert output == flow

    def test_default_spatial(_, segments, flow):
        input = Raster.from_array(flow.values, nodata=0)
        output = segments._validate(input, "")
        assert output == flow

    def test_bad_shape(_, segments, flow):
        a = np.arange(10).reshape(2, 5)
        input = Raster.from_array(a, crs=flow.crs, transform=flow.transform)
        with pytest.raises(RasterShapeError) as error:
            segments._validate(input, "test name")
        assert_contains(error, "test name")

    def test_bad_transform(_, segments, flow):
        flow._transform = Affine(9, 0, 0, 0, 9, 0)
        with pytest.raises(RasterTransformError) as error:
            segments._validate(flow, "test name")
        assert_contains(error, "test name")

    def test_bad_crs(_, segments, flow):
        flow._crs = CRS.from_epsg(4000)
        with pytest.raises(RasterCrsError) as error:
            segments._validate(flow, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize(
        "input, error",
        (
            (5, TypeError),
            (np.ones((3, 3, 3)), DimensionError),
        ),
    )
    def test_invalid_raster(_, segments, input, error):
        with pytest.raises(error) as e:
            segments._validate(input, "test name")
        assert_contains(e, "test name")


class TestValidateIndices:
    def test_valid_ids(_, segments):
        ids = [2, 4, 5]
        expected = np.array([0, 1, 0, 1, 1, 0], dtype=bool)
        output = segments._validate_indices(ids, None)
        assert np.array_equal(output, expected)

    def test_valid_indices(_, segments):
        indices = np.ones(6).astype(bool)
        output = segments._validate_indices(None, indices)
        assert np.array_equal(output, indices)

    def test_both(_, segments):
        ids = [2, 4, 5]
        indices = np.zeros(6, bool)
        indices[[0, 1]] = True
        output = segments._validate_indices(ids, indices)
        expected = np.array([1, 1, 0, 1, 1, 0], dtype=bool)
        assert np.array_equal(output, expected)

    def test_neither(_, segments):
        output = segments._validate_indices(None, None)
        expected = np.zeros(6, bool)
        assert np.array_equal(output, expected)

    def test_duplicate_ids(_, segments):
        ids = [1, 1, 1, 1, 1]
        output = segments._validate_indices(ids, None)
        expected = np.zeros(6, bool)
        expected[0] = 1
        assert np.array_equal(output, expected)

    def test_booleanish_indices(_, segments):
        indices = np.ones(6, dtype=float)
        output = segments._validate_indices(None, indices)
        assert np.array_equal(output, indices.astype(bool))

    def test_not_boolean_indices(_, segments):
        indices = np.arange(6)
        with pytest.raises(ValueError) as error:
            segments._validate_indices(None, indices)
        assert_contains(error, "indices", "0 or 1")

    def test_indices_wrong_length(_, segments):
        indices = np.ones(10)
        with pytest.raises(ShapeError) as error:
            segments._validate_indices(None, indices)
        assert_contains(error, "indices", "6")

    def test_invalid_ids(_, segments):
        ids = [1, 2, 7]
        with pytest.raises(KeyError) as error:
            segments._validate_indices(ids, None)
        assert_contains(error, "ID 2 (value=7)")


class TestValidateProperties:
    def test_valid(_, segments):
        props = {"ones": np.ones(6), "twos": [2, 2, 2, 2, 2, 2]}
        output = segments._validate_properties(props)
        expected = {"ones": np.ones(6), "twos": np.full(6, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])

    def test_none(_, segments):
        output = segments._validate_properties(None)
        assert output == {}

    def test_convert_to_float(_, segments):
        props = {
            "bool": np.ones(6, bool),
            "int": np.ones(6, int),
            "float": np.ones(6, float),
        }
        output = segments._validate_properties(props)
        assert list(output.keys()) == list(props.keys())
        for key in output.keys():
            assert output[key].dtype == float

    def test_not_dict(_, segments):
        with pytest.raises(TypeError) as error:
            segments._validate_properties("invalid")
        assert_contains(error, "properties must be a dict")

    def test_bad_keys(_, segments):
        props = {1: np.ones(6)}
        with pytest.raises(ValueError) as error:
            segments._validate_properties(props)
        assert_contains(error, "keys")

    def test_not_numeric(_, segments):
        props = {"values": ["a", "b", "c", "d", "e", "f"]}
        with pytest.raises(TypeError) as error:
            segments._validate_properties(props)
        assert_contains(error, "properties['values']")

    def test_wrong_length(_, segments):
        props = {"values": np.ones(7)}
        with pytest.raises(ShapeError) as error:
            segments._validate_properties(props)
        assert_contains(error, "properties['values']")


#####
# Utilities
#####


class TestPreallocate:
    def test_basic(_, segments):
        output = segments._preallocate()
        assert isinstance(output, np.ndarray)
        assert output.shape == (6,)
        assert output.dtype == float

    def test_type(_, segments):
        output = segments._preallocate(dtype=int)
        assert isinstance(output, np.ndarray)
        assert output.shape == (6,)
        assert output.dtype == int


class TestAccumulation:
    def test_init(_, segments, npixels):
        segments._npixels = None
        output = segments._accumulation()
        assert np.array_equal(output, npixels)

    def test_basic(_, segments):
        output = segments._accumulation()
        assert np.array_equal(output, segments.npixels)

    def test_weights(_, segments, flow):
        output = segments._accumulation(weights=flow)
        expected = np.array([23, 14, 6, 5, 25, 62])
        assert np.array_equal(output, expected)

    def test_mask(_, segments, mask):
        mask[:, 3:] = False
        expected = np.array([5, 0, 0, 0, 0, 5])
        output = segments._accumulation(mask=mask)
        assert np.array_equal(output, expected)


def test_outlet_values(segments, flow):
    output = segments._outlet_values(flow)
    expected = np.array([1, 7, 3, 5, 6, 7])
    assert np.array_equal(output, expected)


#####
# Confinement Angles
#####


class TestPixelSlopes:
    dem = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 0, 4, 0, 9, 0],
            [0, 0, 6, 5, 8, 0, 0],
            [0, 2, 3, 1, 2, 3, 0],
            [0, 0, 8, 4, 7, 0, 0],
            [0, 9, 0, 5, 0, 6, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    inputs = {
        "lengths": {"horizontal": 2, "vertical": 3, "diagonal": 4},
        "rowcol": [3, 3],
        "kernel": Kernel(neighborhood=2, nRows=7, nCols=7),
        "dem": Raster.from_array(dem, nodata=0),
    }

    def test_horizontal(self):
        output = Segments._pixel_slopes(flow=1, **self.inputs)
        expected = np.array([4 / 3, 4 / 3]).reshape(1, 2)
        assert np.array_equal(output, expected)

    def test_vertical(self):
        output = Segments._pixel_slopes(flow=3, **self.inputs)
        expected = np.ones(2, float).reshape(1, 2)
        assert np.array_equal(output, expected)

    @pytest.mark.parametrize("flow,value", ((2, 6 / 4), (4, 2)))
    def test_diagonal(self, flow, value):
        output = Segments._pixel_slopes(flow, **self.inputs)
        expected = np.array([value, value]).reshape(1, 2)
        assert np.array_equal(output, expected)


class TestSegmentConfinement:
    def test_standard(_, segments, dem):
        pixels = ([1, 2, 3, 3, 4], [1, 1, 1, 2, 2])
        lengths = {"horizontal": 2, "vertical": 3, "diagonal": 4}
        kernel = Kernel(2, 7, 7)
        output = segments._segment_confinement(pixels, lengths, kernel, dem)

        slopes = np.array(
            [
                [-61 / 2, -51 / 2],
                [-51 / 2, 5],
                [-22 / 3, 20 / 3],
                [5, 34],
                [-2 / 3, 40 / 3],
            ]
        )
        angles = np.arctan(slopes)
        angles = np.mean(angles, axis=0)
        theta = np.sum(angles)
        expected = 180 - np.degrees(theta)

        assert output == expected

    def test_nan_flow(_, segments, dem):
        segments._flow._values[1, 1] = 0
        pixels = ([1, 2, 3, 3, 4], [1, 1, 1, 2, 2])
        lengths = {"horizontal": 2, "vertical": 3, "diagonal": 4}
        kernel = Kernel(2, 7, 7)
        output = segments._segment_confinement(pixels, lengths, kernel, dem)
        assert isnan(output)


class TestConfinement:
    def test_basic(_, segments, dem):
        output = segments.confinement(dem, neighborhood=2)
        expected = np.array(
            [
                175.26275123,
                264.20279455,
                175.71489195,
                258.69006753,
                93.94635581,
                21.80295443,
            ]
        )
        assert np.allclose(output, expected)

    def test_nan_flow(_, segments, dem):
        segments._flow._values[1, 1] = 0
        output = segments.confinement(dem, neighborhood=2)
        expected = np.array(
            [nan, 264.20279455, 175.71489195, 258.69006753, 93.94635581, 21.80295443]
        )
        assert np.allclose(output, expected, equal_nan=True)

    def test_nan_dem_center(_, segments, dem):
        dem._nodata = 41
        output = segments.confinement(dem, neighborhood=2)
        expected = np.array(
            [nan, 264.20279455, 175.71489195, 258.69006753, 93.94635581, 21.80295443]
        )
        assert np.allclose(output, expected, equal_nan=True)

    def test_nan_dem_adjacent(_, segments, dem):
        dem._nodata = 19
        output = segments.confinement(dem, neighborhood=2)
        expected = np.array(
            [nan, 264.20279455, 175.71489195, 258.69006753, 93.94635581, nan]
        )
        assert np.allclose(output, expected, equal_nan=True)

    def test_factor(_, segments, dem):
        output = segments.confinement(dem, neighborhood=2, factor=10)
        expected = np.array(
            [
                185.45654969,
                233.5188839,
                161.13428831,
                206.56505118,
                124.60025165,
                124.71632661,
            ]
        )
        assert np.allclose(output, expected)


#####
# Generic Statistical Summaries
#####


class TestSummarize:
    def test_standard(_, segments, flow):
        indices = ([1, 1], [1, 2])
        output = segments._summarize(np.mean, flow, indices)
        assert output == 5

    def test_empty(_, segments, flow):
        indices = ([], [])
        output = segments._summarize(np.mean, flow, indices)
        assert isnan(output)

    def test_nodata(_, segments, flow):
        indices = ([0, 1], [0, 1])
        output = segments._summarize(np.mean, flow, indices)
        assert isnan(output)


class TestSummary:
    def test(_, segments, flow):
        flow._nodata = 3
        output = segments.summary("sum", flow)
        expected = np.array([23, 14, nan, 5, 6, 14])
        assert np.array_equal(output, expected, equal_nan=True)


class TestCatchment:
    def test_sum(_, segments, values):
        output = segments.catchment("sum", values)
        expected = np.array([23, 14, nan, 5, 25, 62])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_mean(_, segments, values):
        output = segments.catchment("mean", values)
        expected = np.array([23, 14, nan, 5, 25, 62]) / segments.npixels
        assert np.array_equal(output, expected, equal_nan=True)

    def test_other(_, segments, values):
        output = segments.catchment("max", values)
        expected = np.array([7, 7, nan, 5, 7, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_sum_masked(_, segments, values, mask2):
        output = segments.catchment("sum", values, mask2)
        expected = np.array([nan, 14, nan, 5, 25, 25])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_mean_masked(_, segments, values, mask2):
        output = segments.catchment("mean", values, mask2)
        expected = np.array([nan, 14, nan, 5, 25, 25]) / np.array(
            [nan, 2, nan, 1, 4, 4]
        )
        assert np.array_equal(output, expected, equal_nan=True)

    def test_other_masked(_, segments, values, mask2):
        output = segments.catchment("max", values, mask2)
        expected = np.array([nan, 7, nan, 5, 7, 7])
        assert np.array_equal(output, expected, equal_nan=True)


class TestCatchmentSummary:
    def test_unmasked(_, segments, values):
        output = segments._catchment_summary(np.amax, values, mask=None)
        expected = np.array([7, 7, nan, 5, 7, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        output = segments._catchment_summary(np.amax, values, mask2)
        expected = np.array([nan, 7, nan, 5, 7, 7])
        assert np.array_equal(output, expected, equal_nan=True)


#####
# Variables
#####


class TestArea:
    def test_basic(_, segments, flow, npixels):
        output = segments.area()
        expected = npixels * flow.pixel_area
        assert np.array_equal(output, expected)

    def test_masked(_, segments, mask2, flow):
        output = segments.area(mask2)
        npixels = np.array([0, 2, 2, 1, 4, 4])
        expected = flow.pixel_area * npixels
        assert np.array_equal(output, expected)


class TestBurnRatio:
    def test(_, segments, mask2):
        output = segments.burn_ratio(mask2)
        expected = np.array([0, 1, 1, 1, 1, 4 / 11])
        assert np.array_equal(output, expected)


class TestBurnedArea:
    def test(_, segments, flow, mask2):
        output = segments.burned_area(mask2)
        expected = np.array([0, 2, 2, 1, 4, 4]) * flow.pixel_area
        assert np.array_equal(output, expected)


class TestKfFactor:
    def test_basic(_, segments, values, npixels):
        output = segments.kf_factor(values)
        sums = np.array([23, 14, nan, 5, 25, 62])
        expected = sums / npixels
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        output = segments.kf_factor(values, mask2)
        sums = np.array([nan, 14, nan, 5, 25, 25])
        npixels = np.array([nan, 2, nan, 1, 4, 4])
        expected = sums / npixels
        assert np.array_equal(output, expected, equal_nan=True)


class TestScaledDnbr:
    def test_basic(_, segments, values, npixels):
        output = segments.scaled_dnbr(values)
        sums = np.array([23, 14, nan, 5, 25, 62])
        expected = sums / npixels / 1000
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        output = segments.scaled_dnbr(values, mask2)
        sums = np.array([nan, 14, nan, 5, 25, 25])
        npixels = np.array([nan, 2, nan, 1, 4, 4])
        expected = sums / npixels / 1000
        assert np.array_equal(output, expected, equal_nan=True)


class TestScaledThickness:
    def test_basic(_, segments, values, npixels):
        output = segments.scaled_thickness(values)
        sums = np.array([23, 14, nan, 5, 25, 62])
        expected = sums / npixels / 100
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        output = segments.scaled_thickness(values, mask2)
        sums = np.array([nan, 14, nan, 5, 25, 25])
        npixels = np.array([nan, 2, nan, 1, 4, 4])
        expected = sums / npixels / 100
        assert np.array_equal(output, expected, equal_nan=True)


class TestSineTheta:
    def test_basic(_, segments, values, npixels):
        values._values = values.values / 10
        output = segments.sine_theta(values)
        sums = np.array([23, 14, nan, 5, 25, 62])
        expected = sums / npixels / 10
        assert np.allclose(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        values._values = values.values / 10
        output = segments.sine_theta(values, mask2)
        sums = np.array([nan, 14, nan, 5, 25, 25])
        npixels = np.array([nan, 2, nan, 1, 4, 4])
        expected = sums / npixels / 10
        assert np.array_equal(output, expected, equal_nan=True)

    def test_outside_interval(_, segments, values):
        with pytest.raises(ValueError) as error:
            segments.sine_theta(values)
        assert_contains(error, "sine_thetas")


class TestSlope:
    def test(_, segments, values):
        output = segments.slope(values)
        expected = np.array([23 / 5, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)


class TestRelief:
    def test(_, segments, values):
        output = segments.relief(values)
        expected = np.array([1, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)


class TestRuggedness:
    def test(_, segments, values, flow, npixels):
        output = segments.ruggedness(values)
        relief = np.array([1, 7, nan, 5, 6, 7])
        area = npixels * flow.pixel_area
        expected = relief / np.sqrt(area)
        assert np.array_equal(output, expected, equal_nan=True)


class TestUpslopeRatio:
    def test(_, segments, mask2):
        output = segments.upslope_ratio(mask2)
        expected = np.array([0, 1, 1, 1, 1, 4 / 11])
        assert np.array_equal(output, expected)


#####
# Filtering
#####


class TestCopy:
    def test(_, segments):
        copy = segments.copy()
        assert copy._flow == segments._flow
        assert copy._segments == segments._segments
        assert copy._indices == segments._indices
        assert np.array_equal(copy.npixels, segments.npixels)

        indices = np.ones(6, bool)
        copy.remove(indices=indices)
        assert copy.length == 0
        assert segments.length == 6


class TestKeep:
    def test_ids(_, segments, flow, linestrings245, indices245, npixels245):
        ids = [2, 4, 5]
        segments.keep(ids=ids)

        assert segments._flow == flow
        assert segments._segments == linestrings245
        assert segments._indices == indices245
        assert np.array_equal(segments._npixels, npixels245)

    def test_indices(_, segments, flow, linestrings245, indices245, npixels245):
        indices = np.array([0, 1, 0, 1, 1, 0])
        segments.keep(indices=indices)

        assert segments._flow == flow
        assert segments._segments == linestrings245
        assert segments._indices == indices245
        assert np.array_equal(segments._npixels, npixels245)

    def test_both(_, segments, flow, linestrings245, indices245, npixels245):
        ids = [2, 2, 2, 4]
        indices = np.array([0, 0, 0, 1, 1, 0])
        segments.keep(ids=ids, indices=indices)

        assert segments._flow == flow
        assert segments._segments == linestrings245
        assert segments._indices == indices245
        assert np.array_equal(segments._npixels, npixels245)


class TestRemove:
    def test_ids(_, segments, flow, linestrings245, indices245, npixels245):
        ids = [1, 3, 6]
        segments.remove(ids=ids)

        assert segments._flow == flow
        assert segments._segments == linestrings245
        assert segments._indices == indices245
        assert np.array_equal(segments._npixels, npixels245)

    def test_indices(_, segments, flow, linestrings245, indices245, npixels245):
        indices = np.array([1, 0, 1, 0, 0, 1])
        segments.remove(indices=indices)

        assert segments._flow == flow
        assert segments._segments == linestrings245
        assert segments._indices == indices245
        assert np.array_equal(segments._npixels, npixels245)

    def test_both(_, segments, flow, linestrings245, indices245, npixels245):
        ids = [1, 1, 1, 3]
        indices = np.array([0, 0, 1, 0, 0, 1])
        segments.remove(ids=ids, indices=indices)

        assert segments._flow == flow
        assert segments._segments == linestrings245
        assert segments._indices == indices245
        assert np.array_equal(segments._npixels, npixels245)


#####
# Export
#####


class TestGeojson:
    def test_no_properties(_, segments):
        segments.keep(ids=[2, 4, 5])
        output = segments.geojson()
        expected = [
            {
                "geometry": {
                    "coordinates": [[4.0, 1.0], [4.0, 2.0], [4.0, 3.0]],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [[5.0, 3.0], [4.0, 3.0]],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [[4.0, 3.0], [3.0, 4.0]],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
        ]
        expected = geojson.FeatureCollection(features=expected)
        assert output == expected

    def test_properties(_, segments):
        segments.keep(ids=[2, 4, 5])
        properties = {"slope": [1, 2, 3], "length": [1.1, 2.2, 3.3]}
        output = segments.geojson(properties)

        expected = [
            {
                "geometry": {
                    "coordinates": [[4.0, 1.0], [4.0, 2.0], [4.0, 3.0]],
                    "type": "LineString",
                },
                "properties": {"length": 1.1, "slope": 1.0},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [[5.0, 3.0], [4.0, 3.0]],
                    "type": "LineString",
                },
                "properties": {"length": 2.2, "slope": 2.0},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [[4.0, 3.0], [3.0, 4.0]],
                    "type": "LineString",
                },
                "properties": {"length": 3.3, "slope": 3.0},
                "type": "Feature",
            },
        ]
        expected = geojson.FeatureCollection(expected)
        assert output == expected


class TestSave:
    def test_no_properties(_, tmp_path, segments):
        path = Path(tmp_path) / "output.geojson"
        segments.keep(ids=[2, 4, 5])
        segments.save(path)

        assert path.is_file()
        with fiona.open(path, "r") as segments:
            output = [segment.__geo_interface__ for segment in segments]
        for k in range(len(output)):
            del output[k]["id"]
        output = geojson.FeatureCollection(output)

        expected = [
            {
                "geometry": {
                    "coordinates": [(4.0, 1.0), (4.0, 2.0), (4.0, 3.0)],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [(5.0, 3.0), (4.0, 3.0)],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [(4.0, 3.0), (3.0, 4.0)],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
        ]
        expected = geojson.FeatureCollection(features=expected)
        assert output == expected

    def test_properties(_, tmp_path, segments):
        path = Path(tmp_path) / "output.geojson"
        properties = {"slope": [1, 2, 3], "length": [1.1, 2.2, 3.3]}
        segments.keep(ids=[2, 4, 5])
        segments.save(path, properties)

        assert path.is_file()
        with fiona.open(path, "r") as segments:
            output = [segment.__geo_interface__ for segment in segments]
        for k in range(len(output)):
            del output[k]["id"]
        output = geojson.FeatureCollection(output)

        expected = [
            {
                "geometry": {
                    "coordinates": [(4.0, 1.0), (4.0, 2.0), (4.0, 3.0)],
                    "type": "LineString",
                },
                "properties": {"length": 1.1, "slope": 1.0},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [(5.0, 3.0), (4.0, 3.0)],
                    "type": "LineString",
                },
                "properties": {"length": 2.2, "slope": 2.0},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [(4.0, 3.0), (3.0, 4.0)],
                    "type": "LineString",
                },
                "properties": {"length": 3.3, "slope": 3.0},
                "type": "Feature",
            },
        ]
        expected = geojson.FeatureCollection(features=expected)
        assert output == expected

    def test_overwrite(_, tmp_path, segments):
        path = Path(tmp_path) / "output.geojson"
        with open(path, "w") as file:
            file.write("some other file")
        assert path.is_file()

        segments.keep(ids=[2, 4, 5])
        segments.save(path, overwrite=True)

        assert path.is_file()
        with fiona.open(path, "r") as segments:
            output = [segment.__geo_interface__ for segment in segments]
        for k in range(len(output)):
            del output[k]["id"]
        output = geojson.FeatureCollection(output)

        expected = [
            {
                "geometry": {
                    "coordinates": [(4.0, 1.0), (4.0, 2.0), (4.0, 3.0)],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [(5.0, 3.0), (4.0, 3.0)],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [(4.0, 3.0), (3.0, 4.0)],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
        ]
        expected = geojson.FeatureCollection(features=expected)
        assert output == expected

    def test_invalid_overwrite(_, tmp_path, segments):
        path = Path(tmp_path) / "output.geojson"
        with open(path, "w") as file:
            file.write("some other file")
        assert path.is_file()

        with pytest.raises(FileExistsError):
            segments.save(path, overwrite=False)
