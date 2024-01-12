from multiprocessing import Pool
from os import cpu_count
from trace import Trace

import numpy as np
import pytest
from affine import Affine

from pfdf._utils import basins
from pfdf.raster import Raster
from pfdf.segments import Segments

#####
# Testing fixtures and utilities
#####


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


@pytest.fixture
def expected():
    "The expected final basins raster"
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 0, 0, 7, 3, 0],
            [0, 7, 0, 0, 7, 3, 0],
            [0, 7, 7, 0, 7, 7, 0],
            [0, 0, 7, 7, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )


@pytest.fixture
def transform():
    return Affine.identity()


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
def mask():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype(bool)


@pytest.fixture
def segments(flow, mask):
    return Segments(flow, mask)


#####
# Utilities (being tested)
#####


class TestValidateNprocess:
    def test_none(_):
        assert basins.validate_nprocess(None) == max(1, cpu_count() - 1)

    def test_valid(_):
        assert basins.validate_nprocess(12) == 12

    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            basins.validate_nprocess("invalid")
        assert_contains(error, "nprocess")

    def test_negative(_):
        with pytest.raises(ValueError) as error:
            basins.validate_nprocess(-3)
        assert_contains(error, "nprocess", "must be greater than 0")

    def test_float(_):
        with pytest.raises(ValueError) as error:
            basins.validate_nprocess(2.2)
        assert_contains(error, "nprocess", "must be integer")


class TestNewRaster:
    def test_default(_):
        output = basins.new_raster((10, 12))
        assert np.array_equal(output, np.zeros((10, 12)))
        assert output.dtype == "int32"

    def test_type(_):
        output = basins.new_raster((10, 12), bool)
        assert np.array_equal(output, np.zeros((10, 12)))
        assert output.dtype == bool


class TestGetOutlets:
    def test(_, segments):
        ids, outlets = basins.get_outlets(segments)
        assert np.array_equal(ids, [1, 3, 7])
        assert outlets == [(3, 1), (1, 5), (5, 3)]


class TestCountOutlets:
    def test(_, segments):
        outlets = segments.outlets(terminal=True)
        output = basins.count_outlets(segments, outlets)
        assert np.array_equal(output, [1, 1, 2])


class TestFilterOutlets:
    def test(_, segments):
        outlets = segments.outlets(terminal=True)
        ingroup = np.array([True, False, True])

        output = basins.filter_outlets(outlets, ingroup)
        assert output == [outlets[0], outlets[2]]


class TestInitializer:
    def test(_):
        basins.initializer(5)
        assert basins.flow == 5


class TestUpdateRaster:
    def test(_):
        final = np.zeros((5, 5))
        raster1 = final.copy()
        raster2 = final.copy()
        raster3 = final.copy()

        raster1[0:2, 0:2] = 1
        raster2[0, 1:] = 2
        raster3[:, :] = 3
        raster3[3:, 3:] = 0

        basins.update_raster(final, [raster1, raster2, raster3])
        expected = np.array(
            [
                [1, 1, 2, 2, 2],
                [1, 1, 3, 3, 3],
                [3, 3, 3, 3, 3],
                [3, 3, 3, 0, 0],
                [3, 3, 3, 0, 0],
            ]
        )
        assert np.array_equal(final, expected)


#####
# Raster Builders
#####


class TestChunkRaster:
    def test(_, flow, segments, expected):
        ids, outlets = basins.get_outlets(segments)
        output = basins.chunk_raster(ids, outlets, flow)
        assert np.array_equal(output, expected)


class TestGroupRasters:
    expected = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 3, 0],
            [0, 1, 0, 0, 0, 3, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )

    def test_multiple_rasters_in_chunk(self, flow, segments):
        nprocess = 1

        ids, outlets = basins.get_outlets(segments)
        ids = ids[0:2]
        outlets = [outlets[0], outlets[1]]
        with Pool(nprocess, initializer=basins.initializer, initargs=[flow]) as pool:
            output = basins.group_rasters(pool, nprocess, ids, outlets)

        assert isinstance(output, list)
        assert len(output) == 1
        output = output[0]
        assert np.array_equal(output, self.expected)

    def test_multiple_chunks(self, flow, segments):
        nprocess = 2

        ids, outlets = basins.get_outlets(segments)
        ids = ids[0:2]
        outlets = [outlets[0], outlets[1]]
        with Pool(nprocess, initializer=basins.initializer, initargs=[flow]) as pool:
            output = basins.group_rasters(pool, nprocess, ids, outlets)

        assert isinstance(output, list)
        assert len(output) == 2
        collected = basins.new_raster(flow.shape)
        basins.update_raster(collected, output)
        assert np.array_equal(collected, self.expected)


class TestBuiltInParallel:
    def test(_, segments, expected):
        output = basins.built_in_parallel(segments, nprocess=2)
        assert np.array_equal(output, expected)


class TestBuiltSequentially:
    def test(_, segments, expected):
        output = basins.built_sequentially(segments)
        assert np.array_equal(output, expected)


class TestBuild:
    def test_sequential(_, segments, expected):
        output = basins.build(segments, parallel=False, nprocess=None)
        assert np.array_equal(output, expected)

    def test_parallel(_, segments, expected):
        output = basins.build(segments, parallel=True, nprocess=2)
        assert np.array_equal(output, expected)
