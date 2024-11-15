from math import nan

import numpy as np
import pytest
from pyproj._crs import Axis

from pfdf.errors import CRSError, DimensionError, MissingCRSError
from pfdf.projection import CRS, crs

#####
# Testing Fixtures
#####


class MissingAxisCRS(CRS):
    @property
    def axis_info(_):
        return []


class UnsupportedAxis(Axis):
    @property
    def unit_name(self):
        return "invalid"

    @property
    def direction(self):
        return "east"


class UnsupportedAxisCRS(CRS):
    @property
    def axis_info(_):
        return [UnsupportedAxis()]


#####
# Supported Units
#####


class TestSupportedLinearUnits:
    def test(_):
        units = crs.supported_linear_units()
        assert "metre" in units
        assert "US survey inch" in units
        assert "foot" in units
        assert "degree" not in units
        assert "radian" not in units
        assert "grad" not in units
        assert "unknown" not in units


class TestSupportedAngularUnits:
    def test(_):
        units = crs.supported_angular_units()
        assert "metre" not in units
        assert "US survey inch" not in units
        assert "foot" not in units
        assert "degree" in units
        assert "radian" in units
        assert "grad" in units
        assert "unknown" not in units


class TestSupportedUnits:
    def test(_):
        units = crs.supported_units()
        assert "metre" in units
        assert "US survey inch" in units
        assert "foot" in units
        assert "degree" in units
        assert "radian" in units
        assert "grad" in units
        assert "unknown" not in units


#####
# Axes
#####


class TestIsX:
    def test(_):
        y, x = CRS(4326).axis_info
        assert crs.isx(x) == True
        assert crs.isx(y) == False


class TestIsY:
    def test(_):
        y, x = CRS(4326).axis_info
        assert crs.isy(x) == False
        assert crs.isy(y) == True


class TestGetAxis:
    @staticmethod
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

    @pytest.mark.parametrize("name", ("x", "dx", "left", "right"))
    def test_x(self, name):
        ax = crs.get_axis(4326, name)
        self.check_axes(ax, CRS(4326).axis_info[1])

    @pytest.mark.parametrize("name", ("y", "dy", "top", "bottom"))
    def test_y(self, name):
        ax = crs.get_axis(4326, name)
        self.check_axes(ax, CRS(4326).axis_info[0])


#####
# Validation
#####


class TestValidateAxis:
    def test_valid(_):
        crs._validate_axis(CRS(4326), "x")

    def test_none(_, assert_contains):
        with pytest.raises(CRSError) as error:
            crs._validate_axis(MissingAxisCRS(4326), "x")
        assert_contains(error, "Could not locate the x-axis")

    def test_unsupported(_, assert_contains):
        with pytest.raises(CRSError) as error:
            crs._validate_axis(UnsupportedAxisCRS(4326), "x")
        assert_contains(error, "the x-axis has an unsupported base unit")


class TestValidate:
    def test_none(_):
        a = crs.validate(None)
        assert a is None

    def test_strict_none(_, assert_contains):
        with pytest.raises(MissingCRSError) as error:
            crs.validate(None, strict=True)
        assert_contains(error, "CRS cannot be None")

    @pytest.mark.parametrize("input", (26911, "WGS 84", CRS(4326)))
    def test_valid(_, input):
        a = crs.validate(input)
        assert isinstance(a, CRS)
        assert a == CRS(input)

    def test_invalid(_, assert_contains):
        with pytest.raises(CRSError) as error:
            crs.validate("invalid")
        assert_contains(
            error,
            "Unsupported CRS. A valid CRS must be convertible to a pyproj.CRS object "
            "via the standard API",
        )


class TestValidateAxName:
    @pytest.mark.parametrize("name", ("x", "DX", "LeFt", "right"))
    def test_x(_, name):
        output = crs._validate_axname(name)
        assert output == "x"

    @pytest.mark.parametrize("name", ("y", "DY", "ToP", "bottom"))
    def test_y(_, name):
        output = crs._validate_axname(name)
        assert output == "y"

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            crs._validate_axname("invalid")
        assert_contains(error, "axis (invalid) is not a recognized option")


