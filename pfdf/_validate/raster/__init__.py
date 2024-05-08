"""
Functions used to validate user inputs to Raster routines
----------
Misc:
    type            - Checks input has the specified type
    option          - Checks input is a recognized string option

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

Preprocessing:
    resampling  - Checks that a resampling algorithm is valid
    bound       - Checks that a bound is castable, or provides a default if missing
    resolution  - Checks that raster resolution represents two positive values

Raster Metadata:
    casting     - Checks that a casting rule is recognized
    nodata      - Checks that a nodata value is valid and castable
    crs         - Checks input represents a pyproj.CRS
    transform   - Checks input represents a Transform object
    bounds      - Checks input represents a BoundingBox object
    spatial     - Checks that CRS and Transform are valid
    metadata    - Checks CRS, Transform, and NoData value
    feature_options - Checks that resolution and bounds are valid
"""

from pfdf._validate.core import (
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
)
from pfdf._validate.raster._preprocess import (
    bounds,
    casting,
    crs,
    data_bound,
    feature_options,
    metadata,
    nodata,
    resampling,
    resolution,
    spatial,
    transform,
)
