from math import inf

import pytest

from pfdf.data.usgs.tnm import _validate

#####
# Paging
#####


class TestCount:
    def test_valid(_):
        output = _validate.count(5, "")
        assert output == 5
        assert isinstance(output, int)

    def test_negative(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.count(-2, "test name")
        assert_contains(error, "The data elements of test name must be greater than 0")

    def test_no_allow_zero(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.count(0, "test name")
        assert_contains(error, "The data elements of test name must be greater than 0")

    def test_allow_zero(_):
        output = _validate.count(0, "", allow_zero=True)
        assert output == 0

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.count("invalid", "test name")
        assert_contains(error, "The dtype of test name (<U7) is not an allowed dtype")

    def test_not_integer(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.count(2.2, "test name")
        assert_contains(error, "The data elements of test name must be integers")

    def test_too_large(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.count(10, "test name", max=5)
        assert_contains(
            error,
            "test name cannot be greater than 5, but the current value (10) is not",
        )


class TestUpperBound:
    def test_none(_):
        output = _validate.upper_bound(None, "")
        assert output == inf

    def test_valid(_):
        output = _validate.upper_bound(10, "")
        assert output == 10

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.upper_bound(0, "test name")
        assert_contains(error, "The data elements of test name must be greater than 0")


class TestMax:
    def test_1000(_):
        output = _validate.max(1000, "")
        assert output == 1000

    def test_too_large(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.max(1001, "test name")
        assert_contains(
            error,
            "test name cannot be greater than 1000, but the current value (1001) is not",
        )


class TestMaxPerQuery:
    def test_over_1000(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.max_per_query(2000)
        assert_contains(
            error,
            "max_per_query cannot be greater than 1000, but the current value (2000) is not",
        )

    def test_valid(_):
        output = _validate.max_per_query(45)
        assert output == 45

    def test_not_5(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.max_per_query(46)
        assert_contains(
            error,
            "max_per_query must be a multiple of 5, but the input value (46) is not",
        )


#####
# NHD
#####


class TestHuc:
    @pytest.mark.parametrize(
        "input, exp_type",
        (
            ("15", "huc2"),
            ("1502", "huc4"),
            ("15020006", "huc8"),
        ),
    )
    def test_valid(_, input, exp_type):
        code, out_type = _validate.huc(input)
        assert code == input
        assert out_type == exp_type

    def test_not_string(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _validate.huc(15)
        assert_contains(error, "huc must be a string")

    def test_wrong_length(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.huc("150200")
        assert_contains(
            error,
            "huc must have either 2, 4, or 8 digits, but the input huc has 6 characters instead",
        )

    def test_not_numeric(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.huc("1502abcd")
        assert_contains(
            error,
            "huc may only contain digits from 0 to 9, but the input huc includes other characters",
        )


class TestHuc48:
    @pytest.mark.parametrize(
        "input, exp_type",
        (
            ("1502", "huc4"),
            ("15020006", "huc8"),
        ),
    )
    def test_valid(_, input, exp_type):
        code, out_type = _validate.huc(input)
        assert code == input
        assert out_type == exp_type

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.huc("1502abcd")
        assert_contains(
            error,
            "huc may only contain digits from 0 to 9, but the input huc includes other characters",
        )

    def test_huc2(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.huc48("15")
        assert_contains(
            error,
            "huc must be an HU-4 or HU-8 code. This command does not support HU-2.",
        )


class TestNhdFormat:
    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.nhd_format("unsupported")
        assert_contains(
            error,
            "format (unsupported) is not a recognized option. Supported options are: shapefile, geopackage, filegdb",
        )

    @pytest.mark.parametrize(
        "input,expected",
        (
            ("SHAPEFILE", "Shapefile"),
            ("GEOPACKAGE", "GeoPackage"),
            ("FILEGDB", "FileGDB"),
        ),
    )
    def test_valid(_, input, expected):
        assert _validate.nhd_format(input) == expected
