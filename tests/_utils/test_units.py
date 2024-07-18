from math import isnan, nan

import pytest

from pfdf._utils import units


class TestUnitsPerMeters:
    def test(_):
        output = units.units_per_meter()
        expected = {
            "base": nan,
            "meters": 1,
            "metres": 1,
            "kilometers": 0.001,
            "kilometres": 0.001,
            "feet": 100 / 2.54 / 12,
            "miles": 100 / 2.54 / 12 / 5280,
        }
        assert "base" in output
        assert isnan(output["base"])
        del output["base"]
        del expected["base"]
        assert output == expected


class TestSupported:
    def test(_):
        assert units.supported() == [
            "base",
            "meters",
            "metres",
            "kilometers",
            "kilometres",
            "feet",
            "miles",
        ]


class TestStandardize:
    @pytest.mark.parametrize(
        "input,expected",
        (
            ("base", "base"),
            ("meters", "meters"),
            ("metres", "meters"),
            ("kilometers", "kilometers"),
            ("kilometres", "kilometers"),
            ("feet", "feet"),
            ("miles", "miles"),
        ),
    )
    def test(_, input, expected):
        assert units.standardize(input) == expected
