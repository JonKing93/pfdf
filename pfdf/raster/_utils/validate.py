"""
Functions that validate user inputs for raster routines
----------
NoData / Casting:
    casting_option  - Checks that a casting rule is recognized
    casting         - Checks that a value can be casted
    nodata          - Checks that a nodata value is valid and castable

Array shape:
    shape2d         - Checks that an input represents the shape of a 2D array
    slices          - Checks that an indexing slice is valid

Preprocessing:
    resampling  - Validates a resampling option
    data_bound  - Checks that a data bound is castable, or provides a default if missing

Factories:
    url             - Validates URL and file reading options
    file            - Validates path and file reading options
    file_options    - Validates file reading options
    reader          - Validates a rasterio.DatasetReader
"""

from __future__ import annotations

import typing
from pathlib import Path

import numpy as np
from rasterio import DatasetReader
from rasterio.enums import Resampling

import pfdf._validate.core as cvalidate
import pfdf._validate.projection as pvalidate
from pfdf._utils import astuple, real
from pfdf.errors import DimensionError
from pfdf.projection import BoundingBox

if typing.TYPE_CHECKING:
    from typing import Any, Literal, Optional

    from pfdf.typing.core import ScalarArray


#####
# NoData / casting
#####

CASTING_RULES = ["no", "equiv", "safe", "same_kind", "unsafe"]


def casting_option(value: Any, name: str) -> str:
    "Checks that a casting option is supported"
    return cvalidate.option(value, name, allowed=CASTING_RULES)


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

    nodata = cvalidate.scalar(nodata, "nodata", dtype=real)
    if dtype is not None:
        casting_ = casting_option(casting_, "casting")
        nodata = casting(nodata, "the NoData value", dtype, casting_)
    return nodata


#####
# Array shape
#####


def slices(indices: tuple[Any, ...], shape: tuple[int, int]) -> tuple[slice, slice]:
    "Checks that indexing slices are valid"

    # Shape cannot be 0
    if 0 in shape:
        raise IndexError(
            "Indexing is not supported when the raster shape contains a 0."
        )

    # Determine the number of dimensions
    if not isinstance(indices, tuple):
        ndims = 1
    else:
        ndims = len(indices)

    # Require exactly 2 dimensions. Extract row and column indices
    if ndims != 2:
        raise IndexError(
            f"You must provide indices for exactly 2 dimensions, but there are "
            f"indices for {ndims} dimension(s) instead."
        )
    rows, cols = indices

    # Validate row and column slices
    rows = _slice(rows, "row", shape[0])
    cols = _slice(cols, "column", shape[1])
    return rows, cols


def _slice(input: Any, name: str, length: int) -> slice:
    "Checks that an indexing slice is valid"

    # Convert int to slice. Must be in valid range
    if isinstance(input, int):
        if input < -length or input >= length:
            raise IndexError(
                f"The {name} index ({input}) is out of range. "
                f"Valid indices are from {-length} to {length-1}"
            )
        input = input % length
        input = slice(input, input + 1, 1)

    # Otherwise must be slice
    elif not isinstance(input, slice):
        raise TypeError(
            f"{name} indices must be an int or slice, "
            f"but they are {type(input).__name__} instead."
        )

    # Resolve slice. Must have step size of 1 and at least 1 element
    start, stop, step = input.indices(length)
    if step != 1:
        raise IndexError(f"{name} indices must have a step size of 1")
    elif stop - start <= 0:
        raise IndexError(f"{name} indices must select at least one element.")
    return slice(start, stop, step)


def shape2d(input: Any, name: str) -> tuple[int, int]:
    """Checks an input represents the shape of a 2D array. Note that the standard
    validators don't work here because they limit shapes to int64"""

    # Must be a sequence of 2 elements
    input = astuple(input)
    if len(input) != 2:
        raise DimensionError(f"{name} must have exactly 2 elements")

    # Must be integers
    error = TypeError(f'The elements of "{name}" must be integers')
    try:
        nrows = int(input[0])
        ncols = int(input[1])
    except Exception:
        raise error
    if nrows != input[0] or ncols != input[1]:
        raise error

    # Must be positive
    if nrows < 0 or ncols < 0:
        raise ValueError(f'The elements of "{name}" cannot be negative')
    return (nrows, ncols)


#####
# Preprocess
#####


def resampling(resampling) -> str:
    "Validates a requested resampling option"

    allowed = [method.name for method in Resampling]
    allowed.remove("gauss")
    method = cvalidate.option(resampling, "resampling", allowed)
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
        value = cvalidate.scalar(value, bound, dtype=real)
        value = casting(value, bound, dtype, "safe")
        return value


#####
# Factories
#####


def url(
    url: Any,
    check_status: bool,
    timeout: Any,
    driver: Any,
    band: Any,
    bounds: Any,
    casting: Any,
) -> tuple[str, BoundingBox | None]:
    "Validates URL and file-reading options"

    # Validate URL. Optionally check http(s) using requests.head
    scheme = cvalidate.url(url)
    if scheme in ["http", "https"] and check_status:
        timeout = cvalidate.timeout(timeout)
        cvalidate.http(url, timeout)

    # Also validate file options
    bounds = file_options(driver, band, casting, bounds)
    return url, bounds


def file(
    path: Any, driver: Any, band: Any, bounds: Any, casting: Any
) -> tuple[Path, BoundingBox | None]:
    "Validate path and file-reading options"

    path = cvalidate.input_file(path)
    bounds = file_options(driver, band, casting, bounds)
    return path, bounds


def file_options(
    driver: Any, band: Any, casting: Any, bounds: Any
) -> BoundingBox | None:
    "Validates read-options for a file-based raster"

    # Driver, band, and casting option
    if driver is not None:
        cvalidate.string(driver, "driver")
    cvalidate.type(band, "band", int, "int")
    casting_option(casting, "casting")

    # Parse bounds
    if bounds is not None:
        bounds = pvalidate.bounds(bounds)
    return bounds


def reader(reader: Any) -> Path:
    "Checks that a rasterio.DatasetReader is valid"

    # Validate type
    cvalidate.type(
        reader,
        "input raster",
        DatasetReader,
        "rasterio.DatasetReader object",
    )

    # Get path. Informative error if file is missing
    path = Path(reader.name)
    if not path.exists():
        raise FileNotFoundError(
            f"The file associated with the input rasterio.DatasetReader "
            f"object no longer exists.\nFile: {path}"
        )
    return path
