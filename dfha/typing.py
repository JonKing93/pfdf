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
Reallike = Union[int, float, Real]

# Numpy shapes
shape = Union[int, Sequence[int]]
shape2d = Tuple[int, int]

# Real-valued arrays
RealArray = NDArray[Any, Real]
ScalarArray = NDArray[Shape["1"], Real]
VectorArray = NDArray[Shape["Elements"], Real]
MatrixArray = NDArray[Shape["Rows", "Columns"], Real]

# Real-valued array inputs
scalar = Union[int, float, ScalarArray]
vector = Union[int, float, VectorArray]
matrix = Union[int, float, MatrixArray]

# Rasters
RasterArray = MatrixArray  # alias for clarity
Raster = Union[str, Path, DatasetReader, RasterArray]
