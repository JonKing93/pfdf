"""
Utility class for working with pyproj.CRS objects
----------
This module holds utility functions for working with pyproj.CRS objects, which
are used for all internal representations of CRSs. In particular, this module
provides the utilties needed to implement the Transform and BoundingBox classes. 
Note that the "name" and "validate" functions permit a CRS that is None, but most
other functions should be guarded by a "if crs is not None" statement.
----------
Constants:
    EARTH_RADIUS_M  - Radius of the earth in meters
    LINEAR          - Supported linear units
    ANGULAR         - Supported angular units

Units:
    _supported_units    - Returns a dict of category units with non-zero conversion factors
    islinear        - True if unit is a supported linear unit
    isangular       - True if unit is a supported angular unit
    issupported     - True if unit is supported for unit conversions

Axis / low level:
    name            - Either the CRS name or "None", as appropriate
    isx             - True if an axis is an X axis
    isy             - True if an axis is a Y axis
    get_axis        - Returns the requested axis

Validation:
    validate        - Checks input represents a CRS or None
    _validate_axis  - Checks an axis exists and has supported units

Unit Conversion:
    base_to_units   - Converts a length from axis base units to other units
    units_to_base   - Converts a length from units to axis base units
    buffers_to_base - Converts buffering distances to axis base units
    
Unit Names:
    _unit           - Returns the unit name for an axis
    xunit           - Returns the unit name for the X axis
    yunit           - Returns the unit name for the Y axis
    units           - Returns the unit names for the X and Y axes

Units per meter:
    _units_per_m    - Returns the number of axis units per meter
    x_units_per_m   - Returns the number of X axis units per meter
    y_units_per_m   - Returns the number of Y axis units per meter
    units_per_m     - Returns the number of (X, Y) axis units per meter

Misc:
    reproject       - Reprojects X and Y coordinates to a different projection
    utm_zone        - Returns the best UTM CRS for an input X,Y coordinate
    different       - True if two CRSs are not equal and neither is None
    parse           - Parses and validates a CRS from a base object and metadata class
"""

from math import asin, atan2, cos, sin, sqrt
from typing import Any, Literal

import numpy as np
import pyproj.exceptions
from pyproj import CRS, Transformer
from pyproj._crs import Axis
from pyproj.aoi import AreaOfInterest
from pyproj.database import Unit, get_units_map, query_utm_crs_info

from pfdf._utils import no_nones
from pfdf.errors import CRSError
from pfdf.typing import XY, Units, scalar, vector
from pfdf.utils.units import convert

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


def base_to_units(
    crs: CRS,
    axname: XY,
    length: float,
    units: Units,
    y: float | None = None,
    array: bool = False,
) -> float:
    "Converts from axis base units to other units"

    # Convert axis unit to standard unit (meters or radians)
    axis = get_axis(crs, axname)
    length = length * axis.unit_conversion_factor

    # Convert radians to meters, using haversine when possible
    if isangular(axis.unit_name):
        if (axname == "x") and (y is not None):
            yaxis = get_axis(crs, "y")
            y = y * yaxis.unit_conversion_factor
            a = cos(y) ** 2 * sin(length / 2) ** 2
            a = min(a, 1)
            length = np.sign(length) * 2 * atan2(sqrt(a), sqrt(1 - a))
        length = length * EARTH_RADIUS_M

    # Convert from meters to requested unit. Return as float if appropriate
    length = convert(length, "meters", units)
    if not array:
        length = float(length)
    return length


def units_to_base(
    crs: CRS,
    axname: XY,
    length: float,
    units: Units,
    y: float | None = None,
    array: bool = False,
) -> float:
    "Converts from units to axis base units"

    # Convert length to meters. Convert to float as needed
    axis = get_axis(crs, axname)
    length = convert(length, units, "meters")
    if not array:
        length = float(length)

    # If angular, convert to radians. Use haversine when possible
    if isangular(axis.unit_name):
        length = length / EARTH_RADIUS_M
        if (axname == "x") and (y is not None):
            yaxis = get_axis(crs, "y")
            lat = y * yaxis.unit_conversion_factor
            cosd = cos(length)
            sinlat = sin(lat)
            y = asin(cosd * sinlat)
            length = atan2(sin(length) * cos(lat), cosd - sinlat * sin(y))

    # Convert from standard unit (meters or degrees) to axis unit
    return length / axis.unit_conversion_factor


def buffers_to_base(obj, buffers: dict[str, float], units: Units) -> dict[str, float]:
    "Converts a dict of edge buffers from units to axis base units"
    _, y = obj.center
    output = {}
    for edge in buffers:
        axis = "x" if edge in ["left", "right"] else "y"
        output[edge] = units_to_base(obj.crs, axis, buffers[edge], units, y)
    return output


#####
# Unit name
#####


def _unit(crs: CRS | None, axis: axis) -> str | None:
    "Returns the name of a CRS axis unit"
    if crs is None:
        return None
    else:
        axis = get_axis(crs, axis)
        return axis.unit_name


def xunit(crs: CRS | None) -> str | None:
    "Returns the name of the X axis unit"
    return _unit(crs, "x")


def yunit(crs: CRS | None) -> str | None:
    "Returns the name of the Y axis unit"
    return _unit(crs, "y")


def units(crs: CRS | None) -> tuple[str, str] | tuple[None, None]:
    "Returns the names of the X and Y axis units"
    return xunit(crs), yunit(crs)


#####
# Units per meter
#####


def _units_per_m(crs: CRS | None, axis: XY, y: float | None = None) -> float | None:
    "Determines the number of axis units per meter"
    if crs is None:
        return None
    else:
        return units_to_base(crs, axis, 1, "meters", y)


def x_units_per_m(crs: CRS | None, y: float | None = None) -> float | None:
    "Returns the number of X axis units per meter"
    return _units_per_m(crs, "x", y)


def y_units_per_m(crs: CRS | None) -> float | None:
    "Returns the number of Y axis units per meter"
    return _units_per_m(crs, "y")


def units_per_m(
    crs: CRS | None, y: float | None = None
) -> tuple[float, float] | tuple[None, None]:
    "Returns the number of units per meter for the X and Y axes"
    x = x_units_per_m(crs, y)
    y = y_units_per_m(crs)
    return x, y


#####
# Misc
#####


def reproject(
    from_crs: CRS, to_crs: CRS, xs: vector, ys: vector
) -> tuple[vector, vector]:
    "Converts X and Y coordinates from one CRS to another"
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
