import numpy as np
import pytest

from pfdf.utils import slope


@pytest.fixture
def slopes():
    return np.arange(0, 10, 0.1)


def check(output, expected):
    assert np.allclose(output, expected)


def test_to_percent(slopes):
    output = slope.to_percent(slopes)
    expected = slopes * 100
    check(output, expected)


def test_to_radians(slopes):
    output = slope.to_radians(slopes)
    expected = np.arctan(slopes)
    check(output, expected)


def test_to_degrees(slopes):
    output = slope.to_degrees(slopes)
    expected = np.degrees(np.arctan(slopes))
    check(output, expected)


def test_to_sine(slopes):
    output = slope.to_sine(slopes)
    expected = np.sin(np.arctan(slopes))
    check(output, expected)


def test_from_percent(slopes):
    input = slope.to_percent(slopes)
    output = slope.from_percent(input)
    check(output, slopes)


def test_from_radians(slopes):
    input = slope.to_radians(slopes)
    output = slope.from_radians(input)
    check(output, slopes)


def test_from_degrees(slopes):
    input = slope.to_degrees(slopes)
    output = slope.from_degrees(input)
    check(output, slopes)


def test_from_sine(slopes):
    input = slope.to_sine(slopes)
    output = slope.from_sine(input)
    check(output, slopes)
