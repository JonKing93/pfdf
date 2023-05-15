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
    * Run `pytest tests/test_segments.py --cov=dfha.segments --cov-fail-under=95`
      from the OS command line.
"""

import pytest
import rasterio
import numpy as np
from math import sqrt
from copy import deepcopy
from dfha import validate, segments
from dfha.segments import Segments


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


@pytest.fixture
def stream3():
    return np.array(
        [
            [0, 2, 2],
            [1, 2, 0],
            [1, 0, 3],
        ]
    )


@pytest.fixture
def segments3(stream3):
    return Segments(stream3)


@pytest.fixture
def values3():
    return np.array(
        [
            [999, 3, 4],
            [-8, 2, 999],
            [-9, 999, 2.2],
        ]
    )


@pytest.fixture
def indices3():
    indices = {1: ([1, 2], [0, 0]), 2: ([0, 0, 1], [1, 2, 1]), 3: ([2], [2])}
    return index_dict(indices)


@pytest.fixture
def streamc():
    return np.array([[0, 0, 0], [1, 2, 0], [0, 0, 0]])


@pytest.fixture
def segmentsc(streamc):
    return Segments(streamc)


@pytest.fixture
def flowc():
    return np.array([[8, 8, 8], [1, 5, 8], [8, 8, 8]])


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

    flow_height = [(k - 1, 2 * k + 9) for k in range(1, 9)]

    @pytest.mark.parametrize("flow, height", flow_height)
    def test_max_height(_, kernel2, dem, flow, height):
        assert kernel2.max_height(flow, dem) == height

    @pytest.mark.parametrize(
        "flow, slopes",
        [
            (1, [1.4, 2.2]),
            (2, [1.6, 2.4]),
            (3, [1.8, 1.0]),
            (4, [2.0, 1.2]),
            (5, [2.2, 1.4]),
            (6, [2.4, 1.6]),
            (7, [1.0, 1.8]),
            (8, [1.2, 2.0]),
        ],
    )
    def test_orthogonal_slopes(_, kernel2, dem, flow, slopes):
        dem[2, 2] = 1
        output = kernel2.orthogonal_slopes(flow, dem, 10)
        slopes = np.array(slopes).reshape(1, 2)
        assert np.array_equal(output, slopes)


#####
# Segments: Properties, Dunders, and Internal (except _filter)
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
        with pytest.raises(validate.DimensionError):
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
        output = segments5._validate(stream, "", load)
        assert np.array_equal(output, stream)

    def test_valid_file(_, segments5, stream_path):
        output = segments5._validate(stream_path, "")
        with rasterio.open(stream_path) as data:
            expected = data.read(1)
        assert np.array_equal(output, expected)

    def test_str_noload(_, segments5, stream_path):
        output = segments5._validate(str(stream_path), "", load=False)
        assert output == stream_path

    def test_path_noload(_, segments5, stream_path):
        output = segments5._validate(stream_path, "", load=False)
        assert output == stream_path

    def test_not_raster(_, segments5, stream):
        bad = np.stack((stream, stream))
        name = "raster name"
        with pytest.raises(validate.DimensionError) as error:
            segments5._validate(bad, name)
        assert_contains(error, name)

    def test_wrong_shape(_, segments5):
        bad = np.array([1, 2, 3])
        name = "raster name"
        with pytest.raises(segments.RasterShapeError) as error:
            segments5._validate(bad, name)
        assert_contains(error, name)


class TestValidateConfinementArgs:
    def test_valid(_, segments5):
        (N, res) = segments5._validate_confinement_args(4, 9.3)
        assert isinstance(N, np.ndarray)
        assert N.shape == (1,)
        assert N == 4
        assert isinstance(res, np.ndarray)
        assert res.shape == (1,)
        assert res == 9.3

    def test_N_nonscalar(_, segments5):
        with pytest.raises(validate.DimensionError) as error:
            segments5._validate_confinement_args([2, 3], 9.3)
        assert_contains(error, "N")

    def test_N_negative(_, segments5):
        with pytest.raises(ValueError) as error:
            segments5._validate_confinement_args(-2, 9.3)
        assert_contains(error, "N")

    def test_N_nonint(_, segments5):
        with pytest.raises(ValueError) as error:
            segments5._validate_confinement_args(4.3, 9.3)
        assert_contains(error, "N")

    def test_res_nonscalar(_, segments5):
        with pytest.raises(validate.DimensionError) as error:
            segments5._validate_confinement_args(4, [2, 3])
        assert_contains(error, "resolution")

    def test_res_negative(_, segments5):
        with pytest.raises(ValueError) as error:
            segments5._validate_confinement_args(4, -3)
        assert_contains(error, "resolution")


class TestValidateFlow:
    name = "flow_directions"

    def test_valid(self, segments5, flow):
        segments5._validate_flow(flow)

    def test_too_low(self, segments5, flow):
        flow[0, 0] = 0
        with pytest.raises(ValueError) as error:
            segments5._validate_flow(flow)
        assert_contains(error, self.name)

    def test_too_high(self, segments5, flow):
        flow[0, 0] = 9
        with pytest.raises(ValueError) as error:
            segments5._validate_flow(flow)
        assert_contains(error, self.name)

    def test_nonint(self, segments5, flow):
        flow = flow.astype(float)
        flow[0, 0] = 2.2
        with pytest.raises(ValueError) as error:
            segments5._validate_flow(flow)
        assert_contains(error, self.name)


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
        output = segmentsc._confinement(demc, flowc, 1, 1)
        assert np.array_equal(output, expected)


class Test_Summary:
    def test_mean(_, segments3, values3):
        expected = np.array([-8.5, 3, 2.2])
        output = segments3._summary(values3, np.mean)
        assert np.array_equal(output, expected)

    def test_max(_, segments3, values3):
        expected = np.array([-8, 4, 2.2])
        output = segments3._summary(values3, np.amax)
        assert np.array_equal(output, expected)


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
        with pytest.raises(segments.RasterShapeError) as error:
            segments3.basins(values3)
        assert_contains(error, "upslope_basins")


class TestConfinement:
    def test(_, segmentsc, demc, flowc):
        expected = np.array([105, 120])
        output = segmentsc.confinement(demc, flowc, 1, 1)
        assert np.array_equal(output, expected)

    def test_invalid_dem(_, segmentsc, demc, flowc):
        demc = np.concatenate((demc, demc), axis=1)
        with pytest.raises(segments.RasterShapeError) as error:
            segmentsc.confinement(demc, flowc, 1, 1)
        assert_contains(error, "dem")

    def test_invalid_flow_shape(_, segmentsc, demc, flowc):
        flowc = np.concatenate((flowc, flowc), axis=1)
        with pytest.raises(segments.RasterShapeError) as error:
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
        with pytest.raises(segments.RasterShapeError) as error:
            segments3.development(values3)
        assert_contains(error, "upslope_development")


class TestPixels:
    def test(_, segments3, values3):
        expected = np.array([-8, 4, 2.2])
        output = segments3.pixels(values3)
        assert np.array_equal(output, expected)

    def test_invalid(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(segments.RasterShapeError) as error:
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
        with pytest.raises(validate.ShapeError):
            segments3.remove(input)


class TestSlope:
    def test(_, segments3, values3):
        expected = np.array([-8.5, 3, 2.2])
        output = segments3.slope(values3)
        assert np.array_equal(output, expected)

    def test_invalid(_, segments3, values3):
        values3 = np.concatenate((values3, values3), axis=1)
        with pytest.raises(segments.RasterShapeError) as error:
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
        with pytest.raises(segments.RasterShapeError) as error:
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


#####
# Filtering
#####


class TestValidateRaster:
    def test_valid_str(_, segments5, stream_path):
        args = ("upslope_area", str(stream_path))
        filters = {
            "area": {args[0]: args[1]},
            "basins": {"upslope_basins": None},
        }
        expected = {
            "area": {"upslope_area": stream_path},
            "basins": {"upslope_basins": None},
        }

        filter = "area"
        segments._validate_raster(filters, filter, segments5, args)
        assert filters == expected

    def test_valid_path(_, segments5, stream_path):
        args = ("upslope_area", stream_path)
        filters = {
            "area": {args[0]: args[1]},
            "basins": {"upslope_basins": None},
        }
        expected = deepcopy(filters)

        filter = "area"
        segments._validate_raster(filters, filter, segments5, args)
        assert filters == expected

    def test_valid_numpy(_, segments5, stream):
        args = ("upslope_area", stream)
        filters = {
            "area": {args[0]: args[1]},
            "basins": {"upslope_basins": None},
        }
        expected = deepcopy(filters)

        filter = "area"
        segments._validate_raster(filters, filter, segments5, args)
        assert np.array_equal(filters["area"][args[0]], expected["area"][args[0]])

    def test_invalid(_, segments5, stream):
        stream = np.concatenate((stream, stream), axis=1)
        args = ("upslope_area", stream)
        filters = {
            "area": {args[0]: args[1]},
            "basins": {"upslope_basins": None},
        }
        filter = "area"

        with pytest.raises(segments.RasterShapeError) as error:
            segments._validate_raster(filters, filter, segments5, args)
        assert_contains(error, args[0])


class Test_Filter:  # This is the internal method in the Segments class
    def test_no_args(_, segments3, values3):
        method = Segments._summary
        type = "<"
        threshold = None
        args = (None, None, None)
        expected = segments3.copy()
        segments3._filter(method, type, threshold, *args)
        validate_indices(segments3._indices, expected._indices)

    def test_lesser(_, segments3, values3):
        method = Segments._summary
        args = (values3, np.mean)
        type = "<"
        threshold = 0
        expected = segments3.copy()
        expected.remove(1)
        segments3._filter(method, type, threshold, *args)
        validate_indices(segments3._indices, expected._indices)

    def test_greater(_, segments3, values3):
        method = Segments._summary
        args = (values3, np.mean)
        type = ">"
        threshold = 0
        expected = segments3.copy()
        expected.remove([2, 3])
        segments3._filter(method, type, threshold, *args)
        validate_indices(segments3._indices, expected._indices)

    @pytest.mark.parametrize("type, failed", [("<", [1]), (">", [2])])
    def test_on_threshold(_, segments3, values3, type, failed):
        method = Segments._summary
        args = (values3, np.amax)
        threshold = 2.2
        expected = segments3.copy()
        expected.remove(failed)
        segments3._filter(method, type, threshold, *args)
        validate_indices(segments3._indices, expected._indices)

    def test_none_removed(_, segments3, values3):
        method = Segments._summary
        args = (values3, np.mean)
        type = "<"
        threshold = -999
        expected = segments3.copy()
        segments3._filter(method, type, threshold, *args)
        validate_indices(segments3._indices, expected._indices)

    def test_all_removed(_, segments3, values3):
        method = Segments._summary
        args = (values3, np.mean)
        type = "<"
        threshold = 999
        segments3._filter(method, type, threshold, *args)
        assert segments3._indices == {}

    def test_confinement(_, segmentsc, demc, flowc):
        method = Segments._confinement
        type = "<"
        threshold = 110
        args = (demc, flowc, 1, 1)
        expected = segmentsc.copy()
        expected.remove(1)
        segmentsc._filter(method, type, threshold, *args)
        validate_indices(segmentsc._indices, expected._indices)


class TestFilter:  # This is the user-facing function
    def test_none(_, stream):
        expected = np.array([1, 2, 3, 4, 5])
        ids = segments.filter(stream)
        assert np.array_equiv(ids, expected)

    def test_partial_args(_, stream):
        with pytest.raises(TypeError) as error:
            segments.filter(stream, slopes=stream)
        assert_contains(error, "minimum_slope")

    def test_partial_threshold(_, stream):
        with pytest.raises(TypeError) as error:
            segments.filter(stream, minimum_slope=2)
        assert_contains(error, "slopes")

    def test_invalid_threshold(_, stream):
        with pytest.raises(TypeError) as error:
            segments.filter(stream, minimum_slope="invalid", slopes=stream)
        assert_contains(error, "minimum_slope")

    def test_invalid_raster(_, stream):
        with pytest.raises(FileNotFoundError):
            segments.filter(stream, minimum_slope=2, slopes="not-a-file")

    def test_invalid_flow(_, streamc, demc, flowc):
        flowc[0, 0] = 0
        with pytest.raises(ValueError) as error:
            segments.filter(
                streamc,
                maximum_confinement=2,
                dem=demc,
                flow_directions=flowc,
                N=1,
                resolution=1,
            )
        assert_contains(error, "flow_directions")

    def test_invalid_N(_, streamc, demc, flowc):
        with pytest.raises(ValueError) as error:
            segments.filter(
                streamc,
                maximum_confinement=2,
                dem=demc,
                flow_directions=flowc,
                N=-2,
                resolution=1,
            )
        assert_contains(error, "N")

    def test_invalid_resolution(_, streamc, demc, flowc):
        with pytest.raises(ValueError) as error:
            segments.filter(
                streamc,
                maximum_confinement=2,
                dem=demc,
                flow_directions=flowc,
                N=1,
                resolution=-2,
            )
        assert_contains(error, "resolution")

    def test_str_raster(_, stream_path):
        basins = str(stream_path)
        ids = segments.filter(stream_path, maximum_basins=3, upslope_basins=basins)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_path_raster(_, stream_path):
        basins = stream_path
        ids = segments.filter(stream_path, maximum_basins=3, upslope_basins=basins)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_numpy_raster(_, stream):
        basins = stream
        ids = segments.filter(stream, maximum_basins=3, upslope_basins=basins)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_statistic(_, stream):
        # Same as previous, but should still be here because it tests a different item
        basins = stream
        ids = segments.filter(stream, maximum_basins=3, upslope_basins=basins)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_confinement(_, streamc, demc, flowc):
        ids = segments.filter(
            streamc,
            maximum_confinement=110,
            dem=demc,
            flow_directions=flowc,
            N=1,
            resolution=1,
        )
        expected = np.array(
            [
                1,
            ]
        )
        assert np.array_equal(ids, expected)

    def test_pixels(_, stream):
        ids = segments.filter(stream, maximum_pixels=3, upslope_pixels=stream)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_basins(_, stream):
        ids = segments.filter(stream, maximum_basins=3, upslope_basins=stream)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_development(_, stream):
        ids = segments.filter(stream, maximum_development=3, upslope_development=stream)
        expected = np.array([1, 2, 3])
        assert np.array_equal(ids, expected)

    def test_slope(_, stream):
        ids = segments.filter(stream, minimum_slope=3, slopes=stream)
        expected = np.array([3, 4, 5])
        assert np.array_equal(ids, expected)

    def test_multiple(_, stream):
        ids = segments.filter(
            stream,
            minimum_slope=2,
            slopes=stream,
            maximum_pixels=4,
            upslope_pixels=stream,
        )
        expected = np.array([2, 3, 4])
        assert np.array_equal(ids, expected)

    def test_remove_all(_, stream):
        basins = stream
        ids = segments.filter(stream, maximum_basins=0, upslope_basins=basins)
        expected = np.array([])
        assert np.array_equal(ids, expected)

    def test_remove_all_early(_, stream):
        # When all segments are removed before the final filter
        ids = segments.filter(
            stream,
            maximum_basins=0,
            upslope_basins=stream,
            minimum_slope=100,
            slopes=stream,
        )
        expected = np.array([])
        assert np.array_equal(ids, expected)
