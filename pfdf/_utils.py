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
"""

from typing import Any, List, Tuple

from numpy import any as any_
from numpy import bool_, floating, integer, isnan

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
