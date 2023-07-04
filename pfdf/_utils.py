"""
_utils  Low-level utilities used throughout the package
----------
This module provides a variety of low-level functions used throughout the package.
Broadly, these include functions for basic input parsing, and functions to help 
locate NoData elements.
----------
Misc:
    real            - A list of numpy dtypes considered to be real-valued numbers
    any_defined     - True if any input is not None

Sequence conversion:
    aslist          - Returns an input as a list
    astuple         - Returns an input as a tuple

NoData:
    data_mask       - Returns the data mask for a raster array
    nodata_mask     - Returns the NoData mask for a raster array
    isdata          - An alias for data_mask
    isnodata        - An alias for nodata_mask
    has_nodata      - True if an array contains NoData values
    default_nodata  - Returns a default NoData value for a dtype
"""

from typing import Any, List, Tuple

from numpy import any as any_
from numpy import bool_, floating, iinfo, integer, isnan, issubdtype, nan

from pfdf.typing import DataMask, RealArray, nodata

# Combination numpy dtypes
real = [integer, floating, bool_]


def any_defined(*args: Any) -> bool:
    "any_defined  True if any input is not None. Otherwise False."
    for arg in args:
        if arg is not None:
            return True
    return False


#####
# Sequences
#####


def aslist(input: Any) -> List:
    """
    aslist  Returns an input as a list
    ----------
    aslist(input)
    Returns the input as a list. If the input is a tuple, converts to a list. If
    the input is a list, returns it unchanged. Otherwise, places the input within
    a new list.
    """
    if isinstance(input, tuple):
        input = list(input)
    elif not isinstance(input, list):
        input = [input]
    return input


def astuple(input: Any) -> Tuple:
    """
    astuple  Returns an input as a tuple
    ----------
    astuple(input)
    Returns the input as a tuple. If the input is a list, converts to a tuple. If
    the input is a tuple, returns it unchanged. Otherwise, places the input within
    a new tuple.
    """
    if isinstance(input, list):
        input = tuple(input)
    elif not isinstance(input, tuple):
        input = (input,)
    return input


#####
# NoData
#####


def data_mask(raster: RealArray, nodata: nodata) -> DataMask:
    """
    data_mask  Returns the valid data mask for a raster
    ----------
    data_mask(raster, nodata)
    Given a NoData value, returns a mask that indicates the valid data elements
    in the raster. True values indicate a valid data element, False values indicate
    elements that are NoData. If the input NoData value is None, returns None,
    as no masking is necessary.
    ----------
    Inputs:
        raster: The raster whose valid data elements should be located
        nodata: A NoData value for the raster

    Outputs:
        boolean numpy array | None: The valid data elements in the array, or
            None if there is not a NoData value.
    """
    if nodata is None:
        return None
    elif isnan(nodata):
        return ~isnan(raster)
    else:
        return raster != nodata


def isdata(raster: RealArray, nodata: nodata) -> DataMask:
    "An alias for data mask"
    return data_mask(raster, nodata)


def nodata_mask(raster: RealArray, nodata: nodata) -> DataMask:
    """
    nodata_mask  Returns the NoData mask for a raster
    ----------
    data_mask(raster, nodata)
    Given a NoData value, returns a mask that indicates the NoData elements
    in the raster. True values indicate a NoData element, False values indicate
    valid data elements. If the input NoData value is None, returns None.
    ----------
    Inputs:
        raster: The raster whose valid data elements should be located
        nodata: A NoData value for the raster

    Outputs:
        boolean numpy array | None: The NoData elements in the array, or
            None if there is not a NoData value.
    """
    if nodata is None:
        return None
    elif isnan(nodata):
        return isnan(raster)
    else:
        return raster == nodata


def isnodata(raster: RealArray, nodata: nodata) -> DataMask:
    "An alias for nodata_mask"
    return nodata_mask(raster, nodata)


def has_nodata(array: RealArray, nodata: nodata) -> bool:
    """
    has_nodata  True if any elements of an array are NoData
    ----------
    has_nodata(array, nodata)
    True if nodata is not None and any elements of the array match the NoData
    values. Otherwise False.
    ----------
    Inputs:
        array: The array whose elements are being compared to NoData
        nodata: The NoData value

    Outputs:
        bool: Whether the array contains NoData values
    """

    if nodata is None:
        return False
    else:
        nodata = nodata_mask(array, nodata)
        return any_(nodata)


def default_nodata(dtype: type) -> nodata:
    """
    default_nodata  Returns a default NoData value based on dtype
    ----------
    default_nodata(dtype)
    Returns a default NoData value for the provided dtype. If a floating dtype,
    the default NoData is NaN. If an integer dtype, the NoData value is the minimum
    value supported by the dtype. If boolean, NoData is set to False.

    This function exists to support third-party libraries that expect a NoData
    value for raster datasets. For example, TauDEM will automatically set nodata=0
    when NoData is None. However, this is not desired as 0 is often a valid data
    value (for example, as a masked value in an upslope sum). This function
    circumvents those issues by providing a sensible default.
    ----------
    Inputs:
        dtype: The dtype whose default NoData value is being queried. Should be
            a floating, integer, or boolean dtype.

    Outputs:
        int | float | False: The NoData value for the dtype
    """
    if issubdtype(dtype, floating):
        return nan
    elif issubdtype(dtype, integer):
        return iinfo(dtype).min
    elif issubdtype(dtype, bool_):
        return False
