"""
test_segments  Unit tests for stream segment filtering
----------
These unit tests are designed to proceed through the module's functions in order
of increasing interdependency. In this way, low-level errors can be identified
before testing more complex, user-facing functions.

The tests use a number of pytest fixtures. Many fixtures are grouped by a common
suffix. These include:
    5: For 5x5 raster datasets - often used to test Segments constructors and filters
    3: For 3x3 datasets - often used to test statistical summary values
    c: Values used to test confinement angle calculations

The tests for each function and class method are grouped into a class. The exception
is for the _Kernel class - all tests for this class are grouped into a single class.
The tests are organized as follows:

* Small utility functions for implementing the tests
* Fixtures
* RasterShapeError
* _Kernel class
* Internal Segments class
* User-facing Segments class
* Filter function and support

RUN THE TESTS:
    * Install pytest, rasterio, and numpy
    * Run `pytest tests/test_segments.py --cov=pfdf.segments --cov-fail-under=95`
      from the OS command line.
"""

from math import sqrt

import numpy as np
import pytest
import rasterio

from pfdf import _validate, segments
from pfdf._rasters import Raster as _Raster
from pfdf.errors import RasterShapeError
from pfdf.segments import Segments


#####
# Testing Utilities
#####
def index_dict(indices):
    for key, (rows, cols) in indices.items():
        indices[key] = (index_array(rows), index_array(cols))
    return indices


def index_array(ints):
    return np.array(ints, dtype="int64").reshape(-1)


def validate_indices(output, expected):
    assert isinstance(output, dict)
    assert sorted(output.keys()) == sorted(expected.keys())
    for key, value in output.items():
        assert isinstance(value, tuple)
        assert len(value) == 2
        assert np.array_equal(value[0], expected[key][0])
        assert np.array_equal(value[1], expected[key][1])


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


#####
# Pytest Fixtures
#####

# Kernel Fixtures


@pytest.fixture
def kernel():
    return segments._Kernel(4, 100, 250)


@pytest.fixture
def kernel5(kernel):
    kernel.update(5, 5)
    return kernel


@pytest.fixture
def kernel2():
    kernel = segments._Kernel(2, 5, 5)
    kernel.update(2, 2)
    return kernel


@pytest.fixture
def dem():
    return np.array(
        [
            [21, 98, 23, 98, 24],
            [98, 20, 22, 25, 98],
            [19, 18, 99, 10, 11],
            [98, 16, 15, 13, 98],
            [17, 98, 14, 98, 12],
        ]
    )


# Segments Fixtures


@pytest.fixture
def stream():
    return np.array(
        [
            [0, 1, 0, 2, 5],
            [1, 1, 0, 2, 0],
            [0, 4, 0, 2, 0],
            [4, 0, 2, 0, 0],
            [4, 0, 2, 0, 3],
        ]
    )


@pytest.fixture
def flow(stream):
    stream[stream == 0] = 6
    return stream


@pytest.fixture
def indices():
    indices = {
        1: ([0, 1, 1], [1, 0, 1]),
        2: ([0, 1, 2, 3, 4], [3, 3, 3, 2, 2]),
        3: ([4], [4]),
        4: ([2, 3, 4], [1, 0, 0]),
        5: ([0], [4]),
    }
    return index_dict(indices)


@pytest.fixture
def stream_path(tmp_path, stream):
    filepath = tmp_path / "stream.tif"
    with rasterio.open(
        filepath,
        "w",
        driver="GTiff",
        height=5,
        width=5,
        count=1,
        nodata=-999,
        dtype=stream.dtype,
        crs="+proj=latlong",
        transform=rasterio.transform.Affine(300, 0, 101985, 0, -300, 2826915),
    ) as raster:
        nulls = stream == 0
        stream[np.nonzero(nulls)] = -999
        raster.write(stream, indexes=1)
        valid = np.logical_not(nulls)
        raster.write_mask(valid)
    return filepath


@pytest.fixture
def segments5(stream):
    return Segments(stream)


@pytest.fixture
def stream0(stream):
    return np.zeros(stream.shape)


@pytest.fixture
def segments0(stream0):
    return Segments(stream0)


# Stream raster with 3 segments
@pytest.fixture
def stream3():
    return np.array(
        [
            [0, 2, 2],
            [1, 2, 0],
            [1, 0, 3],
        ]
    )


# Segments object for network with 3 segments
@pytest.fixture
def segments3(stream3):
    return Segments(stream3)


