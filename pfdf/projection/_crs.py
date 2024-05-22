"""
Utility class for working with pyproj.CRS objects
----------
This module holds utility functions for working with pyproj.CRS objects, which
are used for all internal representations of CRSs. In particular, this module
provides the utilties needed to implement the Transform and BoundingBox classes. 
Note that the "name" and "validate" functions permit a CRS that is None, but all
other functions should be guarded by a "if crs is not None" statement.
----------
Constants:
    EARTH_RADIUS_M  - Radius of the earth in meters

Axis / low level:
    isx             - True if an axis is an X axis
    isy             - True if an axis is a Y axis
    axis            - Returns the indicated axis
    name            - Either the CRS name or "None", as appropriate

Validation:
    validate        - Checks input represents a CRS or None
    _validate_axis  - Checks an axis exists and has supported units

Unit Conversion:
    dx_to_meters    - Converts a length along the x-axis from axis units to meters
    dy_to_meters    - Converts a length along the y-axis from axis units to meters
    dx_from_meters  - Converts a length along the x-axis from meters to axis units
    dy_from_meters  - Converts a length along the y-axis from meters to axis units
    buffers_from_meters - Converts buffering distances from meters to axis units

Unit Info:
    unit_info       - Returns info or None if CRS is None
    unit            - Returns the unit along an axis
    xunit           - Returns the X axis unit
    yunit           - Returns the Y axis unit
    units           - Returns the (X, Y) units
    x_units_per_m   - Returns the number of X axis units per meter
    y_units_per_m   - Returns the number of Y axis units per meter
    units_per_m     - Returns the number of (X, Y) axis units per meter

Misc:
    reproject       - Reprojects X and Y coordinates to a different projection
    utm_zone        - Returns the best UTM CRS for an input X,Y coordinate
    different       - True if two values are not equal and neither is None
    parse           - Parses and validates a CRS from a base object and metadata class
"""

from math import asin, atan2, cos, sin, sqrt
from typing import Any, Callable, Literal

import numpy as np
import pyproj.exceptions
from pyproj import CRS, Transformer
from pyproj._crs import Axis
from pyproj.aoi import AreaOfInterest
from pyproj.database import Unit, get_units_map, query_utm_crs_info

from pfdf._utils import no_nones
from pfdf.errors import CRSError
from pfdf.typing import scalar, vector

EARTH_RADIUS_M = 6371000

axis = Literal["x", "y", "dx", "dy", "left", "right", "bottom", "top"]
CRSInput = CRS | int | str | dict | Any


#####
# Units
#####


def _supported_units(category: str) -> dict[str, Unit]:
    "Returns dict of category units with non-zero conversion factors"
    units = get_units_map(category=category)
    return {key: value for key, value in units.items() if value.conv_factor != 0}


LINEAR = _supported_units("linear")
ANGULAR = _supported_units("angular")


def islinear(unit: str) -> bool:
    "True if a unit is a supported linear (distance) unit"
    return unit in LINEAR


def isangular(unit: str) -> bool:
    "True if a unit is a supported angular unit"
    return unit in ANGULAR


def issupported(unit: str) -> bool:
    "True if a unit is supported for unit conversions"
    return islinear(unit) or isangular(unit)


#####
# Axes
#####


def name(crs: CRS | None) -> str:
    "A short name for the CRS"
    if crs is None:
        return "None"
    else:
        return crs.name


def isx(axis: Axis) -> bool:
    "True if an axis proceeds along an east-west axis"
    return axis.direction in ["east", "west"]


def isy(axis: Axis) -> bool:
    "True if an axis proceeds along a north-south axis"
    return axis.direction in ["north", "south"]


def get_axis(crs: CRS, axis: axis) -> Axis | None:
    "Returns the x or y axis"

    # Determine appropriate axis
    if axis in ["x", "dx", "left", "right"]:
        isaxis = isx
    elif axis in ["y", "dy", "bottom", "top"]:
        isaxis = isy

    # Locate the first valid axis
    axes = crs.axis_info
    for axis in axes:
        if isaxis(axis):
            return axis


#####
# CRS Validation
#####


def validate(crs: Any) -> CRS | None:
    "Checks that input represents a pyproj.CRS or None"

    # Exit if None
    if crs is None:
        return crs

    # Must be convertible to a pyproj CRS
    try:
        crs = CRS(crs)
    except pyproj.exceptions.CRSError as error:
        raise CRSError(
            "Unsupported CRS. A valid CRS must be convertible to a pyproj.CRS "
            "object via the standard API. See the pyproj documentation for examples "
            "of supported CRS inputs: "
            "https://pyproj4.github.io/pyproj/stable/api/crs/crs.html#pyproj.crs.CRS.__init__"
        ) from error

    # Must have supported X and Y axes
    for axis in ["x", "y"]:
        _validate_axis(crs, axis)
    return crs


def _validate_axis(crs: CRS, axname: Literal["x", "y"]) -> None:
    "Checks that an axis exists, and has a supported base unit"

    # Axis must exist
    axis = get_axis(crs, axname)
    if axis is None:
        raise CRSError(f'Could not locate the {axname}-axis for CRS = "{crs.name}"')

    # And must have supported base unit
    elif not issupported(axis.unit_name):
        raise CRSError(
            f"CRS ({crs.name}) is not supported because the {axname}-axis has an "
            f"unsupported base unit ({axis.unit_name}). Supported units must "
            "be recognized by PROJ and either:\n"
            "* linear (distance) units convertible to meters, or\n"
            "* angular units convertible to radians\n"
            "See the PROJ documentation for a list of supported units: "
            "https://proj.org/en/stable/operations/conversions/unitconvert.html"
        )


