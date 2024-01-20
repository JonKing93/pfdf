"""
validate  Functions that validate input numpy arrays
----------
The validate module contains functions that check user inputs and raise
exceptions if the inputs are not valid. Some functions allow user inputs to be 
in multiple different formats. When this is the case, the function will return
the input in a standard format for internal processing.

Note on dtypes:
    In general, it is best to use numpy scalar types to indicate the allowed
    dtypes of a numpy array. Using built-in types can work, but these typically
    alias to a specific numpy scalar, rather than a more abstract type. For
    example, int may alias to numpy.int32, so would not be suitable to allow
    all integer types. Instead, use numpy.integer to enable all integer types.

Note on array elements:
    As a rule, tests that check the elements of an array only check the *valid*
    data elements. NoData elements are ignored and will not trigger errors.
----------
Low-level:
    shape_          - Check that array shape is valid
    dtype_          - Checks that array dtype is valid
    nonsingleton    - Locate nonsingleton dimensions

Shape and type:
    array           - Validates an input array
    scalar          - Validates an input scalar
    vector          - Validates an input vector
    matrix          - Validates an input matrix

Array elements:
    defined         - Checks that an array does not contain NaN elements
    boolean         - Checks that all elements are 0 or 1 (NOT that the dtype is bool)
    integers        - Checks that all elements are integers (NOT that the dtype is an int)
    positive        - Checks that all elements are positive
    inrange         - Checks that all elements are within a given range (inclusive)
    sorted          - Checks that array elements are sorted
    flow            - Checks that an array consists of TauDEM-style D8 flow directions

Raster metadata:
    casting         - Checks that a value is castable to the indicated dtype
    crs             - Checks that a coordinate reference system is valid
    resolution      - Checks that raster resolution is valid
    transform       - Checks that a raster affine transform is valid
    _check_affine   - Checks that a transform coefficient is a valid float
    _check_shear    - Checks that a transform shear coefficient is 0

File paths:
    input_path      - Checks an input is a resolvable path
    output_path     - Checks that a path is suitable for an output file

Misc:
    broadcastable   - Checks that array shapes can be broadcasted
    option          - Checks that a string is a recognized option

Elements utilities:
    _get_data       - Returns the data values and valid data mask for an array
    _check_integers - Checks that all data values are integers
    _check_bound    - Compares the elements of an ndarray to a bound
    _check          - Ensures the data elements of an ndarray passed a validation test
    _first_failure  - Returns the index and value of the first element to fail a validation test
"""

from math import isinf, isnan
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np
import rasterio.transform
from affine import Affine
from numpy import integer as int_
from numpy import issubdtype as istype
from numpy import unsignedinteger as uint_
from rasterio import CRS
from rasterio.errors import CRSError as RasterioCrsError

from pfdf._utils import aslist, astuple, real
from pfdf._utils.nodata import NodataMask
from pfdf.errors import (
    CrsError,
    DimensionError,
    EmptyArrayError,
    ShapeError,
    TransformError,
)
from pfdf.typing import (
    BooleanArray,
    MatrixArray,
    RealArray,
    ScalarArray,
    VectorArray,
    dtypes,
    ignore,
    scalar,
    shape,
    shape2d,
    strs,
)

# Type alias
index = tuple[int, ...]
DataMask = NodataMask  # More clear for when invert=True


#####
# Low Level
#####


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

    # Convert inputs to sequences
    if required is not None:
        axes = aslist(axes)
        required = astuple(required)
        actual = astuple(actual)

        # Check the length of each dimension
        for axis, required, actual in zip(axes, required, actual):
            if required != -1 and required != actual:
                raise ShapeError(
                    f"{name} must have {required} {axis}, but it has {actual} {axis} instead."
                )


