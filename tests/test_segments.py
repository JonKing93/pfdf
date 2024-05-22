from math import isnan, nan
from pathlib import Path

import fiona
import geojson
import numpy as np
import pytest
import rasterio.features
from affine import Affine
from shapely import LineString

from pfdf._utils.kernel import Kernel
from pfdf.errors import (
    DimensionError,
    MissingCRSError,
    MissingTransformError,
    RasterCRSError,
    RasterShapeError,
    RasterTransformError,
    ShapeError,
)
from pfdf.projection import CRS, Transform, _crs
from pfdf.raster import Raster
from pfdf.segments import Segments

##### Standard fixtures

# Note that fixtures are for object attributes, not properties


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
    return Raster.from_array(flow, nodata=0, transform=transform, crs=26911)


@pytest.fixture
def values(flow):
    values = flow.values.copy()
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
    # Used for catchment statistics
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
def outlet_raster():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 6, 0, 0, 6, 3, 0],
            [0, 6, 0, 0, 6, 3, 0],
            [0, 6, 6, 0, 6, 6, 0],
            [0, 0, 6, 6, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype("int32")


@pytest.fixture
def linestrings():
    segments = [
        [[1.5, 1.5], [1.5, 2.5], [1.5, 3.5], [2.5, 3.5], [2.5, 4.5], [3.5, 4.5]],
        [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
        [[5.5, 2.5], [5.5, 1.5], [5.5, 0.5]],
        [[5.5, 3.5], [4.5, 3.5]],
        [[4.5, 3.5], [3.5, 4.5]],
        [[3.5, 4.5], [3.5, 5.5], [3.5, 6.5]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def indices():
    return [
        ([1, 2, 3, 3, 4], [1, 1, 1, 2, 2]),
        ([1, 2], [4, 4]),
        ([2, 1], [5, 5]),
        ([3], [5]),
        ([3], [4]),
        ([4, 5], [3, 3]),
    ]


@pytest.fixture
def npixels():
    return np.array([5, 2, 2, 1, 4, 11])


@pytest.fixture
def child():
    return np.array([5, 4, -1, 4, 5, -1])


@pytest.fixture
def parents():
    return np.array(
        [
            [-1, -1],
            [-1, -1],
            [-1, -1],
            [-1, -1],
            [1, 3],
            [0, 4],
        ]
    )


##### Split point fixtures


@pytest.fixture
def linestrings_split():
    segments = [
        [[1.5, 1.5], [1.5, 2.5], [1.5, 3.5], [2, 3.5]],
        [[2, 3.5], [2.5, 3.5], [2.5, 4.5], [3.5, 4.5]],
        [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
        [[5.5, 2.5], [5.5, 1.5], [5.5, 0.5]],
        [[5.5, 3.5], [4.5, 3.5]],
        [[4.5, 3.5], [3.5, 4.5]],
        [[3.5, 4.5], [3.5, 5.5], [3.5, 6.5]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def indices_split():
    return [
        ([1, 2, 3], [1, 1, 1]),
        ([3, 4], [2, 2]),
        ([1, 2], [4, 4]),
        ([2, 1], [5, 5]),
        ([3], [5]),
        ([3], [4]),
        ([4, 5], [3, 3]),
    ]


##### Nested drainage basin fixtures


@pytest.fixture
def bflow(transform):
    flow = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 5, 1, 7, 3, 0],
            [0, 7, 5, 1, 7, 3, 0],
            [0, 1, 7, 7, 6, 5, 0],
            [0, 5, 1, 7, 5, 1, 0],
            [0, 5, 5, 7, 5, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(flow, nodata=0, transform=transform, crs=26911)


@pytest.fixture
def bsegments(bflow, mask):
    return Segments(bflow, mask)


@pytest.fixture
def basins():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 6, 6, 6, 6, 3, 0],
            [0, 6, 6, 6, 6, 3, 0],
            [0, 6, 6, 6, 6, 6, 0],
            [0, 0, 6, 6, 6, 0, 0],
            [0, 0, 0, 6, 6, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype("int32")


@pytest.fixture
def bpixels():
    return np.array([7, 4, 2, 1, 6, 18])


##### Filtering fixtures


@pytest.fixture
def linestrings245(linestrings):
    return [linestrings[1], linestrings[3], linestrings[4]]


@pytest.fixture
def indices245(indices):
    return [indices[1], indices[3], indices[4]]


@pytest.fixture
def bpixels245():
    return np.array([4, 1, 6])


@pytest.fixture
def child245():
    return np.array([2, 2, -1])


@pytest.fixture
def parents245():
    return np.array(
        [
            [-1, -1],
            [-1, -1],
            [0, 1],
        ]
    )


@pytest.fixture
def basins245():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 2, 0, 0],
            [0, 0, 0, 2, 2, 0, 0],
            [0, 0, 0, 0, 5, 4, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )


#####
# Dunders
#####


class TestInit:
    def test_any_length(_, flow, mask, linestrings, indices, npixels, child, parents):
        segments = Segments(flow, mask)
        assert segments._flow == flow
        assert segments._segments == linestrings
        assert np.array_equal(segments._ids, np.arange(6) + 1)
        assert segments._indices == indices
        assert np.array_equal(segments._npixels, npixels)
        assert np.array_equal(segments._child, child)
        assert np.array_equal(segments._parents, parents)

    def test_split_point_upstream(_, flow, mask, linestrings_split, indices_split):
        npixels = np.array([3, 5, 2, 2, 1, 4, 11])
        child = np.array([1, 6, 5, -1, 5, 6, -1])
        parents = np.array(
            [
                [-1, -1],
                [0, -1],
                [-1, -1],
                [-1, -1],
                [-1, -1],
                [2, 4],
                [1, 5],
            ]
        )
        segments = Segments(flow, mask, 2.5)
        assert segments._flow == flow

        print(segments._segments)
        print(linestrings_split)

        assert segments._segments == linestrings_split
        assert np.array_equal(segments._ids, np.arange(7) + 1)
        assert segments._indices == indices_split
        assert np.array_equal(segments._npixels, npixels)
        assert np.array_equal(segments._child, child)
        assert np.array_equal(segments._parents, parents)

    def test_meters(_, flow, mask, linestrings_split, indices_split):
        npixels = np.array([3, 5, 2, 2, 1, 4, 11])
        child = np.array([1, 6, 5, -1, 5, 6, -1])
        parents = np.array(
            [
                [-1, -1],
                [0, -1],
                [-1, -1],
                [-1, -1],
                [-1, -1],
                [2, 4],
                [1, 5],
            ]
        )
        segments = Segments(flow, mask, 2.5, meters=True)
        assert segments._flow == flow

        print(segments._segments)
        print(linestrings_split)

        assert segments._segments == linestrings_split
        assert np.array_equal(segments._ids, np.arange(7) + 1)
        assert segments._indices == indices_split
        assert np.array_equal(segments._npixels, npixels)
        assert np.array_equal(segments._child, child)
        assert np.array_equal(segments._parents, parents)

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
        flow = Raster.from_array(flow, nodata=0, transform=transform, crs=26911)
        mask = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        segments = Segments(flow, mask, max_length=2.5)

        linestrings = [
            LineString([[5.5, 1.5], [4.5, 1.5], [3.5, 1.5], [3, 1.5]]),
            LineString([[3, 1.5], [2.5, 1.5], [1.5, 1.5], [0.5, 1.5]]),
        ]
        indices = [
            ([1, 1, 1], [5, 4, 3]),
            ([1, 1], [2, 1]),
        ]
        npixels = np.array([3, 5])
        child = np.array([1, -1])
        parents = np.array([[-1, -1], [0, -1]])

        assert segments._flow == flow
        assert segments._segments == linestrings
        assert np.array_equal(segments._ids, np.arange(2) + 1)
        assert segments._indices == indices
        assert np.array_equal(segments._npixels, npixels)
        assert np.array_equal(segments._child, child)
        assert np.array_equal(segments._parents, parents)

    def test_more_than_2_parents(_, transform):
        flow = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 8, 7, 6, 0],
                [0, 0, 7, 0, 0],
                [0, 0, 0, 0, 0],
            ]
        )
        flow = Raster.from_array(flow, nodata=0, transform=transform, crs=26911)
        mask = np.ones(flow.shape, bool)
        output = Segments(flow, mask)
        assert np.array_equal(output._child, [3, 3, 3, -1])
        parents = np.array(
            [
                [-1, -1, -1],
                [-1, -1, -1],
                [-1, -1, -1],
                [0, 1, 2],
            ]
        )
        assert np.array_equal(output._parents, parents)

    def test_no_transform(_, flow, mask, assert_contains):
        flow = Raster.from_array(flow.values, crs=26911)
        with pytest.raises(MissingTransformError) as error:
            Segments(flow, mask)
        assert_contains(
            error, "The flow direction raster must have an affine Transform"
        )

    def test_no_crs(_, flow, mask):
        flow = Raster.from_array(flow.values, transform=flow.transform)
        with pytest.raises(MissingCRSError):
            Segments(flow, mask)

    def test_short_maxlength(_, flow, mask, assert_contains):
        with pytest.raises(ValueError) as error:
            Segments(flow, mask, max_length=1)
        assert_contains(error, "max_length", "diagonal")


def test_len(segments):
    assert len(segments) == 6


def test_str(segments):
    assert str(segments) == "A network of 6 stream segments."


def test_geo_interface(segments):
    segments.keep(ids=[2, 4, 5])
    output = segments.__geo_interface__
    assert isinstance(output, geojson.FeatureCollection)
    expected = {
        "features": [
            {
                "geometry": {
                    "coordinates": [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [[5.5, 3.5], [4.5, 3.5]],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [[4.5, 3.5], [3.5, 4.5]],
                    "type": "LineString",
                },
                "properties": {},
                "type": "Feature",
            },
        ],
        "type": "FeatureCollection",
    }
    assert output == expected


#####
# Properties
#####

##### Network


def test_length(segments):
    assert segments.length == 6


def test_nlocal(segments):
    assert segments.nlocal == 2


def test_crs(segments, flow):
    assert segments.crs == flow.crs


def test_crs_units(segments):
    assert segments.crs_units == ("metre", "metre")


##### Segments


def test_segments(segments, linestrings):
    assert segments.segments == linestrings
    assert segments.segments is not segments._segments


def test_ids(segments):
    assert np.array_equal(segments.ids, np.arange(6) + 1)
    assert segments.ids is not segments._ids


def test_parents(segments):
    expected = [[0, 0], [0, 0], [0, 0], [0, 0], [2, 4], [1, 5]]
    assert np.array_equal(segments.parents, expected)


def test_child(segments):
    expected = [6, 5, 0, 5, 6, 0]
    assert np.array_equal(segments.child, expected)


def test_isterminus(segments):
    expected = [False, False, True, False, False, True]
    assert np.array_equal(segments.isterminus, expected)


def test_indices(segments, indices):
    assert segments.indices == indices
    assert segments.indices is not segments._indices


def test_npixels(segments, npixels):
    assert np.array_equal(segments.npixels, npixels)
    assert segments.npixels is not segments._npixels


##### Raster metadata


def test_flow(segments, flow):
    assert segments.flow == flow
    assert segments.flow is segments._flow


def test_raster_shape(segments, flow):
    assert segments.raster_shape == flow.shape


def test_transform(segments, flow):
    assert segments.transform == flow.transform


def test_bounds(segments, flow):
    assert segments.bounds == flow.bounds


#####
# Utilities
###


class TestIndicesToIds:
    def test(_, segments):
        ids = np.array([1, 2, 5, 6, 9])
        parents = np.array(
            [
                [-1, 1],
                [-1, -1],
                [4, -1],
                [-1, -1],
                [3, -1],
            ]
        )
        expected = np.array(
            [
                [0, 2],
                [0, 0],
                [9, 0],
                [0, 0],
                [6, 0],
            ]
        )
        segments._ids = ids
        output = segments._indices_to_ids(parents)
        assert np.array_equal(output, expected)


class TestPreallocate:
    def test_all(_, segments):
        output = segments._preallocate()
        assert isinstance(output, np.ndarray)
        assert output.shape == (6,)
        assert output.dtype == float

    def test_terminal(_, segments):
        output = segments._preallocate(terminal=True)
        assert isinstance(output, np.ndarray)
        assert output.shape == (2,)
        assert output.dtype == float


class TestAccumulation:
    def test_init(_, segments, npixels):
        segments._npixels = None
        output = segments._accumulation()
        assert np.array_equal(output, npixels)

    def test_basic(_, segments, npixels):
        output = segments._accumulation()
        assert np.array_equal(output, npixels)

    def test_weights(_, segments, flow):
        output = segments._accumulation(weights=flow)
        expected = np.array([23, 14, 6, 5, 25, 62])
        assert np.array_equal(output, expected)

    def test_mask(_, segments, mask):
        mask[:, 3:] = False
        expected = np.array([5, 0, 0, 0, 0, 5])
        output = segments._accumulation(mask=mask)
        assert np.array_equal(output, expected)

    def test_basic_terminal(_, segments, npixels):
        output = segments._accumulation(terminal=True)
        expected = npixels[[2, 5]]
        assert np.array_equal(output, expected)

    def test_weights_terminal(_, segments, flow):
        output = segments._accumulation(weights=flow, terminal=True)
        expected = np.array([6, 62])
        assert np.array_equal(output, expected)

    def test_includenan(_, segments, flow):
        flow._nodata = 7
        output = segments._accumulation(weights=flow)
        expected = np.array([nan, nan, 6, 5, nan, nan])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_omitnan(_, segments, flow):
        flow._nodata = 7
        output = segments._accumulation(weights=flow, omitnan=True)
        expected = np.array([2, 0, 6, 5, 11, 13])
        assert np.array_equal(output, expected, equal_nan=True)


#####
# Generic Validation
#####


class TestValidate:
    def test_valid_raster(_, segments, flow):
        output = segments._validate(flow, "")
        assert output == flow

    def test_default_spatial(_, segments, flow):
        input = Raster.from_array(flow.values, nodata=0)
        output = segments._validate(input, "")
        assert output == flow

    def test_bad_shape(_, segments, flow, assert_contains):
        a = np.arange(10).reshape(2, 5)
        input = Raster.from_array(a, crs=flow.crs, transform=flow.transform)
        with pytest.raises(RasterShapeError) as error:
            segments._validate(input, "test name")
        assert_contains(error, "test name")

    def test_bad_transform(_, segments, flow, assert_contains):
        flow.override(transform=Transform(9, 9, 0, 0))
        with pytest.raises(RasterTransformError) as error:
            segments._validate(flow, "test name")
        assert_contains(error, "test name")

    def test_bad_crs(_, segments, flow, assert_contains):
        flow._crs = CRS.from_epsg(4000)
        with pytest.raises(RasterCRSError) as error:
            segments._validate(flow, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize(
        "input, error",
        (
            (5, TypeError),
            (np.ones((3, 3, 3)), DimensionError),
        ),
    )
    def test_invalid_raster(_, segments, input, error, assert_contains):
        with pytest.raises(error) as e:
            segments._validate(input, "test name")
        assert_contains(e, "test name")


class TestCheckIds:
    def test_in_network(_, segments):
        input = np.array(5).reshape(1)
        segments._check_ids(input, "")

    def test_scalar_missing(_, segments, assert_contains):
        input = np.array(9).reshape(1)
        with pytest.raises(ValueError) as error:
            segments._check_ids(input, "id")
        assert_contains(error, "id (value=9)")

    def test_vector_missing(_, segments, assert_contains):
        input = np.array([1, 9])
        with pytest.raises(ValueError) as error:
            segments._check_ids(input, "ids")
        assert_contains(error, "ids[1] (value=9)")


class TestValidateId:
    def test_valid(_, segments):
        output = segments._validate_id(5)
        assert output == 4

    def test_not_scalar(_, segments, assert_contains):
        with pytest.raises(DimensionError) as error:
            segments._validate_id([5, 2])
        assert_contains(error, "id")

    def test_not_in_network(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments._validate_id(9)
        assert_contains(error, "id (value=9)")


#####
# Outlets
#####


class Test_Terminus:
    def test_end(_, segments):
        assert segments._terminus(2) == 2

    def test_not_end(_, segments):
        assert segments._terminus(1) == 5


class TestTerminus:
    def test_valid(_, segments):
        assert segments.terminus(2) == 6

    def test_invalid(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.terminus(9)
        assert_contains(error, "id (value=9)")


class Test_Termini:
    def test(_, segments):
        output = segments._termini()
        expected = [2, 5]
        assert np.array_equal(output, expected)


class TestTermini:
    def test(_, segments):
        output = segments.termini()
        expected = [3, 6]
        assert np.array_equal(output, expected)


class Test_Outlet:
    def test(_, segments, indices):
        output = segments._outlet(1)
        expected = indices[1][0][-1], indices[1][1][-1]
        assert output == expected


class TestOutlet:
    def test_valid(_, segments, indices):
        output = segments.outlet(1)
        expected = indices[0][0][-1], indices[0][1][-1]
        assert output == expected

    def test_invalid(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.outlet(9)
        assert_contains(error, "id (value=9)")


class TestOutlets:
    def test_all(_, segments, indices):
        output = segments.outlets()
        expected = [(index[0][-1], index[1][-1]) for index in indices]
        assert output == expected

    def test_terminal(_, segments, indices):
        output = segments.outlets(terminal=True)
        expected = [(index[0][-1], index[1][-1]) for index in [indices[2], indices[5]]]
        assert output == expected


#####
# Rasters
#####


class TestBasinMask:
    def test_catchment(_, segments):
        output = segments.basin_mask(id=5)
        expected = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert isinstance(output, Raster)
        assert output.nodata == False
        assert output.crs == segments.crs
        assert output.transform == segments.transform
        assert np.array_equal(output.values, expected)

    def test_outlet(_, segments):
        output = segments.basin_mask(id=5, terminal=True)
        expected = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 1, 0, 0],
                [0, 1, 0, 0, 1, 0, 0],
                [0, 1, 1, 0, 1, 1, 0],
                [0, 0, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        )
        assert isinstance(output, Raster)
        assert output.nodata == False
        assert output.crs == segments.crs
        assert output.transform == segments.transform
        assert np.array_equal(output.values, expected)

    def test_invalid_id(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.basin_mask(id=12)
        assert_contains(error, "id (value=12)")

    def test_multiple_ids(_, segments, assert_contains):
        with pytest.raises(DimensionError) as error:
            segments.basin_mask(id=[1, 2])
        assert_contains(error, "id")


class TestSegmentsRaster:
    def test(_, segments, stream_raster):
        output = segments._segments_raster()
        assert np.array_equal(output, stream_raster)


class TestLocateRaster:
    @pytest.mark.parametrize("parallel, nprocess", ((False, None), (True, 2)))
    def test_sequential(_, segments, parallel, nprocess, outlet_raster):
        assert segments._basins is None
        segments.locate_basins(parallel, nprocess)
        assert np.array_equal(segments._basins, outlet_raster)

    def test_invalid_nprocess(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.locate_basins(parallel=True, nprocess=2.2)
        assert_contains(error, "nprocess", "integer")


class TestRaster:
    def test_segments(_, segments, stream_raster):
        output = segments.raster()
        assert isinstance(output, Raster)
        assert output.nodata == 0
        assert output.crs == segments.crs
        assert output.transform == segments.transform
        assert np.array_equal(output.values, stream_raster)

    def test_basins_new(_, segments, outlet_raster):
        assert segments._basins is None
        output = segments.raster(basins=True)
        assert output.nodata == 0
        assert output.crs == segments.crs
        assert output.transform == segments.transform
        assert np.array_equal(output.values, outlet_raster)
        assert np.array_equal(output.values, segments._basins)

    def test_basins_prebuilt(_, segments, outlet_raster):
        segments.locate_basins()
        original = segments._basins
        assert isinstance(original, np.ndarray)
        output = segments.raster(basins=True)
        assert output.nodata == 0
        assert output.crs == segments.crs
        assert output.transform == segments.transform
        assert np.array_equal(output.values, outlet_raster)
        assert segments._basins is original


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
        flow = segments.flow.values.copy()
        flow[1, 1] = 0
        flow = Raster.from_array(flow, nodata=0, transform=segments.transform)
        segments._flow = flow
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
        flow = segments.flow.values.copy()
        flow[1, 1] = 0
        flow = Raster.from_array(flow, nodata=0, transform=segments.transform)
        segments._flow = flow
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

    def test_meters(_, segments, dem):
        output = segments.confinement(dem, neighborhood=2, meters=True)
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

    def test_factor_meters(_, segments, dem):
        output = segments.confinement(dem, neighborhood=2, factor=10, meters=True)
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
# Generic Statistics
#####


class TestStatistics:
    def test_print(_, capfd):
        Segments.statistics()
        expected = (
            "Statistic | Description\n"
            "--------- | -----------\n"
            "outlet    | Values at stream segment outlet pixels\n"
            "min       | Minimum value\n"
            "max       | Maximum value\n"
            "mean      | Mean\n"
            "median    | Median\n"
            "std       | Standard deviation\n"
            "sum       | Sum\n"
            "var       | Variance\n"
            "nanmin    | Minimum value, ignoring NaNs\n"
            "nanmax    | Maximum value, ignoring NaNs\n"
            "nanmean   | Mean value, ignoring NaNs\n"
            "nanmedian | Median value, ignoring NaNs\n"
            "nanstd    | Standard deviation, ignoring NaNs\n"
            "nansum    | Sum, ignoring NaNs\n"
            "nanvar    | Variance, ignoring NaNs\n"
        )
        printed, _ = capfd.readouterr()
        assert printed == expected

    def test_dict(_):
        output = Segments.statistics(asdict=True)
        expected = {
            "outlet": "Values at stream segment outlet pixels",
            "min": "Minimum value",
            "max": "Maximum value",
            "mean": "Mean",
            "median": "Median",
            "std": "Standard deviation",
            "sum": "Sum",
            "var": "Variance",
            "nanmin": "Minimum value, ignoring NaNs",
            "nanmax": "Maximum value, ignoring NaNs",
            "nanmean": "Mean value, ignoring NaNs",
            "nanmedian": "Median value, ignoring NaNs",
            "nanstd": "Standard deviation, ignoring NaNs",
            "nansum": "Sum, ignoring NaNs",
            "nanvar": "Variance, ignoring NaNs",
        }
        assert output == expected


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

    def test_ignore_nodata(_, segments, flow):
        indices = ([0, 1], [0, 1])
        output = segments._summarize(np.nanmean, flow, indices)
        assert output == 7

    def test_ignore_all_nan(_, segments, flow):
        indices = ([0, 0], [0, 0])
        output = segments._summarize(np.nanmean, flow, indices)
        assert isnan(output)


class TestValuesAtOutlets:
    def test_all(_, segments, flow):
        flow._nodata = 3
        output = segments._values_at_outlets(flow, terminal=False)
        expected = np.array([1, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, flow):
        flow._nodata = 3
        output = segments._values_at_outlets(flow, terminal=True)
        expected = np.array([nan, 7])
        assert np.array_equal(output, expected, equal_nan=True)


class TestSummary:
    def test_standard(_, segments, flow):
        flow._nodata = 3
        output = segments.summary("sum", flow)
        expected = np.array([23, 14, nan, 5, 6, 14])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_outlet(_, segments, flow):
        flow._nodata = 3
        output = segments.summary("outlet", flow)
        expected = np.array([1, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_ignore_all_nan(_, segments, flow):
        flow._nodata = 3
        output = segments.summary("nansum", flow)
        expected = np.array([23, 14, nan, 5, 6, 14])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_invalid_stat(_, segments, flow, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.summary("invalid", flow)
        assert_contains(error, "statistic", "invalid")

    @pytest.mark.parametrize(
        "stat",
        (
            "outlet",
            "min",
            "nanmin",
            "max",
            "nanmax",
            "mean",
            "nanmean",
            "median",
            "nanmedian",
            "sum",
            "nansum",
            "std",
            "nanstd",
            "var",
            "nanvar",
        ),
    )
    def test_statistics(_, segments, flow, stat):
        segments.summary(stat, flow)


class TestAccumulationSummary:
    def test_sum(_, segments, values):
        output = segments._accumulation_summary(
            "sum", values, mask=None, terminal=False
        )
        expected = np.array([23, 14, nan, 5, 25, 62])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_mean(_, segments, values, npixels):
        output = segments._accumulation_summary(
            "mean", values, mask=None, terminal=False
        )
        expected = np.array([23, 14, nan, 5, 25, 62]) / npixels
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        output = segments._accumulation_summary(
            "sum", values, mask=mask2, terminal=False
        )
        expected = np.array([nan, 14, nan, 5, 25, 25])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nansum(_, segments, flow):
        flow._nodata = 7
        output = segments._accumulation_summary(
            "nansum", flow, mask=None, terminal=False
        )
        expected = np.array([2, nan, 6, 5, 11, 13])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nanmean(_, segments, flow):
        flow._nodata = 7
        output = segments._accumulation_summary(
            "nanmean", flow, mask=None, terminal=False
        )
        expected = np.array([1, nan, 3, 5, 5.5, 13 / 4])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values):
        output = segments._accumulation_summary("sum", values, mask=None, terminal=True)
        expected = [nan, 62]
        assert np.array_equal(output, expected, equal_nan=True)


class TestCatchmentSummary:
    def test_standard(_, segments, values):
        output = segments._catchment_summary("sum", values, mask=None, terminal=False)
        expected = np.array([23, 14, nan, 5, 25, 62])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_ignore_all_nan(_, segments, values):
        output = segments._catchment_summary(
            "nansum", values, mask=None, terminal=False
        )
        expected = np.array([23, 14, nan, 5, 25, 62])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked(_, segments, values, mask2):
        output = segments._catchment_summary("sum", values, mask=mask2, terminal=False)
        expected = np.array([nan, 14, nan, 5, 25, 25])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values):
        output = segments._catchment_summary("sum", values, mask=None, terminal=True)
        expected = [nan, 62]
        assert np.array_equal(output, expected, equal_nan=True)


class TestBasinSummary:
    def test_outlet(_, segments, flow):
        flow._nodata = 3
        output = segments.basin_summary("outlet", flow)
        expected = np.array([1, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal_outlet(_, segments, flow):
        flow._nodata = 3
        output = segments.basin_summary("outlet", flow, terminal=True)
        expected = [nan, 7]
        assert np.array_equal(output, expected, equal_nan=True)

    def test_accumulation(_, segments, values):
        output = segments.basin_summary("sum", values)
        expected = np.array([23, 14, nan, 5, 25, 62])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal_accumulation(_, segments, values):
        output = segments.basin_summary("sum", values, terminal=True)
        expected = np.array([nan, 62])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked_accumulation(_, segments, values, mask2):
        output = segments.basin_summary("sum", values, mask2)
        expected = np.array([nan, 14, nan, 5, 25, 25])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_catchment(_, segments, values):
        output = segments.basin_summary("max", values)
        expected = np.array([7, 7, nan, 5, 7, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal_catchment(_, segments, values):
        output = segments.basin_summary("max", values, terminal=True)
        expected = np.array([nan, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_masked_catchment(_, segments, values, mask2):
        output = segments.basin_summary("nansum", values, mask2)
        expected = np.array([nan, 14, nan, 5, 25, 25])
        assert np.array_equal(output, expected, equal_nan=True)


#####
# Variables
#####


class TestLengths:
    def test(_, segments, linestrings):
        expected = np.array([segment.length for segment in linestrings])
        output = segments.lengths()
        assert np.array_equal(output, expected)

    def test_meters(_, segments, linestrings):
        expected = np.array([segment.length for segment in linestrings])
        expected = _crs.dy_to_meters(segments.crs, expected)
        output = segments.lengths(meters=True)
        assert np.array_equal(output, expected)


class TestArea:
    def test_basic(_, segments, flow, npixels):
        output = segments.area()
        expected = npixels * flow.transform.pixel_area()
        assert np.array_equal(output, expected)

    def test_kilometers(_, segments, flow, npixels):
        output = segments.area(kilometers=True)
        expected = npixels * flow.transform.pixel_area()
        expected = _crs.dy_to_meters(segments.crs, expected) / 1e6
        assert np.array_equal(output, expected)

    def test_masked(_, segments, mask2, flow):
        output = segments.area(mask2)
        npixels = np.array([0, 2, 2, 1, 4, 4])
        expected = flow.transform.pixel_area() * npixels
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, flow, npixels):
        output = segments.area(terminal=True)
        expected = npixels[[2, 5]] * flow.transform.pixel_area()
        assert np.array_equal(output, expected)


class TestBurnRatio:
    def test(_, segments, mask2):
        output = segments.burn_ratio(mask2)
        expected = np.array([0, 1, 1, 1, 1, 4 / 11])
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, mask2):
        output = segments.burn_ratio(mask2, terminal=True)
        expected = np.array([1, 4 / 11])
        assert np.array_equal(output, expected)


class TestBurnedArea:
    def test(_, segments, flow, mask2):
        output = segments.burned_area(mask2)
        expected = np.array([0, 2, 2, 1, 4, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, flow, mask2):
        output = segments.burned_area(mask2, terminal=True)
        expected = np.array([2, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)


class TestDevelopedArea:
    def test(_, segments, flow, mask2):
        output = segments.developed_area(mask2)
        expected = np.array([0, 2, 2, 1, 4, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, flow, mask2):
        output = segments.developed_area(mask2, terminal=True)
        expected = np.array([2, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)


class TestInMask:
    def test(_, segments, mask2):
        mask2[2:4, 4] = False
        output = segments.in_mask(mask2)
        assert output.dtype == bool
        expected = np.array([False, True, True, True, False, False])
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, mask2):
        mask2[2:4, 4] = False
        output = segments.in_mask(mask2, terminal=True)
        assert output.dtype == bool
        expected = np.array([True, False])
        assert np.array_equal(output, expected)


class TestInPerimeter:
    def test(_, segments, mask2):
        mask2[2:4, 4] = False
        output = segments.in_perimeter(mask2)
        assert output.dtype == bool
        expected = np.array([False, True, True, True, False, False])
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, mask2):
        mask2[2:4, 4] = False
        output = segments.in_perimeter(mask2, terminal=True)
        assert output.dtype == bool
        expected = np.array([True, False])
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

    def test_terminal(_, segments, values, npixels):
        output = segments.kf_factor(values, terminal=True)
        sums = np.array([nan, 62])
        expected = sums / npixels[[2, 5]]
        assert np.array_equal(output, expected, equal_nan=True)

    def test_omitnan(_, segments, flow):
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = segments.kf_factor(flow, omitnan=True)
        expected = np.array([1, nan, 3, 5, 5.5, 13 / 4])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_negative(_, segments, values, assert_contains):
        values = values.values.copy()
        values[0, 0] = -1
        with pytest.raises(ValueError) as error:
            segments.kf_factor(values)
        assert_contains(error, "kf_factor", "value=-1")


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

    def test_terminal(_, segments, values, npixels):
        output = segments.scaled_dnbr(values, terminal=True)
        sums = np.array([nan, 62])
        expected = sums / npixels[[2, 5]] / 1000
        assert np.array_equal(output, expected, equal_nan=True)

    def test_omitnan(_, segments, flow):
        flow._nodata = 7
        output = segments.scaled_dnbr(flow, omitnan=True)
        expected = np.array([1, nan, 3, 5, 5.5, 13 / 4]) / 1000
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

    def test_omitnan(_, segments, flow):
        values = flow.values.copy()
        values[values == 0] = 7
        flow = Raster.from_array(values, nodata=7)
        output = segments.scaled_thickness(flow, omitnan=True)
        expected = np.array([1, nan, 3, 5, 5.5, 13 / 4]) / 100
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values, npixels):
        output = segments.scaled_thickness(values, terminal=True)
        sums = np.array([nan, 62])
        expected = sums / npixels[[2, 5]] / 100
        assert np.array_equal(output, expected, equal_nan=True)

    def test_negative(_, segments, values, assert_contains):
        values = values.values.copy()
        values[0, 0] = -1
        with pytest.raises(ValueError) as error:
            segments.scaled_thickness(values)
        assert_contains(error, "soil_thickness", "value=-1")


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

    def test_omitnan(_, segments, flow):
        values = flow.values.copy()
        values = values / 10
        flow = Raster.from_array(values, nodata=0.7)
        output = segments.sine_theta(flow, omitnan=True)
        expected = np.array([1, nan, 3, 5, 5.5, 13 / 4]) / 10
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values, npixels):
        values._values = values.values / 10
        output = segments.sine_theta(values, terminal=True)
        sums = np.array([nan, 62])
        expected = sums / npixels[[2, 5]] / 10
        assert np.allclose(output, expected, equal_nan=True)

    def test_outside_interval(_, segments, values, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.sine_theta(values)
        assert_contains(error, "sine_thetas")


class TestSlope:
    def test(_, segments, values):
        output = segments.slope(values)
        expected = np.array([23 / 5, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values):
        output = segments.slope(values, terminal=True)
        expected = np.array([nan, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_omitnan(_, segments, flow):
        flow._nodata = 7
        output = segments.slope(flow, omitnan=True)
        expected = np.array([1, nan, 3, 5, 6, nan])
        assert np.array_equal(output, expected, equal_nan=True)


class TestRelief:
    def test(_, segments, values):
        output = segments.relief(values)
        expected = np.array([1, 7, nan, 5, 6, 7])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values):
        output = segments.relief(values, terminal=True)
        expected = np.array([nan, 7])
        assert np.array_equal(output, expected, equal_nan=True)


class TestRuggedness:
    def test(_, segments, values, flow, npixels):
        output = segments.ruggedness(values)
        relief = np.array([1, 7, nan, 5, 6, 7])
        area = npixels * flow.transform.pixel_area()
        expected = relief / np.sqrt(area)
        assert np.array_equal(output, expected, equal_nan=True)

    def test_meters(_, segments, values, flow, npixels):
        output = segments.ruggedness(values, meters=True)
        relief = np.array([1, 7, nan, 5, 6, 7])
        area = npixels * flow.transform.pixel_area()
        expected = relief / np.sqrt(area)
        assert np.array_equal(output, expected, equal_nan=True)

    def test_terminal(_, segments, values, flow, npixels):
        output = segments.ruggedness(values, terminal=True)
        relief = np.array([nan, 7])
        npixels = np.array([npixels[2], npixels[5]])
        area = npixels * flow.transform.pixel_area()
        expected = relief / np.sqrt(area)
        assert np.array_equal(output, expected, equal_nan=True)


class TestUpslopeRatio:
    def test(_, segments, mask2):
        output = segments.upslope_ratio(mask2)
        expected = np.array([0, 1, 1, 1, 1, 4 / 11])
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, mask2):
        output = segments.upslope_ratio(mask2, terminal=True)
        expected = np.array([1, 4 / 11])
        assert np.array_equal(output, expected)


#####
# Filtering Updates
#####


class TestUpdateSegments:
    def test(_, segments, linestrings245, indices245):
        remove = np.array([1, 0, 1, 0, 0, 1], bool)
        out1, out2 = segments._update_segments(remove)
        assert out1 == linestrings245
        assert out2 == indices245


class TestUpdateFamily:
    def test(_):
        child = np.array([1, 2, 3, 4, 5, 6, 7]) - 1
        parents = np.array([[0, 0], [2, 0], [2, 6], [6, 2], [2, 5], [5, 2], [4, 5]]) - 1
        remove = np.array([0, 1, 0, 0, 1, 0], bool)

        expected_child = np.array([1, 0, 3, 4, 0, 6, 7]) - 1
        expected_parents = (
            np.array([[0, 0], [0, 0], [0, 6], [6, 0], [0, 0], [0, 0], [4, 0]]) - 1
        )
        Segments._update_family(child, parents, remove)

        assert np.array_equal(child, expected_child)
        assert np.array_equal(parents, expected_parents)


class TestUpdateIndices:
    def test(_):
        family = np.array(
            [
                [-1, -1],
                [-1, -1],
                [1, 4],
                [4, 6],
                [7, -1],
                [-1, 7],
            ]
        )
        nremoved = np.array([1, 1, 2, 2, 2, 3, 3, 3, 3])
        expected = np.array(
            [
                [-1, -1],
                [-1, -1],
                [0, 2],
                [2, 3],
                [4, -1],
                [-1, 4],
            ]
        )
        Segments._update_indices(family, nremoved)
        assert np.array_equal(family, expected)


class TestUpdateConnectivity:
    def test(_, segments, child245, parents245):
        remove = np.array([1, 0, 1, 0, 0, 1], bool)
        out1, out2 = segments._update_connectivity(remove)
        assert np.array_equal(out1, child245)
        assert np.array_equal(out2, parents245)


class TestUpdateBasins:
    def test_none(_, bsegments):
        assert bsegments._basins is None
        remove = np.array([0, 0, 0, 0, 0, 0], bool)
        output = bsegments._update_basins(remove)
        assert output is None

    def test_unaltered(_, bsegments, basins):
        bsegments.locate_basins()
        original = bsegments._basins
        assert np.array_equal(original, basins)

        remove = np.array([1, 1, 0, 0, 0, 0], bool)
        output = bsegments._update_basins(remove)
        assert output is original

    def test_reset(_, bsegments, basins):
        bsegments.locate_basins()
        original = bsegments._basins
        assert np.array_equal(original, basins)

        remove = np.array([0, 0, 1, 0, 0, 0], bool)
        output = bsegments._update_basins(remove)
        assert output is None


#####
# Filtering
#####


class TestValidateSelection:
    def test_valid_ids(_, segments):
        ids = [2, 4, 5]
        expected = np.array([0, 1, 0, 1, 1, 0], dtype=bool)
        output = segments._validate_selection(ids, None)
        assert np.array_equal(output, expected)

    def test_valid_indices(_, segments):
        indices = np.ones(6).astype(bool)
        output = segments._validate_selection(None, indices)
        assert np.array_equal(output, indices)

    def test_both(_, segments):
        ids = [2, 4, 5]
        indices = np.zeros(6, bool)
        indices[[0, 1]] = True
        output = segments._validate_selection(ids, indices)
        expected = np.array([1, 1, 0, 1, 1, 0], dtype=bool)
        assert np.array_equal(output, expected)

    def test_neither(_, segments):
        output = segments._validate_selection(None, None)
        expected = np.zeros(6, bool)
        assert np.array_equal(output, expected)

    def test_duplicate_ids(_, segments):
        ids = [1, 1, 1, 1, 1]
        output = segments._validate_selection(ids, None)
        expected = np.zeros(6, bool)
        expected[0] = 1
        assert np.array_equal(output, expected)

    def test_booleanish_indices(_, segments):
        indices = np.ones(6, dtype=float)
        output = segments._validate_selection(None, indices)
        assert np.array_equal(output, indices.astype(bool))

    def test_not_boolean_indices(_, segments, assert_contains):
        indices = np.arange(6)
        with pytest.raises(ValueError) as error:
            segments._validate_selection(None, indices)
        assert_contains(error, "indices", "0 or 1")

    def test_indices_wrong_length(_, segments, assert_contains):
        indices = np.ones(10)
        with pytest.raises(ShapeError) as error:
            segments._validate_selection(None, indices)
        assert_contains(error, "indices", "6")

    def test_invalid_ids(_, segments, assert_contains):
        ids = [1, 2, 7]
        with pytest.raises(ValueError) as error:
            segments._validate_selection(ids, None)
        assert_contains(error, "ids[2] (value=7)")


class TestRemovable:
    child = np.array([6, 5, 6, 5, 0, 0, 0, 0, 0, 0]) - 1
    parents = (
        np.array(
            [
                [2, 4],
                [1, 5],
                [0, 0],
                [0, 0],
                [0, 0],
                [0, 0],
                [2, 4],
                [1, 5],
                [2, 0],
                [0, 5],
            ]
        )
        - 1
    )
    requested = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0]).astype(bool)

    def test_both(self):
        output = Segments._removable(
            self.requested, self.child, self.parents, upstream=True, downstream=True
        )
        expected = np.array([0, 0, 1, 0, 1, 0, 1, 0, 1, 0], bool)
        print(output)
        print(expected)
        assert np.array_equal(output, expected)

    def test_up(self):
        output = Segments._removable(
            self.requested, self.child, self.parents, upstream=True, downstream=False
        )
        expected = np.array([0, 0, 1, 0, 1, 0, 0, 0, 0, 0], bool)
        assert np.array_equal(output, expected)

    def test_down(self):
        output = Segments._removable(
            self.requested, self.child, self.parents, upstream=False, downstream=True
        )
        expected = np.array([0, 0, 0, 0, 1, 0, 1, 0, 1, 0], bool)
        assert np.array_equal(output, expected)

    def test_neither(self):
        output = Segments._removable(
            self.requested, self.child, self.parents, upstream=False, downstream=False
        )
        expected = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], bool)
        assert np.array_equal(output, expected)


class TestContinuousRemoval:
    def test_none_requested(_, segments):
        requested = np.zeros(segments.length, bool)
        expected = requested.copy()
        output = segments._continuous_removal(requested, upstream=True, downstream=True)
        assert np.array_equal(output, expected)

    def test_no_edges(_, segments):
        requested = np.zeros(segments.length, bool)
        requested[4] = 1
        output = segments._continuous_removal(requested, upstream=True, downstream=True)
        expected = np.zeros(segments.length, bool)
        assert np.array_equal(output, expected)

    def test_neither(_, segments):
        requested = np.array([1, 0, 1, 0, 0, 1], bool)
        output = segments._continuous_removal(
            requested, upstream=False, downstream=False
        )
        expected = np.array([0, 0, 0, 0, 0, 0], bool)
        assert np.array_equal(output, expected)

    def test_downstream(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments._continuous_removal(
            requested, upstream=False, downstream=True
        )
        expected = np.array([0, 0, 1, 0, 0, 1], bool)
        assert np.array_equal(output, expected)

    def test_upstream(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments._continuous_removal(
            requested, upstream=True, downstream=False
        )
        expected = np.array([0, 1, 1, 0, 0, 0])
        assert np.array_equal(output, expected)

    def test_both(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments._continuous_removal(requested, upstream=True, downstream=True)
        expected = np.array([0, 1, 1, 0, 0, 1])
        assert np.array_equal(output, expected)

    @pytest.mark.parametrize(
        "requested, expected",
        (
            ([1, 1, 0, 0, 0, 1], [1, 0, 0, 0, 0, 1]),
            ([1, 1, 1, 0, 1, 1], [1, 1, 1, 0, 1, 1]),
        ),
    )
    def test_nested_downstream(_, segments, requested, expected):
        requested = np.array(requested, bool)
        expected = np.array(expected, bool)
        output = segments._continuous_removal(
            requested, upstream=False, downstream=True
        )
        assert np.array_equal(output, expected)

    def test_nested_upstream(_, segments):
        requested = np.array([0, 1, 0, 1, 1, 1], bool)
        expected = np.array([0, 1, 0, 1, 1, 0], bool)
        output = segments._continuous_removal(
            requested, upstream=True, downstream=False
        )
        assert np.array_equal(output, expected)


class TestRemove:
    def test_none(
        _, bsegments, bflow, linestrings, indices, bpixels, child, parents, basins
    ):
        bsegments.locate_basins()
        output = bsegments.remove()
        assert bsegments._flow == bflow
        assert bsegments._segments == linestrings
        assert bsegments._indices == indices
        assert np.array_equal(bsegments._npixels, bpixels)
        assert np.array_equal(bsegments._child, child)
        assert np.array_equal(bsegments._parents, parents)
        assert np.array_equal(bsegments._basins, basins)

        expected = np.zeros(bsegments.length, bool)
        assert np.array_equal(output, expected)

    def test_ids(
        _,
        bsegments,
        bflow,
        linestrings245,
        indices245,
        bpixels245,
        child245,
        parents245,
    ):
        bsegments.locate_basins()
        output = bsegments.remove(ids=[1, 3, 6], continuous=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

        expected = np.array([1, 0, 1, 0, 0, 1], bool)
        assert np.array_equal(output, expected)

    def test_indices(
        _,
        bsegments,
        bflow,
        linestrings245,
        indices245,
        bpixels245,
        child245,
        parents245,
    ):
        bsegments.locate_basins()
        indices = np.array([1, 0, 1, 0, 0, 1], bool)
        output = bsegments.remove(indices=indices, continuous=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

        expected = np.array([1, 0, 1, 0, 0, 1], bool)
        assert np.array_equal(output, expected)

    def test_mixed(
        _,
        bsegments,
        bflow,
        linestrings245,
        indices245,
        bpixels245,
        child245,
        parents245,
    ):
        indices = np.array([1, 0, 1, 0, 0, 0], bool)
        ids = [3, 6]
        bsegments.locate_basins()
        output = bsegments.remove(ids=ids, indices=indices, continuous=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

        expected = np.array([1, 0, 1, 0, 0, 1], bool)
        assert np.array_equal(output, expected)

    def test_continuous_removal(_, bsegments, bflow, linestrings, indices, bpixels):
        bsegments.locate_basins()
        output = bsegments.remove(ids=[1, 2, 6], upstream=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings[1:5]
        assert bsegments.indices == indices[1:5]
        assert np.array_equal(bsegments.npixels, bpixels[1:5])

        child = [5, 0, 5, 0]
        assert np.array_equal(bsegments.child, child)

        parents = np.array(
            [
                [0, 0],
                [0, 0],
                [0, 0],
                [2, 4],
            ]
        )
        assert np.array_equal(bsegments.parents, parents)
        assert bsegments._basins is None

        expected = np.array([1, 0, 0, 0, 0, 1], bool)
        assert np.array_equal(output, expected)

    def test_all(_, bsegments, bflow):
        bsegments.locate_basins()
        output = bsegments.remove(ids=[1, 2, 3, 4, 5, 6])
        assert bsegments.flow == bflow
        assert bsegments.segments == []
        assert bsegments.indices == []
        assert bsegments.npixels.size == 0
        assert bsegments.child.size == 0
        assert bsegments.parents.size == 0
        basins = np.zeros(bflow.shape)
        assert bsegments._basins is None

        expected = np.ones(6, bool)
        assert np.array_equal(output, expected)


class TestKeep:
    def test_all(
        _, bsegments, bflow, linestrings, indices, bpixels, child, parents, basins
    ):
        bsegments.locate_basins()
        output = bsegments.keep(ids=[1, 2, 3, 4, 5, 6])
        assert bsegments._flow == bflow
        assert bsegments._segments == linestrings
        assert bsegments._indices == indices
        assert np.array_equal(bsegments._npixels, bpixels)
        assert np.array_equal(bsegments._child, child)
        assert np.array_equal(bsegments._parents, parents)
        assert np.array_equal(bsegments._basins, basins)

        expected = np.ones(6, bool)
        assert np.array_equal(output, expected)

    def test_ids(
        _,
        bsegments,
        bflow,
        linestrings245,
        indices245,
        bpixels245,
        child245,
        parents245,
        basins245,
    ):
        bsegments.locate_basins()
        output = bsegments.keep(ids=[2, 4, 5], continuous=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

        expected = np.array([0, 1, 0, 1, 1, 0], bool)
        assert np.array_equal(output, expected)

    def test_indices(
        _,
        bsegments,
        bflow,
        linestrings245,
        indices245,
        bpixels245,
        child245,
        parents245,
        basins245,
    ):
        bsegments.locate_basins()
        indices = np.array([0, 1, 0, 1, 1, 0], bool)
        output = bsegments.keep(indices=indices, continuous=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

        expected = np.array([0, 1, 0, 1, 1, 0], bool)
        assert np.array_equal(output, expected)

    def test_mixed(
        _,
        bsegments,
        bflow,
        linestrings245,
        indices245,
        bpixels245,
        child245,
        parents245,
        basins245,
    ):
        bsegments.locate_basins()
        indices = np.array([0, 1, 0, 1, 0, 0], bool)
        ids = [4, 5]
        output = bsegments.keep(ids=ids, indices=indices, continuous=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

        expected = np.array([0, 1, 0, 1, 1, 0], bool)
        assert np.array_equal(output, expected)

    def test_continuous_removal(
        _, bsegments, bflow, linestrings, indices, bpixels, child
    ):
        bsegments.locate_basins()
        output = bsegments.keep(ids=[3, 4, 5], upstream=False)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings[1:5]
        assert bsegments.indices == indices[1:5]
        assert np.array_equal(bsegments.npixels, bpixels[1:5])

        child = [5, 0, 5, 0]
        assert np.array_equal(bsegments.child, child)

        parents = np.array(
            [
                [0, 0],
                [0, 0],
                [0, 0],
                [2, 4],
            ]
        )
        assert np.array_equal(bsegments.parents, parents)
        assert bsegments._basins is None

        expected = np.array([0, 1, 1, 1, 1, 0], bool)
        assert np.array_equal(output, expected)

    def test_none(_, bsegments, bflow):
        bsegments.locate_basins()
        output = bsegments.keep()
        assert bsegments.flow == bflow
        assert bsegments.segments == []
        assert bsegments.indices == []
        assert bsegments.npixels.size == 0
        assert bsegments.child.size == 0
        assert bsegments.parents.size == 0
        basins = np.zeros(bflow.shape)
        assert bsegments._basins is None

        expected = np.zeros(6, bool)
        assert np.array_equal(output, expected)


class TestCopy:
    def test(_, segments):
        copy = segments.copy()
        assert copy._basins is None

        segments.locate_basins()
        copy = segments.copy()
        assert isinstance(copy, Segments)
        assert copy._flow is segments._flow
        assert copy._segments == segments._segments
        assert copy._segments is not segments._segments
        assert np.array_equal(copy._ids, segments._ids)
        assert copy._ids is not segments._ids
        assert copy._indices == segments._indices
        assert copy._indices is not segments._indices
        assert np.array_equal(copy._npixels, segments._npixels)
        assert copy._npixels is not segments._npixels
        assert np.array_equal(copy._child, segments._child)
        assert copy._child is not segments._child
        assert np.array_equal(copy._parents, segments._parents)
        assert copy._parents is not segments._parents
        assert np.array_equal(copy._basins, segments._basins)
        assert copy._basins is segments._basins

        del segments
        assert copy._flow is not None
        assert copy._segments is not None
        assert copy._ids is not None
        assert copy._indices is not None
        assert copy._npixels is not None
        assert copy._child is not None
        assert copy._parents is not None
        assert copy._basins is not None


class TestPrune:
    def test_leaf(_, flow, mask):
        mask[4, 2] = 0
        segments = Segments(flow, mask)
        initial = segments.copy()
        assert segments.length == 5

        segments.prune()
        assert segments.length == 4
        assert segments.segments == initial.segments[1:]
        assert np.array_equal(segments.ids, [2, 3, 4, 5])

    def test_multiple_in_one_network(_, flow, mask):
        mask[3, 4] = 0
        segments = Segments(flow, mask)
        initial = segments.copy()
        assert segments.length == 4

        segments.prune()
        assert segments.length == 2
        assert segments.segments == [initial.segments[0], initial.segments[2]]
        assert np.array_equal(segments.ids, [1, 3])

    def test_multiple_networks(_, flow, mask):
        mask[4, 2] = 0
        mask[3, 4] = 0
        segments = Segments(flow, mask)
        assert segments.length == 5
        initial = segments.copy()

        segments.prune()
        assert segments.length == 2
        assert segments.segments == [initial.segments[2], initial.segments[4]]
        assert np.array_equal(segments.ids, [3, 5])


#####
# Export
#####


class TestValidateProperties:
    def test_valid(_, segments):
        props = {"ones": np.ones(6, float), "twos": [2, 2, 2, 2, 2, 2]}
        output, schema = segments._validate_properties(props, terminal=False)
        expected = {"ones": np.ones(6), "twos": np.full(6, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        print(schema)
        assert schema == {"ones": "float", "twos": "int"}

    def test_none(_, segments):
        output, schema = segments._validate_properties(None, terminal=False)
        assert output == {}
        assert schema == {}

    def test_terminal(_, segments):
        props = {"ones": np.ones(2, float), "twos": [2, 2]}
        output, schema = segments._validate_properties(props, terminal=True)
        expected = {"ones": np.ones(2), "twos": np.full(2, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"ones": "float", "twos": "int"}

    def test_not_dict(_, segments, assert_contains):
        with pytest.raises(TypeError) as error:
            segments._validate_properties("invalid", terminal=False)
        assert_contains(error, "properties must be a dict")

    def test_bad_keys(_, segments, assert_contains):
        props = {1: np.ones(6)}
        with pytest.raises(TypeError) as error:
            segments._validate_properties(props, terminal=False)
        assert_contains(error, "key 0")

    def test_wrong_length(_, segments, assert_contains):
        props = {"values": np.ones(7)}
        with pytest.raises(ShapeError) as error:
            segments._validate_properties(props, terminal=False)
        assert_contains(error, "properties['values']")

    def test_nsegments_basins(_, segments):
        props = {"ones": np.ones(6, float), "twos": [2, 2, 2, 2, 2, 2]}
        output, schema = segments._validate_properties(props, terminal=True)
        expected = {"ones": np.ones(2), "twos": np.full(2, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"ones": "float", "twos": "int"}

    def test_bool(_, segments):
        props = {"test": np.ones(6, bool)}
        output, schema = segments._validate_properties(props, False)
        expected = {"test": np.ones(6, int)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "int"}

    def test_str(_, segments):
        props = {"test": np.full(6, "test"), "test2": np.full(6, "longer")}
        output, schema = segments._validate_properties(props, False)
        expected = props
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "str:4", "test2": "str:6"}

    def test_int(_, segments):
        props = {"test": np.ones(6, int)}
        output, schema = segments._validate_properties(props, False)
        expected = {"test": np.ones(6, int)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "int"}

    def test_float(_, segments):
        props = {"test": np.ones(6, "float32")}
        output, schema = segments._validate_properties(props, False)
        expected = {"test": np.ones(6, float)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "float"}


class TestValidateExport:
    def test_valid_no_properties(_, segments):
        type, properties, schema = segments._validate_export(None, "segments")
        assert properties == {}
        assert type == "segments"
        assert schema == {}

    @pytest.mark.parametrize("type", ("segments", "segment outlets"))
    def test_valid_segments_props(_, segments, type):
        props = {"slope": [1, 2, 3, 4, 5, 6]}
        output_type, properties, schema = segments._validate_export(props, type)
        assert isinstance(properties, dict)
        assert list(properties.keys()) == ["slope"]
        assert np.array_equal(
            properties["slope"], np.array([1, 2, 3, 4, 5, 6]).astype(float)
        )
        assert output_type == type
        assert schema == {"slope": "int"}

    @pytest.mark.parametrize("type", ("basins", "outlets"))
    def test_valid_terminal_props(_, segments, type):
        props = {"slope": [1, 2]}
        outtype, properties, schema = segments._validate_export(props, type)
        assert isinstance(properties, dict)
        assert list(properties.keys()) == ["slope"]
        assert np.array_equal(properties["slope"], np.array([1, 2]).astype(float))
        assert outtype == type
        assert schema == {"slope": "int"}

    @pytest.mark.parametrize(
        "type", ("segments", "basins", "outlets", "segment outlets")
    )
    def test_valid_type(_, segments, type):
        outtype, properties, schema = segments._validate_export(None, type)
        assert properties == {}
        assert outtype == type
        assert schema == {}

    def test_type_casing(_, segments):
        outtype, _, _ = segments._validate_export(None, "SeGmEnTs")
        assert outtype == "segments"

    def test_invalid_type(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments._validate_export(None, "invalid")
        assert_contains(error, "type", "segments", "outlets", "basins")

    def test_invalid_props(_, segments, assert_contains):
        with pytest.raises(TypeError) as error:
            segments._validate_export("invalid", "segments")
        assert_contains(error, "properties must be a dict")


class TestBasinPolygons:
    def test(_, bsegments, basins):
        mask = basins.astype(bool)
        expected = rasterio.features.shapes(
            basins, mask, connectivity=8, transform=bsegments.transform.affine
        )
        output = bsegments._basin_polygons()
        assert list(output) == list(expected)


class TestGeojson:
    def test_segments(_, segments):
        segments.keep(ids=[2, 4, 5])
        output = segments.geojson()
        assert isinstance(output, geojson.FeatureCollection)
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[5.5, 3.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[4.5, 3.5], [3.5, 4.5]],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert output == expected

    def test_terminal_outlets(_, segments):
        output = segments.geojson(type="outlets")
        expected = {
            "features": [
                {
                    "geometry": {"coordinates": [5.5, 0.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 6.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert isinstance(output, geojson.FeatureCollection)
        assert output == expected

    def test_segment_outlets(_, segments):
        output = segments.geojson(type="segment outlets")
        expected = {
            "features": [
                {
                    "geometry": {"coordinates": [3.5, 4.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [4.5, 3.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [5.5, 0.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [4.5, 3.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 4.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 6.5], "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert isinstance(output, geojson.FeatureCollection)
        assert output == expected

    def test_basins(_, bsegments):
        output = bsegments.geojson(type="basins")
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [[5.0, 1.0], [5.0, 3.0], [6.0, 3.0], [6.0, 1.0], [5.0, 1.0]]
                        ],
                        "type": "Polygon",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [
                                [1.0, 1.0],
                                [1.0, 4.0],
                                [2.0, 4.0],
                                [2.0, 5.0],
                                [3.0, 5.0],
                                [3.0, 6.0],
                                [5.0, 6.0],
                                [5.0, 4.0],
                                [6.0, 4.0],
                                [6.0, 3.0],
                                [5.0, 3.0],
                                [5.0, 1.0],
                                [1.0, 1.0],
                            ]
                        ],
                        "type": "Polygon",
                    },
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert isinstance(output, geojson.FeatureCollection)
        assert output == expected

    def test_with_properties(_, segments):
        segments.keep(ids=[2, 4, 5])
        properties = {
            "slope": [1, 2, 3],
            "length": [1.1, 2.2, 3.3],
            "astring": ["Low", "Moderate", "High"],
        }
        output = segments.geojson(properties)
        assert isinstance(output, geojson.FeatureCollection)
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {"length": 1.1, "slope": 1, "astring": "Low"},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[5.5, 3.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {"length": 2.2, "slope": 2, "astring": "Moderate"},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[4.5, 3.5], [3.5, 4.5]],
                        "type": "LineString",
                    },
                    "properties": {"length": 3.3, "slope": 3, "astring": "High"},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert output == expected

    def test_bad_properties(_, segments, assert_contains):
        with pytest.raises(TypeError) as error:
            segments.geojson(properties="invalid")
        assert_contains(error, "properties must be a dict")

    def test_bad_type(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            segments.geojson(type="invalid")
        assert_contains(error, "type", "segments", "outlets", "basins")


class TestSave:
    def read(_, path):
        with fiona.open(path, "r") as file:
            geometries = [feature.__geo_interface__ for feature in file]
        for k in range(len(geometries)):
            del geometries[k]["id"]
        return geojson.FeatureCollection(geometries)

    def test_segments(self, segments, tmp_path):
        path = Path(tmp_path) / "output.geojson"
        segments.keep(ids=[2, 4, 5])
        assert not path.is_file()
        segments.save(path)
        assert path.is_file()

        output = self.read(path)
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [(4.5, 1.5), (4.5, 2.5), (4.5, 3.5)],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [(5.5, 3.5), (4.5, 3.5)],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [(4.5, 3.5), (3.5, 4.5)],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert output == expected

    def test_empty(self, segments, tmp_path):
        path = Path(tmp_path) / "output.geojson"
        segments.keep()
        assert not path.is_file()
        segments.save(path)
        assert path.is_file()

        output = self.read(path)
        expected = {"features": [], "type": "FeatureCollection"}
        assert output == expected

    def test_terminal_outlets(self, segments, tmp_path):
        path = Path(tmp_path) / "output.geojson"
        assert not path.is_file()

        segments.save(path, type="outlets")
        assert path.is_file()

        output = self.read(path)
        expected = {
            "features": [
                {
                    "geometry": {"coordinates": (5.5, 0.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": (3.5, 6.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert isinstance(output, geojson.FeatureCollection)
        assert output == expected

    def test_segment_outlets(self, segments, tmp_path):
        path = Path(tmp_path) / "output.geojson"
        assert not path.is_file()

        segments.save(path, type="segment outlets")
        assert path.is_file()

        output = self.read(path)
        expected = {
            "features": [
                {
                    "geometry": {"coordinates": (3.5, 4.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": (4.5, 3.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": (5.5, 0.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": (4.5, 3.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": (3.5, 4.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": (3.5, 6.5), "type": "Point"},
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert isinstance(output, geojson.FeatureCollection)
        assert output == expected

    def test_basins(self, bsegments, tmp_path):
        path = Path(tmp_path) / "output.geojson"
        assert not path.is_file()

        bsegments.save(path, type="basins")
        assert path.is_file()

        output = self.read(path)
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [(5.0, 1.0), (5.0, 3.0), (6.0, 3.0), (6.0, 1.0), (5.0, 1.0)]
                        ],
                        "type": "Polygon",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [
                                (1.0, 1.0),
                                (1.0, 4.0),
                                (2.0, 4.0),
                                (2.0, 5.0),
                                (3.0, 5.0),
                                (3.0, 6.0),
                                (5.0, 6.0),
                                (5.0, 4.0),
                                (6.0, 4.0),
                                (6.0, 3.0),
                                (5.0, 3.0),
                                (5.0, 1.0),
                                (1.0, 1.0),
                            ]
                        ],
                        "type": "Polygon",
                    },
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert isinstance(output, geojson.FeatureCollection)

        print(output["features"][1])
        print(expected["features"][1])
        assert output["features"][1] == expected["features"][1]

        print(output)
        print(expected)
        assert output == expected

    def test_with_properties(self, segments, tmp_path):
        path = Path(tmp_path) / "output.geojson"

        segments.keep(ids=[2, 4, 5])
        properties = {
            "slope": [1, 2, 3],
            "length": [1.1, 2.2, 3.3],
            "astring": ["low", "moderate", "high"],
        }
        assert not path.is_file()

        segments.save(path, properties)
        assert path.is_file()

        output = self.read(path)
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [(4.5, 1.5), (4.5, 2.5), (4.5, 3.5)],
                        "type": "LineString",
                    },
                    "properties": {"length": 1.1, "slope": 1, "astring": "low"},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [(5.5, 3.5), (4.5, 3.5)],
                        "type": "LineString",
                    },
                    "properties": {"length": 2.2, "slope": 2, "astring": "moderate"},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [(4.5, 3.5), (3.5, 4.5)],
                        "type": "LineString",
                    },
                    "properties": {"length": 3.3, "slope": 3, "astring": "high"},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert output == expected

    def test_bad_properties(_, segments, tmp_path, assert_contains):
        path = Path(tmp_path) / "output.geojson"
        with pytest.raises(TypeError) as error:
            segments.save(path, properties="invalid")
        assert_contains(error, "properties must be a dict")

    def test_bad_type(_, segments, tmp_path, assert_contains):
        path = Path(tmp_path) / "output.geojson"
        with pytest.raises(ValueError) as error:
            segments.geojson(path, type="invalid")
        assert_contains(error, "type", "segments", "basins")

    def test_overwrite(self, tmp_path, segments):
        path = Path(tmp_path) / "output.geojson"
        with open(path, "w") as file:
            file.write("some other file")
        assert path.is_file()

        segments.keep(ids=[2, 4, 5])
        segments.save(path, overwrite=True)
        assert path.is_file()

        output = self.read(path)
        expected = {
            "features": [
                {
                    "geometry": {
                        "coordinates": [(4.5, 1.5), (4.5, 2.5), (4.5, 3.5)],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [(5.5, 3.5), (4.5, 3.5)],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [(4.5, 3.5), (3.5, 4.5)],
                        "type": "LineString",
                    },
                    "properties": {},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert output == expected

    def test_invalid_overwrite(_, tmp_path, segments):
        path = Path(tmp_path) / "output.geojson"
        with open(path, "w") as file:
            file.write("some other file")
        assert path.is_file()

        with pytest.raises(FileExistsError):
            segments.save(path, overwrite=False)