# Raster for network with 3 segments
@pytest.fixture
def values3():
    return np.array(
        [
            [999, 3, 4],
            [-8, 2, 999],
            [-9, 999, 2.2],
        ]
    )


# Values raster for testing catchment mean
@pytest.fixture
def catchment3():
    return np.array([[1, 6, 7], [2, 5, 8], [3, 4, 9]])


# Flow raster for catchment means
@pytest.fixture
def flow3():
    return np.array([[7, 1, 3], [7, 3, 7], [7, 3, 1]])


# Data mask for catchment means
@pytest.fixture
def mask3():
    return np.array(
        [
            [0, 1, 1],
            [1, 0, 1],
            [1, 0, 0],
        ]
    )


@pytest.fixture
def indices3():
    indices = {1: ([1, 2], [0, 0]), 2: ([0, 0, 1], [1, 2, 1]), 3: ([2], [2])}
    return index_dict(indices)


# A stream raster for confinement angle tests
@pytest.fixture
def streamc():
    return np.array([[0, 0, 0], [1, 2, 0], [0, 0, 0]])


# A Segments object for confinement tests
@pytest.fixture
def segmentsc(streamc):
    return Segments(streamc)


# Flow raster based on confinement stream raster
@pytest.fixture
def flowc():
    return np.array([[8, 8, 8], [1, 5, 8], [8, 8, 8]])


# Sample DEM for confinement tests
@pytest.fixture
def demc():
    return np.array([[1, sqrt(3), 0], [0, 0, 0], [1 / sqrt(3), 0, 0]])


#####
# Kernel
#####


