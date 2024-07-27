from math import isnan, nan
from pathlib import Path

import fiona
import geojson
import numpy as np
import pytest
import rasterio.features
from shapely import LineString

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
        segments = Segments(flow, mask, max_length=2.5)
        assert segments._flow == flow
        assert segments._segments == linestrings_split
        assert np.array_equal(segments._ids, np.arange(7) + 1)
        assert segments._indices == indices_split
        assert np.array_equal(segments._npixels, npixels)
        assert np.array_equal(segments._child, child)
        assert np.array_equal(segments._parents, parents)

    def test_units(_, flow, mask, linestrings_split, indices_split):
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
        segments = Segments(flow, mask, max_length=0.0025, units="kilometers")
        assert segments._flow == flow
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
        segments = Segments(flow, mask, max_length=2.5, units="base")

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
        flow = Raster.from_array(flow.values)
        with pytest.raises(MissingCRSError):
            Segments(flow, mask)

    def test_short_maxlength(_, flow, mask, assert_contains):
        with pytest.raises(ValueError) as error:
            Segments(flow, mask, max_length=1)
        assert_contains(error, "max_length", "diagonal")

    def test_short_base_maxlength(_, flow, mask, assert_contains):
        with pytest.raises(ValueError) as error:
            Segments(flow, mask, max_length=1, units="base")
        assert_contains(
            error,
            "max_length (value = 1 metre) must be at least as long as the diagonals of the pixels",
        )


def test_len(segments):
    assert len(segments) == 6


def test_str(segments):
    assert str(segments) == "A set of 6 stream segments in 2 local drainage networks."


def test_geo_interface(segments):
    segments.keep([2, 4, 5], "ids")
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


def test_size(segments):
    assert segments.size == 6


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


def test_terminal_ids(segments):
    assert np.array_equal(segments.terminal_ids, [3, 6])


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

    def test_empty(_, segments):
        indices = np.array([])
        output = segments._indices_to_ids(indices)
        assert np.array_equal(output, [])


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
# Outlets
#####


class TestIsTerminal:
    def test_all(_, segments):
        output = segments.isterminal()
        expected = [False, False, True, False, False, True]
        assert np.array_equal(output, expected)

    def test_ids(_, segments):
        ids = [5, 3]
        output = segments.isterminal(ids)
        expected = [False, True]
        assert np.array_equal(output, expected)


class TestTermini:
    def test_all(_, segments):
        output = segments.termini()
        expected = [6, 6, 3, 6, 6, 6]
        assert np.array_equal(output, expected)

    def test_nested(_, flow, mask):
        mask[4, 2] = 0
        segments = Segments(flow, mask)
        output = segments.termini()
        expected = [1, 5, 3, 5, 5]
        assert np.array_equal(output, expected)

    def test_ids(_, segments):
        ids = [5, 3]
        output = segments.termini(ids)
        expected = [6, 3]
        assert np.array_equal(output, expected)


class TestOutlets:
    def test(_, segments):
        output = segments.outlets()
        expected = [(5, 3), (5, 3), (1, 5), (5, 3), (5, 3), (5, 3)]
        assert output == expected

    def test_ids(_, segments):
        ids = [5, 3]
        output = segments.outlets(ids)
        expected = [(5, 3), (1, 5)]
        assert output == expected

    def test_segment_outlets(_, segments):
        output = segments.outlets(segment_outlets=True)
        expected = [(4, 2), (2, 4), (1, 5), (3, 5), (3, 4), (5, 3)]
        assert output == expected

    def test_as_array(_, segments):
        output = segments.outlets(segment_outlets=True, as_array=True)
        expected = np.array([(4, 2), (2, 4), (1, 5), (3, 5), (3, 4), (5, 3)]).reshape(
            -1, 2
        )
        assert np.array_equal(output, expected)


#####
# Local Networks
#####


class TestGetParents:
    def test_top(_, segments):
        output = segments._get_parents(0)
        assert np.array_equal(output, [])

    def test(_, segments):
        output = segments._get_parents(5)
        assert np.array_equal(output, [0, 4])


