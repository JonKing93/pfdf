from math import inf

import numpy as np
import pytest

from pfdf.data.landfire import _validate
from pfdf.errors import DimensionError


class TestLayer:
    def test_valid(_):
        output = _validate.layer("240EVT")
        assert output == "240EVT"

    def test_multiple(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.layer("240EVT;230EVT")
        assert_contains(error, "layer cannot contain semicolons")


class TestJobTime:
    def test_valid(_):
        input = np.array(15)
        output = _validate.job_time(input, "")
        assert output == 15
        assert isinstance(output, float)

    def test_invalid(_, assert_contains):
        with pytest.raises(DimensionError) as error:
            _validate.job_time([1, 2, 3], "test name")
        assert_contains(error, "test name must have exactly 1 element")

    def test_too_small(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.job_time(10, "test name")
        assert_contains(error, "test name must be greater than or equal to 15")


class TestMaxJobTime:
    def test_none(_):
        output = _validate.max_job_time(None)
        assert output == inf

    def test_valid(_):
        input = np.array(15).reshape(1)
        output = _validate.max_job_time(input)
        assert isinstance(output, float)
        assert output == 15

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.max_job_time(10)
        assert_contains(error, "max_job_time must be greater than or equal to 15")


class TestRefreshRate:
    def test_valid(_):
        input = np.array(15).reshape(1)
        output = _validate.refresh_rate(input)
        assert isinstance(output, float)
        assert output == 15

    def test_too_large(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.refresh_rate(3601)
        assert_contains(
            error, "refresh_rate cannot be greater than 3600 seconds (1 hour)"
        )

    def test_too_small(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.refresh_rate(10)
        assert_contains(error, "refresh_rate must be greater than or equal to 15")
