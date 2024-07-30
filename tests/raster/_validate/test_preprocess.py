from math import inf

import numpy as np
import pytest

import pfdf.raster._validate._preprocess as validate
from pfdf.errors import DimensionError


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
