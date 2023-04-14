"""
utils  Utility functions
----------
Type conversion:
    aslist      - Returns an input as a list
    astuple     - Returns an input as a tuple

Argument Parsing:
    any_defined - True if any input is not None

Rasters:
    load_raster
"""

import rasterio
from pathlib import Path
from typing import List, Any, Tuple, Optional
from dfha.typing import RasterArray


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


def load_raster(raster: Path, band: Optional[int] = 1) -> RasterArray:
    """
    load_raster  Loads a raster band from file
    ----------
    load_raster(raster)
    Uses rasterio to load the first band of the input raster. Returns the loaded
    data as a numpy.ndarray.

    load_raster(raster, band)
    Specifies a band of the raster to load. Default is the first band.
    ----------
    Inputs:
        raster: The Path to a raster file
        band: A raster band to read. Note that bands use 1-indexing. Default is
            the first band.

    Outputs:
        numpy 2D array: The loaded raster as a numpy.ndarray
    """
    with rasterio.open(raster) as raster:
        return raster.read(band)