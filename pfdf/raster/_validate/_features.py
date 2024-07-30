"""
Functions that validate inputs used to build rasters from feature files
----------
User options:
    resolution          - Checks that raster resolution represents two positive values
    field               - Checks that field can be used to build the raster
    resolution_units    - Checks that resolution units can be converted to base units

Coordinate Arrays:
    geometry            - Checks a geometry is valid and returns multi-coordinate array
    point               - Checks a point coordinate array is valid
    polygon             - Checks a polygon coordinate array is valid
"""

from pathlib import Path
from typing import Any

import numpy as np
from shapely import Point, Polygon

import pfdf._validate as validate
from pfdf import raster
from pfdf._utils import real
from pfdf.errors import (
    GeometryError,
    MissingCRSError,
    MissingTransformError,
    PointError,
    PolygonError,
    ShapeError,
)
from pfdf.projection import CRS, Transform
from pfdf.typing import Units, VectorArray

#####
# User options
#####


def resolution(resolution: Any) -> VectorArray | Transform:
    "Checks input can be used to extract resolution"

    # Extract transform from rasters
    if isinstance(resolution, raster.Raster):
        if resolution.transform is None:
            raise MissingTransformError(
                f"Cannot use {resolution.name} to specify resolution because it "
                f"does not have an affine transform."
            )
        resolution = resolution.transform

    # Transform: Return directly if has CRS. Otherwise, extract resolution
    if isinstance(resolution, Transform):
        if resolution.crs is not None:
            return resolution
        else:
            return resolution.resolution()

    # Validate anything else as a vector
    resolution = validate.vector(resolution, "resolution", dtype=real)
    if resolution.size > 2:
        raise ShapeError(
            f"resolution may have either 1 or 2 elements, but it has "
            f"{resolution.size} elements instead"
        )
    validate.finite(resolution, "resolution")
    validate.positive(resolution, "resolution")

    # Convert to list. If a single element, use for both axes
    resolution = resolution.tolist()
    if len(resolution) == 1:
        resolution = resolution * 2
    return resolution


def field(properties: dict, field: Any) -> type:
    "Checks that field can be used to build raster and returns type"

    # If there's no field, return settings for boolean raster
    if field is None:
        return bool

    # Field must be a property key...
    validate.type(field, "field", str, "str")
    if field not in properties:
        allowed = ", ".join(properties.keys())
        raise KeyError(
            f"'{field}' is not the name of a feature data field. "
            f"Allowed field names are: {allowed}"
        )

    # ...and must be int or float
    typestr = properties[field]
    if typestr.startswith("int"):
        return int
    elif typestr.startswith("float"):
        return float
    else:
        typestr = typestr.split(":")[0]
        raise TypeError(
            f"The '{field}' field must be an int or float, but it has "
            f"a '{typestr}' type instead."
        )


def resolution_units(
    units: Units,
    crs: CRS | None,
    resolution: tuple | Transform,
    geometry: str,
    path: Path,
) -> None:
    "Checks that resolution units can be converted to axis base units"
    if (crs is None) and (not isinstance(resolution, Transform)) and (units != "base"):
        raise MissingCRSError(
            f"Cannot convert resolution from {units} because the {geometry} "
            "feature file does not have a CRS.\n"
            f"File: {path}"
        )


#####
# Coordinate geometries
#####


def geometry(f: int, geometry: Any, allowed: tuple[str, str]) -> list:
    "Validates geometry and returns coordinates as a multi-coordinate array"

    # Require a geometry
    if geometry is None:
        raise GeometryError(f"Feature[{f}] does not have a geometry.")

    # Geometry must have an expected type
    type = geometry["type"]
    if type not in allowed:
        allowed = " or ".join(allowed)
        raise GeometryError(
            f"Each feature in the input file must have a {allowed} geometry. "
            f"However, feature[{f}] has a {type} geometry instead."
        )

    # Arrange single geometries as multi-coordinate arrays
    multicoordinates = geometry["coordinates"]
    if "Multi" not in type:
        multicoordinates = [multicoordinates]
    return multicoordinates


def point(f: int, p: int, point: Any) -> Point:
    "Validates a point coordinate array (f: feature index, p: index in the feature)"

    # Must be a tuple with two finite elements
    description = ""
    if not isinstance(point, tuple) and not isinstance(point, list):
        description = "is neither a list nor a tuple"
    elif len(point) != 2:
        description = f"has {len(point)} elements"
    if description != "":
        raise PointError(
            "The coordinate array for each point must be a list or tuple with "
            f"two finite elements. However in feature[{f}], the coordinate array "
            f"for point[{p}] {description}."
        )

    # Points should be int or float
    for coord, axis in zip(point, ["x", "y"]):
        if type(coord) not in [int, float]:
            raise TypeError(
                "The two elements in the coordinate array for each point must "
                f"have an int or float type. But in feature[{f}], the {axis} "
                f"coordinate for point[{p}] is neither an int nor a float."
            )

    # Must be finite
    if not np.all(np.isfinite(point)):
        raise PointError(
            f"The coordinates for each point must be finite. However in "
            f"feature[{f}], the coordinate array for point[{p}] has nan or "
            "infinite elements."
        )

    # Return the coordinate as a shapely Point
    return Point(point)


def polygon(f: int, p: int, rings: Any) -> Polygon:
    "Validates a polygon coordinate array (f: feature index, p: index in feature)"

    # Must be a list of linear rings
    if not isinstance(rings, list):
        raise PolygonError(
            "The coordinates array for each polygon must be a list of linear "
            f"ring coordinates. However in feature[{f}], the coordinates array "
            f"for polygon[{p}] is not a list."
        )

    # Validate each ring. Check each is a list of coordinates...
    for r, ring in enumerate(rings):
        if not isinstance(ring, list):
            raise PolygonError(
                f"Each element of a polygon's coordinates array must be a list "
                f"of linear ring coordinates. However in feature[{f}], "
                f"polygon[{p}].coordinates[{r}] is not a list."
            )

        # ... with at least 4 coordinates...
        elif len(ring) < 4:
            raise PolygonError(
                f"Each linear ring must have at least 4 positions. However "
                f"ring[{r}] in polygon[{p}] of feature[{f}] does not have "
                f"4 positions."
            )

        # ... and matching start/end positions...
        elif ring[0] != ring[-1]:
            raise PolygonError(
                f"The final position in each linear ring must match the first "
                f"position. However, this is not the case for ring[{r}] in "
                f"polygon[{p}] of feature[{f}]."
            )

        # ... and finite coordinates
        elif not np.all(np.isfinite(ring)):
            raise PolygonError(
                f"Each element of a polygon's coordinates array must be finite. "
                f"However in feature[{f}], polygon[{p}].coordinates[{r}] contains "
                "nan or infinite elements."
            )

    # Return as a shapely polygon
    return Polygon(rings[0], rings[1:])