class TestKernel:
    def test_init(_):
        kernel = segments._Kernel(4, 100, 250)
        assert isinstance(kernel, segments._Kernel)
        assert kernel.N == 4
        assert kernel.nRows == 100
        assert kernel.nCols == 250
        assert kernel.row is None
        assert kernel.col is None

    def test_update(_, kernel):
        kernel.update(16, 17)
        assert kernel.row == 16
        assert kernel.col == 17

    @pytest.mark.parametrize(
        "before, expected", [(True, range(4, 6)), (False, range(2, 4))]
    )
    def test_limit(_, before, expected):
        output = segments._Kernel.limit(2, range(2, 6), before)
        assert output == expected

    def test_indices(_, kernel):
        assert kernel.indices(5, 10, before=True) == [1, 2, 3, 4]
        assert kernel.indices(5, 10, before=False) == [6, 7, 8, 9]
        assert kernel.indices(2, 10, before=True) == [0, 1]
        assert kernel.indices(8, 10, before=False) == [9]

    def test_lateral(_, kernel):
        assert kernel.lateral(5, 10, 5, True, True) == (
            [5, 5, 5, 5],
            [1, 2, 3, 4],
        )  # Left
        assert kernel.lateral(5, 10, 5, False, True) == (
            [5, 5, 5, 5],
            [6, 7, 8, 9],
        )  # Right
        assert kernel.lateral(5, 10, 5, True, False) == (
            [1, 2, 3, 4],
            [5, 5, 5, 5],
        )  # Up
        assert kernel.lateral(5, 10, 5, False, False) == (
            [6, 7, 8, 9],
            [5, 5, 5, 5],
        )  # Down

    def test_lateral_edge(_, kernel):
        assert kernel.lateral(1, 10, 2, True, True) == ([2], [0])
        assert kernel.lateral(8, 10, 2, False, True) == ([2], [9])
        assert kernel.lateral(1, 10, 2, True, False) == ([0], [2])
        assert kernel.lateral(8, 10, 2, False, False) == ([9], [2])

        assert kernel.lateral(0, 10, 2, True, True) == ([], [])
        assert kernel.lateral(9, 10, 2, False, True) == ([], [])
        assert kernel.lateral(0, 10, 2, True, False) == ([], [])
        assert kernel.lateral(9, 10, 2, False, False) == ([], [])

    def test_diagonal(_, kernel5):
        assert kernel5.diagonal(True, True) == ([1, 2, 3, 4], [1, 2, 3, 4])
        assert kernel5.diagonal(False, False) == ([6, 7, 8, 9], [6, 7, 8, 9])
        assert kernel5.diagonal(True, False) == ([1, 2, 3, 4], [6, 7, 8, 9])
        assert kernel5.diagonal(False, True) == ([6, 7, 8, 9], [1, 2, 3, 4])

    def test_diagonal_edge(_, kernel):
        kernel.update(1, 1)
        assert kernel.diagonal(True, True) == ([0], [0])
        kernel.update(1, 248)
        assert kernel.diagonal(True, False) == ([0], [249])
        kernel.update(98, 248)
        assert kernel.diagonal(False, False) == ([99], [249])
        kernel.update(98, 1)
        assert kernel.diagonal(False, True) == ([99], [0])

        kernel.update(0, 0)
        assert kernel.diagonal(True, True) == ([], [])
        kernel.update(0, 249)
        assert kernel.diagonal(True, False) == ([], [])
        kernel.update(99, 249)
        assert kernel.diagonal(False, False) == ([], [])
        kernel.update(99, 0)
        assert kernel.diagonal(False, True) == ([], [])

    def test_vertical(_, kernel5):
        assert kernel5.vertical(True) == ([1, 2, 3, 4], [5, 5, 5, 5])
        assert kernel5.vertical(False) == ([6, 7, 8, 9], [5, 5, 5, 5])

    def test_horizontal(_, kernel5):
        assert kernel5.horizontal(True) == ([5, 5, 5, 5], [1, 2, 3, 4])
        assert kernel5.horizontal(False) == ([5, 5, 5, 5], [6, 7, 8, 9])

    def test_identity(_, kernel5):
        assert kernel5.identity(True) == ([1, 2, 3, 4], [1, 2, 3, 4])
        assert kernel5.identity(False) == ([6, 7, 8, 9], [6, 7, 8, 9])

    def test_exchange(_, kernel5):
        assert kernel5.exchange(True) == ([1, 2, 3, 4], [9, 8, 7, 6])
        assert kernel5.exchange(False) == ([6, 7, 8, 9], [4, 3, 2, 1])

    def test_left(_, kernel5):
        assert kernel5.left() == ([5, 5, 5, 5], [1, 2, 3, 4])

    def test_right(_, kernel5):
        assert kernel5.right() == ([5, 5, 5, 5], [6, 7, 8, 9])

    def test_up(_, kernel5):
        assert kernel5.up() == ([1, 2, 3, 4], [5, 5, 5, 5])

    def test_down(_, kernel5):
        assert kernel5.down() == ([6, 7, 8, 9], [5, 5, 5, 5])

    def test_upleft(_, kernel5):
        assert kernel5.upleft() == ([1, 2, 3, 4], [1, 2, 3, 4])

    def test_downright(_, kernel5):
        assert kernel5.downright() == ([6, 7, 8, 9], [6, 7, 8, 9])

    def test_upright(_, kernel5):
        assert kernel5.upright() == ([1, 2, 3, 4], [9, 8, 7, 6])

    def test_downleft(_, kernel5):
        assert kernel5.downleft() == ([6, 7, 8, 9], [4, 3, 2, 1])

    @pytest.mark.parametrize(
        "flow, height",
        (
            (0, 11),
            (1, 25),
            (2, 23),
            (3, 21),
            (4, 19),
            (5, 17),
            (6, 15),
            (7, 13),
        ),
    )
    def test_max_height(_, kernel2, dem, flow, height):
        output = kernel2.max_height(flow, dem, nodata=None)
        assert output == height

    def test_max_height_nodata(_, kernel2, dem):
        output = kernel2.max_height(flow=0, dem=dem, nodata=10)
        assert np.isnan(output)
        output = kernel2.max_height(flow=1, dem=dem, nodata=25)
        assert np.isnan(output)

    @pytest.mark.parametrize(
        "flow, slopes",
        [
            (1, [1.4, 2.2]),
            (8, [1.6, 2.4]),
            (7, [1.8, 1.0]),
            (6, [2.0, 1.2]),
            (5, [2.2, 1.4]),
            (4, [2.4, 1.6]),
            (3, [1.0, 1.8]),
            (2, [1.2, 2.0]),
        ],
    )
    def test_orthogonal_slopes(_, kernel2, dem, flow, slopes):
        dem[2, 2] = 1
        output = kernel2.orthogonal_slopes(flow, length=10, dem=_Raster(dem))
        slopes = np.array(slopes).reshape(1, 2)
        assert np.array_equal(output, slopes)

    def test_orthogonal_slopes_nodata(_, kernel2, dem):
        dem[2, 2] = 1
        dem = _Raster(dem)
        dem.nodata = 23
        output = kernel2.orthogonal_slopes(flow=1, length=10, dem=dem)
        expected = np.array([1.4, np.nan]).reshape(1, 2)
        assert np.array_equal(output, expected, equal_nan=True)

        dem.nodata = 16
        output = kernel2.orthogonal_slopes(flow=8, length=10, dem=dem)
        expected = np.array([np.nan, 2.4]).reshape(1, 2)
        assert np.array_equal(output, expected, equal_nan=True)


