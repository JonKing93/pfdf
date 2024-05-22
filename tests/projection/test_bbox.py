import numpy as np
import pytest
from affine import Affine
from pyproj import CRS

from pfdf.errors import CRSError, MissingCRSError
from pfdf.projection import BoundingBox, Transform, _crs


def check(bounds, crs):
    assert isinstance(bounds, BoundingBox)
    assert bounds.left == 0
    assert bounds.bottom == 10
    assert bounds.right == 50
    assert bounds.top == 100
    assert _crs.name(bounds.crs) == crs


#####
# Properties
#####


class TestNames:
    def test(_):
        assert BoundingBox._names == ["left", "bottom", "right", "top"]


class TestAtts:
    def test(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a._atts == ["_left", "_bottom", "_right", "_top", "crs"]


class TestArgs:
    def test(_):
        assert BoundingBox._args() == ["left", "bottom", "right", "top", "crs"]


class TestCrs:
    def test(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a.crs is None
        a = BoundingBox(1, 2, 3, 4, 4326)
        assert a.crs == CRS(4326)


class TestXunit:
    def test_none(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a.xunit is None

    def test_linear(_):
        a = BoundingBox(1, 2, 3, 4, 26911)
        assert a.xunit == "metre"

    def test_angular(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        assert a.xunit == "degree"


class TestYUnit:
    def test_none(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a.yunit is None

    def test_linear(_):
        a = BoundingBox(1, 2, 3, 4, 26911)
        assert a.yunit == "metre"

    def test_angular(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        assert a.yunit == "degree"


class TestUnits:
    def test_none(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a.units == (None, None)

    def test_linear(_):
        a = BoundingBox(1, 2, 3, 4, 26911)
        assert a.units == ("metre", "metre")

    def test_angular(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        assert a.units == ("degree", "degree")


class TestXUnitsPerM:
    def test_none(_):
        a = BoundingBox(0, 29, 0, 31)
        assert a.x_units_per_m is None

    def test_linear(_):
        a = BoundingBox(0, 29, 0, 31, 26911)
        assert a.x_units_per_m == 1

    def test_angular(_):
        a = BoundingBox(0, 29, 0, 31, 4326)
        output = a.x_units_per_m
        assert np.allclose(output, 1.0384471425304483e-05)


class TestYUnitsPerM:
    def test_none(_):
        a = BoundingBox(0, 29, 0, 31)
        assert a.y_units_per_m is None

    def test_linear(_):
        a = BoundingBox(0, 29, 0, 31, 26911)
        assert a.y_units_per_m == 1

    def test_angular_default(_):
        a = BoundingBox(0, 29, 0, 31, 4326)
        output = a.y_units_per_m
        assert np.allclose(output, 8.993216059187306e-06)


class TestUnitsPerM:
    def test_none(_):
        a = BoundingBox(0, 29, 0, 31)
        assert a.units_per_m == (None, None)

    def test_linear(_):
        a = BoundingBox(0, 29, 0, 31, 26911)
        assert a.units_per_m == (1, 1)

    def test_angular(_):
        a = BoundingBox(0, 29, 0, 31, 4326)
        output = a.units_per_m
        expected = (1.0384471425304483e-05, 8.993216059187306e-06)
        assert np.allclose(output, expected)


class TestOrientation:
    @pytest.mark.parametrize(
        "left,bottom,quadrant",
        ((1, 2, 1), (5, 2, 2), (5, 5, 3), (1, 5, 4)),
    )
    def test(_, left, bottom, quadrant):
        assert BoundingBox(left, bottom, 3, 4).orientation == quadrant


#####
# Edge Properties
#####


class TestLeft:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).left == 0


class TestBottom:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).bottom == 10


class TestRight:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).right == 50


class TestTop:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).top == 100


class TestXs:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).xs == (0, 50)


class TestYs:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).ys == (10, 100)


class TestBounds:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).bounds == (0, 10, 50, 100)


class TestCenter:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).center == (25, 55)


class TestCenterX:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).center_x == 25


class TestCenterY:
    def test(_):
        assert BoundingBox(0, 10, 50, 100).center_y == 55


#####
# Object creation
#####


