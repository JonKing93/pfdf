"""
Utilities for working with NoData values
----------
This module contains several helper functions for working with NoData values.
The "default" function returns the default NoData for a dtype, and the "mask"
function returns the NoData/data mask for an array.
----------
Functions:
    default - Returns the default NoData value for a dtype
    mask    - Returns the NoData/data mask for an array
"""

import numpy as np
from numpy import floating, issubdtype, signedinteger, unsignedinteger

import pfdf._utils.nodata as _nodata
import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.typing import BooleanArray, RealArray, scalar


def default(dtype: type):
    """
    Returns the default NoData value for a numpy dtype
    ----------
    default(dtype)
    Returns the default NoData value for the queried dtype. Returns NaN for floats,
    the lower bound for signed integers, upper bound for unsigned integers, False
    for bool, and None for anything else.
    ----------
    Inputs:
        dtype: The dtype whose default NoData will be returned

    Outputs:
        nan | int | False | None: The default NoData value for the dtype
    """

    if issubdtype(dtype, floating):
        return np.nan
    elif issubdtype(dtype, signedinteger):
        return np.iinfo(dtype).min
    elif issubdtype(dtype, unsignedinteger):
        return np.iinfo(dtype).max
    elif issubdtype(dtype, bool):
        return False
    else:
        return None


def mask(array: RealArray, nodata: scalar, invert: bool = False) -> BooleanArray:
    """
    Returns the NoData mask or data mask for an array
    ----------
    mask(array, nodata)
    Returns the NoData mask for the array. The mask will be a boolean array with
    the same shape as the input array. True elements indicate NoData values,
    and False elements indicate data elements.

    mask(array, nodata, invert=True)
    Returns the data mask for the array. True elements indicate data values, and
    False elements indicate NoData values.
    ----------
    Inputs:
        array: The array whose mask should be returned
        nodata: The nodata value for the array
        invert: True to return the data mask for the array. False (default) to
            return the NoData mask.

    Outputs:
        boolean numpy array: The NoData or data mask for the array
    """

    # Validate array and nodata
    array = validate.array(array, "array", dtype=real)
    if nodata is not None:
        nodata = validate.scalar(nodata, "nodata", dtype=real)

    # Get the mask, invert as needed
    mask = _nodata.mask(array, nodata)
    if invert:
        mask = ~mask
    return mask
