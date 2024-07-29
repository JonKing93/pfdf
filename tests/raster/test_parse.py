import pytest

from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster, _parse


class TestProjection:
    def test_none(_):
        crs = CRS(4326)
        projection = None
        assert _parse.projection(crs, projection, (3, 4)) == (crs, None)

    def test_bounds(_):
        crs = CRS(26911)
        bounds = BoundingBox(0, 1, 100, 501, 26911)
        outcrs, transform = _parse.projection(crs, bounds, (10, 100))
        assert outcrs == crs
        assert transform == Transform(1, -50, 0, 501, 26911)

    def test_transform(_):
        crs = CRS(26911)
        transform = Transform(10, 5, 0, 1)
        outcrs, outtransform = _parse.projection(crs, transform, (10, 100))
        assert outcrs == crs
        assert outtransform == transform

    def test_inherit(_):
        crs = None
        transform = Transform(1, 2, 3, 4, 26911)
        outcrs, outtransform = _parse.projection(crs, transform, (10, 11))
        assert outcrs == CRS(26911)
        assert outtransform == transform

    def test_reproject_from_transform(_):
        crs = CRS(4326)
        transform = Transform(1, 2, 3, 4, 26911)
        outcrs, outtra = _parse.projection(crs, transform, (10, 5))
        expected = Transform(
            dx=8.958995962871086e-06,
            dy=1.8038752956919747e-05,
            left=-121.4887170073974,
            top=3.607750457626307e-05,
            crs=crs,
        )
        assert outcrs == crs
        assert outtra.isclose(expected)

    def test_reproject_from_bounds(_):
        crs = CRS(4326)
        bounds = BoundingBox(0, 0, 100, 500, 26911)
        outcrs, outtra = _parse.projection(crs, bounds, (10, 5))
        expected = Transform(
            dx=0.00017918258576798962,
            dy=-0.0004509677872809176,
            left=-121.48874389822696,
            top=0.004509687904713325,
            crs=crs,
        )
        assert outcrs == crs
        assert outtra.isclose(expected)


class TestTemplate:
    def test_no_template(_):
        output = _parse.template(None, "template", 1, 2)
        assert output == (1, 2)

    def test_no_keywords(_):
        template = Raster()
        template._set_metadata(1, 2, 3)
        crs, transform = _parse.template(template, "template", 1, 2)
        assert crs == 1
        assert transform == 2

    def test_mixed(_):
        template = Raster()
        template._set_metadata(1, 2, 3)
        output = _parse.template(template, "template", None, 4)
        assert output == (1, 4)

    def test_invalid_template(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _parse.template("invalid", "template name", 1, 2)
        assert_contains(error, "Raster object")


class TestSrcDst:
    def test(_):
        assert _parse.src_dst(1, 2, 3) == (1, 2)
        assert _parse.src_dst(None, 2, 3) == (2, 2)
        assert _parse.src_dst(1, None, 3) == (1, 1)
        assert _parse.src_dst(None, None, 3) == (3, 3)
