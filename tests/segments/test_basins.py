from multiprocessing import Pool

import numpy as np
import pytest

from pfdf.segments import _basins


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


#####
# Utilities
#####


class TestNewRaster:
    def test_default(_):
        output = _basins.new_raster((10, 12))
        assert np.array_equal(output, np.zeros((10, 12)))
        assert output.dtype == "int32"

    def test_type(_):
        output = _basins.new_raster((10, 12), bool)
        assert np.array_equal(output, np.zeros((10, 12)))
        assert output.dtype == bool


class TestGetOutlets:
    def test(_, segments):
        print(segments.raster().values)
        ids, outlets = _basins.get_outlets(segments)
        assert np.array_equal(ids, [1, 3, 7])
        assert outlets == [(3, 1), (1, 5), (5, 3)]


class TestCountOutlets:
    def test(_, segments):
        ids = segments.ids[segments.isterminal()]
        outlets = segments.outlets(ids)
        output = _basins.count_outlets(segments, outlets)
        assert np.array_equal(output, [1, 1, 2])


class TestFilterOutlets:
    def test(_, segments):
        ids = segments.ids[segments.isterminal()]
        outlets = segments.outlets(ids)
        ingroup = np.array([True, False, True])

        output = _basins.filter_outlets(outlets, ingroup)
        assert output == [outlets[0], outlets[2]]


class TestInitializer:
    def test(_):
        _basins.initializer(5)
        assert _basins.flow == 5


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

        _basins.update_raster(final, [raster1, raster2, raster3])
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
    def test(_, flow, segments, basin_raster):
        ids, outlets = _basins.get_outlets(segments)
        output = _basins.chunk_raster(ids, outlets, flow)
        assert np.array_equal(output, basin_raster)


@pytest.mark.slow
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

        ids, outlets = _basins.get_outlets(segments)
        ids = ids[0:2]
        outlets = [outlets[0], outlets[1]]
        with Pool(nprocess, initializer=_basins.initializer, initargs=[flow]) as pool:
            output = _basins.group_rasters(pool, nprocess, ids, outlets)

        assert isinstance(output, list)
        assert len(output) == 1
        output = output[0]
        assert np.array_equal(output, self.expected)

    def test_multiple_chunks(self, flow, segments):
        nprocess = 2

        ids, outlets = _basins.get_outlets(segments)
        ids = ids[0:2]
        outlets = [outlets[0], outlets[1]]
        with Pool(nprocess, initializer=_basins.initializer, initargs=[flow]) as pool:
            output = _basins.group_rasters(pool, nprocess, ids, outlets)

        assert isinstance(output, list)
        assert len(output) == 2
        collected = _basins.new_raster(flow.shape)
        _basins.update_raster(collected, output)
        assert np.array_equal(collected, self.expected)


@pytest.mark.slow
class TestBuiltInParallel:
    def test(_, segments, basin_raster):
        output = _basins.built_in_parallel(segments, nprocess=2)
        assert np.array_equal(output, basin_raster)


class TestBuiltSequentially:
    def test(_, segments, basin_raster):
        output = _basins.built_sequentially(segments)
        assert np.array_equal(output, basin_raster)


class TestBuild:
    def test_sequential(_, segments, basin_raster):
        output = _basins.build(segments, parallel=False, nprocess=None)
        assert np.array_equal(output, basin_raster)

    @pytest.mark.slow
    def test_parallel(_, segments, basin_raster):
        output = _basins.build(segments, parallel=True, nprocess=2)
        assert np.array_equal(output, basin_raster)
