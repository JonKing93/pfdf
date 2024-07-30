from math import isnan, nan

import numpy as np
import pytest

from pfdf.raster import Raster
from pfdf.segments import _confinement
from pfdf.segments._confinement import Kernel

#####
# Processing functions
#####


class TestAngles:
    def test_basic(_, segments, dem):
        output = _confinement.angles(segments, dem, 2, None)
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
        output = _confinement.angles(segments, dem, 2, None)
        expected = np.array(
            [nan, 264.20279455, 175.71489195, 258.69006753, 93.94635581, 21.80295443]
        )
        assert np.allclose(output, expected, equal_nan=True)

    def test_nan_dem_center(_, segments, dem):
        dem._nodata = 41
        output = _confinement.angles(segments, dem, 2, None)
        expected = np.array(
            [nan, 264.20279455, 175.71489195, 258.69006753, 93.94635581, 21.80295443]
        )
        assert np.allclose(output, expected, equal_nan=True)

    def test_nan_dem_adjacent(_, segments, dem):
        dem._nodata = 19
        output = _confinement.angles(segments, dem, 2, None)
        expected = np.array(
            [nan, 264.20279455, 175.71489195, 258.69006753, 93.94635581, nan]
        )
        assert np.allclose(output, expected, equal_nan=True)

    def test_crs_meters(_, segments, dem):
        output = _confinement.angles(segments, dem, 2, None)
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
        output = _confinement.angles(segments, dem, 2, None)
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
        output = _confinement.angles(segments, dem, neighborhood=2, dem_per_m=0.001)
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


class TestAngle:
    def test_standard(_, segments, dem):
        pixels = ([1, 2, 3, 3, 4], [1, 1, 1, 2, 2])
        lengths = {"horizontal": 2, "vertical": 3, "diagonal": 4}
        kernel = Kernel(2, 7, 7)
        output = _confinement.angle(segments, pixels, lengths, kernel, dem)

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
        output = _confinement.angle(segments, pixels, lengths, kernel, dem)
        assert isnan(output)


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
        output = _confinement.pixel_slopes(flow=1, **self.inputs)
        expected = np.array([4 / 3, 4 / 3]).reshape(1, 2)
        assert np.array_equal(output, expected)

    def test_vertical(self):
        output = _confinement.pixel_slopes(flow=3, **self.inputs)
        expected = np.ones(2, float).reshape(1, 2)
        assert np.array_equal(output, expected)

    @pytest.mark.parametrize("flow,value", ((2, 6 / 4), (4, 2)))
    def test_diagonal(self, flow, value):
        output = _confinement.pixel_slopes(flow, **self.inputs)
        expected = np.array([value, value]).reshape(1, 2)
        assert np.array_equal(output, expected)


#####
# Kernel fixtures
#####


@pytest.fixture
def kernel():
    return Kernel(4, 100, 250)


@pytest.fixture
def kernel5(kernel):
    kernel.update(5, 5)
    return kernel


@pytest.fixture
def kernel2():
    kernel = Kernel(2, 5, 5)
    kernel.update(2, 2)
    return kernel


@pytest.fixture
def kdem():
    return np.array(
        [
            [21, 98, 23, 98, 24],
            [98, 20, 22, 25, 98],
            [19, 18, 99, 10, 11],
            [98, 16, 15, 13, 98],
            [17, 98, 14, 98, 12],
        ]
    )


#####
# Kernel Tests
#####


def test_init():
    kernel = Kernel(4, 100, 250)
    assert isinstance(kernel, Kernel)
    assert kernel.neighborhood == 4
    assert kernel.nRows == 100
    assert kernel.nCols == 250
    assert kernel.row is None
    assert kernel.col is None


def test_update(kernel):
    kernel.update(16, 17)
    assert kernel.row == 16
    assert kernel.col == 17


@pytest.mark.parametrize(
    "before, expected", [(True, range(4, 6)), (False, range(2, 4))]
)
def test_limit(before, expected):
    output = Kernel.limit(2, range(2, 6), before)
    assert output == expected


def test_indices(kernel):
    assert kernel.indices(5, 10, before=True) == [1, 2, 3, 4]
    assert kernel.indices(5, 10, before=False) == [6, 7, 8, 9]
    assert kernel.indices(2, 10, before=True) == [0, 1]
    assert kernel.indices(8, 10, before=False) == [9]


def test_lateral(kernel):
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


