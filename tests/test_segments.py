"""
test_segments  Unit tests for stream segment filtering
"""

import pytest
import rasterio
import numpy as np
from math import sqrt
from dfha import validate, segments
from dfha.segments import Segments


#####
# Custom Error
#####


class TestRasterShapeError:
    def test(_):
        name = "test"
        cause = validate.ShapeError(name, "rows", 0, required=(10, 10), actual=(9, 10))
        error = segments.RasterShapeError(name, cause)

        assert isinstance(error, Exception)
        assert error.args[0] == (
            "The shape of the test raster (9, 10) does not match the shape of the "
            "stream segment raster used to derive the segments (10, 10)."
        )


#####
# Kernel
#####


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
        dem[2,2] = 1
        output = kernel2.orthogonal_slopes(flow, dem, 10)
        slopes = np.array(slopes).reshape(1,2)
        assert np.array_equal(output, slopes)


#####
# Segments class
#####

@pytest.fixture
def stream():
    return np.array([
        [0,1,0,2,5],
        [1,1,0,2,0],
        [0,4,0,2,0],
        [4,0,2,0,0],
        [4,0,2,0,3],
    ])

@pytest.fixture
def stream0(stream):
    return np.zeros(stream.shape)

@pytest.fixture
def stream_path(tmp_path, stream):
    filepath = tmp_path / "stream.tif"
    with rasterio.open(
        filepath,
        'w',
        driver='GTiff',
        height=5,
        width=5,
        count=1,
        dtype=stream.dtype,
        crs="+proj=latlong",
        transform=rasterio.transform.Affine(300, 0, 101985, 0, -300, 2826915),
    ) as raster:
        nulls = stream==0
        stream[np.nonzero(nulls)] = -999
        raster.write(stream, indexes=1)
        valid = np.logical_not(nulls)
        raster.write_mask(valid)
    return filepath

@pytest.fixture
def indices():
    indices = {
        1: ([0,1,1],[1,0,1]),
        2: ([0,1,2,3,4], [3,3,3,2,2]),
        3: ([4],[4]),
        4: ([2,3,4], [1,0,0]),
        5: ([0], [4]),
    }
    for key, (rows, cols) in indices.items():
        indices[key] = (index_array(rows), index_array(cols))
    return indices

@pytest.fixture
def segments5(stream):
    return Segments(stream)

@pytest.fixture
def segments0(stream0):
    return Segments(stream0)

@pytest.fixture
def flow(stream):
    stream[stream==0] = 6
    return stream

def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


def index_array(ints):
    return np.array(ints, dtype='int64').reshape(-1)

def validate_indices(output, expected):
    assert isinstance(output, dict)
    assert sorted(output.keys()) == sorted(expected.keys())
    for key, value in output.items():
        assert isinstance(value, tuple)
        assert len(value) == 2
        assert np.array_equal(value[0], expected[key][0])
        assert np.array_equal(value[1], expected[key][1])


class TestInit:

    @staticmethod
    def validate(segments, indices):
        assert isinstance(segments, Segments)
        validate_indices(segments._indices, indices)
        assert segments._raster_shape == (5,5)

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
        stream[0,0] = -1
        with pytest.raises(ValueError):
            Segments(stream)

    def test_nonint_failed(self, stream):
        stream = stream.astype(float)
        stream[0,0] = 2.2
        with pytest.raises(ValueError):
            Segments(stream)

    def test_ND_failed(self, stream):
        stream = np.stack((stream, stream))
        with pytest.raises(validate.DimensionError):
            Segments(stream)


class TestIds:

    def test(_, segments5):
        ids = segments5.ids
        expected = np.array([1,2,3,4,5])
        assert np.array_equal(ids, expected)

    def test_empty(_, segments5):
        ids = segments5.ids
        expected = np.array([], dtype=int)
        assert np.array_equal(ids, expected)