class TestValidateConversion:
    def test_valid(_):
        outcrs, axis, length, units, y = crs._validate_conversion(
            4326, "dx", 5, "meters", 35
        )
        assert outcrs == CRS(4326)
        assert axis == "x"
        assert length == 5
        assert units == "meters"
        assert y == 35

    def test_no_y(_):
        outcrs, axis, length, units, y = crs._validate_conversion(
            4326, "dx", 5.0, "meters", None
        )
        assert outcrs == CRS(4326)
        assert axis == "x"
        assert length == 5
        assert units == "meters"
        assert y is None

    def test_broadcastable(_):
        distances = np.array([1, 2, 3, 4]).reshape(1, 4)
        y = np.array([0, 30, 45, 60]).reshape(4, 1)
        outcrs, axis, length, units, outy = crs._validate_conversion(
            4326, "dx", distances, "meters", y
        )
        assert outcrs == CRS(4326)
        assert axis == "x"
        assert np.array_equal(length, distances)
        assert units == "meters"
        assert np.array_equal(y, outy)

    def test_not_broadcastable(_, assert_contains):
        distances = np.array([1, 2, 3, 4, 5]).reshape(5)
        y = np.array([0, 30, 45, 60]).reshape(4)
        with pytest.raises(ValueError) as error:
            crs._validate_conversion(4326, "dx", distances, "meters", y)
        assert_contains(error, "cannot be broadcasted")

    def test_None_crs(_, assert_contains):
        with pytest.raises(MissingCRSError) as error:
            crs._validate_conversion(None, "x", 1, "meters", 1)
        assert_contains(error, "CRS cannot be None")

    def test_invalid_crs(_, assert_contains):
        with pytest.raises(CRSError) as error:
            crs._validate_conversion("invalid", "x", 1, "meters", 1)
        assert_contains(error, "Unsupported CRS")

    def test_invalid_axname(_, assert_contains):
        with pytest.raises(ValueError) as error:
            crs._validate_conversion(4326, "invalid", 1, "meters", 1)
        assert_contains(error, "axis (invalid) is not a recognized option")

    def test_base_units(_, assert_contains):
        with pytest.raises(ValueError) as error:
            crs._validate_conversion(4326, "x", 1, "base", 1)
        assert_contains(error, "units (base) is not a recognized option")

    def test_invalid_units(_, assert_contains):
        with pytest.raises(ValueError) as error:
            crs._validate_conversion(4326, "x", 1, "invalid", 1)
        assert_contains(error, "units (invalid) is not a recognized option")


#####
# IO
#####


class TestName:
    @pytest.mark.parametrize(
        "input,name",
        ((4326, "WGS 84"), (26911, "NAD83 / UTM zone 11N"), (None, "None")),
    )
    def test(_, input, name):
        assert crs.name(input) == name

    def test_invalid(_, assert_contains):
        with pytest.raises(CRSError) as error:
            crs.name("invalid")
        assert_contains(error, "Unsupported CRS")


class TestCompatible:
    def test(_):
        assert crs.compatible(None, None) == True
        assert crs.compatible(None, 4326) == True
        assert crs.compatible(4326, None) == True
        assert crs.compatible(4326, "WGS 84") == True
        assert crs.compatible(4326, 26911) == False


#####
# Unit Name
#####


class TestXunit:
    def test(_):
        assert crs.xunit(None) is None
        assert crs.xunit(26911) == "metre"
        assert crs.xunit(4326) == "degree"


class TestYunit:
    def test(_):
        assert crs.yunit(None) is None
        assert crs.yunit(26911) == "metre"
        assert crs.yunit(4326) == "degree"


class TestUnits:
    def test(_):
        assert crs.units(None) == (None, None)
        assert crs.units(26911) == ("metre", "metre")
        assert crs.units(4326) == ("degree", "degree")


