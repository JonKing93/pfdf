"""
validate  Functions that validate user inputs
----------
The validate module contains functions that check user inputs and raise exceptions
if the inputs are not valid. Some functions allow user inputs to be in multiple
different formats. When this is the case, the function will return the input in 
a standard format for internal processing. For example, the "raster"
function accepts both file paths and numpy 2D arrays, but will return the
validated raster as a numpy 2D array.

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

Loaded arrays:
    positive        - Checks that all elements are positive
    integers        - Checks that all elements are integers (NOT that the dtype is an int)
    inrange         - Checks that all elements are within a given range (inclusive)
    mask            - Checks that an array is boolean-like (all 1s and 0s)
    flow            - Checks that an array consists of TauDEM-style D8 flow directions

Rasters:
    raster          - Check that an input is a valid raster
    output_path     - Check that an input is a valid path for an output raster

Low-level:
    shape_          - Check that array shape is valid
    dtype_          - Checks that array dtype is valid
    nonsingleton    - Locate nonsingleton dimensions

Internal:
    _check_bound    - Compares the elements of an ndarray to a bound
"""

import numpy as np
from numpy import issubdtype as istype, unsignedinteger as uint_, integer as int_
from pathlib import Path
import rasterio
from warnings import catch_warnings, simplefilter
from dfha.utils import aslist, astuple, real, replace_nodata, data_mask
from dfha.errors import DimensionError, ShapeError
from typing import Any, Optional, List, Union, Tuple
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
    ValidatedRaster,
    MaskArray,
    BooleanArray,
    BooleanMask,
    nodata,
)

# Type aliases
RasterAndMask = Tuple[ValidatedRaster, BooleanMask]
OutputPath = Union[None, Path]
save = bool
DataMask = Union[None, BooleanArray]
index = Tuple[int, ...]


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
        indices = range(0, len(axes))
        for axis, index, required_, actual_ in zip(axes, indices, required, actual):
            if required_ != -1 and required_ != actual_:
                raise ShapeError(name, axis, index, required, actual)


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


#####
# Array shapes and types
#####


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


#####
# Rasters
#####


