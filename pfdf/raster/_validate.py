"""
Functions that validate user inputs for raster routines
----------
NoData:
    casting_option  - Checks that a casting rule is recognized
    casting         - Checks that a value can be casted
    nodata          - Checks that a nodata value is valid and castable
    
Multiple Metadatas:
    spatial     - Checks that CRS and Transform are valid
    metadata    - Checks CRS, Transform, and NoData value

Preprocessing:
    resampling  - Validates a resampling option
    data_bound  - Checks that a data bound is castable, or provides a default if missing
"""

from typing import Any, Literal, Optional

import numpy as np
from rasterio.enums import Resampling

import pfdf._validate.projection as _validate
from pfdf._utils import no_nones, real
from pfdf._validate.core import option, scalar
from pfdf.typing.core import ScalarArray

#####
# NoData / casting
#####

CASTING_RULES = ["no", "equiv", "safe", "same_kind", "unsafe"]


def casting_option(value: Any, name: str) -> str:
    "Checks that a casting option is supported"
    return option(value, name, allowed=CASTING_RULES)


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

    casted = value.astype(dtype, casting="unsafe")
    if (value == casted) or np.can_cast(value, dtype, casting):
        return casted
    else:
        raise TypeError(
            f"Cannot cast {name} (value = {value}) to the raster dtype ({dtype}) "
            f"using '{casting}' casting."
        )


def nodata(nodata, casting_, dtype: Optional[Any] = None):
    """Checks that a NoData value is valid. If a dtype is valid, checks that the
    NoData value is castable to the dtype"""

    nodata = scalar(nodata, "nodata", dtype=real)
    if dtype is not None:
        casting_ = casting_option(casting_, "casting")
        nodata = casting(nodata, "the NoData value", dtype, casting_)
    return nodata


#####
# Multiple metadatas
#####


def spatial(crs, transform):
    "Validates CRS and transform"
    if crs is not None:
        crs = _validate.crs(crs)
    if transform is not None:
        transform = _validate.transform(transform)
    return crs, transform


def metadata(crs, transform, bounds, nodata_, casting, dtype=None):
    "Validates CRS, Transform, Bounds, and NoData"

    # Transform and bounds are mutually exclusive
    if no_nones(transform, bounds):
        raise ValueError(
            'You cannot specify both "transform" and "bounds" metadata. The '
            "two inputs are mutually exclusive."
        )

    # Validate projections and nodata
    crs, transform = spatial(crs, transform)
    if bounds is not None:
        bounds = _validate.bounds(bounds)
    if nodata_ is not None:
        nodata_ = nodata(nodata_, casting, dtype)

    # Return CRS, projection class, and nodata
    projection = transform or bounds
    return crs, projection, nodata_


#####
# Preprocess
#####


def resampling(resampling) -> str:
    "Validates a requested resampling option"

    allowed = [method.name for method in Resampling]
    allowed.remove("gauss")
    method = option(resampling, "resampling", allowed)
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
        value = scalar(value, bound, dtype=real)
        value = casting(value, bound, dtype, "safe")
        return value
