"""
Functions for working with pyproj.CRS objects
----------
The pfdf package uses pyproj.CRS objects to represent coordinate reference systems for
raster and vector datasets. The package also allows some datasets to lack CRS
metadata. This is to support cases where a CRS can be inferred from another dataset, 
such as for a numpy array derived from a Raster object. This module contains utility
functions for working with pyproj.CRS objects and for cases where CRS metadata may
be either a pyproj.CRS object or None.
----------
IO:
    validate        - Checks an input represents a CRS
    name            - Returns a short name describing a CRS
    compatible      - True if two CRSs are equivalent or either CRS is None

Axes:
    get_axis        - Returns the X or Y axis for a CRS
    isx             - True if a CRS axis proceeds along an east-west diration
    isy             - True if a CRS axis proceeds along a north-south direction
    
Supported Units:
    supported_linear_units  - Returns a list of supported linear (projected) unit systems
    supported_angular_units - Returns a list of supported angular (geographic) unit systems
    supported_units         - Returns a list of supported unit systems

Unit Names:
    xunit           - Returns the unit system for the X-axis
    yunit           - Returns the unit system for the Y-axis
    units           - Returns the units for the X and Y axes

Unit conversions:
    base_to_units   - Converts a distance from axis base units to another unit system
    units_to_base   - Converts a distance to axis base units from another unit system

Units per meter:
    x_units_per_m   - Returns the number of X-axis base units per meter
    y_units_per_m   - Returns the number of Y-axis base units per meter
    units_per_m     - Returns the number of base units per meter for the X and Y axes

Reprojection:
    reproject       - Reprojects XY coordinates from one CRS to another
    utm_zone        - Returns the CRS of the best UTM zone for an XY coordinate

Internal Validation:
    _validate_axis      - Checks an axis exists and has a valid base unit
    _validate_axname    - Checks that an axis name is valid
    _validate_conversion- Checks that unit conversion options are valid

Internal Units:
    _supported_units    - Returns a dict of category units with non-zero conversion factors
    _unit               - Returns the name of an axis unit
    _units_per_m        - Returns the number of axis base units per meter
"""

from __future__ import annotations

import typing

import numpy as np
import pyproj.exceptions
from numpy import arcsin, arctan2, cos, sin, sqrt
from pyproj import CRS, Transformer
from pyproj._crs import Axis
from pyproj.aoi import AreaOfInterest
from pyproj.database import get_units_map, query_utm_crs_info

import pfdf._validate.core as _validate
from pfdf._utils import no_nones, real
from pfdf.errors import CRSError, MissingCRSError
from pfdf.utils import units as _units

# Type hints
if typing.TYPE_CHECKING:
    from typing import Any, Literal, Optional

    from pyproj.database import Unit

    from pfdf.typing.core import (
        XY,
        CRSlike,
        ScalarArray,
        Units,
        VectorArray,
        scalar,
        vector,
    )

    category = Literal["linear", "angular"]
    SupportedUnits = dict[str, Unit]
    AxisName = Literal["x", "dx", "left", "right", "y", "dy", "top", "bottom"]


#####
# Supported Units
#####


def _supported_units(category: category) -> SupportedUnits:
    "Returns dict of category units with non-zero conversion factors"
    units = get_units_map(category=category)
    return {key: value for key, value in units.items() if value.conv_factor != 0}


_LINEAR: SupportedUnits = _supported_units("linear")
_ANGULAR: SupportedUnits = _supported_units("angular")


def supported_linear_units() -> list[str]:
    """
    Returns a list of supported linear CRS unit systems
    ----------
    supported_linear_units()
    Returns a list of supported linear CRS unit systems. A projected CRS will typically
    use a linear unit system.
    ----------
    Outputs:
        list[str]: The names of supported linear CRS unit systems
    """
    return list(_LINEAR.keys())


def supported_angular_units() -> list[str]:
    """
    Returns a list of supported angular CRS unit systems.
    ----------
    supported_angular_units()
    Returns a list of supported angular CRS unit systems. A geographic CRS will
    typically use an angular unit system.
    ----------
    Outputs:
        list[str]: The names of supported angular CRS unit systems
    """
    return list(_ANGULAR.keys())