def raster(
    raster: Any,
    name: str,
    *,
    dtype: dtypes = real,
    shape: Optional[shape2d] = None,
    load: bool = True,
    numpy_nodata: Optional[scalar] = None,
    nodata_name: str = "nodata",
    nodata_to: Optional[scalar] = None,
    return_mask: bool = False,
) -> Union[ValidatedRaster, RasterAndMask]:
    """
    raster  Check input is valid raster and return in requested format
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
        * a numpy array dtype is not an integer, floating, or boolean dtype
        * the input is some other type

    raster(..., *, dtype)
    Requires the raster to be one of the specified dtypes. Default is to allow
    integer and floating dtypes. Raises a TypeError if the condition is not met.

    raster(..., *, shape)
    Require the raster to have the specified shape. Raises a ShapeError if this
    condition is not met.

    raster(..., *, load=False)
    Indicates that file-based rasters (those derived from a string, pathlib.Path,
    or rasterio.DatasetReader object) should not be loaded into memory after
    validating. If the input was a file-based raster, returns a pathlib.Path
    object for the validated raster file instead of a numpy array. Input numpy
    arrays are not affected and still return a numpy array.

    raster(..., *, numpy_nodata)
    Specifies a value to treat as NoData when the input raster is a numpy array.
    This option is typically combined with the "nodata_to" and/or "return_mask"
    options (see below).

    raster(..., *, nodata_to)
    Converts NoData values to the indicated value. If the input raster is file-based,
    determines the NoData value from the file metadata. If the input is a numpy
    array, determines the NoData value from the "numpy_nodata" option (if provided).
    This option is ignored if load=False, but see utils.load_raster for similar
    functionality.

    raster(..., *, return_mask=True)
    Also returns the NoData mask for the array. This option is ignored if load=False.
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

    # Note whether replacing nodata
    if nodata_to is None or load == False:
        replace = False
    else:
        replace = True

    # Convert str to Path
    if isinstance(raster, str):
        raster = Path(raster)

    # If Path, require file exists
    if isinstance(raster, Path):
        raster = raster.resolve(strict=True)
        isfile = True

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
        isfile = True

    # Anything else should be a numpy matrix. Validate this
    else:
        if not isinstance(raster, np.ndarray):
            raise TypeError(
                f"{name} is not a recognized raster type. Allowed types are: "
                "str, pathlib.Path, rasterio.DatasetReader, or numpy.ndarray"
            )
        raster = matrix(raster, name, shape=shape, dtype=dtype)
        isfile = False

    # Validate band 1 of file-based rasters
    if isfile:
        band = 1

        # Suppress georeferencing warnings
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)

            # Get file metadata, use to validate the raster
            with rasterio.open(raster) as file:
                dtype_(name, allowed=dtype, actual=file.dtypes[band - 1])
                if shape is not None:
                    shape_(
                        name,
                        ["rows", "columns"],
                        required=shape,
                        actual=(file.height, file.width),
                    )

                # Optionally load into memory.
                if load:
                    raster = file.read(band)

                # Get NoData values if needed
                if replace:
                    nodata = file.nodata

    # Validate NoData for numpy rasters
    elif replace:
        nodata = scalar(numpy_nodata, nodata_name, real)

    # Optionally replace nodata. Use copies of input numpy arrays
    if replace:
        copy = not isfile
        raster, mask = replace_nodata(raster, nodata, nodata_to, copy, return_mask)

    # Return raster and optionally NoData mask
    if return_mask:
        return raster, mask
    else:
        return raster


def output_path(path: Any, overwrite: bool) -> Tuple[OutputPath, save]:
    """
    output_path  Validate and parse options for an output raster path
    ----------
    output_path(path, overwrite)
    Validates the Path for an output raster. A valid path may either be None (for
    returning the raster directly as an array), or convertible to a Path object.
    Returns the Path to the output file (which may be None), and a bool indicating
    whether the output raster should be saved to file.

    When a file path is provided, ensures the output file ends with a ".tif"
    extension. Files ending with ".tif" or ".tiff" (case-insensitive) are given
    to a ".tif" extension. Otherwise, appends ".tif" to the end of the file name.

    If the file already exists and overwrite is set to False, raises a FileExistsError.
    ----------
    Inputs:
        path: The user-provided Path to an output raster.

    Outputs:
        (None|pathlib.Path, bool): A 2-tuple. First element is the Path for the
            output raster - this may be None if not saving. Second element
            indicates whether the output raster should be saved to file.

    Raises:
        FileExistsError: If the file exists and overwrite=False
    """

    # Note whether saving to file
    if path is None:
        save = False
    else:
        save = True

        # If saving, get an absolute Path
        path = Path(path).resolve()

        # Optionally prevent overwriting
        if not overwrite and path.is_file():
            raise FileExistsError(
                f"Output file already exists:\n\t{path}\n"
                'If you want to replace existing files, use the "overwrite" option.'
            )

        # Ensure a .tif extension
        extension = path.suffix
        if extension.lower() in [".tiff", ".tif"]:
            path = path.with_suffix(".tif")
        else:
            name = path.name + ".tif"
            path = path.with_name(name)
    return path, save


#####
# Loaded arrays
#####


def positive(
    array: RealArray,
    name: str,
    *,
    allow_zero: bool = False,
    isdata: Optional[BooleanArray] = None,
    nodata: Optional[scalar] = None,
) -> None:
    """
    positive  Checks the elements of a numpy array are all positive
    ----------
    positive(array, name)
    Checks that the data elements of the input numpy array are all greater than
    zero. Raises a ValueError if not.

    positive(..., *, allow_zero=True)
    Checks that elements are greater than or equal to zero.

    positive(..., *, isdata)
    Specifies which elements of the array to check. True elements of isdata are
    checked, False elements are not.

    positive(..., *, nodata)
    Specifies a NoData value for the array. Array elements matching this value
    are not checked. This option is ignored if "isdata" is also provided.
    ----------
    Inputs:
        array: The numeric ndarray being checked.
        name: A name for the input for use in error messages.
        allow_zero: Set to True to allow elements equal to zero.
            False (default) to only allow elements greater than zero.
        isdata: A valid data mask for the array. Only True elements are validated.
        nodata: A NoData value for the array

    Raises:
        ValueError: If the array contains negative elements
    """

    # If allowing zero, then unsigned integers and booleans are all valid.
    # Otherwise, get the valid data elements
    dtype = array.dtype
    skip = allow_zero and (istype(dtype, uint_) or array.dtype == bool)
    if not skip:
        data, isdata = _isdata(raster, isdata, nodata)

        # Get the appropriate operator and validate
        if allow_zero:
            operator = ">="
        else:
            operator = ">"
        _check_bound(data, name, isdata, operator, bound=0)


def integers(
    array: RealArray,
    name: str,
    *,
    isdata: Optional[BooleanArray] = None,
    nodata: Optional[scalar] = None,
) -> None:
    """
    integers  Checks the elements of a numpy array are all integers
    ----------
    integers(array, name)
    Checks that the elements of the input numpy array are all integers. Raises a
    ValueError if not.

    Note that this function *IS NOT* checking the dtype of the input array. Rather
    it checks that each element is an integer. Thus, arrays of floating-point
    integers (e.g. 1.0, 2.000, -3.0) will pass the test.

    integers(..., *, isdata)
    Specifies a valid data mask for the array. Only the True elements of the
    data mask will be validated.

    integers(..., *, nodata)
    Specifies a NoData value for the array. Elements matching the NoData value
    will not be checked. This option is ignored if "isdata" is also provided.
    ----------
    Inputs:
        array: The numeric ndarray being checked.
        name: A name of the input for use in error messages.
        isdata: A valid data mask for the array
        NoData: A NoData value for the array

    Raises:
        ValueError: If the array contains non-integer elements
    """

    # Integer and boolean dtype always pass. If not one of these, test the data elements
    if not istype(array.dtype, int_) and array.dtype != bool:
        data, isdata = _isdata(array, isdata, nodata)
        isinteger = np.mod(data, 1) == 0

        # Indicate first bad element if failed
        if not np.all(isinteger):
            index, value = _first_failure(array, isdata, isinteger)
            raise ValueError(
                f"The data elements of {name} must be integers, "
                f"but element {index} ({value}) is not."
            )


def inrange(
    array: RealArray,
    name: str,
    min: Optional[scalar] = None,
    max: Optional[scalar] = None,
    *,
    isdata: Optional[BooleanArray] = None,
    nodata: Optional[scalar] = None,
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

    inrange(..., *, isdata)
    Specifies a valid data mask for the array. Only the True elements of the
    data mask will be validated.

    inrange(..., *, nodata)
    Specifies a NoData value for the array. Array elements matching the NoData
    value will not be validated. This option is ignored if "isdata" is also provided.
    ----------
    Inputs:
        array: The ndarray being checked
        name: The name of the array for use in error messages
        min: An optional lower bound (inclusive)
        max: An optional upper bound (inclusive)
        isdata: A valid data mask for the array
        nodata: A NoData value for the array.

    Raises:
        ValueError: If any element is not within the bounds
    """

    isdata = _isdata(array, isdata, nodata)
    _check_bound(array, name, ">=", min, where=isdata)
    _check_bound(array, name, "<=", max, where=isdata)