def nonsingleton(array: np.ndarray) -> list[bool]:
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
        list[bool]: Indicates the non-singleton dimensions.
    """
    return [shape > 1 for shape in array.shape]


#####
# Shapes and types
#####


def array(input: Any, name: str, dtype=None) -> RealArray:
    """
    array  Validates an input numpy array
    ----------
    array(input, name)
    Converts the input to a numpy array with at least 1 dimension. Raises an
    EmptyArrayError if the array does not contain any elements.

    array(input, name, dtype)
    Also checks the input is derived from one of the listed dtypes.
    ----------
    Inputs:
        input: The input being checked
        name: The name of the input for use in error messages.
        dtype: A list of allowed dtypes

    Outputs:
        numpy array (at least 1D): The input as a numpy array

    Raises:
        EmptyArrayError - If the array is empty
    """

    # Convert to array with minimum of 1D
    input = np.array(input, copy=False)
    input = np.atleast_1d(input)

    # Can't be empty. Optionally check dtype
    if input.size == 0:
        raise EmptyArrayError(f"{name} does not have any elements.")
    dtype_(name, allowed=dtype, actual=input.dtype)
    return input


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
        DimensionError: If the input has more than one element
    """

    input = array(input, name, dtype)
    if input.size != 1:
        raise DimensionError(
            f"{name} must have exactly 1 element, but it has {input.size} elements instead."
        )
    return input[0]


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
        DimensionError: If the input has more than 1 non-singleton dimension
    """

    # Initial validation
    input = array(input, name, dtype)

    # Only 1 non-singleton dimension is allowed
    nonsingletons = nonsingleton(input)
    if sum(nonsingletons) > 1:
        raise DimensionError(
            f"{name} can only have 1 dimension with a length greater than 1."
        )

    # Optionally check shape. Return as 1D vector.
    shape_(name, "element(s)", required=length, actual=input.size)
    return input.reshape(-1)


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

    # Initial validation. Handle vector shapes
    input = array(input, name, dtype)
    if input.ndim == 1:
        input = input.reshape(input.size, 1)

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


#####
# Array elements
#####


def defined(array: RealArray, name: str) -> None:
    """
    defined  Checks that an array does not contain NaN elements
    ----------
    defined(array, name)
    Checks that an array does not contain NaN elements. Raises a ValueError if
    NaN elements are present.
    ----------
    Inputs:
        array: The array being checked
        name: A name for the array for use in error messages

    Raises:
        ValueError: If the array's data elements contains NaN values
    """

    array, mask = _get_data(array, ignore=None)
    defined = ~np.isnan(array)
    if not np.all(defined):
        index, _ = _first_failure(defined, array, mask)
        raise ValueError(
            f"{name} cannot contain NaN elements, but element {index} is NaN."
        )


def boolean(
    array: RealArray, name: str, ignore: Optional[ignore] = None
) -> BooleanArray:
    """
    boolean  Checks that array elements are all 0s and 1s
    ----------
    boolean(array, name)
    Checks that the elements of the input numpy array are all 0s and 1s. Raises
    a ValueError if not. Note that this function *IS NOT* checking the dtype of the
    input array. Rather, it checks that each element is 0 or 1. Thus, array of
    floating points 0s and 1s (1.0, 0.0) will pass the test. If the array is valid,
    returns the array as a boolean dtype.

    boolean(..., ignore)
    Specifies data values to ignore. Elements matching these values will not be
    checked and will be set to False in the returned boolean array.
    ----------
    Inputs:
        array: The ndarray being validated
        name: A name for the array for use in error messages.
        ignore: A list of data values to ignore in the array

    Outputs:
        boolean numpy array: A copy of the array with a boolean dtype.

    Raises:
        ValueError: If the array's data elements have values that are neither 0 nor 1
    """

    # Boolean dtype is always valid. Otherwise, test the valid data elements.
    if array.dtype != bool:
        data, mask = _get_data(array, ignore)
        valid = np.isin(data, [0, 1])
        _check(valid, "0 or 1", array, name, mask)

    # Return boolean copy in which NoData values are False
    output = array.astype(bool, copy=True)
    if array.dtype != bool:
        mask.fill(output, False, invert=True)
    return output


def integers(array: RealArray, name: str, ignore: Optional[ignore] = None) -> None:
    """
    integers  Checks the elements of a numpy array are all integers
    ----------
    integers(array, name)
    Checks that the elements of the input numpy array are all integers. Raises a
    ValueError if not. Note that this function *IS NOT* checking the dtype of the
    input array. Rather it checks that each element is an integer. Thus, arrays
    of floating-point integers (e.g. 1.0, 2.000, -3.0) will pass the test.

    integers(..., ignore)
    Specifies data values to ignore. Elements matching these values will not
    be checked.
    ----------
    Inputs:
        array: The numeric ndarray being checked.
        name: A name of the input for use in error messages.
        ignore: A list of data values to ignore in the array

    Raises:
        ValueError: If the array's data elements contain non-integer values
    """

    # Integer and boolean dtype always pass. If not one of these, test the data elements
    if not istype(array.dtype, int_) and array.dtype != bool:
        data, mask = _get_data(array, ignore)
        _check_integers(data, name, array, mask)


def positive(
    array: RealArray,
    name: str,
    *,
    allow_zero: bool = False,
    ignore: Optional[ignore] = None,
) -> None:
    """
    positive  Checks the elements of a numpy array are all positive
    ----------
    positive(array, name)
    Checks that the data elements of the input numpy array are all greater than
    zero. Raises a ValueError if not.

    positive(..., *, allow_zero=True)
    Checks that elements are greater than or equal to zero.

    positive(..., *, ignore)
    Specifies data values to ignore. Elements matching these values will not
    be checked.
    ----------
    Inputs:
        array: The numeric ndarray being checked.
        name: A name for the input for use in error messages.
        allow_zero: Set to True to allow elements equal to zero.
            False (default) to only allow elements greater than zero.
        ignore: A list of data values to ignore in the array

    Raises:
        ValueError: If the array's data elements contain non-positive values
    """

    # If allowing zero, then unsigned integers and booleans are all valid.
    dtype = array.dtype
    always_valid = allow_zero and (istype(dtype, uint_) or dtype == bool)
    if not always_valid:
        # Otherwise, get the appropriate operator
        if allow_zero:
            operator = ">="
        else:
            operator = ">"

        # Validate the data elements
        data, mask = _get_data(array, ignore)
        _check_bound(data, name, operator, 0, array, mask)


def inrange(
    array: RealArray,
    name: str,
    min: Optional[scalar] = None,
    max: Optional[scalar] = None,
    ignore: Optional[ignore] = None,
) -> None:
    """
    inrange  Checks the elements of a numpy array are within a given range
    ----------
    inrange(array, name, min, max)
    Checks that the elements of a real-valued numpy array are all within a
    specified range. min and max are optional arguments, you can specify a single
    one to only check an upper or a lower bound. Use both to check elements are
    within a range. Uses an inclusive comparison (values equal to a bound will
    pass validation).

    inrange(..., ignore)
    Specifies data values to ignore. Elements matching these values will not
    be checked.
    ----------
    Inputs:
        array: The ndarray being checked
        name: The name of the array for use in error messages
        min: An optional lower bound (inclusive)
        max: An optional upper bound (inclusive)
        ignore: A list of data values to ignore in the array

    Raises:
        ValueError: If the array's data elements contain values not within the bounds
    """

    data, mask = _get_data(array, ignore)
    _check_bound(data, name, ">=", min, array, mask)
    _check_bound(data, name, "<=", max, array, mask)


def sorted(array: RealArray, name: str) -> None:
    """
    sorted  Checks that array values are sorted in ascending order
    ----------
    sorted(array, name)
    Checks that the elements of an array are sorted in ascending order. Raises a
    ValueError if not. Note that this function checks the flattened versions of
    N-dimensional arrays. Also, NaN values are treated as unknown, and so will
    not cause the validation to fail.
    ----------
    Inputs:
        array: The array being checked
        name: The name of the array for use in error messages

    Raises:
        ValueError: If array elements are not sorted in ascending order
    """

    if np.any(array[:-1] > array[1:]):
        raise ValueError(f"The elements of {name} must be sorted in increasing order.")


def flow(array: RealArray, name: str, ignore: Optional[ignore] = None) -> None:
    """
    flow  Checks that an array represents TauDEM-style D8 flow directions
    ----------
    flow(array, name)
    Checks that all elements of the input array are integers on the interval 1 to 8.
    Raises a ValueError if not.

    flow(..., ignore)
    Specifies data values to ignore. Elements matching these values will not
    be checked.
    ----------
    Inputs:
        array: The input array being checked
        name: A name for the array for use in error messages
        ignore: A list of data values to ignore in the array

    Raises:
        ValueError: If the array's data elements contain values that are not
            integer from 1 to 8
    """

    data, mask = _get_data(array, ignore)
    _check_bound(data, name, ">=", 1, array, mask)
    _check_bound(data, name, "<=", 8, array, mask)
    _check_integers(data, name, array, mask)


#####
# Raster metadata
#####


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

    # Allow 1 and 0 to pass for booleans
    if dtype == bool and (value == 1 or value == 0):
        return value.astype(bool)

    # Otherwise, check the casting
    elif not np.can_cast(value, dtype, casting):
        raise TypeError(
            f"Cannot cast {name} ({value}) to the raster dtype ({dtype}) "
            f"using '{casting}' casting."
        )
    else:
        return value.astype(dtype, casting=casting)


def crs(crs: Any) -> CRS:
    """
    crs  Checks that CRS is convertible to a rasterio.crs.CRS object
    ----------
    crs(crs)
    Checks that the input CRS is convertible to a rasterio.crs.CRS object. Raises
    a TypeError if not. If valid, returns the associated rasterio.crs.CRS object.
    ----------
    Inputs:
        crs: A user provided coordinate reference system

    Outputs:
        rasterio.crs.CRS: The validated CRS

    Raises:
        CrsError: If the CRS is not convertible to a rasterio CRS object
    """

    # Exit immediately if already a CRS
    if isinstance(crs, CRS):
        return crs

    # Otherwise, attempt to convert to CRS. Informative error if failed
    try:
        return CRS.from_user_input(crs)
    except RasterioCrsError:
        raise CrsError(
            "Unsupported CRS. A valid CRS must be be convertible to a rasterio.crs.CRS "
            "object via the rasterio API. See the rasterio documentation for examples "
            "of supported CRS inputs: https://rasterio.readthedocs.io/en/stable/index.html"
        )


def resolution(resolution: Any) -> VectorArray:
    """
    resolution  Checks that a raster resolution is valid
    ----------
    resolution(resolution)
    Checks that the input is either a scalar positive number, or a vector of 2
    positive numbers. If valid, returns the resolution as a vector of 2 numbers.
    ----------
    Inputs:
        resolution: The resolution being checked

    Outputs:
        numpy 1D array: Resolution as a 2 element vector
    """

    resolution = vector(resolution, "resolution", dtype=real)
    if resolution.size > 2:
        raise ShapeError("resolution may have either 1 or 2 elements")
    positive(resolution, "resolution")
    if resolution.size == 1:
        resolution = np.full((2,), resolution)
    return resolution


def transform(transform: Any) -> Affine:
    """
    transform  Checks that an input is convertible to an affine.Affine object
    ----------
    transform(transform)
    Checks that the input affine transformation is convertible to an affine.Affine
    object via the rasterio API. If so, checks that the affine matrix's b and d
    coefficients are 0. If valid, returns the affine.Affine object. Otherwise,
    raises a TransformError.
    ----------
    Inputs:
        transform: A user provided affine transformation

    Outputs:
        affine.Affine: The affine transformation

    Raises:
        TransformError: If the input is not convertible to an Affine object, or
            if the affine matrix has non-zero b and d coefficients
    """

    # Convert to Affine object
    try:
        affine = rasterio.transform.guard_transform(transform)
    except Exception:
        raise TransformError(
            "Unsupported transform. A valid transformation must be convertible to "
            "an affine.Affine object via the rasterio API. If problems persist, "
            "consider using an affine.Affine object directly as the transform."
        )

    # Check the coefficients are valid
    for coeff in ["a", "b", "c", "d", "e", "f"]:
        _check_affine(affine, coeff)
    _check_shear(affine, "b")
    _check_shear(affine, "d")
    return affine


def _check_affine(affine: Affine, coeff: str) -> None:
    value = getattr(affine, coeff)
    if not isinstance(value, float):
        raise TransformError(
            f"Transform coefficients must be floats, but coefficient '{coeff}' is not."
        )
    elif isnan(value):
        raise TransformError(
            f"Transform coefficients cannot be NaN, but coefficient '{coeff}' is NaN."
        )
    elif isinf(value):
        raise TransformError(
            f"Transform coefficients cannot be Inf, but coefficient '{coeff}' is Inf"
        )


def _check_shear(affine: Affine, coeff: str) -> None:
    value = getattr(affine, coeff)
    if value != 0:
        raise TransformError(
            "The raster transform must only support scaling and translation. "
            "Equivalently, the affine transformation matrix must have form:\n"
            "    |a b c|     |a 0 c|\n"
            "    |d e f|  =  |0 e f|\n"
            "    |0 0 1|     |0 0 0|\n"
            "such that coefficients b and d are 0. "
            f"However, coefficient '{coeff}' is not 0 (value = {value})."
        )


#####
# Paths
#####


def input_path(path: Any, name: str) -> Path:
    """
    input_path  Checks that an input path exists
    ----------
    input_path(path, name)
    Checks that an input path is a resolvable Path. Returns the resolved pathlib.Path.
    Raises a TypeError if not a Path, and a FileNotFoundError if not resolvable.
    ----------
    Inputs:
        path: A user provided path to an input file
        name: A name for the input path for use in error messages.

    Outputs:
        pathlib.Path: The resolved path to the file

    Raises:
        TypeError: If the input is not a string or Path
        FileNotFoundError: If the file does not exist.
    """

    if isinstance(path, str):
        path = Path(path)
    type(path, name, Path, "file path")
    return path.resolve(strict=True)


def output_path(path: Any, overwrite: bool) -> Path:
    """
    output_path  Checks that a path is suitable for an output file
    ----------
    output_path(path, overwrite)
    Checks that an input path is resolvable. Raises a FileExistsError if overwrite=False
    and the file already exists. Otherwise, returns the resolved pathlib.Path to the file.
    ----------
    Inputs:
        path: A user provided path for an output file
        overwrite: True if the file can already exist. False to raise an error
            for exists (i.e. prevent overwriting)

    Outputs:
        pathlib.Path: The resolved path to the output file

    Raises:
        FileExistsError: If the path exists and overwrite=False
    """

    path = Path(path).resolve()
    if (not overwrite) and path.exists():
        raise FileExistsError(
            f"Output file already exists:\n\t{path}\n"
            'If you want to replace existing files, set "overwrite=True"'
        )
    return path


#####
# Misc
#####


def type(input: Any, name: str, type: type, type_name: str) -> None:
    """
    type  Checks that the input is the indicated type
    ----------
    type(input, types)
    Checks that the input is the indicated type. Raises a TypeError if not.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages
        type: The required type for the input
        type_name: A name for the type for use in error messages
    """

    if not isinstance(input, type):
        raise TypeError(f"{name} must be a {type_name}")


def broadcastable(shape1: shape, name1: str, shape2: shape, name2: str) -> shape:
    """
    broadcastable  Checks that two array shapes can be broadcasted
    ----------
    broadcastable(shape1, name1, shape2, name2
    Checks that the input arrays have broadcastable shapes. Raises a ValueError
    if not. If the shapes are compatible, returns the broadcasted shape.
    ----------
    Inputs:
        shape1: The first shape being checked
        name1: The name of the array associated with shape1
        shape2: The second shape being checked
        name2: The name of the array associated with shape2

    Outputs:
        int tuple: The broadcasted shape

    Raises:
        ValueError  - If the arrays are not broadcastable
    """

    try:
        return np.broadcast_shapes(shape1, shape2)
    except ValueError:
        raise ValueError(
            f"The shape of the {name1} array ({shape1}) cannot be broadcasted "
            f"with the shape of the {name2} array ({shape2})."
        )


def option(input: Any, name: str, allowed: Sequence[str]) -> str:
    """
    option  Checks that an input string selects a recognized option
    ----------
    option(input, allowed)
    First checks that an input is a string (TypeError if not). Then, checks that
    the (case-insensitive) input belongs to a list of allowed options (ValueError
    if not). If valid, returns a lowercased version of the input.
    ----------
    Inputs:
        input: The input option being checked
        name: A name to identify the option in error messages
        allowed: A list of allowed strings

    Outputs:
        lowercased string: The lowercased version of the input

    Raises:
        TypeError: If the input is not a string
        ValueError: If the the lowercased string is not in the list of recognized options
    """

    type(input, name, str, "string")
    input_lowered = input.lower()
    if input_lowered not in allowed:
        allowed = ", ".join(allowed)
        raise ValueError(
            f"{name} ({input}) is not a recognized option. Supported options are: {allowed}"
        )
    return input_lowered


#####
# Element Utilities
#####


def _get_data(array: RealArray, ignore: ignore) -> tuple[RealArray, DataMask]:
    "Returns the data values and valid data mask for an array"
    mask = NodataMask(array, ignore, invert=True)
    values = mask.values(array)
    return values, mask


def _check_integers(
    data: RealArray, name: str, array: RealArray, mask: DataMask
) -> None:
    "Checks that elements are integers"
    isinteger = np.mod(data, 1) == 0
    _check(isinteger, "integers", array, name, mask)


def _check_bound(
    data: RealArray,
    name: str,
    operator: str,
    bound: scalar,
    array: RealArray,
    mask: DataMask,
) -> None:
    """
    _check_bound  Checks that elements of a numpy array are valid relative to a bound
    ----------
    _check_bound(data, name, operator, bound, array, mask)
    Checks that the elements of the input numpy array are valid relative to a
    bound. Valid comparisons are >, <, >=, and <=. Raises a ValueError if the
    criterion is not met.
    ----------
    Inputs:
        data: The data values being checked
        name: A name for the input for use in error messages
        operator: The comparison operator to apply. Options are '<', '>', '<=',
            and '>='. Elements must satisfy: (input operator bound) to be valid.
            For example, input < bound.
        bound: The bound being compared to the elements of the array.
        array: The complete array that the data values were extracted from
        mask: The valid data mask for the complete array.

    Raises:
        ValueError: If any element fails the comparison
    """

    # Only compare if bounds were specified. Get the comparison operator
    if bound is not None:
        if operator == "<":
            description = "less than"
            operator = np.less
        elif operator == "<=":
            description = "less than or equal to"
            operator = np.less_equal
        elif operator == ">=":
            description = "greater than or equal to"
            operator = np.greater_equal
        elif operator == ">":
            description = "greater than"
            operator = np.greater

        # Test the valid data elements.
        passed = operator(data, bound)
        _check(passed, f"{description} {bound}", array, name, mask)


def _check(
    passed: BooleanArray,
    description: str,
    array: RealArray,
    name: str,
    mask: DataMask,
) -> None:
    """Checks that all data elements passed a validation check. Raises a
    ValueError indicating the first failed element if not."""

    if not np.all(passed):
        index, value = _first_failure(passed, array, mask)
        raise ValueError(
            f"The data elements of {name} must be {description}, "
            f"but element {index} ({value=}) is not."
        )


def _first_failure(
    passed: BooleanArray, array: RealArray, mask: DataMask
) -> tuple[index, ScalarArray]:
    "Returns the index and data value of the first failed element"

    indices = mask.indices()
    first = np.argmin(passed)
    first = indices[first]
    first = np.unravel_index(first, array.shape)
    value = array[first]
    return aslist(first), value
