"""
Functions to check the values of array elements
----------
Elements:
    defined     - Checks elements are not NaN
    finite      - Checks elements are neither infinite nor NaN
    boolean     - Checks elements are all 1s and 0s
    integers    - Checks elements are all integers
    positive    - Checks elements are all positive
    inrange     - Checks elements are all within a valid data range
    sorted      - Checks elements are in sorted order
    flow        - Checks elements represents TauDEM-style flow directions (integers 1 to 8)

Utilities:
    _get_data       - Returns the data elements and data mask for an array
    _check_integers - Checks that elements are integers
    _check_bound    - Checks that elements have a comparison relationship with a bound
    _check          - Checks that elements passed a validation check
    _first_failure  - Returns the index and value of the first failed element
"""

from __future__ import annotations

import typing

import numpy as np
from numpy import integer, issubdtype, unsignedinteger

from pfdf._utils import aslist
from pfdf._utils.nodata import NodataMask

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import BooleanArray, RealArray, ScalarArray, ignore, scalar

    index = tuple[int, ...]
    DataMask = NodataMask  # More clear for when invert=True


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

    defined = ~np.isnan(array)
    if not np.all(defined):
        index, _ = _first_failure(defined, array)
        raise ValueError(
            f"{name} cannot contain NaN elements, but element {index} is NaN."
        )


def finite(array, name):
    finite = np.isfinite(array)
    if not np.all(finite):
        index, value = _first_failure(finite, array)
        raise ValueError(
            f"{name} can only contain finite elements, "
            f"but element {index} (value={value}) is not finite."
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
    if not issubdtype(array.dtype, integer) and array.dtype != bool:
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
    always_valid = allow_zero and (issubdtype(dtype, unsignedinteger) or dtype == bool)
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
    passed: BooleanArray,
    array: RealArray = None,
    mask: Optional[DataMask] = None,
) -> tuple[index, ScalarArray]:
    "Returns the index and data value of the first failed element"

    # Get data indices
    if mask is None:
        indices = np.arange(array.size)
    else:
        indices = mask.indices()

    # Locate the index and value of the first failed element
    first = np.argmin(passed)
    first = indices[first]
    first = np.unravel_index(first, array.shape)
    return aslist(first), array[first]
