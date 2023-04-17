"""
utils  Low-level utility functions used throughout the package
----------
Numpy dtypes:
    real        - A list of numpy dtypes considered to be real-valued numbers

Sequence conversion:
    aslist      - Returns an input as a list
    astuple     - Returns an input as a tuple

Argument Parsing:
    any_defined - True if any input is not None

Rasters:
    load_raster - Returns a pre-validated raster as a numpy array
"""

from numpy import ndarray, integer, floating
import rasterio
from pathlib import Path
from typing import List, Any, Tuple, Optional, Union
from dfha.typing import RasterArray


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


def load_raster(
    raster: Union[Path, RasterArray], band: Optional[int] = 1
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
    ----------
    Inputs:
        raster: The Path to a raster file or a raster as an numpy array

    Outputs:
        numpy 2D array: The raster as a numpy.ndarray
    """
    if not isinstance(raster, ndarray):
        with rasterio.open(raster) as raster:
            raster = raster.read(band)
    return raster
