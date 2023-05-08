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

from numpy import ndarray, integer, floating, array
import rasterio
from pathlib import Path
from typing import List, Any, Tuple, Optional, Union
from dfha.typing import RasterArray, ValidatedRaster, scalar


# Real-valued numpy dtypes
real = [integer, floating]


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


def load_raster(raster: ValidatedRaster, band: Optional[int] = 1) -> RasterArray:
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
    ----------
    Inputs:
        raster: The Path to a raster file or a raster as a 2D numpy array

    Outputs:
        numpy 2D array: The raster as a numpy.ndarray
    """
    if not isinstance(raster, ndarray):
        with rasterio.open(raster) as raster:
            raster = raster.read(band)
    return raster


def write_raster(
    raster: RasterArray, path: Path, nodata: Optional[scalar] = None
) -> Path:
    """
    write_raster  Writes a numpy array (raster) to a GeoTIFF file
    ----------
    write_raster(raster, path)
    Writes a 2D numpy array to a GeoTIFF file.

    write_raster(raster, path, nodata)
    Also specifies a nodata value for the raster. The nodata value is saved in
    the GeoTIFF metadata (rather than as a nodata mask).
    ----------
    Inputs:
        raster: A numpy 2D array. Should have an integer or floating dtype.
        path: The path to the file in which to write the raster
        nodata: A nodata value that should be saved in the GeoTIFF metadata.

    Saves:
        A GeoTIFF file matching the "path" input.
    """

    placeholder_transform = (0.03, 0, -4, 0, 0.03, -3)
    placeholder_crs = "+proj=latlon"
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
