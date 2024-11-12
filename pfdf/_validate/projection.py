"""
Functions that validate raster projection metadata
----------
Note that this module relies on the raster subpackage, so cannot be used for modules
in the raster subpackage's dependencies. In particular, this module cannot be used by
the projection subpackage.
----------
Functions:
    _name       - Returns an identifying name for a Raster or RasterMetadata input
    crs         - Checks input represents a pyproj.CRS
    bounds      - Checks input represents a BoundingBox object
    transform   - Checks input represents a Transform object
"""

from __future__ import annotations

import typing

from affine import Affine

from pfdf import raster
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.projection import crs as _crs

if typing.TYPE_CHECKING:
    from typing import Any

    from pfdf.raster import Raster, RasterMetadata


def _name(input: Raster | RasterMetadata) -> str:
    "Returns an identifying name for a Raster or RasterMetadata input"
    name = input.name
    if isinstance(input, raster.RasterMetadata):
        name = f"{name} metadata"
    return name


def crs(crs: Any) -> CRS:
    "Checks that CRS is convertible to a pyproj.CRS"

    # Just exit if already a CRS
    if isinstance(crs, CRS):
        return crs

    # Extract from Raster or RasterMetadata
    elif isinstance(crs, (raster.Raster, raster.RasterMetadata)):
        if crs.crs is None:
            raise MissingCRSError(
                f"Cannot use {_name(crs)} to specify a CRS "
                "because it does not have a CRS."
            )
        return crs.crs

    # Validate anything else
    else:
        return _crs.validate(crs)


def bounds(bounds: Any) -> BoundingBox:
    "Checks that bounds represent a BoundingBox object"

    # Already a BoundingBox
    if isinstance(bounds, BoundingBox):
        return bounds.copy()

    # Extract from Raster or RasterMetadata
    elif isinstance(bounds, (raster.Raster, raster.RasterMetadata)):
        if bounds.bounds is None:
            raise MissingTransformError(
                f"Cannot use {_name(bounds)} to specify bounds because it does not "
                "have an affine Transform."
            )
        return bounds.bounds

    # Factories
    elif isinstance(bounds, dict):
        return BoundingBox.from_dict(bounds)
    elif isinstance(bounds, (list, tuple)):
        return BoundingBox.from_list(bounds)

    # Error for anything else
    else:
        raise TypeError(
            "bounds must be a BoundingBox, Raster, RasterMetadata, "
            "dict, list, or tuple."
        )


def transform(transform: Any) -> Transform:
    "Checks that input represents a Transform object"

    # Already a Transform
    if isinstance(transform, Transform):
        return transform.copy()

    # Extract from Raster
    elif isinstance(transform, (raster.Raster, raster.RasterMetadata)):
        if transform.transform is None:
            raise MissingTransformError(
                f"Cannot use {_name(transform)} to specify an affine Transform because "
                "it does not have an affine Transform."
            )
        return transform.transform

    # Transform factories
    elif isinstance(transform, Affine):
        return Transform.from_affine(transform)
    elif isinstance(transform, dict):
        return Transform.from_dict(transform)
    elif isinstance(transform, (list, tuple)):
        return Transform.from_list(transform)

    # Error if anything else
    else:
        raise TypeError(
            "transform must be a Transform, Raster, RasterMetadata, "
            "dict, list, tuple, or affine.Affine."
        )