class TestIndices:

    def test(_, segments5, indices):
        validate_indices(segments5.indices, indices)

    def test_empty(_, segments0, indices):
        validate_indices(segments0.indices, {})


class TestRasterShape:
    def test(_, segments5):
        assert segments5.raster_shape == (5,5)


class TestLen:
    def test(_, segments5, segments0):
        assert len(segments5) == 5
        assert len(segments0) == 0

class TestStr:
    def test(_, segments5, segments0):
        assert str(segments5) == 'Stream Segments: 1, 2, 3, 4, 5'
        assert str(segments0) == 'Stream Segments: None'

class TestValidate:

    def test_valid_numpy(_, segments5):
        output = segments5._validate(stream, '')
        assert np.array_equal(output, stream)

    def test_valid_file(_, segments5, stream_path):
        output = segments5._validate(stream_path, '')
        with rasterio.open(stream_path) as data:
            expected = data.read(1)
        assert np.array_equal(output, expected)

    def test_notraster(_, segments5, stream):
        bad = np.stack((stream, stream))
        name = 'raster name'
        with pytest.raises(validate.DimensionError) as error:
            segments5._validate(bad, name)
        assert_contains(error, name)    

    def test_wrong_shape(_, segments5):
        bad = np.array([1,2,3])
        name = 'raster name'
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
        assert res.shape==(1,)
        assert res==9.3

    def test_N_nonscalar(_, segments5):
        with pytest.raises(validate.DimensionError) as error:
            segments5._validate_confinement_args([2,3], 9.3)
        assert_contains(error, 'N')


    def test_N_negative(_, segments5):
        with pytest.raises(ValueError) as error:
            segments5._validate_confinement_args(-2, 9.3)
        assert_contains(error, 'N')

    def test_N_nonint(_, segments5):
        with pytest.raises(ValueError) as error:
            segments5._validate_confinement_args(4.3, 9.3)
        assert_contains(error, 'N')


    def test_res_nonscalar(_, segments5):
        with pytest.raises(validate.DimensionError) as error:
            segments5._validate_confinement_args(4, [2, 3])
        assert_contains(error, 'resolution')

    def test_res_negative(_, segments5):
        with pytest.raises(ValueError) as error:
            segments5._validate_confinement_args(4, -3)
        assert_contains(error, 'resolution')


class TestValidateFlow:
    name = 'flow_directions'

    def test_valid(self, segments5, flow):
        segments5._validate_flow(flow)

    def test_too_low(self, segments5, flow):
        flow[0,0] = 0
        with pytest.raises(ValueError) as error:
            segments5._validate_flow(flow)
        assert_contains(error, self.name)

    def test_too_high(self, segments5, flow):
        flow[0,0] = 9
        with pytest.raises(ValueError) as error:
            segments5._validate_flow(flow)
        assert_contains(error, self.name)

    def test_nonint(self, segments5, flow):
        flow = flow.astype(float)
        flow[0,0] = 2.2
        with pytest.raises(ValueError) as error:
            segments5._validate_flow(flow)
        assert_contains(error, self.name)


class TestFlowLength:

    @pytest.mark.parametrize('flow, expected',
        [(1, 10), (2, 14), (3, 10), (4, 14), (5, 10), (6, 14), (7, 10), (8, 14)]
        )
    def test(_, flow, expected):
        assert Segments._flow_length(flow, 10, 14) == expected

class TestConfinementAngle:

    def test_single_pixel(_):
        # 45 degree slope on either side. 90 degrees of empty space remain from open plain
        slopes = np.array([1, 1]).reshape(1,2)
        assert Segments._confinement_angle(slopes) == 90

    def test_multiple(_):
        # clockwise slopes are 45 and 30. counterclockwise are 60 and 0.
        # Mean slopes are 37.5 and 30 so 112.5 degrees of open space remain from open plain
        slopes = np.array([
            [1, sqrt(3)],
            [1/sqrt(3), 0],
        ])
        assert Segments._confinement_angle(slopes) == 112.5