def mask(
    array: BooleanArray,
    name: str,
    *,
    isdata: Optional[BooleanArray] = None,
    nodata: Optional[scalar] = None,
) -> BooleanArray:
    """
    mask  Validates a boolean-like mask
    ----------
    mask(array, name)
    Checks that the elements in an array are all 0 or 1. Raises a ValueError if
    not. If the array is valid, returns it as a boolean dtype.

    mask(..., *, isdata)
    Specifies a valid data mask for the array. Only the True elements of the
    mask are checked.

    mask(..., *, nodata)
    Specifies a NoData value for the array. Array elements matching this value
    are not checked. This option is ignored if "isdata" is also provided.
    ----------
    Inputs:
        array: The ndarray being validated
        name: A name for the array for use in error messages.
        isdata: A valid data mask for the array.
        nodata: A NoData value for the array.

    Outputs:
        boolean numpy array: The mask array with a boolean dtype.
    """

    # Boolean dtype is always valid. Otherwise, get the valid data mask
    if array.dtype != bool:
        data, isdata = _isdata(array, isdata, nodata)

        # Validate
        invalid = np.isin()
        valid = np.isin(array[isdata], [0, 1])
        if not np.all(valid):
            raise ValueError(f"The data elements of {name} must all be 0 or 1.")

    # Always return as a boolean array
    return array.astype(bool)