#####
# Unit Conversions
#####


class TestBaseToUnits:
    @pytest.mark.parametrize("y", (None, nan))
    @pytest.mark.parametrize("axis", ("x", "y"))
    def test_linear(_, axis, y):
        assert crs.base_to_units(26911, axis, 1, "meters", y) == 1
        assert crs.base_to_units(26911, axis, -1, "kilometers", y) == -0.001

    def test_angular_x_default(_):
        output = crs.base_to_units(4326, "x", 1, "meters", None)
        assert np.allclose(output, 111194.92664455874)
        output = crs.base_to_units(4326, "x", -1, "kilometres", None)
        assert np.allclose(output, -111.19492664455874)

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
    def test_angular_x_haversine(_, lat, dx):
        for sign in [1, -1]:
            for latsign in [1, -1]:
                output = crs.base_to_units(4326, "x", sign, "meters", latsign * lat)
                assert np.allclose(output, sign * dx)

    def test_angular_y(_):
        assert crs.base_to_units(4326, "y", 1, "meters") == 111194.92664455874
        output = crs.base_to_units(4326, "y", -1, "kilometers")
        assert np.allclose(output, -111.19492664455874)

    def test_angular_yy(_):
        assert crs.base_to_units(4326, "y", 1, "meters", nan) == 111194.92664455874
        output = crs.base_to_units(4326, "y", -1, "kilometers", nan)
        assert np.allclose(output, -111.19492664455874)

    def test_array(_):
        distances = [1, 2, 3, 4]
        output = crs.base_to_units(4326, "x", distances, "meters")
        expected = [111194.92664456 * k for k in distances]
        assert np.allclose(output, expected)

    def test_array_scalar_y(_):
        distances = [1, 2, 3, 4]
        output = crs.base_to_units(4326, "x", distances, "meters", y=30)
        expected = [96297.32567761, 192592.81778351, 288884.64194295, 385170.96217451]
        assert np.allclose(output, expected)

    def test_array_vector_y(_):
        distances = [1, 2, 3, 4]
        y = [0, 30, 45, 60]
        output = crs.base_to_units(4326, "x", distances, "meters", y)
        expected = [111194.92664456, 192592.81778351, 235866.58590534, 222355.97879842]
        assert np.allclose(output, expected)

    def test_broadcast(_):
        distances = np.array([1, 2, 3, 4]).reshape(4, 1)
        y = np.array([0, 30, 45, 60]).reshape(1, 4)
        output = crs.base_to_units(4326, "x", distances, "meters", y)
        expected = np.array(
            [
                [111194.92664456, 96297.32567761, 78626.18767687, 55596.93407114],
                [222389.85328912, 192592.81778351, 157249.38127194, 111190.692575],
                [333584.77993368, 288884.64194295, 235866.58590534, 166778.09964205],
                [444779.70657823, 385170.96217451, 314474.80510087, 222355.97879842],
            ]
        )
        assert np.allclose(output, expected)


