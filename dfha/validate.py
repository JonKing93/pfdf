"""
validate  Functions that validate user inputs
----------
The validate module contains functions that check user inputs and raise exceptions
if the inputs are not valid. Some functions allow user inputs to be in multiple
different formats. When this is the case, the function will return the input in 
a standard format for internal processing. For example, the "raster"
function accepts both file paths and numpy 2D arrays, but will return the
validated raster as a numpy 2D array. 

The module also defines several custom exceptions relating to the shape of input
numpy arrays.

Note on dtypes:
    In general, it is best to use numpy scalar types to indicate the allowed
    dtypes of a numpy array. Using built-in types can work, but these typically
    alias to a specific numpy scalar, rather than a more abstract type. For
    example, int may alias to numpy.int32, so would not be suitable to allow
    all integer types. Instead, use numpy.integer to enable all integer types.
----------
Array shape and type:
    scalar          - Validates an input scalar
    vector          - Validates an input vector
    matrix          - Validates an input matrix

Numeric arrays:
    positive        - Checks that all elements are positive
    integers        - Checks that all elements are integers (NOT that the dtype is an int)
    inrange         - Checks that all elements are within a given range (inclusive)

Rasters:
    raster          - Check that an input is a raster and return it as a numpy 2D array

Low-level:
    shape_          - Check that array shape is valid
    dtype_          - Checks that array dtype is valid
    nonsingleton    - Locate nonsingleton dimensions   

Exceptions:
    DimensionError  - Raised when an input has invalid nonsingleton dimensions or no elements
    ShapeError      - Raised when an input has an incorrect shape

Internal:
    _check_bound    - Compares the elements of an ndarray to a bound
"""

import numpy as np
from pathlib import Path
import rasterio
from dfha.utils import aslist, astuple, real
from typing import Any, Optional, List, Union
from dfha.typing import (
    strs,
    dtypes,
    shape,
    shape2d,
    scalar,
    RealArray,
    ScalarArray,
    VectorArray,
    MatrixArray,
    RasterArray,
)


def _check_bound(input, name, operator, bound):
    """
    _check_bound  Checks that elements of a numpy array are valid relative to a bound
    ----------
    _check_bound(input, name, operator, bound)
    Checks that the elements of the input numpy array are valid relative to a
    bound. Valid comparisons are >, <, >=, and <=. Raises a ValueError if the
    criterion is not met.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages
        operator: The comparison operator to apply. Options are '<', '>', '<=',
            and '>='. Elements must satisfy: (input operator bound) to be valid.
            For example, input < bound.
        bound: The bound being compared to the elements of the array.

    Raises:
        ValueError: If any element fails the comparison
    """

    # Only compare if bounds were specified
    if bound is not None:
        # Get the operator for the comparison. Note that we are testing for failed
        # elements, so actually need the *inverse* of the input operator.
        if operator == "<":
            description = "less than"
            operator = np.greater_equal
        elif operator == "<=":
            description = "less than or equal to"
            operator = np.greater
        elif operator == ">=":
            description = "greater than or equal to"
            operator = np.less
        elif operator == ">":
            description = "greater than"
            operator = np.less_equal

        # Test elements. Raise ValueError if any fail
        failed = operator(input, bound)
        if np.any(failed):
            bad = np.argwhere(failed)[0]
            raise ValueError(
                f"The elements of {name} must be {description} {bound}, but element {bad} is not."
            )


class DimensionError(Exception):
    "When a numpy array has invalid non-singleton dimensions"

    def __init__(self, message: str) -> None:
        super().__init__(message)