def supported_units() -> list[str]:
    """
    Returns a list of supported CRS unit systems
    ----------
    supported_units()
    Returns a list of supported CRS unit systems. This includes both linear and angular
    unit systems.
    ----------
    Outputs:
        list[str]: The names of supported CRS unit systems.

    """
    return supported_linear_units() + supported_angular_units()


#####
# Axes
#####


def isx(axis: Axis) -> bool:
    """
    True if a pyproj Axis proceeds along an east-west axis
    ----------
    isx(axis)
    True if an input pyproj._crs.Axis object proceeds along an east-west axis.
    ----------
    Inputs:
        axis: A pyproj._crs.Axis object

    Outputs:
        bool: True if the axis proceeds along an east-west axis. Otherwise False
    """
    _validate.type(axis, "axis", Axis, "pyproj._crs.Axis")
    return axis.direction in ["east", "west"]


def isy(axis: Axis) -> bool:
    """
    True if a pyproj Axis proceeds along a north-south axis
    ----------
    isy(axis)
    True if an input pyproj._crs.Axis object proceeds along a north-south axis.
    ----------
    Inputs:
        axis: A pyproj._crs.Axis object

    Outputs:
        bool: True if the axis proceeds along a north-south axis. Otherwise False
    """
    _validate.type(axis, "axis", Axis, "pyproj._crs.Axis")
    return axis.direction in ["north", "south"]


def get_axis(crs: CRSlike, axis: AxisName) -> Axis | None:
    """
    Returns the requested axis for a CRS
    ----------
    get_axis(crs, axis)
    Returns the requested axis for the input CRS. The "axis" input should be a string
    indicating whether to return the X or Y axis. To return the X axis, set the input
    to "x", "dx", "left", or "right". To return the Y axis, set the input to "y", "dy",
    "bottom", or "top". Returns None if the CRS does not have an axis matching the
    selection.
    ----------
    Inputs:
        crs: A CRS whose axis should be returned
        axis: A string indicating the axis that should be returned

    Outputs:
        pyproj._crs.Axis | None: The requested Axis for the CRS
    """

    # Validate
    if not isinstance(crs, CRS):
        crs = validate(crs)

    # Determine appropriate axis
    axis = _validate_axname(axis)
    if axis == "x":
        isaxis = isx
    else:
        isaxis = isy

    # Locate the first valid axis
    axes = crs.axis_info
    for axis in axes:
        if isaxis(axis):
            return axis


#####
# Validation
#####


def _validate_axis(crs: CRS, axname: XY) -> None:
    "Checks that an axis exists, and has a supported base unit"

    # Axis must exist
    axis = get_axis(crs, axname)
    if axis is None:
        raise CRSError(f'Could not locate the {axname}-axis for CRS = "{crs.name}"')

    # And must have supported base unit
    elif axis.unit_name not in supported_units():
        raise CRSError(
            f"CRS ({crs.name}) is not supported because the {axname}-axis has an "
            f"unsupported base unit ({axis.unit_name}). Supported units must "
            "be recognized by PROJ and either:\n"
            "* linear (distance) units convertible to meters, or\n"
            "* angular units convertible to radians\n"
            "See the PROJ documentation for a list of supported units: "
            "https://proj.org/en/stable/operations/conversions/unitconvert.html"
        )


def validate(crs: CRSlike | None, strict: bool = False) -> CRS | None:
    """
    Checks that an input represents a pyproj.CRS object or is None
    ----------
    validate(crs)
    Checks that the input either (1) represents a supported pyproj.CRS object or
    (2) is None. If 1, returns the input as a CRS object. Raises an error if the input
    is neither 1 nor 2.

    validate(crs, strict=True)
    Checks that an input represents a supported pyproj.CRS. Does not allow the CRS to
    be None.
    ----------
    Inputs:
        crs: An input being validated.
        strict: True to require a CRS-like input. False (default) to also allow None.

    Outputs:
        pyproj.CRS | None: The input as a pyproj.CRS or None
    """

    # Exit if None
    if crs is None:
        if strict:
            raise MissingCRSError("CRS cannot be None")
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