def test_lateral_edge(kernel):
    assert kernel.lateral(1, 10, 2, True, True) == ([2], [0])
    assert kernel.lateral(8, 10, 2, False, True) == ([2], [9])
    assert kernel.lateral(1, 10, 2, True, False) == ([0], [2])
    assert kernel.lateral(8, 10, 2, False, False) == ([9], [2])

    assert kernel.lateral(0, 10, 2, True, True) == ([], [])
    assert kernel.lateral(9, 10, 2, False, True) == ([], [])
    assert kernel.lateral(0, 10, 2, True, False) == ([], [])
    assert kernel.lateral(9, 10, 2, False, False) == ([], [])


def test_diagonal(kernel5):
    assert kernel5.diagonal(True, True) == ([1, 2, 3, 4], [1, 2, 3, 4])
    assert kernel5.diagonal(False, False) == ([6, 7, 8, 9], [6, 7, 8, 9])
    assert kernel5.diagonal(True, False) == ([1, 2, 3, 4], [6, 7, 8, 9])
    assert kernel5.diagonal(False, True) == ([6, 7, 8, 9], [1, 2, 3, 4])


def test_diagonal_edge(kernel):
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


def test_vertical(kernel5):
    assert kernel5.vertical(True) == ([1, 2, 3, 4], [5, 5, 5, 5])
    assert kernel5.vertical(False) == ([6, 7, 8, 9], [5, 5, 5, 5])


def test_horizontal(kernel5):
    assert kernel5.horizontal(True) == ([5, 5, 5, 5], [1, 2, 3, 4])
    assert kernel5.horizontal(False) == ([5, 5, 5, 5], [6, 7, 8, 9])


def test_identity(kernel5):
    assert kernel5.identity(True) == ([1, 2, 3, 4], [1, 2, 3, 4])
    assert kernel5.identity(False) == ([6, 7, 8, 9], [6, 7, 8, 9])


def test_exchange(kernel5):
    assert kernel5.exchange(True) == ([1, 2, 3, 4], [9, 8, 7, 6])
    assert kernel5.exchange(False) == ([6, 7, 8, 9], [4, 3, 2, 1])


def test_left(kernel5):
    assert kernel5.left() == ([5, 5, 5, 5], [1, 2, 3, 4])


def test_right(kernel5):
    assert kernel5.right() == ([5, 5, 5, 5], [6, 7, 8, 9])


def test_up(kernel5):
    assert kernel5.up() == ([1, 2, 3, 4], [5, 5, 5, 5])


def test_down(kernel5):
    assert kernel5.down() == ([6, 7, 8, 9], [5, 5, 5, 5])


def test_upleft(kernel5):
    assert kernel5.upleft() == ([1, 2, 3, 4], [1, 2, 3, 4])


def test_downright(kernel5):
    assert kernel5.downright() == ([6, 7, 8, 9], [6, 7, 8, 9])


def test_upright(kernel5):
    assert kernel5.upright() == ([1, 2, 3, 4], [9, 8, 7, 6])


def test_downleft(kernel5):
    assert kernel5.downleft() == ([6, 7, 8, 9], [4, 3, 2, 1])


class TestMaxHeight:
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
    def test_basic(_, kernel2, kdem, flow, height):
        output = kernel2.max_height(flow, Raster(kdem))
        assert output == height

    def test_nodata(_, kernel2, kdem):
        adem = Raster.from_array(kdem, nodata=10)
        output = kernel2.max_height(flow=0, dem=adem)
        assert np.isnan(output)

        adem = Raster.from_array(kdem, nodata=25)
        output = kernel2.max_height(flow=1, dem=adem)
        assert np.isnan(output)


class TestOrthogonalSlopes:
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
    def test_basic(_, kernel2, kdem, flow, slopes):
        kdem[2, 2] = 1
        output = kernel2.orthogonal_slopes(flow, length=10, dem=Raster(kdem))
        slopes = np.array(slopes).reshape(1, 2)
        assert np.array_equal(output, slopes)

    def test_nodata_adjacent(_, kernel2, kdem):
        kdem[2, 2] = 1
        kdem = Raster.from_array(kdem, nodata=23)
        output = kernel2.orthogonal_slopes(flow=1, length=10, dem=kdem)
        expected = np.array([1.4, np.nan]).reshape(1, 2)
        assert np.array_equal(output, expected, equal_nan=True)

        kdem._nodata = 16
        output = kernel2.orthogonal_slopes(flow=8, length=10, dem=kdem)
        expected = np.array([np.nan, 2.4]).reshape(1, 2)
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nodata_center(_, kernel2, kdem):
        kdem = Raster.from_array(kdem, nodata=99)
        output = kernel2.orthogonal_slopes(flow=1, length=10, dem=kdem)
        expected = np.array([nan, nan]).reshape(1, 2)
        assert np.array_equal(output, expected, equal_nan=True)
