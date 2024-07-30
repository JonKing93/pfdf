"""
Functions used to validate user inputs to Raster routines
----------
Misc:
    type            - Checks input has the specified type
    option          - Checks input is a recognized string option
    units           - Checks units are supported

Paths:
    input_path      - Checks input is a path to an existing file
    output_path     - Checks output is a path, and optionally prevents overwriting

Array Shape and Type:
    array           - Checks an input represents a numpy array
    scalar          - Checks input represents a scalar
    matrix          - Checks input represents a matrix

Array Elements:
    defined         - Checks elements are not NaN
    finite          - Checks elements are neither infinite nor NaN
    boolean         - Checks elements are all 1s and 0s

Features:
    resolution          - Checks that raster resolution represents two positive values
    field               - Checks that field can be used to build the raster
    resolution_units    - Checks that resolution units can be converted to base units
    geometry            - Checks a feature geometry is valid
    point               - Checks a point coordinate array is valid
    polygon             - Checks a polygon coordinate array is valid

Metadata
    casting     - Checks that a casting rule is recognized
    nodata      - Checks that a nodata value is valid and castable
    crs         - Checks input represents a pyproj.CRS
    bounds      - Checks input represents a BoundingBox object
    transform   - Checks input represents a Transform object
    spatial     - Checks that CRS and Transform are valid
    metadata    - Checks CRS, Transform, and NoData value

Preprocessing:
    resampling  - Validates a resampling option
    data_bound  - Checks that a data bound is castable, or provides a default if missing

Internal Modules:
    _features   - Functions to validate vector feature inputs
    _metadata   - Functions to validate raster metadata
    _preprocess - Functions to validate preprocessing inputs
"""

from pfdf._validate import (
    array,
    boolean,
    buffers,
    defined,
    finite,
    input_path,
    matrix,
    option,
    output_path,
    scalar,
    type,
    units,
)
from pfdf.raster._validate._features import (
    field,
    geometry,
    point,
    polygon,
    resolution,
    resolution_units,
)
from pfdf.raster._validate._metadata import (
    bounds,
    casting,
    crs,
    metadata,
    nodata,
    spatial,
    transform,
)
from pfdf.raster._validate._preprocess import data_bound, resampling