def flow(
    array: RealArray,
    name: str,
    *,
    isdata: Optional[BooleanArray],
    nodata: Optional[scalar],
):
    """
    flow  Checks that an array represents TauDEM-style D8 flow directions
    ----------
    flow(array, name)
    Checks that all elements of the input array are integers on the interval 1 to 8.
    Raises a ValueError if not.

    flow(..., *, isdata)
    Specifies a valid data mask for the array. Only the True elements of the
    valid data mask are checked.

    flow(..., *, nodata)
    Specifies a NoData value for the array. Array elements matching the NoData
    value are not checked. This option is ignored if "isdata" is also provided.
    ----------
    Inputs:
        array: The input array being checked
        name: A name for the array for use in error messages
        isdata: A valid data mask for the array
        nodata: A NoData value for the array

    Raises:
    """

    isdata = _isdata(array, isdata, flow)
    integers(array, name, isdata=isdata)
    inrange(array, name, min=1, max=8, isdata=isdata)


#####
# Loaded Array Utilities
#####


def _check_bound(
    array: RealArray,
    name: str,
    isdata: DataMask,
    operator: str,
    bound: scalar,
) -> None:
    """
    _check_bound  Checks that elements of a numpy array are valid relative to a bound
    ----------
    _check_bound(array, name, isdata, operator, bound)
    Checks that the elements of the input numpy array are valid relative to a
    bound. Valid comparisons are >, <, >=, and <=. Raises a ValueError if the
    criterion is not met.
    ----------
    Inputs:
        array: The input being checked
        name: A name for the input for use in error messages
        isdata: The valid data mask for the array.
        operator: The comparison operator to apply. Options are '<', '>', '<=',
            and '>='. Elements must satisfy: (input operator bound) to be valid.
            For example, input < bound.
        bound: The bound being compared to the elements of the array.

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
        data, isdata = _isdata(array, isdata, None)
        passed = operator(data, bound)

        # Indicate first bad element if failed
        if not np.all(passed):
            index, value = _first_failure(array, isdata, passed)
            raise ValueError(
                f"The data elements of {name} must be {description} {bound}, "
                f"but element {index} ({value}) is not."
            )


def _isdata(
    array: RealArray, isdata: BooleanArray, nodata: nodata
) -> Tuple[RealArray, DataMask]:
    """
    _isdata  Locate and return valid data elements in an array
    ----------
    _isdata(array, isdata, nodata)
    Parses "isdata" and "nodata" options to locate the valid data elements in an
    array. Returns two outputs: the first is a numpy array holding only the valid
    data elements from the input array. The second output is the valid data mask
    for the input array.

    If both isdata and nodata are None, then all array elements are treated as
    valid. The output valid data mask will be None, since no masking is necessary.
    If isdata is provided, it is used directly as the valid data mask. If only
    a nodata option is provided, builds the valid data mask by checking if array
    elements match the NoData value.
    ----------
    Inputs:
        array: The array whose valid data elements should be located
        isdata: A pre-existing valid data mask. None if this has not been built.
        nodata: A NoData value for the array. None if not provided.

    Outputs:
        numpy array: The valid data elements of the array
        None | numpy boolean array: The isdata mask for the input array
    """

    if isdata is None:
        if nodata is None:
            return array, None
        else:
            isdata = data_mask(raster, nodata)
    return array[isdata], isdata


def _first_failure(
    array: RealArray,
    isdata: DataMask,
    passed: Optional[BooleanArray] = None,
) -> Tuple[index, scalar]:
    """
    _first_failure  Returns the indices and value of the first invalid data element
    ----------
    _first_failure(array, isdata, passed)
    Given an array, valid data mask, and results of a validation check (see below)
    locates the index of the first invalid data element in the full array. Returns the
    index and associated value.

    The "passed" option should be a boolean array indicating which data elements
    (i.e. elements that are not NoData) passed the validation check. As such, the
    size of this array is often smaller than the size of the "array" input.
    ----------
    Inputs:
        array: An input array that failed a validation check
        isdata: The valid data mask for the array
        passed: A logical array indicating which data elements of the array passed
            the validation check

    Outputs:
        Tuple[int, ...]: The index of the first invalid data element in the array
        int | float | bool: The value of the invalid data element
    """

    # Get the indices of valid data elements within the array
    data_indices = np.arange(0, array.size)
    if isdata is not None:
        isdata = isdata.reshape(-1)
        data_indices = data_indices[isdata]

    # Locate the first failure within the set of data elements. Then locate
    # this data element with the full array and return the associated value.
    first = np.argmin(passed)
    first = data_indices[first]
    first = np.unravel_index(first, array.shape)
    return first, array[first]
