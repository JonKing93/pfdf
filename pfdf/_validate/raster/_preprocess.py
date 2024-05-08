"""
Functions that validate input arguments used for raster preprocessing
----------
Misc:
    resampling  - Checks that a resampling algorithm is valid
    data_bound  - Checks that a data bound is castable, or provides a default if missing
    resolution  - Checks that raster resolution represents two positive values

NoData:
    casting     - Checks that a casting rule is recognized
    nodata      - Checks that a nodata value is valid and castable

Projection:
    crs         - Checks input represents a pyproj.CRS
    transform   - Checks input represents a Transform object
    bounds      - Checks input represents a BoundingBox object

Multiple Metadatas:
    feature_options - Checks that resolution and bounds are valid
    spatial     - Checks that CRS and Transform are valid
    metadata    - Checks CRS, Transform, and NoData value
"""

from typing import Any, Literal, Optional

import numpy as np
from affine import Affine
from rasterio.enums import Resampling

from pfdf import raster
from pfdf._utils import real
from pfdf._validate import core as validate
from pfdf.errors import MissingCRSError, MissingTransformError, ShapeError
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.typing import ScalarArray, VectorArray

#####
# Misc Preprocessing
#####


def resampling(resampling) -> str:
    "Validates a requested resampling option"

    allowed = [method.name for method in Resampling]
    allowed.remove("gauss")
    method = validate.option(resampling, "resampling", allowed)
    return getattr(Resampling, method)


def data_bound(value: Any, bound: Literal["min", "max"], dtype: type) -> ScalarArray:
    """Checks that a user provided data bound is castable to the raster dtype.
    If no bound is provided, provides a default value."""

    # Get default bounds. Bool default is True or False
    if value is None:
        if dtype == bool:
            return bound == "max"

        # Integer default is the min/max value representable in the dtype
        elif np.issubdtype(dtype, np.integer):
            info = np.iinfo(dtype)
            return getattr(info, bound)

        # Floating default is -inf/inf
        elif bound == "min":
            return -np.inf
        else:
            return np.inf

    # Otherwise, validate user values
    else:
        value = validate.scalar(value, bound, dtype=real)
        value = casting(value, bound, dtype, "safe")
        return value


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


def feature_options(resolution_, bounds_):
    "Validates mandatory resolution and optional bounds"
    resolution_ = resolution(resolution_)
    if bounds_ is not None:
        bounds_ = bounds(bounds_)
    return resolution_, bounds_


def spatial(crs_, transform_):
    "Validates CRS and transform"
    if crs_ is not None:
        crs_ = crs(crs_)
    if transform_ is not None:
        transform_ = transform(transform_)
    return crs_, transform_


def metadata(crs_, transform_, nodata_, casting, dtype=None):
    "Validates CRS, Transform, and NoData"
    crs_, transform_ = spatial(crs_, transform_)
    if nodata_ is not None:
        nodata_ = nodata(nodata_, casting, dtype)
    return crs_, transform_, nodata_