#####
# Segments: Properties, Dunders, and Internal
#####


class TestInit:
    @staticmethod
    def validate(segments, indices):
        assert isinstance(segments, Segments)
        validate_indices(segments._indices, indices)
        assert segments._raster_shape == (5, 5)

    def test(self, stream, indices):
        segments = Segments(stream)
        self.validate(segments, indices)

    def test_negative_nodata(self, stream_path, indices):
        segments = Segments(stream_path)
        self.validate(segments, indices)

    def test_floating_ints(self, stream, indices):
        stream = stream.astype(float)
        segments = Segments(stream)
        self.validate(segments, indices)

    def test_nosegments(self, stream0):
        segments = Segments(stream0)
        assert isinstance(segments, Segments)
        assert segments._indices == {}

    def test_negative_failed(self, stream):
        stream[0, 0] = -1
        with pytest.raises(ValueError):
            Segments(stream)

    def test_nonint_failed(self, stream):
        stream = stream.astype(float)
        stream[0, 0] = 2.2
        with pytest.raises(ValueError):
            Segments(stream)

    def test_ND_failed(self, stream):
        stream = np.stack((stream, stream))
        with pytest.raises(_validate.DimensionError):
            Segments(stream)


class TestIds:
    def test(_, segments5):
        ids = segments5.ids
        expected = np.array([1, 2, 3, 4, 5])
        assert np.array_equal(ids, expected)

    def test_empty(_, segments0):
        ids = segments0.ids
        expected = np.array([], dtype=int)
        assert np.array_equal(ids, expected)


class TestIndices:
    def test(_, segments5, indices):
        validate_indices(segments5.indices, indices)

    def test_empty(_, segments0, indices):
        validate_indices(segments0.indices, {})


class TestRasterShape:
    def test(_, segments5):
        assert segments5.raster_shape == (5, 5)


class TestLen:
    def test(_, segments5, segments0):
        assert len(segments5) == 5
        assert len(segments0) == 0


class TestStr:
    def test(_, segments5, segments0):
        assert str(segments5) == "Stream Segments: 1, 2, 3, 4, 5"
        assert str(segments0) == "Stream Segments: None"


class TestValidate:
    @pytest.mark.parametrize("load", [(True), (False)])
    def test_valid_numpy(_, segments5, stream, load):
        output = segments5._validate(stream, "", load=load)
        assert isinstance(output, _Raster)
        assert np.array_equal(output.values, stream)

    def test_valid_file(_, segments5, stream_path):
        output = segments5._validate(stream_path, "")
        assert isinstance(output, _Raster)
        assert np.array_equal(output.values, _Raster(stream_path).values)

    def test_file_noload(_, segments5, stream_path):
        output = segments5._validate(str(stream_path), "", load=False)
        assert isinstance(output, _Raster)
        assert output.values is None

    def test_not_raster(_, segments5, stream):
        bad = np.stack((stream, stream))
        name = "raster name"
        with pytest.raises(_validate.DimensionError) as error:
            segments5._validate(bad, name)
        assert_contains(error, name)

    def test_wrong_shape(_, segments5):
        bad = np.array([1, 2, 3])
        name = "raster name"
        with pytest.raises(RasterShapeError) as error:
            segments5._validate(bad, name)
        assert_contains(error, name)


class TestFlowLength:
    @pytest.mark.parametrize(
        "flow, expected",
        [(1, 10), (2, 14), (3, 10), (4, 14), (5, 10), (6, 14), (7, 10), (8, 14)],
    )
    def test(_, flow, expected):
        assert Segments._flow_length(flow, 10, 14) == expected


class TestConfinementAngle:
    def test_single_pixel(_):
        # 45 degree slope on either side. 90 degrees of empty space remain from open plain
        slopes = np.array([1, 1]).reshape(1, 2)
        assert Segments._confinement_angle(slopes) == 90

    def test_multiple(_):
        # clockwise slopes are 45 and 30. counterclockwise are 60 and 0.
        # Mean slopes are 37.5 and 30 so 112.5 degrees of open space remain from open plain
        slopes = np.array(
            [
                [1, sqrt(3)],
                [1 / sqrt(3), 0],
            ]
        )
        assert Segments._confinement_angle(slopes) == 112.5