class TestParents:
    def test(_, segments):
        output = segments.parents(5)
        assert output == [2, 4]

    def test_none(_, segments):
        output = segments.parents(1)
        assert output is None


class TestChild:
    def test(_, segments):
        output = segments.child(2)
        assert output == 5

    def test_none(_, segments):
        output = segments.child(3)
        assert output is None


class TestAncestors:
    def test_top(_, segments):
        output = segments.ancestors(1)
        assert np.array_equal(output, [])

    def test(_, segments):
        output = segments.ancestors(6)
        assert np.array_equal(output, [1, 5, 2, 4])


class TestDescendents:
    def test_bottom(_, segments):
        output = segments.descendents(6)
        assert np.array_equal(output, [])

    def test(_, segments):
        output = segments.descendents(2)
        assert np.array_equal(output, [5, 6])


class TestFamily:
    def test_isolated(_, segments):
        output = segments.family(3)
        assert np.array_equal(output, [3])

    def test(_, segments):
        output = segments.family(5)
        assert np.array_equal(output, [6, 1, 5, 2, 4])


class TestIsNested:
    def test_no_nests(_, segments):
        output = segments.isnested()
        expected = [False] * 6
        assert np.array_equal(output, expected)

    def test_nested(_, flow, mask):
        mask[4, 2] = 0
        segments = Segments(flow, mask)
        output = segments.isnested()
        expected = [True, False, False, False, False]
        assert np.array_equal(output, expected)

    def test_multiple_in_one_network(_, flow, mask):
        mask[3, 4] = 0
        segments = Segments(flow, mask)
        output = segments.isnested()
        expected = [False, True, False, True]
        assert np.array_equal(output, expected)

    def test_multiple_nests(_, flow, mask):
        mask[4, 2] = 0
        mask[3, 4] = 0
        segments = Segments(flow, mask)
        output = segments.isnested()
        expected = [True, True, False, True, False]
        assert np.array_equal(output, expected)

    def test_ids(_, flow, mask):
        mask[4, 2] = 0
        segments = Segments(flow, mask)
        ids = [3, 1]
        output = segments.isnested(ids)
        assert np.array_equal(output, [False, True])


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


class TestArea:
    def test_basic(_, segments, flow, npixels):
        output = segments.area(units="base")
        expected = npixels * flow.transform.pixel_area()
        assert np.array_equal(output, expected)

    def test_kilometers(_, segments, flow, npixels):
        output = segments.area()
        expected = npixels * flow.transform.pixel_area("kilometers")
        assert np.array_equal(output, expected)

    def test_masked(_, segments, mask2, flow):
        output = segments.area(mask2, units="base")
        npixels = np.array([0, 2, 2, 1, 4, 4])
        expected = flow.transform.pixel_area() * npixels
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, flow, npixels):
        output = segments.area(units="base", terminal=True)
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
        output = segments.burned_area(mask2, units="base")
        expected = np.array([0, 2, 2, 1, 4, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, flow, mask2):
        output = segments.burned_area(mask2, units="base", terminal=True)
        expected = np.array([2, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)


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
        flow = Raster.from_array(
            flow, nodata=0, transform=segments.transform, crs=segments.crs
        )
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

    def test_crs_meters(_, segments, dem):
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

    def test_crs_not_meters(_, segments, dem):
        segments._flow.override(crs=4326)
        output = segments.confinement(dem, neighborhood=2)
        expected = np.array(
            [
                180.00200957,
                180.00888846,
                179.99600663,
                180.00257637,
                179.99253076,
                179.99458963,
            ]
        )
        assert np.allclose(output, expected)

    def test_convert_units(_, segments, dem):
        dem = Raster.from_array(dem.values / 1000, nodata=dem.nodata)
        output = segments.confinement(dem, neighborhood=2, dem_per_m=0.001)
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


class TestDevelopedArea:
    def test(_, segments, flow, mask2):
        output = segments.developed_area(mask2, units="base")
        expected = np.array([0, 2, 2, 1, 4, 4]) * flow.transform.pixel_area()
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, flow, mask2):
        output = segments.developed_area(mask2, units="base", terminal=True)
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


class TestLength:
    def test_base_unit(_, segments, linestrings):
        expected = np.array([segment.length for segment in linestrings])
        output = segments.length(units="base")
        assert np.array_equal(output, expected)

    def test(_, segments, linestrings):
        expected = np.array([segment.length for segment in linestrings])
        expected = expected / 1000
        output = segments.length(units="kilometers")
        assert np.array_equal(output, expected)

    def test_terminal(_, segments, linestrings):
        expected = np.array([segment.length for segment in linestrings])
        expected = expected / 1000
        expected = expected[[False, False, True, False, False, True]]
        output = segments.length(terminal=True, units="kilometers")
        assert np.array_equal(output, expected)


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

    def test_conversion(_, segments, values, flow, npixels):
        values._values = values.values.copy() / 1000
        output = segments.ruggedness(values, relief_per_m=0.001)
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

    def test_keep_neither(self):
        output = Segments._removable(
            self.requested,
            self.child,
            self.parents,
            keep_upstream=False,
            keep_downstream=False,
        )
        expected = np.array([0, 0, 1, 0, 1, 0, 1, 0, 1, 0], bool)
        print(output)
        print(expected)
        assert np.array_equal(output, expected)

    def test_keep_down(self):
        output = Segments._removable(
            self.requested,
            self.child,
            self.parents,
            keep_upstream=False,
            keep_downstream=True,
        )
        expected = np.array([0, 0, 1, 0, 1, 0, 0, 0, 0, 0], bool)
        assert np.array_equal(output, expected)

    def test_keep_up(self):
        output = Segments._removable(
            self.requested,
            self.child,
            self.parents,
            keep_upstream=True,
            keep_downstream=False,
        )
        expected = np.array([0, 0, 0, 0, 1, 0, 1, 0, 1, 0], bool)
        assert np.array_equal(output, expected)

    def test_keep_both(self):
        output = Segments._removable(
            self.requested,
            self.child,
            self.parents,
            keep_upstream=True,
            keep_downstream=True,
        )
        expected = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], bool)
        assert np.array_equal(output, expected)


