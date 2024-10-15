"""
Functions used to parse raster metadata from a feature file
----------
Functions:
    dtype       - Determines the dtype of the output raster
    nodata      - Determines the NoData value for the output raster
    resolution  - Determines the resolution of the output raster
    extent      - Determines the Transform and shape of the output raster
"""

from math import ceil
from typing import Any

import numpy as np

import pfdf.raster._validate as validate
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.raster._features.typing import Resolution, value
from pfdf.typing.core import Units, shape2d
from pfdf.utils.nodata import default as default_nodata

#####
# Data field
#####


def dtype(field: str | None, properties: dict, dtype: np.dtype | None) -> np.dtype:
    "Returns the dtype for the output raster"

    # If there's no field, the raster is always boolean
    if field is None:
        return np.dtype(bool)

    # Next prioritize user-provided dtype
    elif dtype is not None:
        return dtype

    # Otherwise, use default int or float as appropriate
    elif properties[field].startswith("int"):
        return np.dtype(int)
    else:
        return np.dtype(float)


def nodata(nodata: Any | None, casting: str, dtype: type) -> value:
    "Determines the NoData value for the output raster"

    if dtype == bool:
        return False
    elif nodata is None:
        return default_nodata(dtype)
    else:
        return validate.nodata(nodata, casting, dtype)


#####
# Spatial
#####


def resolution(
    resolution: Resolution,
    units: Units,
    crs: CRS | None,
    bounds: BoundingBox,
) -> tuple[Resolution, CRS | None]:
    "Returns resolution in axis units"

    # Transform: Reproject as needed, then extract resolution
    if isinstance(resolution, Transform):
        crs = _crs.parse(crs, resolution.crs)
        if _crs.different(crs, resolution.crs):
            y = bounds.reproject(resolution.crs).center_y
            resolution = resolution.reproject(crs, y)
        resolution = resolution.resolution()

    # Vector: Convert to base units as needed
    elif units != "base":
        xres, yres = resolution
        xres = _crs.units_to_base(crs, "x", xres, units, bounds.center_y)
        yres = _crs.units_to_base(crs, "y", yres, units)
        resolution = (xres, yres)
    return resolution, crs


def extent(
    bounds: BoundingBox, resolution: tuple[float, float]
) -> tuple[Transform, shape2d]:
    "Computes the transform and shape from the raster bounds and resolution"

    # Build the transform
    xres, yres = resolution
    transform = Transform(xres, -yres, bounds.left, bounds.top)

    # Compute the shape
    nrows = ceil(bounds.ydisp() / yres)
    ncols = ceil(bounds.xdisp() / xres)
    return transform, (nrows, ncols)