class Test_Confinement:
    def test(_, segmentsc, flowc, demc):
        expected = np.array([105, 120])
        dem = _Raster(demc)
        flow = _Raster(flowc)
        output = segmentsc._confinement(dem, flow, 1, 1)
        assert np.array_equal(output, expected)

    def test_flow_nodata(_, segmentsc, flowc, demc):
        expected = np.array([np.nan, 120])
        dem = _Raster(demc)
        flow = _Raster(flowc)
        flow.nodata = 1
        output = segmentsc._confinement(dem, flow, N=1, resolution=1)
        assert np.array_equal(output, expected, equal_nan=True)

    def test_dem_nodata(_, segmentsc, flowc, demc):
        expected = np.array([np.nan, 120])
        dem = _Raster(demc)
        dem.nodata = 1
        flow = _Raster(flowc)
        output = segmentsc._confinement(dem, flow, 1, 1)
        assert np.array_equal(output, expected, equal_nan=True)


class Test_Summary:
    def test_mean(_, segments3, values3):
        expected = np.array([-8.5, 3, 2.2])
        output = segments3._summary(_Raster(values3), np.mean)
        assert np.array_equal(output, expected)

    def test_max(_, segments3, values3):
        expected = np.array([-8, 4, 2.2])
        output = segments3._summary(_Raster(values3), np.amax)
        assert np.array_equal(output, expected)

    def test_nodata(_, segments3, values3):
        expected = np.array([-8.5, 3, 2.2])
        raster = _Raster(values3)
        raster.nodata = -8.5
        output = segments3._summary(raster, np.mean)
        assert np.array_equal(output, expected, equal_nan=True)


#####
# Segments: User-facing
#####


