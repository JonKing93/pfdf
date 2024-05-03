import numpy as np
import pytest

from pfdf._utils import clip
from pfdf.errors import MissingNoDataError
from pfdf.projection import BoundingBox, Transform


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
        rows = [15, -5]
        cols = [-2, 13]

        araster = np.arange(100).reshape(10, 10) + 1
        values = clip._exterior(araster, rows, cols, nodata=np.array(0))

        expected = np.full((20, 15), 0)
        expected[5:15, 2:12] = araster
        assert np.array_equal(values, expected)

    def test_missing_nodata(_, assert_contains):
        rows = [15, -5]
        cols = [-2, 13]

        araster = np.arange(100).reshape(10, 10) + 1
        with pytest.raises(MissingNoDataError) as error:
            clip._exterior(araster, rows, cols, nodata=None)
        assert_contains(error, "must provide a NoData value")

    def test_partial(_):
        rows = [15, -5]
        cols = [3, 8]

        araster = np.arange(100).reshape(10, 10) + 1
        values = clip._exterior(araster, rows, cols, nodata=np.array(0))

        expected = np.full((20, 5), 0)
        expected[5:15, :] = araster[:, 3:8]
        assert np.array_equal(values, expected)


class TestInterior:
    def test(_):
        araster = np.arange(100).reshape(10, 10)
        rows = [7, 2]
        cols = [3, 6]
        values = clip._interior(araster, rows, cols)

        expected = araster[2:7, 3:6]
        assert np.array_equal(values, expected)
        assert values.base is araster.base


class TestValues:
    def test_interior(_):
        araster = np.arange(100).reshape(10, 10)
        bounds = BoundingBox(2, 8, 8, 3)
        stransform = Transform(1, 1, 0, 0).affine
        values = clip.values(araster, bounds, stransform, nodata=np.array(-9))
        assert np.array_equal(values, araster[3:8, 2:8])
        assert values.base is araster.base

    def test_exterior(_):
        araster = np.arange(100).reshape(10, 10)
        bounds = BoundingBox(-5, 15, 8, 3)
        affine = Transform(1, 1, 0, 0).affine
        values = clip.values(araster, bounds, affine, nodata=np.array(0))

        expected = np.zeros((12, 13))
        expected[:7, 5:] = araster[3:, :8]
        assert np.array_equal(values, expected)

    @pytest.mark.parametrize(
        "clipped",
        (
            {"left": 1.9, "right": 7.9, "bottom": 7.9, "top": 2.9},
            {"left": 2.2, "right": 8.2, "bottom": 8.2, "top": 3.2},
        ),
    )
    def test_inexact(_, clipped):
        araster = np.arange(100).reshape(10, 10)
        bounds = BoundingBox.from_dict(clipped)
        affine = Transform(1, 1, 0, 0).affine
        values = clip.values(araster, bounds, affine, nodata=np.array(-9))
        assert np.array_equal(values, araster[3:8, 2:8])
        assert values.base is araster.base
