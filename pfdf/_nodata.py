"""
_nodata  Functions that facilitate working with NoData values in raster datasets
----------
Functions:
    default     - Returns the default NoData value for a dtype
    mask        - Returns the NoData mask or valid data mask for a raster
    isin        - True if an array contains NoData elements
"""

from typing import Union

from numpy import any as any_
from numpy import bool_, floating, iinfo, integer, isnan, issubdtype, nan

from pfdf.typing import DataMask, RealArray, nodata


def default(dtype: type) -> Union[int, float, bool]:
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


def mask(raster: RealArray, nodata: nodata, invert: bool = False) -> DataMask:
    """
    mask  Returns the NoData or valid data mask for a raster
    ----------
    mask(raster, nodata)
    Given a NoData value, returns a mask that indicates the valid data elements
    in the raster. True values indicate a NoData value. False values indicate
    valid data elements. If the NoData value is None, returns None.

    mask(raster, nodata, invert=True)
    Returns the valid data mask for the raster. True values indicate valid data
    elements. False values indicate NoData values.
    ----------
    Inputs:
        raster: The raster whose valid data elements should be located
        nodata: A NoData value for the raster
        invert: False (default) to return the NoData mask. True to return the
            valid data mask

    Outputs:
        boolean numpy array | None: The valid data elements in the array, or
            None if the NoData value is None.
    """

    if nodata is None:
        return None
    elif isnan(nodata) and invert:
        return ~isnan(raster)
    elif isnan(nodata):
        return isnan(raster)
    elif invert:
        return raster != nodata
    else:
        return raster == nodata


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
