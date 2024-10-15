"""
Functions that validate raster projection metadata
----------
Note that this module relies on the Raster class, so cannot be used for modules in the
class's dependencies.
----------
Functions:
    crs         - Checks input represents a pyproj.CRS
    bounds      - Checks input represents a BoundingBox object
    transform   - Checks input represents a Transform object
"""

from typing import Any

from affine import Affine

from pfdf import raster
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform, _crs


def crs(crs: Any) -> CRS:
    "Checks that CRS is convertible to a pyproj.CRS"

    if isinstance(crs, CRS):
        return crs
    elif isinstance(crs, raster.Raster):
        if crs.crs is None:
            raise MissingCRSError(
                f"Cannot use {crs.name} to specify a CRS because it does not have a CRS."
            )
        return crs._crs
    else:
        return _crs.validate(crs)


def bounds(bounds: Any) -> BoundingBox:
    "Checks that bounds represent a BoundingBox object"

    # Already a BoundingBox
    if isinstance(bounds, BoundingBox):
        return bounds.copy()

    # Extract from Raster (error if no transform)
    elif isinstance(bounds, raster.Raster):
        if bounds.bounds is None:
            raise MissingTransformError(
                f"Cannot use {bounds.name} to specify bounds because it does not "
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
            "bounds must be a dict, list, tuple, BoundingBox, or Raster object."
        )


def transform(transform: Any) -> Transform:
    "Checks that input represents a Transform object"

    # Already a Transform
    if isinstance(transform, Transform):
        return transform.copy()

    # Extract from Raster
    elif isinstance(transform, raster.Raster):
        if transform.transform is None:
            raise MissingTransformError(
                f"Cannot use {transform.name} to specify an affine transform because "
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
            "transform must be a dict, list, tuple, affine.Affine, Transform, or Raster object."
        )