#####
# Unit conversions
#####


def dy_to_meters(crs: CRS, dy: float) -> float:
    "Converts a distance along the Y axis from axis units to meters"

    yaxis = get_axis(crs, "y")
    dy = dy * yaxis.unit_conversion_factor
    if isangular(yaxis.unit_name):
        dy = dy * EARTH_RADIUS_M
    return dy


def dx_to_meters(crs: CRS, dx: float, y: float | None) -> float:
    """Converts a distance along the X axis from axis units to meters.
    If y is not specified, measures dx along the equator. Both dx and
    y should be in axis units"""

    # Get x axis. Convert dx to meters (linear) or radians (angular)
    xaxis = get_axis(crs, "x")
    dx = dx * xaxis.unit_conversion_factor

    # Convert angular units to meters, using haversine when possible
    if isangular(xaxis.unit_name):
        if y is not None:
            yaxis = get_axis(crs, "y")
            y = y * yaxis.unit_conversion_factor
            a = cos(y) ** 2 * sin(dx / 2) ** 2
            a = min(a, 1)
            dx = np.sign(dx) * 2 * atan2(sqrt(a), sqrt(1 - a))
        dx = dx * EARTH_RADIUS_M
    return dx


def dx_from_meters(crs: CRS, dx: float, y: float | None) -> float:
    "Converts a length along the x-axis from meters to axis units"

    # Get axis. If angular CRS, first convert meters to radians
    xaxis = get_axis(crs, "x")
    if isangular(xaxis.unit_name):
        dx = dx / EARTH_RADIUS_M

        # If possible, use inverse haversine for distance
        if y is not None:
            yaxis = get_axis(crs, "y")
            lat = y * yaxis.unit_conversion_factor
            cosd = cos(dx)
            sinlat = sin(lat)
            y = asin(cosd * sinlat)
            dx = atan2(sin(dx) * cos(lat), cosd - sinlat * sin(y))

    # Convert to axis units
    return dx / xaxis.unit_conversion_factor


def dy_from_meters(crs: CRS, dy: float) -> float:
    "Converts a length along the Y axis from meters to axis coordinates"

    yaxis = get_axis(crs, "y")
    if isangular(yaxis.unit_name):
        dy = dy / EARTH_RADIUS_M
    return dy / yaxis.unit_conversion_factor


def buffers_from_meters(obj, buffers):
    "Converts a dict of edge buffers from meters to axis units"
    _, y = obj.center
    left = dx_from_meters(obj.crs, buffers["left"], y)
    right = dx_from_meters(obj.crs, buffers["right"], y)
    top = dy_from_meters(obj.crs, buffers["top"])
    bottom = dy_from_meters(obj.crs, buffers["bottom"])
    return {"left": left, "bottom": bottom, "right": right, "top": top}


#####
# Unit Info
#####


def unit_info(crs: CRS | None, info: Callable, *args: Any) -> Any | None:
    "Returns unit information or None if CRS is None"
    if crs is None:
        return None
    else:
        return info(crs, *args)


def unit(crs: CRS, axis: axis) -> str:
    "Returns an axis unit"
    axis = get_axis(crs, axis)
    return axis.unit_name


def xunit(crs: CRS | None) -> str | None:
    "Returns the X axis unit"
    return unit_info(crs, unit, "x")


def yunit(crs: CRS | None) -> str | None:
    "Returns the Y axis unit"
    return unit_info(crs, unit, "y")


def units(crs: CRS | None) -> tuple[str, str] | None:
    "Returns the X and Y axis units"
    return xunit(crs), yunit(crs)


def x_units_per_m(crs: CRS | None, y: float | None) -> float | None:
    "Returns the number of X axis units per meter"
    return unit_info(crs, dx_from_meters, 1, y)


def y_units_per_m(crs: CRS | None) -> float | None:
    "Returns the number of Y axis units per meter"
    return unit_info(crs, dy_from_meters, 1)


def units_per_m(crs: CRS | None, y: float | None) -> tuple[float, float] | None:
    "Returns the number of CRS units per meter along the X and Y axes"
    x = x_units_per_m(crs, y)
    y = y_units_per_m(crs)
    return x, y


#####
# Misc
#####


def reproject(
    from_crs: CRS, to_crs: CRS, xs: vector, ys: vector
) -> tuple[vector, vector]:
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    return transformer.transform(xs, ys)


def utm_zone(crs: CRS, x: scalar, y: scalar) -> CRS | None:
    "Returns the best UTM CRS for the input coordinate"

    # Convert point to lon-lat
    transformer = Transformer.from_crs(crs, 4326, always_xy=True)
    lon, lat = transformer.transform(x, y)

    # Query UTM
    aoi = AreaOfInterest(lon, lat, lon, lat)
    zones = query_utm_crs_info("WGS 84", aoi)
    if len(zones) == 0:
        return None
    else:
        return CRS(zones[0].name)


def different(template: CRS, current: CRS) -> bool:
    "True if two CRSs are different and neither is None"
    return no_nones(current, template) and (current != template)


def parse(base: Any, other: Any) -> CRS | None:
    "Parses final CRS for a base object and new metadata object"

    if base is not None:
        crs = base
    else:
        crs = other
    return validate(crs)
