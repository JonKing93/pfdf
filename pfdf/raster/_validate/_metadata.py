"""
Functions that validate raster metadata inputs
----------
NoData:
    casting     - Checks that a casting rule is recognized
    nodata      - Checks that a nodata value is valid and castable

Projection:
    crs         - Checks input represents a pyproj.CRS
    bounds      - Checks input represents a BoundingBox object
    transform   - Checks input represents a Transform object

Multiple Metadatas:
    spatial     - Checks that CRS and Transform are valid
    metadata    - Checks CRS, Transform, and NoData value
"""

from typing import Any, Optional

import numpy as np
from affine import Affine

import pfdf._validate as validate
from pfdf import raster
from pfdf._utils import no_nones, real
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.typing import ScalarArray

#####
# NoData / casting
#####

CASTING_RULES = ["no", "equiv", "safe", "same_kind", "unsafe"]


def casting(value: ScalarArray, name: str, dtype: type, casting: str) -> ScalarArray:
    """
    casting  Checks that a NoData value can be casted to a raster dtype
    ----------
    casting(nodata, dtype, casting)
    Checks that the NoData value can be casted to the indicated type via the
    specified casting rule. If so, returns the casted value. Otherwise, raises
    a TypeError. Note that the NoData value should already be validated as a
    scalar array before using this function.
    ----------
    Inputs:
        nodata: The NoData value being checked
        dtype: The dtype that the NoData value should be casted to
        casting: The casting rule to use

    Outputs:
        numpy 1D array: The casted NoData value
    """

    casted = value.astype(dtype)
    if (value == casted) or np.can_cast(value, dtype, casting):
        return casted
    else:
        raise TypeError(
            f"Cannot cast {name} ({value}) to the raster dtype ({dtype}) "
            f"using '{casting}' casting."
        )


def nodata(nodata, casting_, dtype: Optional[Any] = None):
    """Checks that a NoData value is valid. If a dtype is valid, checks that the
    NoData value is castable to the dtype"""

    nodata = validate.scalar(nodata, "nodata", dtype=real)
    if dtype is not None:
        casting_ = validate.option(casting_, "casting", allowed=CASTING_RULES)
        nodata = casting(nodata, "the NoData value", dtype, casting_)
    return nodata


#####
# Projection classes
#####


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


#####
# Multiple metadatas
#####


def spatial(crs_, transform_):
    "Validates CRS and transform"
    if crs_ is not None:
        crs_ = crs(crs_)
    if transform_ is not None:
        transform_ = transform(transform_)
    return crs_, transform_


def metadata(crs_, transform_, bounds_, nodata_, casting, dtype=None):
    "Validates CRS, Transform, Bounds, and NoData"

    # Transform and bounds are mutually exclusive
    if no_nones(transform_, bounds_):
        raise ValueError(
            'You cannot specify both "transform" and "bounds" metadata. The '
            "two inputs are mutually exclusive."
        )

    # Validate projections and nodata
    crs_, transform_ = spatial(crs_, transform_)
    if bounds_ is not None:
        bounds_ = bounds(bounds_)
    if nodata_ is not None:
        nodata_ = nodata(nodata_, casting, dtype)

    # Return CRS, projection class, and nodata
    projection = transform_ or bounds_
    return crs_, projection, nodata_
