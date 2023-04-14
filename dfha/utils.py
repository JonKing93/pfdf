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

from typing import List, Any, Tuple, Union
from dfha.typing import RasterArray
import rasterio
from pathlib import Path


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


def load_raster(raster: Path) -> RasterArray:
    """
    load_raster  Loads the first band of a raster from file
    ----------
    load_raster(raster)
    Uses rasterio to load the first band of a raster file. 




    Takes an input raster and returns it as a numpy array. This function is
    typically used in conjunction with validate.raster(..., load=False) and
    allows the developer to control when a validated raster is loaded into
    memory as a numpy array.

    Inputs may either be a pathlib.Path or a numpy array. If the raster is already
    a numpy array, it is returned back to the user. If a Path object, data is
    read from     
    
    
    
    The input
    raster should either be a Pathlib.path or a numpy array.
    
    
    """