def _validate_axname(axis: Any) -> XY:
    "Checks that an axis name is valid"

    # Check the input is allowed
    xnames = ["x", "dx", "left", "right"]
    ynames = ["y", "dy", "bottom", "top"]
    axis = _validate.option(axis, "axis", xnames + ynames)

    # Convert to either 'x' or 'y'
    if axis in xnames:
        return "x"
    else:
        return "y"


def _validate_conversion(
    crs: Any, axis: Any, distances: Any, units: Any, y: Any
) -> tuple[CRS, XY, float, Units, float | None]:
    "Checks that unit conversion options are valid"

    # CRS and axis
    crs = validate(crs, strict=True)
    axis = _validate_axname(axis)

    # Units
    allowed = _units.supported()
    allowed.remove("base")
    units = _validate.option(units, "units", allowed)

    # Arrays
    distances = _validate.array(distances, "distances", dtype=real)
    if y is not None:
        y = _validate.array(y, "y", dtype=real)
        _validate.broadcastable(distances.shape, "distances", y.shape, "y")
    return crs, axis, distances, units, y


#####
# IO
#####


def name(crs: CRSlike | None) -> str:
    """
    Returns a short (one-line) name for a CRS
    ----------
    name(crs)
    Returns a string with a short (one-line) name describing the CRS.
    ----------
    Inputs:
        crs: A CRS-like input or None

    Outputs:
        str: A string describing the CRS
    """
    if crs is None:
        return "None"
    else:
        return validate(crs).name


def compatible(crs1: CRSlike | None, crs2: CRSlike | None) -> bool:
    """
    True if two CRS options are equivalent, or either is None
    ----------
    compatible(crs1, crs2)
    True if either (1) two inputs represent the same CRS, or (2) either input is None.
    Otherwise False.
    ----------
    Inputs:
        crs1: A first CRS-like input
        crs2: A second CRS-like input

    Outputs:
        bool: True if the two inputs represent the same CRS or either is None.
            Otherwise False
    """
    crs1 = validate(crs1)
    crs2 = validate(crs2)
    if no_nones(crs1, crs2) and crs1 != crs2:
        return False
    else:
        return True


#####
# Unit names
#####


def _unit(crs: CRS | None, axis: AxisName) -> str | None:
    "Returns the name of a CRS axis unit"
    if crs is None:
        return None
    else:
        axis = get_axis(crs, axis)
        return axis.unit_name


def xunit(crs: CRSlike | None) -> str | None:
    """
    Returns the name of the X-axis unit
    ----------
    xunit(crs)
    Returns the name of the CRS's X-axis unit or None if the CRS is None.
    ----------
    Inputs:
        crs: A pyproj.CRS or None

    Outputs:
        str | None: The name of the X-axis unit
    """
    crs = validate(crs)
    return _unit(crs, "x")


def yunit(crs: CRSlike | None) -> str | None:
    """
    Returns the name of the Y-axis unit
    ----------
    yunit(crs)
    Returns the name of the CRS's Y-axis unit or None if the CRS is None.
    ----------
    Inputs:
        crs: A pyproj.CRS or None

    Outputs:
        str | None: The name of the Y-axis unit
    """
    crs = validate(crs)
    return _unit(crs, "y")


def units(crs: CRSlike | None) -> tuple[str, str] | tuple[None, None]:
    """
    Returns the name of the X and Y-axis units
    ----------
    yunit(crs)
    Returns the names of the CRS's X and Y-axis units.
    ----------
    Inputs:
        crs: A pyproj.CRS or None

    Outputs:
        (str, str) | (None, None): The names of the X and Y axis units
    """
    crs = validate(crs)
    return _unit(crs, "x"), _unit(crs, "y")


#####
# Unit Conversions
#####

_EARTH_RADIUS_M = 6371000