def dtype_(name: str, allowed: dtypes, actual: type) -> None:
    """
    dtype_  Checks that a dtype is an allowed value
    ----------
    dtype_(name, allowed, actual)
    Checks that the input dtype is an allowed type. Raises an exception if not.
    Note that the dtypes in "allowed" should consist of numpy scalar types and
    not Python built-in types. By contrast, "actual" may be either a numpy or
    built-in type. If allowed=None, conducts no checking and exits.
    ----------
    Inputs:
        name: A name for the input being tested for use in error messages.
        allowed: A list of allowed dtypes. Must consist of numpy scalar types.
            If None, disables type checking.
        actual: The dtype of the array being tested

    Raises:
        TypeError: If the dtype is not allowed
    """
    # Iterate through allowed types. Exit if any match
    if allowed is not None:
        allowed = aslist(allowed)
        for type in allowed:
            if np.issubdtype(actual, type):
                return

        # TypeError if type was not allowed
        allowed = ", ".join([str(type)[8:-2] for type in allowed])
        raise TypeError(
            f"The dtype of {name} ({actual}) is not an allowed dtype. "
            f"Allowed types are: {allowed}"
        )


def inrange(
    input: RealArray,
    name: str,
    min: Optional[scalar] = None,
    max: Optional[scalar] = None,
) -> None:
    """
    inrange  Checks the elements of a numpy array are within a given range
    ----------
    inrange(input, name, min, max)
    Checks that the elements of a real-valued numpy array are all within a
    specified range. min and max are optional arguments, you can specify a single
    one to only check an upper or a lower bound. Use both to check elements are
    within a range. Uses an inclusive comparison (values equal to a bound will
    pass validation).
    ----------
    Inputs:
        input: The ndarray being checked
        name: The name of the array for use in error messages
        min: An optional lower bound (inclusive)
        max: An optional upper bound (inclusive)

    Raises:
        ValueError: If any element is not within the bounds
    """

    _check_bound(input, name, ">=", min)
    _check_bound(input, name, "<=", max)


def integers(input: RealArray, name: str) -> None:
    """
    integers  Checks the elements of a numpy array are all integers
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


def matrix(
    input: Any,
    name: str,
    *,
    dtype: Optional[dtypes] = None,
    shape: Optional[shape2d] = None,
) -> MatrixArray:
    """
    matrix  Validate input represents a 2D numpy array
    ----------
    matrix(input, name)
    Checks the input represents a 2D numpy array. Raises an exception
    if not. Otherwise, returns the output as a 2D numpy array. Valid inputs may
    have any number of dimension, but only the first two dimensions may be
    non-singleton. A 1D array is interpreted as a 1xN array.

    matrix(..., *, dtype)
    Also checks the array has an allowed dtype. Raises a TypeError if not.

    matrix(..., *, shape)
    Also checks that the array matches the requested shape. Raises a ShapeError
    if not. Use -1 to disable shape checking for a particular axis.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.
        dtype: A list of allowed dtypes
        shape: A requested shape for the matrix. A tuple with two elements - the
            first element is the number of rows, and the second is the number
            of columns. Setting an element to -1 disables the shape checking for
            that axis.

    Outputs:
        numpy 2D array: The input as a 2D numpy array

    Raises:
        TypeError: If the input does not have an allowed dtype
        DimensionError: If the input has non-singleton dimensions that are not
            the first 2 dimensions.
        ShapeError: If the input does not have an allowed shape
    """

    # Optionally check type
    input = np.array(input)
    input = np.atleast_2d(input)
    dtype_(name, allowed=dtype, actual=input.dtype)

    # Can't be empty
    if input.size == 0:
        raise DimensionError(f"{name} does not have any elements.")

    # Only the first 2 dimensions can be non-singleton
    if input.ndim > 2:
        nonsingletons = nonsingleton(input)[2:]
        if any(nonsingletons):
            raise DimensionError(
                f"Only the first two dimension of {name} can be longer than 1. "
            )

    # Cast as 2D array. Optionally check shape. Return array
    nrows, ncols = input.shape[0:2]
    input = input.reshape(nrows, ncols)
    shape_(name, ["row(s)", "column(s)"], required=shape, actual=input.shape)
    return input


def nonsingleton(array: np.ndarray) -> List[bool]:
    """
    nonsingleton  Finds the non-singleton dimensions of a numpy array
    ----------
    nonsingleton(array)
    Returns a bool list with one element per dimension of the input array.
    True indicates a nonsingleton dimensions (length > 1). False is singleton.
    ----------
    Inputs:
        array: The ndarray being inspected

    Returns:
        List[bool]: Indicates the non-singleton dimensions.
    """
    return [shape > 1 for shape in array.shape]


def positive(input: RealArray, name: str, *, allow_zero: bool = False) -> None:
    """
    positive  Checks the elements of a numpy array are all positive
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

    # Exit immediately if unsigned integers (all are positive).
    if not np.issubdtype(input.dtype, np.unsignedinteger):
        # Determine the comparison type
        if allow_zero:
            operator = ">="
        else:
            operator = ">"

        # Check for elements below the 0 bound
        _check_bound(input, name, operator, 0)


