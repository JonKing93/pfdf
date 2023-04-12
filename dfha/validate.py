"""
validate  Functions that validate user inputs
----------
The validate module contains functions that check user inputs and raise exceptions
if the inputs are not valid. Some functions allow user inputs to be in multiple
different formats. When this is the case, the function will usually return the
input in a standard format for internal processing. For example, the "raster"
function accepts both file paths and numpy 2D arrays, but will return the
validated raster as a numpy 2D array. 

The module also defines several custom errors (mainly relating to the shape of
numpy arrays), which may be used to add identify errors originating from this
package.

Note on dtypes:
    In general, it is best to use numpy scalar types to indicate the allowed
    dtypes of a numpy array. Using built-in types can work, but these typically
    alias to a specific numpy scalar, rather than a more abstract type. For
    example, int may alias to numpy.int32, so would not be suitable to allow
    all integer types. Instead, use numpy.integer to enable all integer types.
----------
Size and type:
    ndarray         - Check that an input is a numpy ndarray
    vector          - Check an input is a 1D numpy array. Optionally check dtype and length
    matrix          - Check an input is a 2D numpy array. Optionally check dtype and shape

Numeric numpy:
    positive        - Checks that all elements are positive
    integers        - Checks that all elements are integers (NOT that the dtype is an int)

GIS:
    raster          - Check that an input is a raster and return it as a numpy 2D array

Custom Errors:
    NDimError       - Raised when an input has an incorrect number of dimensions
    ShapeError      - Raised when an input has an incorrect shape
"""

import numpy as np
from pathlib import Path
import rasterio
from dfha.utils import aslist
from typing import Any, Optional, List
from dfha.typing import (
    strs,
    shape,
    shape2d,
    RealArray,
    ScalarArray,
    VectorArray,
    MatrixArray,
    RasterArray,
)


def _nonsingleton(input: np.ndarray) -> List[bool]:
    "Finds the non-singleton dimensions of a numpy array"
    return [shape > 1 for shape in input.shape]


def _shape(input: Any, name: str, axes: strs, shape: shape) -> None:
    "Checks the shape of each axis is correct"
    if shape is not None:
        for axis, required, actual in zip(aslist(axes), aslist(shape), input.shape):
            if required != -1 and required != actual:
                raise ShapeError(name, axis, required, actual)


def real(input: Any, name: str) -> RealArray:
    """
    real  Validate a real-valued numpy array
    ----------
    real(input, name)
    Checks that an input represents a real-valued numpy array. If not, raises a
    TypeError. Otherwise, returns the input as a numpy array. Valid inputs may be
    an int, float, or real-valued numpy array. Here, real-valued indicates that
    the array dtype is derived from numpy.integer or numpy.floating.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.

    Outputs:
        np.ndarray: The input as an ndarray

    Raises:
        TypeError: If the input is neither an int, float, or real-value numpy array
    """

    # Check for basic numpy array
    if isinstance(input, int) or isinstance(input, float):
        input = np.array(input)
    elif not isinstance(input, np.ndarray):
        raise TypeError(f"{name} is not a numpy.ndarray")

    # Check real-valued
    dtype = input.dtype
    isinteger = np.issubdtype(dtype, np.integer)
    isfloating = np.issubdtype(dtype, np.floating)
    if not isinteger and not isfloating:
        raise TypeError(
            f"{name} does not have a real-valued dtype. Allowed types are numpy.integer and numpy.floating"
        )

    # Return as numpy array for internal use
    return input


def scalar(input: Any, name: str) -> ScalarArray:
    """
    scalar  Validate an input represents a scalar, real-valued number
    ----------
    scalar(input, name)
    Checks that an input represents a scalar, real-valued number. Valid inputs
    can be int, float, or a real-valued numpy array with a size of 1. Raises an
    exception if these criteria are not met. Returns the input as a 1D numpy array.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.

    Outputs:
        numpy 1D array: The input as a 1D numpy array.

    Raises:
        TypeError: If the input does not represent a real-valued numpy array
        ShapeError: If the input has more than one element
    """
    input = real(input, name)
    if input.size != 1:
        raise ShapeError(name, "element", required=1, actual=input.size)
    return input.reshape(1)


def vector(input: Any, name: str, *, length: Optional[int] = None) -> VectorArray:
    """
    vector  Validate an input represents a 1D real-valued numpy array
    ----------
    vector(input, name)
    Checks the input represents a 1D, real-valued numpy array. Valid inputs can
    be int, float, or a numpy array. If a numpy array, may only have a single
    non-singleton dimension. Raises an exception if any of these criteria are
    not met. Otherwise, returns the array as a numpy 1D array.

    vector(..., *, length)
    Also checks that the vector has the specified length. Raises a ShapeError if
    this criteria is not met.
    ----------
    Input:
        input: The input being checked
        name: A name for the input for use in error messages.
        length: A required length for the vector

    Outputs:
        numpy 1D array: The input as a 1D numpy array

    Raises:
        TypeError: If the input does not represent a real-valued numpy array
        NDimError: If the input does not have exactly 1 dimension
        ShapeError: If the input does not have the specified length
    """

    # Real-valued
    input = real(input, name)

    # Only 1 non-singleton dimension
    nonsingletons = _nonsingleton(input)
    if sum(nonsingletons) > 1:
        message = f"{name} can only have 1 dimension with a length greater than 1."
        raise DimensionError(
            f"{name} can only have 1 dimension with a length greater than 1."
        )

    # Optionally check length. Return 1D array
    _shape(input, name, "Element(s)", length)
    return input.reshape(input.size)


