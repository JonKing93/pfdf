from collections import namedtuple

import numpy as np
import pytest
from pyproj import CRS

from pfdf.errors import CRSError
from pfdf.projection import BoundingBox, _crs

#####
# Testing utilities
#####

Axis = namedtuple("Axis", ["unit_name", "direction"], defaults=[None, None])


class MockCRS:
    @property
    def name(_):
        return "test"


class MissingAxis(MockCRS):
    @property
    def axis_info(_):
        return []


class UnsupportedAxis(MockCRS):
    @property
    def axis_info(_):
        return [Axis(unit_name="invalid", direction="east")]


def check_axes(ax1, ax2):
    for field in [
        "name",
        "abbrev",
        "direction",
        "unit_auth_code",
        "unit_code",
        "unit_name",
    ]:
        assert getattr(ax1, field) == getattr(ax2, field)


#####
# Units
#####


@pytest.mark.parametrize(
    "unit,tf",
    (
        ("metre", True),
        ("US survey inch", True),
        ("foot", True),
        ("degree", False),
        ("unknown", False),
    ),
)
def test_islinear(unit, tf):
    assert _crs.islinear(unit) == tf


@pytest.mark.parametrize(
    "unit,tf", (("metre", False), ("degree", True), ("grad", True), ("unknown", False))
)
def test_isangular(unit, tf):
    assert _crs.isangular(unit) == tf


@pytest.mark.parametrize(
    "unit,tf", (("metre", True), ("degree", True), ("unknown", False))
)
def test_issupported(unit, tf):
    assert _crs.issupported(unit) == tf


#####
# Axes
#####


class TestName:
    @pytest.mark.parametrize(
        "crs,name", ((4326, "WGS 84"), (26911, "NAD83 / UTM zone 11N"), (None, "None"))
    )
    def test(_, crs, name):
        a = _crs.validate(crs)
        assert _crs.name(a) == name


class TestIsX:
    @pytest.mark.parametrize(
        "direction,tf",
        (("north", False), ("south", False), ("east", True), ("west", True)),
    )
    def test(_, direction, tf):
        ax = Axis(direction=direction)
        assert _crs.isx(ax) == tf


class TestIsY:
    @pytest.mark.parametrize(
        "direction,tf",
        (("north", True), ("south", True), ("east", False), ("west", False)),
    )
    def test(_, direction, tf):
        ax = Axis(direction=direction)
        assert _crs.isy(ax) == tf


class TestGetAxis:
    @pytest.mark.parametrize("name", ("x", "dx", "left", "right"))
    def test_x(_, name):
        ax = _crs.get_axis(CRS(4326), name)
        check_axes(ax, CRS(4326).axis_info[1])

    @pytest.mark.parametrize("name", ("y", "dy", "top", "bottom"))
    def test_y(_, name):
        ax = _crs.get_axis(CRS(4326), name)
        check_axes(ax, CRS(4326).axis_info[0])


#####
# Validation
#####


class TestValidate:
    def test_none(_):
        a = _crs.validate(None)
        assert a is None

    @pytest.mark.parametrize("input", (26911, "WGS 84", CRS(4326)))
    def test_valid(_, input):
        a = _crs.validate(input)
        assert isinstance(a, CRS)
        assert a == CRS(input)

    def test_invalid(_, assert_contains):
        with pytest.raises(CRSError) as error:
            _crs.validate("invalid")
        assert_contains(
            error,
            "Unsupported CRS. A valid CRS must be convertible to a pyproj.CRS object via the standard API",
        )


class TestValidateAxis:
    def test_valid(_):
        _crs._validate_axis(CRS(4326), "x")

    def test_none(_, assert_contains):
        with pytest.raises(CRSError) as error:
            _crs._validate_axis(MissingAxis(), "x")
        assert_contains(error, "Could not locate the x-axis")

    def test_unsupported(_, assert_contains):
        with pytest.raises(CRSError) as error:
            _crs._validate_axis(UnsupportedAxis(), "x")
        assert_contains(error, "the x-axis has an unsupported base unit")


#####
# Unit Conversion
#####


