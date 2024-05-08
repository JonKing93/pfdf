"""
Functions that validate vector feature coordinate arrays
----------
Functions:
    point       - Checks a point coordinate array is valid
    polygon     - Checks a polygon coordinate array is valid
    field       - Checks that field and fill are valid
"""

from typing import Any

import numpy as np
from shapely import Point, Polygon

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import PointError, PolygonError

# Type hints
coordinates = list[tuple[float, float]]
geometry = dict[str, Any]
features_ = list[dict]
nodata = float | bool
fill = float | bool


def point(f: int, p: int, point: tuple[float, float]) -> Point:
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


def field(properties: dict, field: Any, fill: Any) -> tuple[type, nodata, fill]:
    "Checks that field and fill can be used to build raster"

    # If there's no field, return settings for boolean raster
    if field is None:
        return bool, False, False

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
    if not typestr.startswith(("int", "float")):
        typestr = typestr.split(":")[0]
        raise TypeError(
            f"The '{field}' field must be an int or float, but it has "
            f"a '{typestr}' type instead."
        )

    # Validate fill value and return data raster settings
    if fill is None:
        fill = np.nan
    else:
        fill = validate.scalar(fill, "fill", dtype=real)
        fill = float(fill)
    return float, np.nan, fill
