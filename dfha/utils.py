"""
utils  Low-level utilities used throughout the package
----------
This module provides a variety of low-level functions used throughout the package.
Broadly, these include functions for basic input parsing, raster IO, and functions
to help locate NoData elements.
----------
Misc:
    real            - A list of numpy dtypes considered to be real-valued numbers
    any_defined     - True if any input is not None

Sequence conversion:
    aslist          - Returns an input as a list
    astuple         - Returns an input as a tuple

Rasters:
    load_raster     - Returns a pre-validated raster as a numpy array
    save_raster     - Saves a 2D numpy array raster to a GeoTIFF file
    raster_shape    - Returns the shape of a file-based or numpy raster

NoData:
    data_mask       - Returns the data mask for a raster array
    nodata_mask     - Returns the NoData mask for a raster array
    isdata          - An alias for data_mask
    isnodata        - An alias for nodata_mask
"""

from numpy import ndarray, integer, floating, bool_, isnan
import rasterio
from warnings import simplefilter, catch_warnings
from pathlib import Path
from typing import List, Any, Tuple, Optional
from dfha.typing import (
    RasterArray,
    ValidatedRaster,
    scalar,
    RealArray,
    DataMask,
    nodata,
)


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
# Raster IO
#####


def load_raster(
    raster: ValidatedRaster,
    *,
    band: int = 1,
) -> RasterArray:
    """
    load_raster  Returns a raster as a numpy.ndarray
    ----------
    load_raster(raster)
    Returns the input raster as a numpy.ndarray, loading data into memory if
    given a raster file. This function is intended to be used in conjunction
    with the validate.raster function with the load=False option, and enables
    the loading of validated raster file at a later point. If given a numpy array,
    returns the array back as output. If given a file-based raster, uses rasterio to
    load the first band.

    load_raster(..., *, band)
    Loads the indicated raster band. The band option is ignored is the input is
    a numpy array.
    ----------
    Inputs:
        raster: The Path to a raster file or a raster as a 2D numpy array
        band: The raster band to load from file. Default is band 1.

    Outputs:
        numpy 2D array: The raster as a numpy.ndarray
    """

    # If not a numpy array, load from file. Temporarily suppress georef warning
    if not isinstance(raster, ndarray):
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
            with rasterio.open(raster) as file:
                raster = file.read(band)
    return raster


def save_raster(
    raster: RasterArray, path: Path, nodata: Optional[scalar] = None
) -> None:
    """
    save_raster  Saves a numpy array (raster) to a GeoTIFF file
    ----------
    save_raster(raster, path)
    Saves a 2D numpy array to the indicated GeoTIFF file. If the array is boolean,
    saves as an int8 dtype. Note that this function does not currently support
    geotransform options.

    save_raster(raster, path, nodata)
    Also specifies a nodata value for the raster. The nodata value is saved in
    the GeoTIFF metadata (rather than as a nodata mask).
    ----------
    Inputs:
        raster: A numpy 2D array. Should be an integer, floating, or boolean dtype
        path: The path to the file in which to write the raster
        nodata: A nodata value that should be saved in the GeoTIFF metadata.

    Saves:
        A GeoTIFF file matching the "path" input.
    """

    # Rasterio does not accept boolean dtype, so convert to int8 first
    if raster.dtype == bool:
        raster = raster.astype("int8")

    # Temporarily disable the NotGeoreferencedWarning. This should eventually be
    # replaced with functionality for crs and transform options.
    with catch_warnings():
        simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)

        # Save the raster
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=raster.shape[0],
            width=raster.shape[1],
            count=1,
            dtype=raster.dtype,
            nodata=nodata,
        ) as file:
            file.write(raster, 1)


def raster_shape(raster: ValidatedRaster):
    """
    raster_shape  Returns the 2D shape of a file-based or numpy raster
    ----------
    raster_shape(raster)
    Returns the 2D shape of a validated raster. Supports both file-based and
    numpy rasters.
    ----------
    Inputs:
        raster: The raster to return the shape of

    Outputs:
        (int, int): The 2D shape of the raster
    """

    if isinstance(raster, ndarray):
        return raster.shape
    else:
        with catch_warnings():
            simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
            with rasterio.open(raster) as raster:
                return (raster.height, raster.width)


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