class TestDyToMeters:
    def test_linear(_):
        crs = CRS(26911)
        assert _crs.dy_to_meters(crs, 1) == 1
        assert _crs.dy_to_meters(crs, -1) == -1

    def test_angular(_):
        crs = CRS(4326)
        assert _crs.dy_to_meters(crs, 1) == 111194.92664455874
        assert _crs.dy_to_meters(crs, -1) == -111194.92664455874


class TestDxToMeters:
    def test_linear(_):
        crs = CRS(26911)
        assert _crs.dx_to_meters(crs, 1, None) == 1
        assert _crs.dx_to_meters(crs, -1, None) == -1

    def test_angular_default(_):
        crs = CRS(4326)
        assert _crs.dx_to_meters(crs, 1, None) == 111194.92664455874
        assert _crs.dx_to_meters(crs, -1, None) == -111194.92664455874

    @pytest.mark.parametrize(
        "lat, dx",
        (
            (0, 111194.92664455874),
            (30, 96297.32567761187),
            (45, 78626.18767687454),
            (60, 55596.934071140866),
            (89, 1940.5944300618733),
            (90, 0),
        ),
    )
    def test_angular_haversine(_, lat, dx):
        crs = CRS(4326)
        for sign in [1, -1]:
            for latsign in [1, -1]:
                output = _crs.dx_to_meters(crs, sign, latsign * lat)
                assert np.allclose(output, sign * dx)


class TestDyFromMeters:
    def test_linear(_):
        crs = CRS(26911)
        assert _crs.dy_from_meters(crs, 1) == 1
        assert _crs.dy_from_meters(crs, -1) == -1

    def test_angular(_):
        crs = CRS(4326)
        assert _crs.dy_from_meters(crs, 111194.92664455874) == 1
        assert _crs.dy_from_meters(crs, -111194.92664455874) == -1


class TestDxFromMeters:
    def test_linear(_):
        crs = CRS(26911)
        assert _crs.dx_from_meters(crs, 1, None) == 1
        assert _crs.dx_from_meters(crs, -1, None) == -1

    def test_angular_default(_):
        crs = CRS(4326)
        assert _crs.dx_from_meters(crs, 111194.92664455874, None) == 1
        assert _crs.dx_from_meters(crs, -111194.92664455874, None) == -1

    @pytest.mark.parametrize(
        "lat, dx",
        (
            (0, 111194.92664455874),
            (30, 96297.32567761187),
            (45, 78626.18767687454),
            (60, 55596.934071140866),
        ),
    )
    def test_angular_haversine(_, lat, dx):
        crs = CRS(4326)
        for sign in [1, -1]:
            for latsign in [1, -1]:
                output = _crs.dx_from_meters(crs, sign * dx, latsign * lat)
                print(output)
                assert np.allclose(output, sign, atol=1e-4)


class TestBuffersFromMeters:
    def test(_):
        obj = BoundingBox(0, 0, 0, 0, 4326)
        edges = ["left", "bottom", "right", "top"]
        b = 111194.92664455874
        buffers = {name: b for name in edges}
        output = _crs.buffers_from_meters(obj, buffers)
        assert output == {name: 1 for name in edges}


#####
# Misc
#####


class TestReproject:
    def test(_):
        xs, ys = _crs.reproject(CRS(26911), CRS(4326), (0, 10, 200), (0, 10, 200))
        assert np.allclose(
            xs, (-121.48874388438703, -121.48865429442026, -121.48695208505038)
        )
        assert np.allclose(ys, (0.0, 9.019376924314101e-05, 0.001803879619663406))


class TestUtmZone:
    def test(_):
        assert _crs.utm_zone(CRS(4326), -121, 35) == CRS(32610)

    def test_outside_domain(_):
        assert _crs.utm_zone(CRS(4326), -121, 86) is None


class TestDifferent:
    def test(_):
        assert _crs.different(None, None) == False
        assert _crs.different(None, 1) == False
        assert _crs.different(1, None) == False
        assert _crs.different(1, 2) == True


class TestParse:
    def test(_):
        assert _crs.parse(None, None) is None
        assert _crs.parse(26911, 4326) == CRS(26911)
        assert _crs.parse(None, 4326) == CRS(4326)
        assert _crs.parse(26911, None) == CRS(26911)
