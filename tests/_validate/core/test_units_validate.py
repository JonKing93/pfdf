import pytest

import pfdf._validate.core._units as validate


class TestUnits:
    @pytest.mark.parametrize(
        "supported",
        ("base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"),
    )
    def test_valid(_, supported):
        assert validate.units(supported) == supported

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.units("inches")
        assert_contains(
            error,
            "units (inches) is not a recognized option. Supported options are: base, meters, metres, kilometers, kilometres, feet, miles",
        )

    def test_include(_):
        assert validate.units("pixels", include="pixels") == "pixels"


class TestConversion:
    def test_none(_):
        assert validate.conversion(None, "") is None

    def test_valid(_):
        assert validate.conversion(5, "") == 5

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.conversion(0, "dem_per_m")
        assert_contains(error, "dem_per_m must be greater than 0")
