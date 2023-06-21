"""
typing  Type aliases for the post-wildfire debris-flow package
----------
The typing module contains various type aliases used throughout the package.
Note that this module does not provide *every* type alias used within the package.
Rather, it provides common aliases that are used in multiple modules. As such,
individual modules may still define aliases unique to their implementations.

nptyping Primer:
    Many of these type aliases are derived from the nptyping package, which
    provides enhanced type hints for numpy arrays. Specifically, the package allows
    type hints to indicate the shape and dtype of a numpy array. These are
    indicated via the syntax: NDArray[Shape[...], Dtype]
    Shapes are usually expressed as a comma-separated list of dimensions.
    Dimensions may be represented as "<Dimension Name>" for a dimension of
    unspecified size (for example, "Rows"). Or as "<N> <label>" for a dimension
    of specific length (for example, "2 columns").

    In this package, all user-facing functions that operate on numpy arrays 
    allow float, int, and boolean dtypes. Unfortunately, there is currently no 
    good way to indicate this combination of types, so we use the following 
    conventions:

    * An array typed with a float dtype is a numeric dataset - typically a raster
      of some sort. Although only the float dtype is listed, the array may also
      be an integer or boolean dtype.

    * An array typed with a boolean dtype is usually a data mask - such as a
      valid-data/NoData mask. A boolean dtype is preferred, but the function
      will also accept float and integer dtypes, so long as all valid
      data elements are either 1 or 0.
"""

from pathlib import Path
from typing import Any, Dict, Sequence, Tuple, Union

from nptyping import Bool, Floating, Integer, NDArray, Shape
from rasterio import DatasetReader

# Singular / plural
strs = Union[str, Sequence[str]]
ints = Union[int, Sequence[int]]
floats = Union[float, Sequence[float]]
dtypes = Union[type, Sequence[type]]

# Paths
Pathlike = Union[str, Path]
Pathdict = Dict[str, Path]

# Inputs that are literally shapes
shape = ints
shape2d = Tuple[int, int]

# Generic array shapes
Scalar_Shape = Shape["1"]
Vector_Shape = Shape["Elements"]
Matrix_Shape = Shape["Rows, Columns"]

# Generic real-valued arrays
Real_Array = NDArray[Any, Floating]
Scalar_Array = NDArray[Scalar_Shape, Floating]
Vector_Array = NDArray[Vector_Shape, Floating]
Matrix_Array = NDArray[Matrix_Shape, Floating]

# Real-valued array inputs
scalar = Union[int, float, Scalar_Array]
vector = Union[ints, floats, Vector_Array]
matrix = Union[ints, floats, Matrix_Array]

# Rasters
Raster_Array = Matrix_Array  # alias for clarity
Raster = Union[str, Path, DatasetReader, Raster_Array]
Validated_Raster = Union[Path, Raster_Array]
Output_Raster = Union[Path, Raster_Array]

# Generic Masks
Mask = Union[  # This is for user-provided masks
    NDArray[Matrix_Shape, Integer],
    NDArray[Matrix_Shape, Floating],
    NDArray[Matrix_Shape, Bool],
]
Boolean_Mask = NDArray[Matrix_Shape, Bool]  # This is a validated mask for internal use
Boolean_Array = NDArray[Any, Bool]

# NoData values
nodata = Union[None, Scalar_Array]
Data_Mask = Union[None, Boolean_Array]

# Segments
Segments_Shape = Shape["Segments"]
Segment_Values = NDArray[Segments_Shape, Floating]

# Burn severities
Threshold_Sequence = Sequence[scalar]
Threshold_Array = NDArray[Shape["3 thresholds"], Floating]
Thresholds = Union[Threshold_Sequence, Threshold_Array]
