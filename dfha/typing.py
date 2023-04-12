"""
typing  Type aliases for the post-wildfire debris-flow package
"""

from typing import Any, Union, Sequence, Dict, Tuple
from nptyping import NDArray, Shape, Integer, Floating
from pathlib import Path
from rasterio import DatasetReader

# Singular / plural built-ins
strs = Union[str, Sequence[str]]

# Paths
Pathlike = Union[str, Path]
Pathdict = Dict[str, Path]

# Numpy dtypes
dtypes = Union[type, Sequence[type]]
Real = Union[Integer, Floating]
RealArray = NDArray[Any, Real]
Reallike = Union[int, float, Real]

# Numpy shapes
shape = Union[int, Sequence[int]]
shape1d = Union[int, Tuple[int]]
shape2d = Tuple[int, int]

# Real-valued arrays
ScalarArray = NDArray[Shape['1'], Real]
VectorArray = NDArray[Shape['Elements'], Real]
MatrixArray = NDArray[Shape['Rows','Columns'], Real]

# Real-valued array inputs
scalar = Union[int, float, ScalarArray]
vector = Union[int, float, VectorArray]
matrix = Union[int, float, MatrixArray]

# Rasters
RasterArray = NDArray[Shape["Rows", "Columns"], Real]
Raster = Union[str, Path, DatasetReader, RasterArray]