def base_to_units(
    crs: CRSlike,
    axis: AxisName,
    distances: np.ndarray,
    units: Units,
    y: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Converts distances from axis base units to another unit system
    ----------
    base_to_units(crs, axis, distances, units)
    base_to_units(..., y)
    Converts distances from axis base units to another unit system.
    See pfdf.utils.units.supported for a list of supported unit systems. If
    converting units for an angular (geographic) coordinate system, converts units as if
    distances were measured at the equator. Use the "y" input to specify different
    latitudes instead. Note that y should be in axis base units.

    The "distances" input may be an array of any shape. If using the "y" input, then
    "y" should be an array that can be broadcasted against the distances. The shape of
    the output array will match this broadcasted shape.
    ----------
    Inputs:
        crs: A pyproj.CRS used to convert units
        axis: The name of the axis along which to convert units. Should be 'x' or 'y'
        distances: An array of distances in axis base units
        units: The units that the distances should be converted to
        y: The latitudes for unit conversion for angular coordinate systems.
            Should be in axis base units.

    Outputs:
        numpy array: The distances in the specified units
    """

    # Validate. Convet axis unit to standard unit
    crs, axname, distances, units, y = _validate_conversion(
        crs, axis, distances, units, y
    )
    axis = get_axis(crs, axname)
    distances = distances * axis.unit_conversion_factor

    # Convert radians to meters, using haversine when possible
    if axis.unit_name in supported_angular_units():
        if (axname == "x") and (y is not None):
            yaxis = get_axis(crs, "y")
            y = y * yaxis.unit_conversion_factor
            a = cos(y) ** 2 * sin(distances / 2) ** 2
            a[a > 1] = 1
            distances = np.sign(distances) * 2 * arctan2(sqrt(a), sqrt(1 - a))
        distances = distances * _EARTH_RADIUS_M

    # Convert from meters to requested unit
    return _units.convert(distances, "meters", units)


def units_to_base(
    crs: CRSlike,
    axis: AxisName,
    distances: np.ndarray,
    units: Units,
    y: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Converts distances to axis base units
    ----------
    units_to_base(crs, axis, distances, unit)
    units_to_base(..., y)
    Converts distances to axis base units from another unit system supported by pfdf.
    See pfdf.utils.units.supported for a list of supported unit systems. If converting
    units for an angular (geographic) coordinate system, converts units as if the
    distances were measured at the equator. Use the "y" input to specify a different
    latitudes instead. Note that y should be in axis base units.

    The "distances" input may be an array of any shape. TIf using the "y" input, then
    "y" should be an array that can be broadcasted against the distances. The shape of
    the output array will match this broadcasted shape.
    ----------
    Inputs:
        crs: A pyproj.CRS used to convert units
        axis: The name of the axis along which to convert units. Should be 'x' or 'y'
        distances: An array of distances that should be converted to axis base units
        units: The units that the distances should be converted to
        y: The latitudes for unit conversion for angular coordinate systems.
            Should be in axis base units.

    Outputs:
        numpy array: The distances in axis base units
    """

    # Validate. Convert distance to meters. Convert to float as needed
    crs, axname, distances, units, y = _validate_conversion(
        crs, axis, distances, units, y
    )
    axis = get_axis(crs, axname)
    distances = _units.convert(distances, units, "meters")

    # If angular, convert to radians. Use haversine when possible
    if axis.unit_name in supported_angular_units():
        distances = distances / _EARTH_RADIUS_M
        if (axname == "x") and (y is not None):
            yaxis = get_axis(crs, "y")
            lat = y * yaxis.unit_conversion_factor
            cosd = cos(distances)
            sinlat = sin(lat)
            y = arcsin(cosd * sinlat)
            distances = arctan2(sin(distances) * cos(lat), cosd - sinlat * sin(y))

    # Convert from standard unit (meters or degrees) to axis unit
    return distances / axis.unit_conversion_factor


#####
# Units per meter
#####


def _units_per_m(
    crs: CRSlike, axis: AxisName, y: Optional[np.ndarray] = None
) -> np.ndarray | None:
    "Determines the number of axis units per meter"
    if crs is None:
        return None
    else:
        return units_to_base(crs, axis, 1, "meters", y)


def x_units_per_m(
    crs: CRSlike | None, y: Optional[np.ndarray] = None
) -> np.ndarray | None:
    """
    Returns the number of X axis units per meter
    ----------
    x_units_per_m(crs)
    x_units_per_m(crs, y)
    Returns the number of X-axis units per meter. If the CRS uses an angular
    (geographic) coordinate system, returns the number of units per meter at the
    equator. Use the "y" input to specify different latitudes. Note that y should be
    in axis base units.
    ----------
    Inputs:
        crs: The CRS being queried
        y: Specifies the latitudes for unit conversion for angular coordinate systems.
            Should be in axis base units

    Outputs:
        numpy array: The number of axis base units per meter
    """
    return _units_per_m(crs, "x", y)


def y_units_per_m(crs: CRSlike | None) -> ScalarArray | None:
    """
    Returns the number of Y axis units per meter
    ----------
    y_units_per_m(crs)
    Returns the number of Y-axis units per meter.
    ----------
    Inputs:
        crs: The CRS being queried

    Outputs:
        scalar numpy array: The number of axis base units per meter
    """
    return _units_per_m(crs, "y")


def units_per_m(
    crs: CRSlike | None, y: Optional[np.ndarray] = None
) -> tuple[np.ndarray, ScalarArray] | tuple[None, None]:
    """
    Returns the number of X and Y-axis base units per meter
    ----------
    units_per_m(crs)
    units_per_m(crs, y)
    Returns the number of X and Y-axis base units per meter. If the CRS uses an angular
    (geographic) coordinate system, returns the number of units per meter at the
    equator. Use the "y" input to specify different latitudes. Note that y should be
    in axis base units.
    ----------
    Inputs:
        crs: The CRS being queried
        y: Specifies the latitudes for unit conversion for angular coordinate systems.
            Should be in axis base units

    Outputs:
        numpy array: The number of X-axis base units per meter
        scalar numpy array: The number of Y-axis base units per meter
    """
    x = x_units_per_m(crs, y)
    y = y_units_per_m(crs)
    return x, y


#####
# Reprojection
#####


def reproject(
    from_crs: CRSlike, to_crs: CRSlike, xs: vector, ys: vector
) -> tuple[VectorArray, VectorArray]:
    """
    Converts X and Y coordinates from one CRS to another
    ----------
    reproject(from_crs, to_crs, xs, ys)
    Reprojects X and Y coordinates from one CRS to another.
    ----------
    Inputs:
        from_crs: The CRS that the coordinates are currently in
        to_crs: The CRS that the coordinates should be projected to
        xs: The X coordinates being reprojected
        ys: The Y coordinates being reprojected

    Outputs:
        1D numpy array: The reprojected X coordinates
        1D numpy array: The reprojected Y coordinates
    """

    # Validate
    from_crs = validate(from_crs, strict=True)
    to_crs = validate(to_crs, strict=True)
    xs = _validate.vector(xs, "xs", dtype=real)
    ys = _validate.vector(ys, "ys", dtype=real, length=xs.size)

    # Reproject
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    return transformer.transform(xs, ys)


def utm_zone(crs: CRSlike, x: scalar, y: scalar) -> CRS | None:
    """
    Returns the best UTM CRS for the input coordinate
    ----------
    utm_zone(crs, x, y)
    Returns the CRS of the best UTM zone for the input coordinate, or None if the
    coordinate does not have a well-defined UTM zone.
    ----------
    Inputs:
        crs: The CRS that the coordinates are in
        x: The X coordinate
        y: The Y coordinate

    Outputs:
        pyproj.CRS | None: The CRS of the best UTM zone for the coordinate
    """

    # Validate
    crs = validate(crs, strict=True)
    x = _validate.scalar(x, "x", dtype=real)
    y = _validate.scalar(y, "y", dtype=real)

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