def matrix(input: Any, name: str, *, shape: Optional[shape2d] = None) -> MatrixArray:
    """
    matrix  Validate input represents a 2D real-valued numpy array
    ----------
    matrix(input, name)
    Checks the input represents a 2D real-valued numpy array. Raises an exception
    if not. Returns the output as a 2D numpy array. Valid inputs can be int,
    float, or a numpy array. If a numpy array, may have any number of dimension,
    but only the first two dimensions may be non-singleton. A 1D array is
    interpreted as a 1xN array.

    matrix(..., *, shape)
    Also checks that the array matches the requested shape. Use -1 to disable
    shape checking for a particular axis.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.
        shape: A requested shape for the matrix. A tuple with two elements - the
            first element is the number of rows, and the second is the number
            of columns. Setting an element to -1 disables the shape checking for
            that axis.

    Outputs:
        numpy 2D array: The input as a 2D numpy array

    Raises:
        TypeError: If the input does not represent a 2D real-valued numpy array
    """

    # Real valued
    input = real(input, name)

    # Only first 2 dimensions can be non-singleton
    if input.ndim > 2:
        nonsingletons = _nonsingleton(input)[2:]
        if any(nonsingletons):
            bad = np.argwhere(nonsingletons) + 2
            raise DimensionError(
                f"Only the first two dimension of {name} can be longer than 1. "
                "But dimension {bad} is longer than 1."
            )

    # Convert 1D to 2D. Optionally check shape
    if input.ndim == 1:
        input = input.reshape(1, -1)
    _shape(input, name, ["Row(s)", "Column(s)"], shape)

    # Return 2D array
    nrows, ncols = input.shape[0:2]
    return input.reshape(nrows, ncols)


def raster(raster: Any, name: str, *, nodata: Optional[scalar] = None) -> RasterArray:
    """
    raster  Check input is valid raster and return as numpy 2D array
    ----------
    raster(raster, name)
    Checks that the input is a valid raster. Valid rasters may be:
        * A string with the path to a raster file path,
        * A pathlib.Path to a raster file,
        * An open rasterio.DatasetReader object, or
        * A numpy 2D array with real-valued dtype

    Returns the raster as a numpy 2D array. If the input was not a numpy array,
    then the function will read the raster from file. Rasters will always be
    read from band 1.

    Raises exceptions if:
        * a raster file does not exist
        * a raster file cannot be opened by rasterio
        * a DatasetReader object is closed
        * a numpy array does not have 2 dimensions
        * a numpy array dtype is not a numpy.integer or numpy.floating
        * the input is some other type

    raster(..., *, nodata)
    Specify a value for NoData elements when reading a raster from file. All
    NoData elements will be replaced with this value. This option has no effect
    when a numpy array is provided.
    ----------
    Inputs:
        raster: The input being checked
        name: The name of the input for use in error messages
        nodata: A fill value for NoData elements when reading from file

    Outputs:
        numpy 2D array: The raster represented as a numpy array.
    """

    # Convert str to Path
    if isinstance(raster, str):
        raster = Path(raster)

    # Require file exists. Open with rasterio
    if isinstance(raster, Path):
        raster = raster.resolve(strict=True)
        raster = rasterio.open(raster)

    # Require open DatasetReader
    if isinstance(raster, rasterio.DatasetReader):
        if raster.closed:
            raise ValueError(
                f"{name} must be an open rasterio.DatasetReader, but it is closed"
            )

        # Read raster from band 1. Optionally convert NoData to fill value
        if nodata is None:
            raster = raster.read(1)
        else:
            mask = raster.read_masks(1)
            raster = raster.read(1)
            raster[mask == 0] = nodata

    # Require numpy 2D real-valued array. Return array
    if not isinstance(raster, np.ndarray):
        raise TypeError(
            f"{name} is not a recognized raster type. Allowed types are: "
            "str, pathlib.Path, rasterio.DatasetReader, or numpy.ndarray"
        )
    return matrix(raster, name)


def integers(input: RealArray, name: str) -> None:
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


def positive(input: RealArray, name: str, *, allow_zero: bool = False) -> None:
    """
    positive  Checks a numeric numpy array's elements are positive
    ----------
    positive(input, name)
    Checks that the elements of the input numpy array are all greater than zero.
    Raises a ValueError if not.

    positive(..., *, allow_zero=True)
    Checks that elements are greater than or equal to zero.
    ----------
    Inputs:
        input: The numeric ndarray being checked.
        name: A name for the input for use in error messages.
        allow_zero: Set to True to allow elements equal to zero.
            False (default) to only allow elements greater than zero.

    Raises:
        ValueError: If the array contains negative elements
    """

    # Exit immediately if unsigned integers (all are positive)
    if not np.issubdtype(input.dtype, np.unsignedinteger):

        # Search for negative values
        if allow_zero:
            operator = np.less
        else:
            operator = np.less_equal
        negative = operator(input, 0)

        # Error if any were negative
        if np.any(negative):
            bad = np.argwhere(negative)[0]
            raise ValueError(
                f"The elements of {name} cannot be negative, but element {bad} is negative."
            )


class DimensionError(Exception):
    "When a numpy array invalid non-singleton dimensions"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ShapeError(Exception):
    "When a numpy axis has the wrong shape"

    def __init__(self, name: str, axis: str, required: int, actual: int) -> None:
        message = (
            f"{name} must have {required} {axis}, but it has {actual} {axis} instead."
        )
        super().__init__(message)