class TestBasins:
    def test(_, segments3, values3):
        expected = np.array([-8, 4, 2.2])
        output = segments3.basins(values3)
        assert np.array_equal(output, expected)

    def test_invalid(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segments3.basins(values3)
        assert_contains(error, "upslope_basins")


@pytest.mark.taudem
class TestCatchmentMean:
    def test_have_npixels(_, segments3, flow3, catchment3):
        # Use npixels=1 (instead of real N) to check not calculating internally
        # Value should be sum rather than mean.
        npixels = np.ones((3,))
        expected = np.array([6, 22, 17]).reshape(-1)
        output = segments3.catchment_mean(flow3, catchment3, npixels=npixels)
        assert np.array_equal(output, expected)

    def test_npixels_0(_, segments3, flow3, catchment3):
        npixels = np.array([0, 1, 1])
        expected = np.array([np.nan, 22, 17]).reshape(-1)
        output = segments3.catchment_mean(flow3, catchment3, npixels=npixels)
        assert np.array_equal(output, expected, equal_nan=True)

    def test_standard(_, segments3, flow3, catchment3):
        expected = np.array([2, 5.5, 8.5]).reshape(-1)
        output = segments3.catchment_mean(flow3, catchment3)
        assert np.array_equal(output, expected)

    def test_masked(_, segments3, flow3, catchment3, mask3):
        expected = np.array([2.5, 6.5, 8]).reshape(-1)
        output = segments3.catchment_mean(flow3, catchment3, mask=mask3)
        assert np.array_equal(output, expected)

    def test_mask_and_npixels(_, segments3, flow3, catchment3, mask3):
        npixels = np.ones((3,))
        expected = np.array([5, 13, 8])
        output = segments3.catchment_mean(
            flow3, catchment3, npixels=npixels, mask=mask3
        )
        assert np.array_equal(output, expected)


# Note that the actual confinement angle calculations are tested in
# Test_Confinements. Only need to check the validation steps for this function
class TestConfinement:
    def test(_, segmentsc, demc, flowc):
        expected = np.array([105, 120])
        output = segmentsc.confinement(demc, flowc, 1, 1)
        assert np.array_equal(output, expected)

    def test_invalid_dem(_, segmentsc, demc, flowc):
        demc = np.concatenate((demc, demc), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segmentsc.confinement(demc, flowc, 1, 1)
        assert_contains(error, "dem")

    def test_invalid_flow_shape(_, segmentsc, demc, flowc):
        flowc = np.concatenate((flowc, flowc), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segmentsc.confinement(demc, flowc, 1, 1)
        assert_contains(error, "flow_directions")

    def test_invalid_flow_values(_, segmentsc, demc, flowc):
        flowc[0, 0] = 0
        with pytest.raises(ValueError) as error:
            segmentsc.confinement(demc, flowc, 1, 1)
        assert_contains(error, "flow_directions")

    def test_invalid_N(_, segmentsc, demc, flowc):
        with pytest.raises(ValueError) as error:
            segmentsc.confinement(demc, flowc, -2, 1)
        assert_contains(error, "N")

    def test_invalid_resolution(_, segmentsc, demc, flowc):
        with pytest.raises(ValueError) as error:
            segmentsc.confinement(demc, flowc, 1, -2)
        assert_contains(error, "resolution")


class TestCopy:
    def test(_, segments3):
        output = segments3.copy()
        assert output._raster_shape == segments3._raster_shape
        validate_indices(output._indices, segments3._indices)

    def test_empty(_, segments0):
        output = segments0.copy()
        assert output._raster_shape == segments0._raster_shape
        validate_indices(output._indices, segments0._indices)


class TestDevelopment:
    def test(_, segments3, values3):
        expected = np.array([-8.5, 3, 2.2])
        output = segments3.development(values3)
        assert np.array_equal(output, expected)

    def test_invalid(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segments3.development(values3)
        assert_contains(error, "upslope_development")


class TestPixels:
    def test(_, segments3, values3):
        expected = np.array([-8, 4, 2.2])
        output = segments3.pixels(values3)
        assert np.array_equal(output, expected)

    def test_invalid(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segments3.pixels(values3)
        assert_contains(error, "upslope_pixels")


class TestRemove:
    def test_ints(_, segments3, indices3):
        segments3.remove([2, 3])
        del indices3[2]
        del indices3[3]
        validate_indices(segments3._indices, indices3)

    def test_unordered(_, segments3, indices3):
        segments3.remove([3, 2])
        del indices3[2]
        del indices3[3]
        validate_indices(segments3._indices, indices3)

    def test_duplicate(_, segments3, indices3):
        segments3.remove([1, 1, 1, 1, 1])
        del indices3[1]
        validate_indices(segments3._indices, indices3)

    def test_nonlist(_, segments3, indices3):
        segments3.remove(1)
        del indices3[1]
        validate_indices(segments3._indices, indices3)

    def test_all(_, segments3):
        segments3.remove([1, 2, 3])
        validate_indices(segments3._indices, {})

    @pytest.mark.parametrize("input", [(4), (2.2)])
    def test_invalid_ints(_, segments3, input):
        with pytest.raises(KeyError):
            segments3.remove(input)

    def test_invalid_type(_, segments3):
        with pytest.raises(TypeError):
            segments3.remove("3")

    def test_bools(_, segments3, indices3):
        segments3.remove([False, True, True])
        del indices3[2]
        del indices3[3]
        validate_indices(segments3._indices, indices3)

    def test_bools_none(_, segments3, indices3):
        segments3.remove([False, False, False])
        validate_indices(segments3._indices, indices3)

    def test_bools_all(_, segments3):
        segments3.remove([True, True, True])
        validate_indices(segments3._indices, {})

    @pytest.mark.parametrize("input", [([True, False]), ([True, False, True, False])])
    def test_invalid_bools(_, segments3, input):
        with pytest.raises(_validate.ShapeError):
            segments3.remove(input)


class TestSlope:
    def test(_, segments3, values3):
        expected = np.array([-8.5, 3, 2.2])
        output = segments3.slope(values3)
        assert np.array_equal(output, expected)

    def test_invalid(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segments3.slope(values3)
        assert_contains(error, "slopes")


class TestSummary:
    @pytest.mark.parametrize(
        "statistic, expected",
        [
            ("mean", [-8.5, 3, 2.2]),
            ("median", [-8.5, 3, 2.2]),
            ("max", [-8, 4, 2.2]),
            ("min", [-9, 2, 2.2]),
            ("std", [0.5, np.std([2, 3, 4]), 0]),
            ("MAX", [-8, 4, 2.2]),  # Test case-insensitive
        ],
    )
    def test(_, segments3, values3, statistic, expected):
        expected = np.array(expected)
        output = segments3.summary(statistic, values3)
        assert np.array_equal(output, expected)

    def test_invalid_values(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(RasterShapeError) as error:
            segments3.summary("mean", values3)
        assert_contains(error, "input raster")

    def test_invalid_stattype(_, segments3, values3):
        with pytest.raises(TypeError) as error:
            segments3.summary(5, values3)
        assert_contains(error, "statistic must be a string.")

    def test_invalid_stat(_, segments3, values3):
        bad = "some invalid string"
        with pytest.raises(ValueError) as error:
            segments3.summary(bad, values3)
        assert_contains(error, bad)
