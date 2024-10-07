"""
Manage and preprocess raster datasets
----------
This subpackage contains modules used to implement the Raster class, which is
used to manage raster datasets within pfdf.
----------
Rasters:
    Raster      - Class to manage raster datasets

Internal Subpackages:
    _features   - Subpackage to process vector feature files

Internal Modules:
    _align      - Functions used to align a reprojected raster to a target transform
    _clip       - Functions used to clip raster arrays
    _merror     - Functions used to supplement memory-related errors
    _parse      - Functions that parse spatial metadata options
    _raster     - Module implementing the Raster class
    _validate   - Functions to validate inputs for Raster routines
    _window     - Functions used to build rasterio windowing objects
"""

from pfdf.raster._raster import Raster
