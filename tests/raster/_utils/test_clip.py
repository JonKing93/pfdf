import numpy as np
import pytest

from pfdf.errors import MissingNoDataError
from pfdf.raster import RasterMetadata
from pfdf.raster._utils import clip


class TestIndices:
    def test_mins(_):
        current = np.arange(-5, 5)
        clipped = np.arange(0, 10)
        sout, cout = clip._indices(current, clipped, 20)

        assert sout == slice(0, 5)
        assert cout == slice(5, 10)

    def test_maxs(_):
        current = np.arange(5, 15)
        clipped = np.arange(0, 10)
        sout, cout = clip._indices(current, clipped, 10)

        assert sout == slice(5, 10)
        assert cout == slice(0, 5)

    def test_both(_):
        current = np.arange(-5, 20)
        clipped = np.arange(0, 25)
        length = 10
        sout, cout = clip._indices(current, clipped, length)

        assert sout == slice(0, 10)
        assert cout == slice(5, 15)

    def test_empty(_):
        current = np.arange(1000, 1020)
        clipped = np.arange(0, 20)
        length = 20
        sout, cout = clip._indices(current, clipped, length)

        assert sout == slice(0, 0)
        assert cout == slice(0, 0)


class TestExterior:
    def test_keyword_nodata(_):
        araster = np.arange(100).reshape(10, 10) + 1
        metadata = RasterMetadata((20, 15), dtype=araster.dtype, nodata=0)
        rows = [-5, 15]
        cols = [-2, 13]

        values = clip._exterior(araster, metadata, rows, cols)

        expected = np.full((20, 15), 0)
        expected[5:15, 2:12] = araster
        print(values)
        print(expected)
        assert np.array_equal(values, expected)

    def test_missing_nodata(_, assert_contains):
        araster = np.arange(100).reshape(10, 10) + 1
        metadata = RasterMetadata((20, 15), dtype=araster.dtype)
        rows = [-5, 15]
        cols = [-2, 13]

        with pytest.raises(MissingNoDataError) as error:
            clip._exterior(araster, metadata, rows, cols)
        assert_contains(
            error, "Cannot clip raster because it does not have a NoData value"
        )

    def test_partial(_):
        araster = np.arange(100).reshape(10, 10) + 1
        metadata = RasterMetadata((20, 5), dtype=araster.dtype, nodata=0)
        rows = [-5, 15]
        cols = [3, 8]

        values = clip._exterior(araster, metadata, rows, cols)

        expected = np.full((20, 5), 0)
        expected[5:15, :] = araster[:, 3:8]
        assert np.array_equal(values, expected)

    def test_memory(_, assert_contains):
        araster = np.arange(100).reshape(10, 10)
        metadata = RasterMetadata((200000000, 200000000), dtype=araster.dtype, nodata=0)
        rows = [-200000000, 0]
        cols = [0, 200000000]
        with pytest.raises(MemoryError) as error:
            clip._exterior(araster, metadata, rows, cols)
        assert_contains(error, "clipped raster is too large for memory")


class TestInterior:
    def test(_):
        araster = np.arange(100).reshape(10, 10)
        rows = [2, 7]
        cols = [3, 6]
        values = clip._interior(araster, rows, cols)

        expected = araster[2:7, 3:6]
        assert np.array_equal(values, expected)
        assert values.base is araster.base


class TestValues:
    def test_interior(_):
        araster = np.arange(100).reshape(10, 10)
        metadata = None
        rows = [3, 8]
        cols = [2, 8]

        values = clip.values(araster, metadata, rows, cols)
        assert np.array_equal(values, araster[3:8, 2:8])
        assert values.base is araster.base

    def test_exterior(_):
        araster = np.arange(100).reshape(10, 10)
        metadata = RasterMetadata((12, 13), dtype=araster.dtype, nodata=0)
        rows = [3, 15]
        cols = [-5, 8]

        values = clip.values(araster, metadata, rows, cols)
        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]
        assert np.array_equal(values, expected)
