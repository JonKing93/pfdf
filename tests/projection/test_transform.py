from cmath import sqrt

import numpy as np
import pytest
from affine import Affine
from pyproj import CRS

from pfdf.errors import CRSError, DimensionError, MissingCRSError, TransformError
from pfdf.projection import BoundingBox, Transform
from pfdf.projection import crs as _crs


def check(transform, crs):
    assert isinstance(transform, Transform)
    assert transform.dx() == 1
    assert transform.dy() == 2
    assert transform.left == 3
    assert transform.top == 4
    assert _crs.name(transform.crs) == crs


#####
# Properties
#####


class TestNames:
    def test(_):
        assert Transform._names == ["dx", "dy", "left", "top"]


class TestAtts:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a._atts == ["_dx", "_dy", "_left", "_top", "crs"]


class TestArgs:
    def test(_):
        assert Transform._args() == ["dx", "dy", "left", "top", "crs"]


class TestCrs:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a.crs is None
        a = Transform(1, 2, 3, 4, 4326)
        assert a.crs == CRS(4326)


class TestXunit:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        assert a.xunit is None

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.xunit == "metre"

    def test_angular(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.xunit == "degree"


class TestYUnit:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        assert a.yunit is None

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.yunit == "metre"

    def test_angular(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.yunit == "degree"


class TestUnits:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        assert a.units == (None, None)

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.units == ("metre", "metre")

    def test_angular(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.units == ("degree", "degree")


class TestClass:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a._class == "Transform"


class TestLeft:
    def test(_):
        assert Transform(1, 2, 3, 4).left == 3


class TestTop:
    def test(_):
        assert Transform(1, 2, 3, 4).top == 4


class TestOrientation:
    @pytest.mark.parametrize(
        "dx,dy,quadrant",
        ((1, -2, 1), (-1, -2, 2), (-1, 2, 3), (1, 2, 4)),
    )
    def test(_, dx, dy, quadrant):
        assert Transform(dx, dy, 3, 4).orientation == quadrant


class TestAffine:
    def test(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.affine == Affine(1, 0, 3, 0, 2, 4)


#####
# Object creation
#####


class TestInit:
    def test_nocrs(_):
        a = Transform(1, 2, 3, 4)
        check(a, "None")

    def test_with_crs(_):
        a = Transform(1, 2, 3, 4, 4326)
        check(a, "WGS 84")

    def test_invalid(_):
        with pytest.raises(TypeError):
            Transform("invalid", 2, 3, 4)

    @pytest.mark.parametrize("bad", (np.inf, -np.inf, np.nan))
    def test_nonfinite(_, bad):
        with pytest.raises(ValueError):
            Transform(bad, 2, 3, 4)


class TestFromDict:
    def test_valid_crs(_):
        a = {"dx": 1, "dy": 2, "left": 3, "top": 4, "crs": 4326}
        a = Transform.from_dict(a)
        check(a, "WGS 84")

    def test_valid_nocrs(_):
        a = {"dx": 1, "dy": 2, "left": 3, "top": 4}
        a = Transform.from_dict(a)
        check(a, "None")

    def test_invalid_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Transform.from_dict("invalid")
        assert_contains(error, "Transform dict")

    def test_missing_key(_, assert_contains):
        a = {"dx": 1, "dy": 2, "left": 3}
        with pytest.raises(KeyError) as error:
            Transform.from_dict(a)
        assert_contains(error, "Transform dict is missing the 'top' key")

    def test_bad_key(_, assert_contains):
        a = {"dx": 1, "dy": 2, "left": 3, "top": 4, "invalid": 5}
        with pytest.raises(KeyError) as error:
            Transform.from_dict(a)
        assert_contains(error, "Transform dict has an unrecognized key: invalid")


class TestFromAffine:
    def test_invalid_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Transform.from_affine("invalid")
        assert_contains(error, "Transform input", "affine.Affine")

    def test_invalid_coeff(_, assert_contains):
        a = Affine(1, 0, 3, 0, 5, sqrt(-1))
        with pytest.raises(TypeError) as error:
            Transform.from_affine(a)
        assert_contains(error, "Affine coefficient 'f'")

    def test_nonscalar_coeff(_, assert_contains):
        a = Affine(1, 0, 0, 0, 0, np.array([1, 2, 3, 4]))
        with pytest.raises(DimensionError) as error:
            Transform.from_affine(a)
        assert_contains(error, "Affine coefficient 'f'")

    def test_shear(_, assert_contains):
        a = Affine(1, 2, 3, 4, 5, 6)
        with pytest.raises(TransformError) as error:
            Transform.from_affine(a)
        assert_contains(
            error, "affine transform must only support scaling and translation"
        )

    def test_valid(_):
        a = Affine(1, 0, 3, 0, 2, 4)
        a = Transform.from_affine(a)
        check(a, "None")


class TestFromList:
    def test_invalid_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            Transform.from_list("test")
        assert_contains(error, "Transform sequence", "list or tuple")

    def test_affine(_):
        a = [1, 0, 3, 0, 2, 4]
        a = Transform.from_list(a)
        check(a, "None")

    def test_valid_crs(_):
        a = [1, 2, 3, 4, 4326]
        a = Transform.from_list(a)
        check(a, "WGS 84")

    def test_valid_nocrs(_):
        a = [1, 2, 3, 4]
        a = Transform.from_list(a)
        check(a, "None")

    def test_invalid_length(_, assert_contains):
        a = [1, 2, 3]
        with pytest.raises(ValueError) as error:
            Transform.from_list(a)
        assert_contains(error, "must have either 4 or 5 elements")


class TestCopy:
    def test(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = a.copy()
        assert a == b
        assert a is not b


#####
# Dunders
#####


class TestRepr:
    def test_crs(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert (
            a.__repr__() == 'Transform(dx=1.0, dy=2.0, left=3.0, top=4.0, crs="WGS 84")'
        )

    def test_nocrs(_):
        a = Transform(1, 2, 3, 4)
        assert a.__repr__() == "Transform(dx=1.0, dy=2.0, left=3.0, top=4.0, crs=None)"


class TestEq:
    def test_other_type(_):
        assert Transform(1, 2, 3, 4) != 5

    def test_other_transform(_):
        assert Transform(1, 2, 3, 4) != Transform(4, 5, 6, 7)

    def test_same(_):
        assert Transform(1, 2, 3, 4, None) == Transform(1, 2, 3, 4, None)

    def test_same_crs(_):
        assert Transform(1, 2, 3, 4, 26911) == Transform(1, 2, 3, 4, 26911)


#####
# Resolution and pixel geometry
#####


class TestDx:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a.dx() == 1

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.dx(units="meters") == 1

    def test_unit_conversion(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.dx(units="kilometres") == 0.001

    def test_angular_default(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.dx(units="meters") == 111194.92664455874

    def test_angular_y(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.dx(units="meters", y=30) == 96297.32567761187

    def test_invalid_meters(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.dx(units="meters")
        assert_contains(
            error,
            "Cannot convert dx to meters because the Transform does not have a CRS",
        )

    def test_invalid_y(_, assert_contains):
        a = Transform(1, 2, 3, 4, 4326)
        with pytest.raises(TypeError) as error:
            a.dx(units="meters", y="invalid")
        assert_contains(error, "y")


class TestDy:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a.dy() == 2

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.dy(units="meters") == 2

    def test_unit_conversion(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.dy(units="kilometers") == 0.002

    def test_angular(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a.dy(units="meters") == 2 * 111194.92664455874

    def test_invalid_meters(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.dy(units="meters")
        assert_contains(
            error,
            "Cannot convert dy to meters because the Transform does not have a CRS",
        )


class TestXres:
    def test(_):
        a = Transform(-1, 2, 3, 4)
        assert a.xres() == 1

    def test_linear(_):
        a = Transform(-1, 2, 3, 4, 26911)
        assert a.xres(units="meters") == 1

    def test_units(_):
        a = Transform(-1, 2, 3, 4, 26911)
        assert a.xres(units="kilometers") == 0.001

    def test_angular_default(_):
        a = Transform(-1, 2, 3, 4, 4326)
        assert a.xres(units="meters") == 111194.92664455874

    def test_angular_y(_):
        a = Transform(-1, 2, 3, 4, 4326)
        assert a.xres(units="meters", y=30) == 96297.32567761187


class TestYres:
    def test(_):
        a = Transform(1, -2, 3, 4)
        assert a.yres() == 2

    def test_meters(_):
        a = Transform(1, -2, 3, 4, 4326)
        assert a.yres(units="meters") == 2 * 111194.92664455874

    def test_units(_):
        a = Transform(1, -2, 3, 4, 4326)
        assert a.yres(units="kilometers") == 2 * 111194.92664455874 / 1000


class TestResolution:
    def test(_):
        a = Transform(-1, 2, 3, 4)
        assert a.resolution() == (1, 2)

    def test_linear(_):
        a = Transform(-1, 2, 3, 4, 26911)
        assert a.resolution(units="meters") == (1, 2)

    def test_units(_):
        a = Transform(-1, 2, 3, 4, 26911)
        assert a.resolution(units="kilometers") == (0.001, 0.002)

    def test_angular_default(_):
        a = Transform(-1, 2, 3, 4, 4326)
        assert a.resolution(units="meters") == (
            111194.92664455874,
            2 * 111194.92664455874,
        )

    def test_angular_y(_):
        a = Transform(-1, 2, 3, 4, 4326)
        assert a.resolution(units="meters", y=30) == (
            96297.32567761187,
            2 * 111194.92664455874,
        )


class TestPixelArea:
    def test(_):
        a = Transform(10, -5, 3, 4)
        assert a.pixel_area() == 50

    def test_linear(_):
        a = Transform(10, -5, 3, 4, 26911)
        assert a.pixel_area(units="meters") == 50

    def test_units(_):
        a = Transform(10, -5, 3, 4, 26911)
        assert a.pixel_area(units="kilometers") == 0.00005

    def test_angular_default(_):
        a = Transform(-1, 2, 3, 4, 4326)
        assert a.pixel_area(units="meters") == 2 * 111194.92664455874**2

    def test_angular_y(_):
        a = Transform(-1, 2, 3, 4, 4326)
        assert (
            a.pixel_area(units="meters", y=30)
            == 96297.32567761187 * 2 * 111194.92664455874
        )


class TestPixelDiagonal:
    def test(_):
        a = Transform(3, 4, 0, 0)
        assert a.pixel_diagonal() == 5

    def test_meters(_):
        a = Transform(1, 1, 0, 0, 4326)
        output = a.pixel_diagonal(units="meters")
        expected = sqrt(2 * 111194.92664455874**2)
        assert output == expected

    def test_units(_):
        a = Transform(1, 1, 0, 0, 4326)
        output = a.pixel_diagonal(units="kilometers")
        expected = sqrt(2 * 111194.92664455874**2) / 1000
        assert output == expected


#####
# units per m
#####


class TestXUnitsPerM:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        assert a.x_units_per_m() is None

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.x_units_per_m() == 1

    def test_angular_default(_):
        a = Transform(1, 2, 3, 4, 4326)
        output = a.x_units_per_m()
        assert np.allclose(output, 8.993216059187306e-06)

    def test_angular_y(_):
        a = Transform(1, 2, 3, 4, 4326)
        output = a.x_units_per_m(30)
        assert np.allclose(output, 1.0384471425304483e-05)


class TestYUnitsPerM:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        assert a.y_units_per_m() is None

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.y_units_per_m() == 1

    def test_angular_default(_):
        a = Transform(1, 2, 3, 4, 4326)
        output = a.y_units_per_m()
        assert np.allclose(output, 8.993216059187306e-06)


class TestUnitsPerM:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        assert a.units_per_m() == (None, None)

    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        assert a.units_per_m() == (1, 1)

    def test_angular_default(_):
        a = Transform(1, 2, 3, 4, 4326)
        output = a.units_per_m()
        expected = (8.993216059187306e-06, 8.993216059187306e-06)
        assert np.allclose(output, expected)

    def test_angular_y(_):
        a = Transform(1, 2, 3, 4, 4326)
        output = a.units_per_m(30)
        expected = (1.0384471425304483e-05, 8.993216059187306e-06)
        assert np.allclose(output, expected)


#####
# Bounds Conversion
#####


class TestEdge:
    def test_valid(_):
        a = Transform(1, 2, 3, 4)
        assert a._edge(5, "dx", 1, 14) == 1 + 14 * 5

    def test_invalid(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        with pytest.raises(ValueError) as error:
            a._edge(2.2, "dx", 1, 14)
        assert_contains(error, "dx", "integer")

    def test_zero(_):
        a = Transform(1, 2, 3, 4)
        assert a._edge(0, "dx", 1, 14) == 1


class TestRight:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a.right(5) == 8

    def test_zero(_):
        a = Transform(1, 2, 3, 4)
        assert a.right(0) == 3


class TestBottom:
    def test(_):
        a = Transform(1, 2, 3, 4)
        assert a.bottom(6) == 16

    def test_zero(_):
        a = Transform(1, 2, 3, 4)
        assert a.bottom(0) == 4


class TestBounds:
    def test(_):
        a = Transform(1, 2, 3, 4)
        b = a.bounds(6, 5)
        assert b == BoundingBox(3, 16, 8, 4)

    def test_zero(_):
        a = Transform(1, 2, 3, 4)
        b = a.bounds(0, 0)
        assert b == BoundingBox(3, 4, 3, 4)


#####
# CRS Validation
#####


class TestValidateReprojection:
    def test(_):
        a = Transform(1, 2, 3, 4, 4326)
        output = a._validate_reprojection(26911)
        assert output == CRS(26911)

    def test_missing(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a._validate_reprojection(26911)
        assert_contains(
            error, "Cannot reproject the Transform because it does not have a CRS"
        )

    def test_none(_, assert_contains):
        a = Transform(1, 2, 3, 4, 4326)
        with pytest.raises(CRSError) as error:
            a._validate_reprojection(None)
        assert_contains(error, "The 'crs' input cannot be None")


class TestValidateUnits:
    def test_valid(_):
        a = Transform(1, 2, 3, 4, 4326)
        assert a._validate_units("meters", "") == "meters"

    def test_invalid_units(_, assert_contains):
        a = Transform(1, 2, 3, 4, 4326)
        with pytest.raises(ValueError) as error:
            a._validate_units("inches", "test")
        assert_contains(
            error,
            "units (inches) is not a recognized option. Supported options are: base, meters, metres, kilometers, kilometres, feet, miles",
        )

    def test_base_no_crs(_):
        a = Transform(1, 2, 3, 4)
        assert a._validate_units("base", "") == "base"

    def test_invalid_no_crs(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a._validate_units("meters", "test")
        assert_contains(
            error,
            "Cannot convert test to meters because the Transform does not have a CRS",
        )


#####
# Builtin Conversion
#####


class TestToList:
    def test(_):
        assert Transform(1, 2, 3, 4).tolist() == [1, 2, 3, 4, None]
        assert Transform(1, 2, 3, 4, 4326).tolist() == [1, 2, 3, 4, CRS(4326)]

    def test_no_crs(_):
        assert Transform(1, 2, 3, 4, 4326).tolist(crs=False) == [1, 2, 3, 4]


class TestToDict:
    def test(_):
        assert Transform(1, 2, 3, 4).todict() == {
            "dx": 1,
            "dy": 2,
            "left": 3,
            "top": 4,
            "crs": None,
        }
        assert Transform(1, 2, 3, 4, 4326).todict() == {
            "dx": 1,
            "dy": 2,
            "left": 3,
            "top": 4,
            "crs": CRS(4326),
        }


#####
# Reprojection / CRS operations
#####


class TestReproject:
    def test_linear(_):
        a = Transform(1, 2, 3, 4, 26911)
        b = a.reproject(26910)
        assert b.crs == CRS("NAD83 / UTM zone 10N")
        expected = Transform(
            0.997261140611954,
            1.9945226908862739,
            668187.5941248297,
            3.989045184176652,
        )
        assert b.isclose(expected)

    def test_same(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = a.reproject(4326)
        assert a == b
        assert a is not b

    def test_angular(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = a.reproject(26910)
        assert b == Transform(
            dx=-228708.41881171148,
            dy=-346679.85445676744,
            left=7643815.39840066,
            top=19241274.847857088,
            crs="NAD83 / UTM zone 10N",
        )

    def test_missing(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        with pytest.raises(MissingCRSError) as error:
            a.reproject(26911)
        assert_contains(
            error, "Cannot reproject the Transform because it does not have a CRS"
        )


class TestMatchCRS:
    def test_both_none(_):
        a = Transform(1, 2, 3, 4)
        b = a.match_crs(None)
        assert a == b

    def test_crs_none(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = a.match_crs(None)
        assert a == b

    def test_self_none(_):
        a = Transform(1, 2, 3, 4)
        b = a.match_crs(4326)
        assert a.tolist(crs=False) == b.tolist(crs=False)
        assert b.crs == 4326
        assert a.crs is None

    def test_reproject(_):
        a = Transform(1, 2, 3, 4, 26911)
        b = a.reproject(26910)
        assert b.crs == CRS("NAD83 / UTM zone 10N")
        expected = Transform(
            0.997261140611954,
            1.9945226908862739,
            668187.5941248297,
            3.989045184176652,
        )
        assert b.isclose(expected)


class TestRemoveCRS:
    def test_none(_):
        a = Transform(1, 2, 3, 4)
        b = a.remove_crs()
        assert a == b

    def test(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = a.remove_crs()
        assert a.crs == 4326
        assert b.crs is None


#####
# Testing
#####


class TestIsClose:
    def test_close(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = Transform(1.0000000000000000001, 2, 3, 4, 4326)
        assert a.isclose(b) == True

    def test_not_close(_):
        a = Transform(1, 2, 3, 4)
        b = Transform(2, 2, 3, 4)
        assert a.isclose(b) == False

    def test_invalid(_, assert_contains):
        a = Transform(1, 2, 3, 4)
        b = (1, 2, 3, 4)
        with pytest.raises(TypeError) as error:
            a.isclose(b)
        assert_contains(error, "Other object must also be a Transform object")

    def test_different_crs(_):
        a = Transform(1, 2, 3, 4, 4326)
        b = Transform(1, 2, 3, 4, 26911)
        assert a.isclose(b) == False

    def test_none_crs(_):
        a = Transform(1, 2, 3, 4)
        b = Transform(1, 2, 3, 4, 4326)
        assert a.isclose(b) == True
