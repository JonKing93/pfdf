"""
test_segments  Unit tests for stream segment filtering
"""

import pytest
import rasterio
import numpy as np
from dfha import validate, segments


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
        assert kernel.lateral(5, 10, 5, True, True) == ([5,5,5,5], [1, 2, 3, 4])  # Left
        assert kernel.lateral(5, 10, 5, False, True) == ([5,5,5,5], [6, 7, 8, 9])  # Right
        assert kernel.lateral(5, 10, 5, True, False) == ([1, 2, 3, 4], [5,5,5,5])  # Up
        assert kernel.lateral(5, 10, 5, False, False) == ([6, 7, 8, 9], [5,5,5,5])  # Down

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
        kernel.update(1,1)
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
        assert kernel5.vertical(True) == ([1, 2, 3, 4], [5,5,5,5])
        assert kernel5.vertical(False) == ([6, 7, 8, 9], [5,5,5,5])

    def test_horizontal(_, kernel5):
        assert kernel5.horizontal(True) == ([5,5,5,5], [1, 2, 3, 4])
        assert kernel5.horizontal(False) == ([5,5,5,5], [6, 7, 8, 9])

    def test_identity(_, kernel5):
        assert kernel5.identity(True) == ([1, 2, 3, 4], [1, 2, 3, 4])
        assert kernel5.identity(False) == ([6, 7, 8, 9], [6, 7, 8, 9])

    def test_exchange(_, kernel5):
        assert kernel5.exchange(True) == ([1, 2, 3, 4], [9, 8, 7, 6])
        assert kernel5.exchange(False) == ([6, 7, 8, 9], [4, 3, 2, 1])

    def test_left(_, kernel5):
        assert kernel5.left() == ([5,5,5,5], [1, 2, 3, 4])

    def test_right(_, kernel5):
        assert kernel5.right() == ([5,5,5,5], [6, 7, 8, 9])

    def test_up(_, kernel5):
        assert kernel5.up() == ([1, 2, 3, 4], [5,5,5,5])

    def test_down(_, kernel5):
        assert kernel5.down() == ([6, 7, 8, 9], [5,5,5,5])

    def test_upleft(_, kernel5):
        assert kernel5.upleft() == ([1, 2, 3, 4], [1, 2, 3, 4])

    def test_downright(_, kernel5):
        assert kernel5.downright() == ([6, 7, 8, 9], [6, 7, 8, 9])

    def test_upright(_, kernel5):
        assert kernel5.upright() == ([1, 2, 3, 4], [9, 8, 7, 6])

    def test_downleft(_, kernel5):
        assert kernel5.downleft() == ([6, 7, 8, 9], [4, 3, 2, 1])
