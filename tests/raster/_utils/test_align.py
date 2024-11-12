import pytest

from pfdf.projection import Transform
from pfdf.raster import RasterMetadata
from pfdf.raster._utils import align


class TestLength:
    def test_oriented(_):
        assert align._npixels(10, 4, 2) == 3

    def test_flipped(_):
        assert align._npixels(4, 10, 2) == 3

    def test_partial(_):
        assert align._npixels(10, 5, 2) == 3


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
        assert align._edge(dx, 3, redge) == expected


class TestReprojection:
    def test_resolution_overlapping(_, crs):
        bounds = Transform(1, 1, 0, 0).bounds(10, 10)
        template = RasterMetadata((1, 1), crs=crs, transform=(2, 2, 0, 0))
        transform, shape = align.reprojection(bounds, template)
        assert transform == Transform(2, 2, 0, 0, crs)
        assert shape == (5, 5)

    def test_resolution_no_overlap(_, crs):
        bounds = Transform(1, 1, 0, 0).bounds(10, 10)
        template = RasterMetadata((1, 1), crs=crs, transform=(2, 2, 100, 50))
        transform, shape = align.reprojection(bounds, template)
        assert transform == Transform(2, 2, 0, 0, crs)
        assert shape == (5, 5)

    def test_alignment(_, crs):
        bounds = Transform(1, 1, 0, 0).bounds(10, 10)
        template = RasterMetadata((1, 1), crs=crs, transform=(1, 1, 0.1, 0.1))
        transform, shape = align.reprojection(bounds, template)
        assert transform == Transform(1, 1, -0.9, -0.9, crs)
        assert shape == (11, 11)

    def test_resolution_alignment(_, crs):
        bounds = Transform(1, 1, 5, 6).bounds(10, 10)
        template = RasterMetadata((1, 1), crs=crs, transform=(2, 3, 20.1, 10))
        transform, shape = align.reprojection(bounds, template)
        assert transform.isclose(Transform(2, 3, 4.1, 4, crs))
        assert shape == (4, 6)

    def test_invert_orientation(_, crs):
        bounds = Transform(1, 1, 0, 0).bounds(10, 10)
        template = RasterMetadata((1, 1), crs=crs, transform=(-1, -1, 0, 0))
        transform, shape = align.reprojection(bounds, template)
        assert transform == Transform(-1, -1, 10, 10, crs)
        assert shape == (10, 10)

    def test_negative_orientation(_, crs):
        bounds = Transform(-1, -1, 10, 10).bounds(10, 10)
        template = RasterMetadata((1, 1), crs=crs, transform=(-2, -2, 6, 6))
        transform, shape = align.reprojection(bounds, template)
        assert transform == Transform(-2, -2, 10, 10, crs)
        assert shape == (5, 5)

    def test_reproject(_):
        bounds = Transform(10, -10, 492850, 3787000, 26911).bounds(10, 10)
        template = RasterMetadata(
            (1, 1), crs=26910, transform=(10, -10, 492850, 3787000)
        )
        transform, shape = align.reprojection(bounds, template)
        assert transform == Transform(10, -10, 1045830, 3802910, 26910)
        assert shape == (12, 12)