class TestContinuous:
    def test_none(_, segments):
        requested = np.zeros(segments.size, bool)
        expected = requested.copy()
        output = segments.continuous(requested, remove=True)
        assert np.array_equal(output, expected)

    def test_no_edges(_, segments):
        requested = np.zeros(segments.size, bool)
        requested[4] = 1
        output = segments.continuous(requested, remove=True)
        expected = np.zeros(segments.size, bool)
        assert np.array_equal(output, expected)

    def test_neither_up_nor_down(_, segments):
        requested = np.array([1, 0, 1, 0, 0, 1], bool)
        output = segments.continuous(
            requested, remove=True, keep_upstream=True, keep_downstream=True
        )
        expected = np.array([0, 0, 0, 0, 0, 0], bool)
        assert np.array_equal(output, expected)

    def test_no_up(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments.continuous(requested, remove=True, keep_upstream=True)
        expected = np.array([0, 0, 1, 0, 0, 1], bool)
        assert np.array_equal(output, expected)

    def test_no_down(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments.continuous(requested, remove=True, keep_downstream=True)
        expected = np.array([0, 1, 1, 0, 0, 0])
        assert np.array_equal(output, expected)

    def test_both_up_and_down(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments.continuous(requested, remove=True)
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
        output = segments.continuous(requested, remove=True, keep_upstream=True)
        assert np.array_equal(output, expected)

    def test_nested_upstream(_, segments):
        requested = np.array([0, 1, 0, 1, 1, 1], bool)
        expected = np.array([0, 1, 0, 1, 1, 0], bool)
        output = segments.continuous(requested, remove=True, keep_downstream=True)
        assert np.array_equal(output, expected)

    def test_indices(_, segments):
        requested = np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments.continuous(requested, remove=True)
        expected = np.array([0, 1, 1, 0, 0, 1])
        assert np.array_equal(output, expected)

    def test_ids(_, segments):
        ids = [2, 6, 3]
        output = segments.continuous(ids, type="ids", remove=True)
        expected = np.array([0, 1, 1, 0, 0, 1])
        assert np.array_equal(output, expected)

    def test_keep(_, segments):
        requested = ~np.array([0, 1, 1, 0, 0, 1], bool)
        output = segments.continuous(requested, keep_upstream=True)
        expected = ~np.array([0, 0, 1, 0, 0, 1], bool)
        assert np.array_equal(output, expected)


class TestRemove:
    def test_none(
        _, bsegments, bflow, linestrings, indices, bpixels, child, parents, basins
    ):
        bsegments.locate_basins()
        bsegments.remove(np.zeros(6))
        assert bsegments._flow == bflow
        assert bsegments._segments == linestrings
        assert bsegments._indices == indices
        assert np.array_equal(bsegments._npixels, bpixels)
        assert np.array_equal(bsegments._child, child)
        assert np.array_equal(bsegments._parents, parents)
        assert np.array_equal(bsegments._basins, basins)

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
        bsegments.remove([1, 3, 6], "ids")
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

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
        bsegments.remove(indices)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

    def test_all(_, bsegments, bflow):
        bsegments.locate_basins()
        bsegments.remove([1, 2, 3, 4, 5, 6], "ids")
        assert bsegments.flow == bflow
        assert bsegments.segments == []
        assert bsegments.indices == []
        assert bsegments.npixels.size == 0
        assert bsegments._child.size == 0
        assert bsegments._parents.size == 0
        assert bsegments._basins is None


class TestKeep:
    def test_all(
        _, bsegments, bflow, linestrings, indices, bpixels, child, parents, basins
    ):
        bsegments.locate_basins()
        bsegments.keep([1, 2, 3, 4, 5, 6], "ids")
        assert bsegments._flow == bflow
        assert bsegments._segments == linestrings
        assert bsegments._indices == indices
        assert np.array_equal(bsegments._npixels, bpixels)
        assert np.array_equal(bsegments._child, child)
        assert np.array_equal(bsegments._parents, parents)
        assert np.array_equal(bsegments._basins, basins)

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
        bsegments.keep([2, 4, 5], "ids")
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

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
        keep = np.array([0, 1, 0, 1, 1, 0], bool)
        bsegments.keep(keep)
        assert bsegments.flow == bflow
        assert bsegments.segments == linestrings245
        assert bsegments.indices == indices245
        assert np.array_equal(bsegments.npixels, bpixels245)
        assert np.array_equal(bsegments._child, child245)
        assert np.array_equal(bsegments._parents, parents245)
        assert bsegments._basins is None

    def test_none(_, bsegments, bflow):
        bsegments.locate_basins()
        bsegments.keep(np.zeros(6))
        assert bsegments.flow == bflow
        assert bsegments.segments == []
        assert bsegments.indices == []
        assert bsegments.npixels.size == 0
        assert bsegments._child.size == 0
        assert bsegments._parents.size == 0
        assert bsegments._basins is None


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


#####
# Export
#####


class TestBasinPolygons:
    def test(_, bsegments, basins):
        mask = basins.astype(bool)
        expected = rasterio.features.shapes(
            basins, mask, connectivity=8, transform=bsegments.transform.affine
        )
        output = bsegments._basin_polygons()
        assert list(output) == list(expected)


class TestGeojson:
    def test_crs_segments(_, segments):
        segments.keep([2, 4, 5], "ids")
        output0 = segments.geojson()
        output1 = segments.geojson(crs=5070)
        print(output0)
        print("-----")
        print(output1)
        assert False

    def test_crs_outlets(_, segments):
        output0 = segments.geojson(type="outlets")
        output1 = segments.geojson(type="outlets", crs=5070)
        print(output0)
        print("----------")
        print(output1)
        assert False

    def test_crs_basins(_, segments):
        output0 = segments.geojson(type="basins")
        output1 = segments.geojson(type="basins", crs=5070)
        print(output0)
        print("----------")
        print(output1)
        assert False

    def test_segments(_, segments):
        segments.keep([2, 4, 5], "ids")
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
        segments.keep([2, 4, 5], "ids")
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
        segments.keep([2, 4, 5], "ids")
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
        segments.keep(np.zeros(segments.size))
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

        segments.keep([2, 4, 5], "ids")
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

        segments.keep([2, 4, 5], "ids")
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
