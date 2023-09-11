"""
nodata_  Functions that facilitate working with NoData values in raster datasets
----------
Functions:
    default     - Returns the default NoData value for a dtype
    fill        - Fills indicated array elements with a NoData value
    isin        - True if an array contains NoData elements
    mask        - Returns the NoData mask or valid data mask for a raster
"""

from numpy import any as any_
from numpy import bool_, floating, iinfo, integer, isnan, issubdtype, nan

from pfdf.typing import DataMask, RealArray, nodata


def default(dtype: type) -> int | float | bool:
    """
    default  Returns the default NoData value for a dtype
    ----------
    default(dtype)
    Returns the default NoData value for the provided dtype. If a floating dtype,
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


def fill(array: RealArray, masks: tuple[DataMask], nodata: nodata) -> RealArray:
    """
    fill  Replaces the indicated elements of an array with a NoData value
    ----------
    fill(array, masks, nodata)
    Fills indicated elements of an array with a NoData value. Elements are indicated
    using the "masks" input, which is a tuple of NoData masks. True elements
    indicate the array elements that should be replaced by the nodata value. False
    elements will not be altered. Mask elements are assessed using logical "or",
    so if an array element is True in any mask, then it will be set to NoData.
    ----------
    Inputs:
        array: The array which will have elements replaced with NoData
        masks: A tuple of NoData masks associated with the array.
        nodata: The NoData value for the array

    Outputs:
        numpy array: The array whose elements have been replaced with NoData
    """

    # Get the final mask
    nodatas = None
    for mask in masks:
        if (mask is not None) and (nodatas is None):
            nodatas = mask
        elif mask is not None:
            nodatas = nodatas | mask

    # Fill the array with NoDatas
    if nodatas is not None:
        array[nodatas] = nodata
    return array


def isin(array: RealArray, nodata: nodata) -> bool:
    """
    isin  True if any elements of an array are NoData
    ----------
    isin(array, nodata)
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
        nodata = mask(array, nodata)
        return any_(nodata)


def mask(array: RealArray, nodata: nodata, invert: bool = False) -> DataMask:
    """
    mask  Returns the NoData or valid data mask for an array
    ----------
    mask(array, nodata)
    Given a NoData value, returns a mask that indicates the valid data elements
    in the array. True values indicate a NoData value. False values indicate
    valid data elements. If the NoData value is None, returns None.

    mask(array, nodata, invert=True)
    Returns the valid data mask for the array. True values indicate valid data
    elements. False values indicate NoData values.
    ----------
    Inputs:
        array: The array whose valid data elements should be located
        nodata: A NoData value for the array
        invert: False (default) to return the NoData mask. True to return the
            valid data mask

    Outputs:
        boolean numpy array | None: The valid data elements in the array, or
            None if the NoData value is None.
    """

    if nodata is None:
        return None
    elif isnan(nodata) and invert:
        return ~isnan(array)
    elif isnan(nodata):
        return isnan(array)
    elif invert:
        return array != nodata
    else:
        return array == nodata
