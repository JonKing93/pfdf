"""
utils  Low-level utility functions used throughout the package
----------
Numpy dtypes:
    real            - A list of numpy dtypes considered to be real-valued numbers

Sequence conversion:
    aslist          - Returns an input as a list
    astuple         - Returns an input as a tuple

Argument Parsing:
    any_defined     - True if any input is not None

Rasters:
    load_raster     - Returns a pre-validated raster as a numpy array
    write_raster    - Writes a 2D numpy array (raster) to a GeoTIFF file
"""

from numpy import ndarray, integer, floating, bool_, isnan, nan
import rasterio
from pathlib import Path
from typing import List, Any, Tuple, Optional, Union
from dfha.typing import RealArray, RasterArray, ValidatedRaster, scalar


# Combination numpy dtypes
real = [integer, floating]
mask = [integer, floating, bool_]


def any_defined(*args: Any) -> bool:
    "any_defined  True if any input is not None. Otherwise False."
    for arg in args:
        if arg is not None:
            return True
    return False


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


def load_raster(
        raster: ValidatedRaster,
        *,
        band: int = 1,
        nodata_to: Optional[scalar] = None
    ) -> RasterArray:
    """
    load_raster  Returns a raster as a numpy.ndarray
    ----------
    load_raster(raster)
    Returns the input raster as a numpy.ndarray, loading data into memory if
    given a raster file. This function is intended to be used in conjunction
    with the validate.raster function with the load=False option, and enables
    the loading of validated raster file at a later point. If given a numpy array,
    returns the array back as output. If given a raster Path, uses rasterio to
    load the first band.

    load_raster(raster, *, band)
    Loads the indicated raster band. The band option is ignored is the input is
    a numpy array.

    load_raster(..., *, nodata_to)
    Converts NoData values to the indicated value. This option is ignored if the
    input is a numpy array.
    ----------
    Inputs:
        raster: The Path to a raster file or a raster as a 2D numpy array
        band: The raster band to load from file. Default is band 1.
        nodata_to: The value to which NoData values will be converted

    Outputs:
        numpy 2D array: The raster as a numpy.ndarray
    """

    if not isinstance(raster, ndarray):
        with rasterio.open(raster) as file:
            raster = file.read(band)
            if nodata_to is not None:
                replace_nodata(raster, file.nodata, nodata_to)
    return raster


def replace_nodata(array: RealArray, nodata: Union[None, scalar], value: scalar) -> None:
    """
    replace_nodata  Replaces NoData values in a numpy array
    ----------
    replace_nodata(array, nodata, value)
    Given a numpy array, replaces NoData values with the indicated value.
    ----------
    Inputs:
        raster: A numpy array raster
        nodata: The current NoData value
        value: The value that NoData should be replaced with
    """
    if nodata is not None:
        if isnan(nodata):
            nodata = isnan(array)
        else:
            nodata = array == nodata
        array[nodata] = value


def save_raster(
    raster: RasterArray, path: Path, nodata: Optional[scalar] = None
) -> None:
    """
    save_raster  Saves a numpy array (raster) to a GeoTIFF file
    ----------
    save_raster(raster, path)
    Saves a 2D numpy array to the indicated GeoTIFF file. If the array is boolean,
    saves as an int8 dtype.

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

    # Use a placeholder until the package supports projections
    placeholder_transform = (0.03, 0, -4, 0, 0.03, -3)
    placeholder_crs = "+proj=latlon"

    # Rasterio does not accept boolean dtype, so convert to (equivalent) int8
    if raster.dtype==bool:
        raster = raster.astype('int8')

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
        transform=placeholder_transform,
        crs=placeholder_crs,
    ) as file:
        file.write(raster, 1)
