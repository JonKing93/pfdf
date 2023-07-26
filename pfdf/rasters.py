"""
rasters  Classes to facilitate working with rasters
----------
The rasters module provides the Raster class, which allows users to more 
easily use numpy arrays as raster datasets. Specifically, the class allows users
to tag numpy arrays with raster metadata (such as NoData values). Please see the
documentation of the Raster class for details.

Additionally, this module provides several type hints derived from Rasters.
----------
Classes:
    Raster          - Adds raster metadata values to a numpy array

Type Hints:
    RasterInput     - A raster dataset used as input to a pfdf routine
    RasterOutput    - An output raster produced by a pfdf routine
"""

from pathlib import Path
from typing import Optional, Union

import rasterio

from pfdf import _validate as validate
from pfdf._utils import real
from pfdf.typing import RasterArray, nodata, scalar, shape2d


class Raster:
    """
    Raster  Adds raster metadata values to numpy arrays
    ----------
    The Raster class allows users to associate metadata values with rasters
    represented by numpy arrays. These objects can then be passed as input to
    commands in the pfdf package. Currently, the class supports raster NoData values.

    To use the class, call "Raster" on a 2D real-valued numpy array that
    represents a raster dataset. The "nodata" option allows you to associate a
    NoData value with the dataset.

    You can use the ".array" property to return the numpy array associated with
    the object. Note that changing the original array will alter the array values
    reported by the object.

    You can use the ".nodata" property to return the NoData value that the package
    will use for the raster. Note that this value may differ from the NoData value
    used to initialize the NumpyRaster object, because the object will convert the
    input NoData value to the same dtype as the numpy array.
    ----------
    Methods:
        __init__    - Creates a new NumpyRaster object

    Properties:
        array       - The array representing the raster
        shape       - The shape of the raster
        dtype       - The dtype of the raster
        nodata      - The NoData value for the raster
    """

    """
    Internal Properties:
        _array:
        _nodata
    """

    def __init__(self, raster: RasterArray, *, nodata: Optional[scalar] = None) -> None:
        """
        __init__  Returns a new Raster object
        ----------
        Raster(raster)
        Creates a Raster object from a 2D numpy array. Sets the NoData value
        to None.

        Raster(raster, *, nodata)
        Specifies a NoData value for the numpy array raster. The input NoData
        value will be converted to the same dtype as the array.
        ----------
        Inputs:
            raster: A 2D numpy array representing a raster dataset
            nodata: A NoData value for the raster

        Outputs:
            Raster: The new Raster object

        """
        self._array = validate.matrix(raster, "input raster", dtype=real)
        if nodata is not None:
            nodata = validate.scalar(nodata, "nodata", dtype=real)
            nodata = nodata.astype(self.dtype)
        self._nodata = nodata

    @property
    def array(self) -> RasterArray:
        "The array representing the raster"
        return self._array

    @property
    def shape(self) -> shape2d:
        "The shape of the raster (nRows, nCols)"
        return self._array.shape

    @property
    def dtype(self) -> type:
        "The numpy dtype of the raster"
        return self._array.dtype

    @property
    def nodata(self) -> nodata:
        return self._nodata


# Raster type aliases
RasterInput = Union[str, Path, rasterio.DatasetReader, RasterArray, Raster]
RasterOutput = Union[Path, Raster]
