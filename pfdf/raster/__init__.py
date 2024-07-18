"""
Manage and preprocess raster datasets
----------
This subpackage contains modules used to implement the Raster class, which is
used to manage raster datasets within pfdf.
----------
Rasters:
    Raster      - Class to manage raster datasets
    RasterInput - Type hint for inputs that can be converted to Raster objects

Internal:
    _validate   - Subpackage of modules used to validate inputs for Raster routines
    _align      - Functions used to align a reprojected raster to a target transform
    _clip       - Functions used to clip raster arrays
    _features   - Functions to process vector feature files
    _merror     - Functions used to supplement memory-related errors
    _raster     - Module implementing the Raster class
    _window     - Functions used to build rasterio windowing objects
"""

from pfdf.raster._raster import Raster, RasterInput
