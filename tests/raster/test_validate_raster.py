from math import inf

import numpy as np
import pytest

from pfdf.errors import DimensionError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import _validate as validate

#####
# Nodata
#####


class TestCastingOption:
    @pytest.mark.parametrize(
        "input, expected",
        (
            ("safe", "safe"),
            ("UNSAFE", "unsafe"),
            ("EqUiV", "equiv"),
        ),
    )
    def test_valid(_, input, expected):
        output = validate.casting_option(input, "test")
        assert output == expected

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.casting_option("invalid", "test name")
        assert_contains(
            error,
            "test name (invalid) is not a recognized option",
            "Supported options are: no, equiv, safe, same_kind, unsafe",
        )


class TestCasting:
    def test_bool(_):
        a = np.array(True).reshape(1)
        assert validate.casting(a, "", bool, "safe") == True

    def test_bool_as_number(_):
        a = np.array(1.00).reshape(1)
        assert validate.casting(a, "", bool, casting="safe") == True

    def test_castable(_):
        a = np.array(2.2).reshape(1)
        assert validate.casting(a, "", int, casting="unsafe") == 2

    def test_not_castable(_, assert_contains):
        a = np.array(2.2).reshape(1)
        with pytest.raises(TypeError) as error:
            validate.casting(a, "test name", int, casting="safe")
        assert_contains(error, "Cannot cast test name")


class TestNodata:
    def test_nodata(_):
        output = validate.nodata(5, "safe")
        assert output == 5

    def test_casting(_):
        output = validate.nodata(2.2, "unsafe", int)
        assert output == 2

    def test_invalid_casting_option(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.nodata(1, "invalid", bool)
        assert_contains(error, "casting")

    def test_invalid_nodata(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.nodata("invalid", "unsafe")
        assert_contains(error, "nodata")

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.nodata(2.2, "safe", int)
        assert_contains(error, "Cannot cast the NoData value")


#####
# Multiple Metadatas
#####


class TestSpatial:
    def test_none(_):
        assert validate.spatial(None, None) == (None, None)

    def test(_):
        output = validate.spatial(4326, (1, 2, 3, 4))
        assert output == (CRS(4326), Transform(1, 2, 3, 4))


class TestMetadata:
    def test_none(_):
        assert validate.metadata(None, None, None, None, None, None) == (
            None,
            None,
            None,
        )

    def test(_):
        output = validate.metadata(4326, (1, 2, 3, 4), None, 5, "safe", int)
        assert output == (CRS(4326), Transform(1, 2, 3, 4), 5)

    def test_bounds_transform(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.metadata(None, (1, 2, 3, 4), (10, 20, 30, 40), None, "safe")
        assert_contains(
            error,
            'You cannot specify both "transform" and "bounds" metadata.',
            "The two inputs are mutually exclusive.",
        )

    def test_bounds(_):
        crs, bounds, nodata = validate.metadata(
            None, None, (10, 20, 30, 40), None, "safe"
        )
        assert crs is None
        assert bounds == BoundingBox(10, 20, 30, 40)
        assert nodata is None


#####
# Preprocess
#####


class TestResampling:
    @pytest.mark.parametrize(
        "name, value",
        (
            ("nearest", 0),
            ("bilinear", 1),
            ("cubic", 2),
            ("cubic_spline", 3),
            ("lanczos", 4),
            ("average", 5),
            ("mode", 6),
            ("max", 8),
            ("min", 9),
            ("med", 10),
            ("q1", 11),
            ("q3", 12),
            ("sum", 13),
            ("rms", 14),
        ),
    )
    def test_valid(_, name, value):
        assert validate.resampling(name) == value

    def test_invalid(_):
        with pytest.raises(ValueError):
            validate.resampling("invalid")


class TestDataBound:
    @pytest.mark.parametrize(
        "dtype, edge, expected",
        (
            ("int16", "min", np.iinfo("int16").min),
            ("int16", "max", np.iinfo("int16").max),
            ("uint8", "min", np.iinfo("uint8").min),
            ("uint8", "max", np.iinfo("uint8").max),
            (bool, "min", False),
            (bool, "max", True),
            ("float32", "min", -inf),
            ("float32", "max", inf),
        ),
    )
    def test_default(_, dtype, edge, expected):
        output = validate.data_bound(None, edge, dtype)
        assert output == expected

    def test_valid(_):
        output = validate.data_bound(2.2, min, float)
        assert output == 2.2

    def test_invalid(_):
        with pytest.raises(TypeError):
            validate.data_bound("invalid", "min", float)

    def test_not_scalar(_):
        with pytest.raises(DimensionError):
            validate.data_bound([1, 2, 3], "min", float)

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.data_bound(2.2, "min", int)
        assert_contains(error, "min", "cast", "safe")