class TestInit:
    def test_nocrs(_):
        a = BoundingBox(0, 10, 50, 100)
        check(a, "None")

    def test_with_crs(_):
        a = BoundingBox(0, 10, 50, 100, 4326)
        check(a, "WGS 84")

    def test_invalid(_):
        with pytest.raises(TypeError):
            BoundingBox("invalid", 2, 3, 4)

    @pytest.mark.parametrize("bad", (np.inf, -np.inf, np.nan))
    def test_nonfinite(_, bad):
        with pytest.raises(ValueError):
            BoundingBox(bad, 2, 3, 4)


class TestFromDict:
    def test_valid_crs(_):
        a = {"left": 0, "bottom": 10, "right": 50, "top": 100, "crs": 4326}
        a = BoundingBox.from_dict(a)
        check(a, "WGS 84")

    def test_valid_nocrs(_):
        a = {"left": 0, "bottom": 10, "right": 50, "top": 100}
        a = BoundingBox.from_dict(a)
        check(a, "None")

    def test_invalid_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            BoundingBox.from_dict("invalid")
        assert_contains(error, "BoundingBox dict")

    def test_missing_key(_, assert_contains):
        a = {"left": 1, "right": 2, "bottom": 3}
        with pytest.raises(KeyError) as error:
            BoundingBox.from_dict(a)
        assert_contains(error, "BoundingBox dict is missing the 'top' key")

    def test_bad_key(_, assert_contains):
        a = {"left": 0, "bottom": 10, "right": 50, "top": 100, "invalid": 5}
        with pytest.raises(KeyError) as error:
            BoundingBox.from_dict(a)
        assert_contains(error, "BoundingBox dict has an unrecognized key: invalid")


class TestFromList:
    def test_invalid_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            BoundingBox.from_list("test")
        assert_contains(error, "BoundingBox sequence", "list or tuple")

    def test_valid_crs(_):
        a = [0, 10, 50, 100, 4326]
        a = BoundingBox.from_list(a)
        check(a, "WGS 84")

    def test_valid_nocrs(_):
        a = [0, 10, 50, 100]
        a = BoundingBox.from_list(a)
        check(a, "None")

    def test_invalid_length(_, assert_contains):
        a = [1, 2, 3]
        with pytest.raises(ValueError) as error:
            BoundingBox.from_list(a)
        assert_contains(error, "must have either 4 or 5 elements")


