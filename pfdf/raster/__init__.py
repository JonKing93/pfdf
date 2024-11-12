"""
Manage and preprocess raster datasets
----------
This package contains modules that implement the Raster and RasterMetadata classes,
which are used to manage raster datasets within pfdf.
----------
Classes:
    Raster          - Class to manage raster datasets
    RasterMetadata  - Class to manage raster metadata

Internal modules:
    _raster         - Module implementing the Raster class
    _metadata       - Module implementing the RasterMetadata class

Internal subpackages:
    _features       - Modules to process vector feature files
    _utils          - Utility modules used throughout the package
"""

from pfdf.raster._metadata import RasterMetadata
from pfdf.raster._raster import Raster
