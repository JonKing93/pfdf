"""
Utilites for building rasters from vector feature files.
----------
Functions:
    parse_file  - Validates a feature file and computes values for raster creation

Internal modules:
    _bounds     - Utility functions to determine the bounds of the raster
    _features   - Functions to validate and read feature geometries and values
    _ffile      - Context manager class for opening vector feature files
    _main       - Module implementing the "parse_file" function
    _parse      - Functions that parse raster metadata from a feature file
    _validate   - Functions to validate options used to build rasters from features
"""

from pfdf.raster._features._main import parse_file