class TestUnitsToBase:
    @pytest.mark.parametrize("y", (None, nan))
    @pytest.mark.parametrize("axis", ("x", "y"))
    def test_linear(_, axis, y):
        assert crs.units_to_base(26911, axis, 1, "meters", y) == 1
        assert crs.units_to_base(26911, axis, -1, "kilometers", y) == -1000

    def test_angular_x_default(_):
        assert crs.units_to_base(4326, "x", 111194.92664455874, "meters", None) == 1
        output = crs.units_to_base(4326, "x", -111194.92664455874, "kilometers", None)
        assert np.allclose(output, -1000)

    @pytest.mark.parametrize(
        "lat, dx",
        (
            (0, 111194.92664455874),
            (30, 96297.32567761187),
            (45, 78626.18767687454),
            (60, 55596.934071140866),
        ),
    )
    def test_angular_x_haversine(_, lat, dx):
        for sign in [1, -1]:
            for latsign in [1, -1]:
                output = crs.units_to_base(
                    4326, "x", sign * dx, "meters", latsign * lat
                )
                assert np.allclose(output, sign, atol=1e-4)

    def test_angular_y(_):
        assert crs.units_to_base(4326, "y", 111194.92664455874, "meters") == 1
        output = crs.units_to_base(4326, "y", -111194.92664455874, "kilometers")
        assert np.allclose(output, -1000)

    def test_angular_yy(_):
        assert crs.units_to_base(4326, "y", 111194.92664455874, "meters", nan) == 1
        output = crs.units_to_base(4326, "y", -111194.92664455874, "kilometers", nan)
        assert np.allclose(output, -1000)

    def test_array(_):
        distances = [111194.92664456 * k for k in [1, 2, 3, 4]]
        output = crs.units_to_base(4326, "x", distances, "meters")
        expected = [1, 2, 3, 4]
        assert np.allclose(output, expected)

    def test_array_scalar_y(_):
        distances = [96297.32567761, 192592.81778351, 288884.64194295, 385170.96217451]
        output = crs.units_to_base(4326, "x", distances, "meters", y=30)
        expected = [0.99997144, 1.99977162, 2.99922954, 3.99817484]
        assert np.allclose(output, expected)

    def test_array_vector_y(_):
        distances = [111194.92664456, 192592.81778351, 235866.58590534, 222355.97879842]
        y = [0, 30, 45, 60]
        output = crs.units_to_base(4326, "x", distances, "meters", y)
        expected = [1.0, 1.99977162, 2.99845959, 3.9945309]
        assert np.allclose(output, expected)

    def test_broadcast(_):
        distances = np.array(
            [96297.32567761, 192592.81778351, 288884.64194295, 385170.96217451]
        ).reshape(4, 1)
        y = np.array([0, 30, 45, 60]).reshape(1, 4)
        output = crs.units_to_base(4326, "x", distances, "meters", y)
        expected = np.array(
            [
                [0.86602266, 0.99997144, 1.22464773, 1.73164979],
                [1.73202882, 1.99977162, 2.44871307, 3.46089786],
                [2.598002, 2.99922954, 3.67161573, 5.18536448],
                [3.46392568, 3.99817484, 4.89277972, 6.90271332],
            ]
        )
        assert np.allclose(output, expected)


class TestUnitsPerM:
    def test_none(_):
        assert crs.units_per_m(None, None) == (None, None)

    def test_linear(_):
        assert crs.units_per_m(26911, None) == (1, 1)

    def test_angular_default(_):
        output = crs.units_per_m(4326, None)
        expected = (8.993216059187306e-06, 8.993216059187306e-06)
        assert np.allclose(output, expected)

    def test_angular_y(_):
        output = crs.units_per_m(4326, 30)
        assert len(output) == 2
        assert np.allclose(output[0], 1.0384471425304483e-05)
        assert np.allclose(output[1], 8.993216059187306e-06)

    def test_array_y(_):
        output = crs.units_per_m(4326, (0, 30, 45, 60))
        xs = np.array([8.99321606e-06, 1.03844714e-05, 1.27183281e-05, 1.79864321e-05])
        y = 8.993216059187306e-06
        assert len(output) == 2
        assert np.allclose(output[0], xs)
        assert np.allclose(output[1], y)


#####
# Reprojection
#####


class TestReproject:
    def test(_):
        xs, ys = crs.reproject(CRS(26911), CRS(4326), (0, 10, 200), (0, 10, 200))
        assert np.allclose(
            xs, (-121.48874388438703, -121.48865429442026, -121.48695208505038)
        )
        assert np.allclose(ys, (0.0, 9.019376924314101e-05, 0.001803879619663406))


class TestUtmZone:
    def test(_):
        assert crs.utm_zone(CRS(4326), -121, 35) == CRS(32610)

    def test_outside_domain(_):
        assert crs.utm_zone(CRS(4326), -121, 86) is None
