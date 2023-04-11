"""
validate  Functions that validate user inputs
----------
Key functions:
    ndarray     - Check that an input is a numpy ndarray
    matrix      - Check an input is a 2D numpy array. Optionally check dtype and shape

Custom Errors:
    NDimError   - Raised when an input has an incorrect number of dimensions
    ShapeError  - Raised when an input has an incorrect shape
"""

import numpy as np
from typing import Any, Union, List, Optional, Tuple
from nptyping import NDArray, Number, Shape
import numbers
from pathlib import Path
from dfha.utils import aslist
import rasterio

# Type aliases
dtype = Union[np.dtype, str, object]
dtypes = Union[dtype, List[dtype]]
shape2d = Tuple[int, int]
raster_array = NDArray[Shape["Rows, Cols"], Number]
Raster = Union[str, Path, rasterio.DatasetReader, raster_array]


def _dtype(input: Any, name: str, allowed: dtypes) -> None:
    "Check a numpy dtype is valid"
    if allowed is not None:
        allowed = aslist(dtypes)
        actual = input.dtype
        isvalid = [np.issubdtype(actual, type) for type in allowed]
        if not any(isvalid):
            raise TypeError(f"The dtype of {name} ({actual}) is not allowed.")


def _shape(input: Any, name: str, axes: List[str], shape: shape2d) -> None:
    "Check that the shape of each axis is correct"
    if shape is not None:
        for axis, required, actual in zip(axes, shape, input.shape):
            if required != -1 and required != actual:
                raise ShapeError(name, axis, required, actual)


def _ndim(input: Any, name: str, N: int) -> None:
    "Check that the number of dimensions are correct"
    if input.ndim != N:
        raise NDimError(name, N, input.ndim)


def matrix(
    input: Any,
    name: str,
    *,
    dtypes: Optional[dtypes] = None,
    shape: Optional[shape2d] = None,
) -> None:
    """
    matrix  Checks an input is a numpy 2D array. Optionally checks dtype and shape
    ----------
    matrix(input, name)
    Checks that an input is a numpy ndarray with two dimensions. Raises a
    TypeError if not an ndarray. Raises a NDimError if the number of dimensions
    is not 2.

    matrix(..., *, dtypes, ...)
    Also checks that the ndarray has one of the specified dtypes. Raises a
    TypeError if not.

    matrix(..., *, shape, ...)
    Also checks that the ndarray has the specified shape. Raises a ShapeError
    if not.
    ----------
    Inputs:
        input: The input being checked
        name: The name of the input (for use in error messages)
        dtypes: The set of allowed dtypes. May be a single dtype, or a list. A
            dtype may be any value accepted by the numpy.dtype constructor.
        shape: A required shape for the matrix. Use -1 to not check the shape
            of an axis.

    Raises:
        TypeError: If the input is not a numpy ndarray
        NDimError: If the input does not have 2 dimensions
        TypeError: If the input is not an allowed dtype
        ShapeError: If the input does not have the required shape
    """

    ndarray(input, name)
    _ndim(input, name, 2)
    _dtype(input, name, dtypes)
    _shape(input, name, ["row(s)", "column(s)"], shape)


def ndarray(input: Any, name: str) -> None:
    """
    ndarray  Checks that an input is a numpy ndarray
    ----------
    ndarray(input)
    Checks that the input is an numpy ndarray. Raises a TypeError if not.
    ----------
    Inputs:
        input: The input being checked

    Raises:
        TypeError: If the input is not a numpy ndarray
    """
    if not isinstance(input, np.ndarray):
        raise TypeError(f"{name} is not a numpy ndarray")


def non_negative(input: NDArray[Any, Number], name: str) -> None:
    """
    non_negative  Checks a numeric numpy array's elements are >= 0
    ----------
    non_negative(input, name)
    Checks that the elements of the input numpy array are all greater than or
    equal to zero. Raises a ValueError if not.
    ----------
    Inputs:
        input: The numeric ndarray being checked.
        name: A name for the input for use in error messages.

    Raises:
        ValueError: If the array contains negative elements
    """

    if not np.issubdtype(input.dtype, np.unsignedinteger):
        negative = input < 0
        if np.any(negative):
            bad = np.argwhere(negative)[0]
            raise ValueError(
                f"The elements of {name} cannot be negative, but element {bad} is negative."
            )


def integers(input: NDArray[Any, Number], name: str) -> None:
    """
    integers  Checks a numeric numpy array's elements are integers
    ----------
    integers(input, name)
    Checks that the elements of the input numpy array are all integers. Raises a
    ValueError if not.

    Note that this function *IS NOT* checking the dtype of the input array. Rather
    it checks that each element is an integer. Thus, arrays of floating-point
    integers (e.g. 1.0, 2.000, -3.0) will pass the test.
    ----------
    Inputs:
        input: The numeric ndarray being checked.
        name: A name of the input for use in error messages.

    Raises:
        ValueError: If the array contains non-integer elements
    """

    if not np.issubdtype(input.dtype, np.integer):
        noninteger = input % 1 != 0
        if np.any(noninteger):
            bad = np.argwhere(noninteger)[0]
            raise ValueError(
                f"The elements of {name} must be integers, but element {bad} is not an integer."
            )


def raster(
    raster: Raster,
    name: str,
    *,
    nodata: Optional[numbers.Number] = None,
    dtypes: Optional[dtypes] = None,
    shape: Optional[shape2d] = None,
) -> raster_array:
    """
    raster  Check input is valid raster and return as numpy 2D array
    ----------

    """

    # Convert str to Path
    if isinstance(raster, str):
        raster = Path(raster)

    # Require file exists. Open with rasterio
    if isinstance(raster, Path):
        raster = raster.resolve(strict=True)
        raster = rasterio.open(raster)

    # Read band 1. Optionally convert NoData to specified value
    if isinstance(raster, rasterio.DataReader):
        if nodata is None:
            raster = raster.read(1)
        else:
            mask = raster.read_masks(1)
            raster = raster.read(1)
            raster[mask == 0] = nodata

    # Require numpy 2D numeric array. Return array
    matrix(raster, name, dtypes=dtypes, shape=shape)
    return raster


class NDimError(Exception):
    "When a numpy array has the wrong number of dimensions"

    def __init__(self, name: str, nrequired: int, nactual: int) -> None:
        message = (
            f"{name} must have {nrequired} dimension(s), but it has {nactual} instead."
        )
        super().__init__(message)


class ShapeError(Exception):
    "When a numpy axis has the wrong shape"

    def __init__(self, name: str, axis: str, required: int, actual: int) -> None:
        message = (
            f"{name} must have {required} {axis}, but it has {actual} {axis} instead."
        )
        super().__init__(message)