class TestCopy:
    def test(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        b = a.copy()
        assert a == b
        assert a is not b


#####
# Dunders
#####


class TestRepr:
    def test_crs(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        assert (
            a.__repr__()
            == 'BoundingBox(left=1, bottom=2, right=3, top=4, crs="WGS 84")'
        )

    def test_nocrs(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a.__repr__() == "BoundingBox(left=1, bottom=2, right=3, top=4, crs=None)"


class TestEq:
    def test_other_type(_):
        assert BoundingBox(1, 2, 3, 4) != 5

    def test_other_transform(_):
        assert BoundingBox(1, 2, 3, 4) != BoundingBox(4, 5, 6, 7)

    def test_same(_):
        assert BoundingBox(1, 2, 3, 4, None) == BoundingBox(1, 2, 3, 4, None)

    def test_same_crs(_):
        assert BoundingBox(1, 2, 3, 4, 26911) == BoundingBox(1, 2, 3, 4, 26911)


#####
# Box Lengths
#####


class TestXdisp:
    def test(_):
        a = BoundingBox(1, 2, -3, 4)
        assert a.xdisp() == -4

    def test_linear(_):
        a = BoundingBox(1, 2, -3, 4, 26911)
        assert a.xdisp(meters=True) == -4

    def test_angular(_):
        a = BoundingBox(1, 2, -3, 4, 4326)
        assert a.xdisp(meters=True) == -444169.90426228574

    def test_invalid_meters(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.xdisp(meters=True)
        assert_contains(
            error,
            "Cannot convert xdisp to meters because the BoundingBox does not have a CRS",
        )


class TestYdisp:
    def test(_):
        a = BoundingBox(1, 4, 3, 2)
        assert a.ydisp() == -2

    def test_linear(_):
        a = BoundingBox(1, 4, 3, 2, 26911)
        assert a.ydisp(meters=True) == -2

    def test_angular(_):
        a = BoundingBox(1, 4, 3, 2, 4326)
        assert a.ydisp(meters=True) == -2 * 111194.92664455874

    def test_invalid_meters(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.ydisp(meters=True)
        assert_contains(
            error,
            "Cannot convert ydisp to meters because the BoundingBox does not have a CRS",
        )


class TestWidth:
    def test(_):
        a = BoundingBox(1, 2, -3, 4)
        assert a.width() == 4

    def test_meters(_):
        a = BoundingBox(1, 2, -3, 4, 4326)
        assert a.width(meters=True) == 444169.90426228574


class TestHeight:
    def test(_):
        a = BoundingBox(1, 4, 3, 2)
        assert a.height() == 2

    def test_meters(_):
        a = BoundingBox(1, 4, 3, 2, 4326)
        assert a.height(meters=True) == 2 * 111194.92664455874


#####
# Orientation
#####


class TestInversion:
    @pytest.mark.parametrize(
        "quadrant,inverted,expected",
        (
            (1, [2, 3], False),
            (2, [2, 3], True),
            (3, (2, 3), True),
            (4, [2, 3], False),
            (1, [3, 4], False),
            (2, [3, 4], False),
            (3, [3, 4], True),
            (4, [3, 4], True),
        ),
    )
    def test(_, quadrant, inverted, expected):
        a = BoundingBox(0, 0, 10, 10)
        assert a._inversion(quadrant, inverted) == expected

    @pytest.mark.parametrize(
        "quadrant,inverted,expected",
        (
            (1, [2, 3], True),
            (2, [2, 3], False),
            (3, (2, 3), False),
            (4, [2, 3], True),
            (1, [3, 4], True),
            (2, [3, 4], True),
            (3, [3, 4], False),
            (4, [3, 4], False),
        ),
    )
    def test_inverted(_, quadrant, inverted, expected):
        a = BoundingBox(0, 0, -10, -10)
        assert a._inversion(quadrant, inverted) == expected


class TestOrient:
    def test(_):
        a = BoundingBox(0, 10, 50, 100)
        assert a.orient(1) == a
        assert a.orient(2) == BoundingBox(50, 10, 0, 100)
        assert a.orient(3) == BoundingBox(50, 100, 0, 10)
        assert a.orient(4) == BoundingBox(0, 100, 50, 10)

    def test_invalid(_, assert_contains):
        a = BoundingBox(0, 10, 50, 100)
        with pytest.raises(ValueError) as error:
            a.orient(5)
        assert_contains(error, "Orientation quadrant must be 1, 2, 3, or 4")


#####
# Buffer
####


class TestBufferEdges:
    def test(_):
        output = BoundingBox._buffer_edges(0, 5, 50, 10)
        assert output == (-5, 60)

    def test_inverted(_):
        output = BoundingBox._buffer_edges(50, 5, 0, 10)
        assert output == (55, -10)


class TestBuffer:
    def test_missing_crs(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.buffer(5, meters=True)
        assert_contains(
            error,
            "Cannot convert buffering distances from meters",
            "BoundingBox does not have a CRS",
        )

    def test_basic(_):
        a = BoundingBox(0, 10, 50, 100)
        output = a.buffer(5)
        assert output == BoundingBox(-5, 5, 55, 105)

    def test_mixed(_):
        a = BoundingBox(0, 10, 50, 100)
        output = a.buffer(5, left=20, top=1)
        assert output == BoundingBox(-20, 5, 55, 101)

    def test_inverted(_):
        a = BoundingBox(50, 100, 0, 10)
        output = a.buffer(5)
        assert output == BoundingBox(55, 105, -5, 5)

    def test_meters(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        output = a.buffer(5, meters=True)
        assert output == BoundingBox(
            left=0.9999549722106837,
            bottom=1.999955033919704,
            right=3.0000450277893163,
            top=4.000044966080296,
            crs="WGS 84",
        )


#####
# Reprojection
#####


class TestUtmZone:
    def test(_):
        a = BoundingBox(-122, 34, -120, 36, 4326)
        assert a.utm_zone() == CRS(32610)

    def test_nocrs(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.utm_zone()
        assert_contains(
            error,
            "Cannot determine the UTM zone for the BoundingBox because it does not have a CRS",
        )

    def test_outside_domain(_):
        a = BoundingBox(-120, 86, -119, 88, 4326)
        assert a.utm_zone() is None


class TestReproject:
    def test_nocrs(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.reproject(4326)
        assert_contains(
            error, "Cannot reproject the BoundingBox because it does not have a CRS"
        )

    def test_none_crs(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4, 26911)
        with pytest.raises(CRSError) as error:
            a.reproject(None)
        assert_contains(error, "The 'crs' input cannot be None")

    def test(_):
        a = BoundingBox(0, 10, 50, 100, 26911)
        output = a.reproject(4326)
        assert output == BoundingBox(
            left=-121.48874388494063,
            bottom=9.019375809670199e-05,
            right=-121.48829593442018,
            top=0.0009019381382659413,
            crs="WGS 84",
        )

    def test_outside_domain(_, assert_contains):
        a = BoundingBox(100, 100, 105, 105, 4326)
        with pytest.raises(RuntimeError) as error:
            a.reproject(26911)
        assert_contains(
            error,
            "Cannot reproject the BoundingBox because it contains points outside the domain of its CRS",
        )


class TestToUtm:
    def test(_):
        a = BoundingBox(-122, 34, -120, 36, 4326)
        a = a.to_utm()
        assert a.crs == CRS("WGS 84 / UTM zone 10N")
        expected = BoundingBox(
            590129.04941026,
            3762606.6598762735,
            777091.295474178,
            3988111.9623426683,
        )
        assert a.isclose(expected)

    def test_outside_domain(_, assert_contains):
        a = BoundingBox(-120, 86, -119, 88, 4326)
        with pytest.raises(ValueError) as error:
            a.to_utm()
        assert_contains(
            error,
            "Cannot reproject the BoundingBox to UTM because its center is not in the UTM domain",
        )


class TestTo4326:
    def test(_):
        a = BoundingBox(0, 10, 50, 100, 26911)
        assert a.to_4326() == BoundingBox(
            left=-121.48874388494063,
            bottom=9.019375809670199e-05,
            right=-121.48829593442018,
            top=0.0009019381382659413,
            crs="WGS 84",
        )


#####
# Transform Conversion
#####


class TestDelta:
    def test_valid(_):
        a = BoundingBox(1, 2, 3, 4)
        assert a._delta(5, "dx", a.xdisp, False) == 2 / 5

    def test_invalid(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        with pytest.raises(ValueError) as error:
            a._delta(2.2, "dx", a.xdisp, False)
        assert_contains(error, "dx", "integer")


class TestDx:
    def test(_):
        a = BoundingBox(0, 10, 50, 100)
        assert a.dx(10) == 5


class TestDy:
    def test(_):
        a = BoundingBox(0, 10, 50, 100)
        assert a.dy(5) == -18


class TestTransform:
    def test(_):
        a = BoundingBox(0, 10, 50, 100)
        b = a.transform(5, 10)
        assert b == Transform(5, -18, 0, 100)

    def test_inverted(_):
        a = BoundingBox(50, 100, 0, 10)
        b = a.transform(10, 10)
        assert b == Transform(-5, 9, 50, 10)


#####
# Builtin Conversion
#####


class TestToList:
    def test(_):
        assert BoundingBox(1, 2, 3, 4).tolist() == [1, 2, 3, 4, None]
        assert BoundingBox(1, 2, 3, 4, 4326).tolist() == [1, 2, 3, 4, CRS(4326)]

    def test_no_crs(_):
        assert BoundingBox(1, 2, 3, 4, 4326).tolist(crs=False) == [1, 2, 3, 4]


class TestToDict:
    def test(_):
        assert BoundingBox(1, 2, 3, 4).todict() == {
            "left": 1,
            "bottom": 2,
            "right": 3,
            "top": 4,
            "crs": None,
        }
        assert BoundingBox(1, 2, 3, 4, 4326).todict() == {
            "left": 1,
            "bottom": 2,
            "right": 3,
            "top": 4,
            "crs": CRS(4326),
        }


#####
# Testing
#####


class TestIsClose:
    def test_close(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        b = BoundingBox(1.0000000000000000001, 2, 3, 4, 4326)
        assert a.isclose(b) == True

    def test_not_close(_):
        a = BoundingBox(1, 2, 3, 4)
        b = BoundingBox(2, 2, 3, 4)
        assert a.isclose(b) == False

    def test_invalid(_, assert_contains):
        a = BoundingBox(1, 2, 3, 4)
        b = (1, 2, 3, 4)
        with pytest.raises(TypeError) as error:
            a.isclose(b)
        assert_contains(error, "Other object must also be a BoundingBox object")

    def test_different_crs(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        b = BoundingBox(1, 2, 3, 4, 26911)
        assert a.isclose(b) == False

    def test_none_crs(_):
        a = BoundingBox(1, 2, 3, 4)
        b = BoundingBox(1, 2, 3, 4, 4326)
        assert a.isclose(b) == True
