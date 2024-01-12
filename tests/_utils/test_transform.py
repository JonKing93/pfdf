from math import isnan, nan

import pytest
from affine import Affine
from rasterio.coords import BoundingBox

from pfdf._utils.transform import Transform
from pfdf.errors import TransformError


@pytest.fixture
def transform():
    matrix = Affine(1, 0, 2, 0, 3, 4)
    return Transform(matrix)


@pytest.fixture
def ntransform():
    return Transform(Affine(-1, 0, 2, 0, -3, 4))


@pytest.fixture
def tnone():
    return Transform(None)


@pytest.fixture
def oriented():
    return Transform(Affine(1, 0, 2, 0, -3, 4))


@pytest.fixture
def unoriented():
    return Transform(Affine(-1, 0, 2, 0, 3, 4))


class TestBuild:
    def test(_):
        a = Transform.build(1, 2, 3, 4)
        assert a == Affine(1, 0, 3, 0, 2, 4)


class TestInit:
    def test_none(_):
        a = Transform(None)
        assert isinstance(a, Transform)
        assert a.affine is None

    def test_shear(_):
        a = Affine(1, 2, 3, 4, 5, 6)
        with pytest.raises(TransformError):
            Transform(a)

    def test_standard(_):
        a = Affine(1, 0, 2, 0, 3, 4)
        output = Transform(a)
        assert isinstance(output, Transform)
        assert output.affine == a


class TestCoefficient:
    @pytest.mark.parametrize("k", (0, 1, 2, 3, 4, 5))
    def test_none(_, tnone, k):
        output = tnone.coefficient(k)
        assert isnan(output)

    @pytest.mark.parametrize(
        "k, expected",
        (
            (0, 1),
            (1, 0),
            (2, 2),
            (3, 0),
            (4, 3),
            (5, 4),
        ),
    )
    def test(_, transform, k, expected):
        assert transform.coefficient(k) == expected


class TestDx:
    def test(_, transform):
        assert transform.dx == 1

    def test_none(_, tnone):
        assert isnan(tnone.dx)

    def test_flipped(_, ntransform):
        assert ntransform.dx == -1


class TestDy:
    def test(_, transform):
        assert transform.dy == 3

    def test_none(_, tnone):
        assert isnan(tnone.dy)

    def test_flipped(_, ntransform):
        assert ntransform.dy == -3


class TestLeft:
    def test(_, transform):
        assert transform.left == 2

    def test_none(_, tnone):
        assert isnan(tnone.left)

    def test_flipped(_, ntransform):
        assert ntransform.left == 2


class TestTop:
    def test(_, transform):
        assert transform.top == 4

    def test_none(_, tnone):
        assert isnan(tnone.top)

    def test_flipped(_, ntransform):
        assert ntransform.top == 4


class TestRight:
    def test(_, transform):
        assert transform.right(5) == 7

    def test_none(_, tnone):
        assert isnan(tnone.right(5))

    def test_flipped(_, ntransform):
        assert ntransform.right(5) == -3


class TestBottom:
    def test(_, transform):
        assert transform.bottom(5) == 19

    def test_none(_, tnone):
        assert isnan(tnone.bottom(5))

    def test_flipped(_, ntransform):
        assert ntransform.bottom(5) == -11


class TestBounds:
    def test(_, transform):
        assert transform.bounds((5, 5)) == BoundingBox(2, 19, 7, 4)

    def test_none(_, tnone):
        bounds = tnone.bounds((5, 5))
        assert isinstance(bounds, BoundingBox)
        for edge in ["left", "right", "bottom", "top"]:
            value = getattr(bounds, edge)
            assert isnan(value)

    def test_flipped(_, ntransform):
        assert ntransform.bounds((5, 5)) == BoundingBox(2, -11, -3, 4)


class TestOrientedBounds:
    def test_default_oriented(_, oriented):
        assert oriented.oriented_bounds((5, 5)) == BoundingBox(2, -11, 7, 4)

    def test_default_reorient(_, unoriented):
        assert unoriented.oriented_bounds((5, 5)) == BoundingBox(-3, 4, 2, 19)

    def test_flip_x(_, oriented):
        output = oriented.oriented_bounds((5, 5), False, True)
        assert output == BoundingBox(7, -11, 2, 4)

    def test_flip_y(_, oriented):
        output = oriented.oriented_bounds((5, 5), True, False)
        assert output == BoundingBox(2, 4, 7, -11)


class TestXres:
    def test(_, transform):
        assert transform.xres == 1

    def test_none(_, tnone):
        assert isnan(tnone.xres)

    def test_fippped(_, ntransform):
        assert ntransform.xres == 1


class TestYres:
    def test(_, transform):
        assert transform.yres == 3

    def test_none(_, tnone):
        assert isnan(tnone.yres)

    def test_flipped(_, ntransform):
        assert ntransform.yres == 3


class TestResolution:
    def test(_, transform):
        assert transform.resolution == (1, 3)

    def test_none(_, tnone):
        output = tnone.resolution
        assert isinstance(output, tuple)
        assert len(output) == 2
        assert isnan(output[0])
        assert isnan(output[1])

    def test_flipped(_, ntransform):
        assert ntransform.resolution == (1, 3)
