import pytest
from pyproj import CRS

from pfdf.projection import Transform
from pfdf.raster import _align


class TestLength:
    def test_oriented(_):
        assert _align._npixels(10, 4, 2) == 3

    def test_flipped(_):
        assert _align._npixels(4, 10, 2) == 3

    def test_partial(_):
        assert _align._npixels(10, 5, 2) == 3


class TestEdge:
    @pytest.mark.parametrize(
        "dx, redge, expected",
        (
            (2, 27, 27),
            (2, 2.9, 1),
            (2, 5.1, 5),
            (-2, 3.1, 5),
            (-2, 0.9, 1),
        ),
    )
    def test(_, dx, redge, expected):
        assert _align._edge(dx, 3, redge) == expected


class TestReprojection:
    def test_resolution_overlapping(_, crs):
        source = Transform(1, 1, 0, 0)
        bounds = source.bounds(10, 10)
        transform = Transform(2, 2, 0, 0)

        output = _align.reprojection(crs, crs, bounds, transform)
        assert output == (transform, (5, 5))

    def test_resolution_no_overlap(_, crs):
        source = Transform(1, 1, 0, 0)
        bounds = source.bounds(10, 10)
        ttransform = Transform(2, 2, 100, 50)

        aligned, shape = _align.reprojection(crs, crs, bounds, ttransform)
        assert shape == (5, 5)
        assert aligned == Transform(2, 2, 0, 0)

    def test_alignment(_, crs):
        bounds = Transform(1, 1, 0, 0).bounds(10, 10)
        ttransform = Transform(1, 1, 0.1, 0.1)

        transform, shape = _align.reprojection(crs, crs, bounds, ttransform)
        assert shape == (11, 11)
        assert transform == Transform(1, 1, -0.9, -0.9)

    def test_resolution_alignment(_, crs):
        bounds = Transform(1, 1, 5, 6).bounds(10, 10)
        ttransform = Transform(2, 3, 20.1, 10)

        transform, shape = _align.reprojection(crs, crs, bounds, ttransform)
        assert shape == (4, 6)
        expected = Transform(2, 3, 4.1, 4)
        assert transform.isclose(expected)

    def test_invert_orientation(_, crs):
        bounds = Transform(1, 1, 0, 0).bounds(10, 10)
        ttransform = Transform(-1, -1, 0, 0)

        transform, shape = _align.reprojection(crs, crs, bounds, ttransform)
        assert shape == (10, 10)
        assert transform == Transform(-1, -1, 10, 10)

    def test_negative_orientation(_, crs):
        bounds = Transform(-1, -1, 10, 10).bounds(10, 10)
        ttransform = Transform(-2, -2, 6, 6)

        transform, shape = _align.reprojection(crs, crs, bounds, ttransform)
        assert shape == (5, 5)
        assert transform == Transform(-2, -2, 10, 10)

    def test_reproject(_):
        icrs = CRS(26911)
        fcrs = CRS(26910)
        transform = Transform(10, -10, 492850, 3787000)
        bounds = transform.bounds(10, 10)

        transform, shape = _align.reprojection(icrs, fcrs, bounds, transform)
        assert shape == (12, 12)
        expected = Transform(10, -10, 1045830, 3802910)
        assert transform.isclose(expected)