def raster(
    raster: Any,
    name: str,
    *,
    nodata: Optional[scalar] = None,
    shape: Optional[shape2d] = None,
    load: Optional[bool] = True,
) -> Union[Path, RasterArray]:
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
        * a numpy array does not have 2 dimensions
        * a numpy array dtype is not a numpy.integer or numpy.floating
        * the input is some other type

    raster(..., *, nodata)
    Specify a value for NoData elements when reading a raster from file. All
    NoData elements will be replaced with this value. This option has no effect
    when a numpy array is provided.

    raster(..., *, shape)
    Require the raster to have the specified shape. Raises a ShapeError if this
    condition is not met.

    raster(..., *, load=False)
    Indicates that file-based rasters (those derived from a string, pathlib.Path,
    or rasterio.DatasetReader object) should not be loaded into memory after
    validating. If the input was a file-based raster, returns a pathlib.Path
    object for the validated raster file instead of a numpy array. Input numpy
    arrays are not affected and still return a numpy array.
    ----------
    Inputs:
        raster: The input being checked
        name: The name of the input for use in error messages
        nodata: A fill value for NoData elements when reading from file
        shape: A required shape for the raster. A 2-tuple, first element is rows
            second element is columns. If an element is -1, disables shape checking
            for that axis.
        load: True (default) if validated file-based rasters should be loaded
            into memory and returned as a numpy array. If False, returns a
            pathlib.Path object for file-based rasters.

    Outputs:
        numpy 2D array: The raster represented as a numpy array.
        pathlib.Path: If load=False and the input is a file-based raster
    """

    # Convert str to Path
    if isinstance(raster, str):
        raster = Path(raster)

    # If Path, require file exists
    if isinstance(raster, Path):
        raster = raster.resolve(strict=True)

    # If DatasetReader, check that the associated file exists. Get the
    # associated Path to allow loading within a context manager without closing
    # the user's object
    elif isinstance(raster, rasterio.DatasetReader):
        raster = Path(raster.name)
        if not raster.exists():
            raise FileNotFoundError(
                f"The raster file associated with the input rasterio.DatasetReader "
                f"object no longer exists.\nFile: {raster}"
            )

    # Anything else should be a numpy array. Validate and return the array
    else:
        if not isinstance(raster, np.ndarray):
            raise TypeError(
                f"{name} is not a recognized raster type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, or numpy.ndarray"
            )
        return matrix(raster, name, shape=shape, dtype=real)

    # Validate band 1 of file-based rasters
    band = 1
    with rasterio.open(raster) as data:
        dtype_(name, allowed=real, actual=data.dtypes[band - 1])
        if shape is not None:
            nrows = data.height
            ncols = data.width
            shape_(name, ["rows", "columns"], required=shape, actual=(nrows, ncols))
            shape = None

        # Optionally load into memory. Optionally convert NoData values
        if load:
            if nodata is None:
                raster = data.read(band)
            else:
                mask = data.read_masks(band)
                raster = data.read(band)
                raster[mask == 0] = nodata

        # Return the array or Path
        return raster


def scalar(input: Any, name: str, dtype: Optional[dtypes] = None) -> ScalarArray:
    """
    scalar  Validate an input represents a scalar
    ----------
    scalar(input, name)
    Checks that an input represents a scalar. Raises an exception if not. Returns
    the input as a 1D numpy array.

    scalar(input, name, dtype)
    Also check that the input is derived from one of the listed dtypes.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.
        dtype: A list of allowed dtypes

    Outputs:
        numpy 1D array: The input as a 1D numpy array.

    Raises:
        ShapeError: If the input has more than one element
        TypeError: If the input does not have an allowed dtype
    """

    # Optionally check dtype
    input = np.array(input)
    dtype_(name, allowed=dtype, actual=input.dtype)

    # No non-singleton dimensions
    if input.size != 1:
        raise DimensionError(
            f"{name} must have exactly 1 element, but it has {input.size} elements instead."
        )

    # Return as 1D array
    return input.reshape(1)


def shape_(name: str, axes: strs, required: shape, actual: shape) -> None:
    """
    shape_  Checks that a numpy ndarray shape is valid
    ----------
    shape_(name, axes, required, actual)
    Checks that an input shape is valid. Raises an exception if not. Setting
    required=None disables shape checking altogether. If an element of required
    is -1, disables shape checking for that dimension.
    ----------
    Inputs:
        name: The name of the array being tested for use in error messages
        axes: The names of the elements of each dimension being tested. Should
            have one string per element of the required shape.
        shape: The required shape of the numpy array. If an element of shape is
            -1, disables shape checking for that dimension.
        actual: The actual shape of the numpy array

    Raises:
        ShapeError: If the array does not have the required shape.
    """
    if required is not None:
        axes = aslist(axes)
        indices = range(0, len(axes))
        for axis, index, required_, actual_ in zip(
            axes, indices, astuple(required), astuple(actual)
        ):
            if required_ != -1 and required_ != actual_:
                raise ShapeError(name, axis, index, required, actual)


class ShapeError(Exception):
    """
    When a numpy axis has the wrong shape
    ----------
    Properties:
        required: The required shape of the numpy array
        actual: The actual shape of the numpy array
        index: The index of the bad axis
    """

    def __init__(
        self, name: str, axis: str, index: int, required: shape, actual: shape
    ) -> None:
        message = f"{name} must have {required[index]} {axis}, but it has {actual[index]} {axis} instead."
        self.index = index
        self.required = required
        self.actual = actual
        super().__init__(message)


def vector(
    input: Any,
    name: str,
    *,
    dtype: Optional[dtypes] = None,
    length: Optional[int] = None,
) -> VectorArray:
    """
    vector  Validate an input represents a 1D numpy array
    ----------
    vector(input, name)
    Checks the input represents a 1D numpy array. Valid inputs may only have a
    single non-singleton dimension. Raises an exception if this criteria is not
    met. Otherwise, returns the array as a numpy 1D array.

    vector(..., *, dtype)
    Also checks that the vector has an allowed dtype. Raises a TypeError if not.

    vector(..., *, length)
    Also checks that the vector has the specified length. Raises a ShapeError if
    this criteria is not met.
    ----------
    Input:
        input: The input being checked
        name: A name for the input for use in error messages.
        dtype: A list of allowed dtypes
        length: A required length for the vector

    Outputs:
        numpy 1D array: The input as a 1D numpy array

    Raises:
        TypeError: If the input does not have an allowed dtype
        DimensionError: If the input does not have exactly 1 dimension
        ShapeError: If the input does not have the specified length
    """

    # Optionally check dtype
    input = np.array(input)
    input = np.atleast_1d(input)
    dtype_(name, allowed=dtype, actual=input.dtype)

    # Can't be empty
    if input.size == 0:
        raise DimensionError(f"{name} does not have any elements.")

    # Only 1 non-singleton dimension
    nonsingletons = nonsingleton(input)
    if sum(nonsingletons) > 1:
        raise DimensionError(
            f"{name} can only have 1 dimension with a length greater than 1."
        )

    # Optionally check length
    shape_(name, "element(s)", required=length, actual=input.size)
    return input.reshape(-1)
