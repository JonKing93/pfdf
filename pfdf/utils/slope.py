"""
Functions that convert slopes to different units
----------
This module contains functions that convert between slope gradients (rise/run),
and other common slope measurements: slope percent (slope * 100), slope angle
(theta) in either radians or degrees, and sin(theta). Each slope measure has
associated "to" and "from" methods which convert to the measure from a slope
gradient, or from the measure to a slope gradient, respectively. All functions
are designed to work on numpy arrays, in addition to numeric scalars.
----------
To measure from gradient:
    to_percent: Converts gradient to the slope percent (i.e. slope * 100)
    to_radians: Converts gradient to slope angle in radians
    to_degrees: Converts gradient to slope angle in degrees
    to_sine: Converts gradient to sin(theta)

From measure to gradient:
    from_percent: Converts slope percent to gradient
    from_radians: Converts slope angle in radians to gradient
    from_degrees: Converts slope angle in degrees to gradian t
    from_sine: Convert sin(theta) to gradient
"""

import numpy as np

from pfdf.typing import RealArray

#####
# To measure
#####


def to_percent(slope: RealArray) -> RealArray:
    "Converts slope gradient (rise/run) to slope percent (slope * 100)"
    return slope * 100


def to_radians(slope: RealArray) -> RealArray:
    "Converts slope gradient (rise/run) to slope angle (theta) in radians"
    return np.arctan(slope)


def to_degrees(slope: RealArray) -> RealArray:
    "Converts slope gradient (rise/run) to slope angle (theta) in degrees"
    theta = to_radians(slope)
    return np.degrees(theta)


def to_sine(slope: RealArray) -> RealArray:
    "Converts slope gradient (rise/run) to the sine of the slope angle, sin(theta)"
    theta = to_radians(slope)
    return np.sin(theta)


#####
# From measure
#####


def from_percent(slope_percent: RealArray) -> RealArray:
    "Converts slope percent (slope * 100) to slope gradient (rise/run)"
    return slope_percent / 100


def from_radians(theta: RealArray) -> RealArray:
    "Converts slope angle (theta) in radians to slope gradient (rise/run)"
    return np.tan(theta)


def from_degrees(theta: RealArray) -> RealArray:
    "Converts slope angle (theta) in degrees to slope gradient (rise/run)"
    theta = np.radians(theta)
    return from_radians(theta)


def from_sine(sine_theta: RealArray) -> RealArray:
    "Converts sin(theta) to slope gradient (rise/run)"
    theta = np.arcsin(sine_theta)
    return from_radians(theta)
