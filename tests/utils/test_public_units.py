from math import isnan, nan

import numpy as np

from pfdf.utils import units


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


class TestConvert:
    def test_m_to_km(_):
        input = [2, 81, 36.33]
        output = units.convert(input, "meters", "kilometers")
        assert np.array_equal(output, [0.002, 0.081, 0.03633])

    def test_spelling(_):
        input = [2, 81, 36.33]
        output = units.convert(input, "metres", "kilometres")
        assert np.array_equal(output, [0.002, 0.081, 0.03633])

    def test_km_to_m(_):
        input = [2, 81, 36.33]
        output = units.convert(input, "kilometers", "meters")
        assert np.array_equal(output, [2000, 81000, 36330])

    def test_trivial(_):
        input = [2, 81, 36.33]
        output = units.convert(input, "meters", "meters")
        assert np.array_equal(input, output)

    def test_metric_imperial(_):
        assert units.convert(15, "meters", "feet") == 49.21259842519685
        assert units.convert(1500, "meters", "miles") == 0.932056788356001

    def test_imperial_metric(_):
        assert units.convert(100, "feet", "meters") == 30.48
        assert units.convert(2.2, "miles", "kilometers") == 3.5405568
