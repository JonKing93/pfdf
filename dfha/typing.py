"""
typing  Type aliases for the post-wildfire debris-flow package
"""

from typing import Any, Union, Sequence, Dict, Tuple
from nptyping import NDArray, Shape, Integer, Floating
from pathlib import Path
from rasterio import DatasetReader

# Singular / plural built-ins
strs = Union[str, Sequence[str]]
ints = Union[int, Sequence[int]]

# Paths
Pathlike = Union[str, Path]
Pathdict = Dict[str, Path]

# Numpy dtypes
dtypes = Union[type, Sequence[type]]
real = Union[int, float]
Real = Union[Integer, Floating]
Reallike = Union[int, float, Real]

# Numpy shapes
shape = Union[int, Sequence[int]]
shape2d = Tuple[int, int]
ScalarShape = Shape["1"]
VectorShape = Shape["Elements"]
MatrixShape = Shape["Rows, Columns"]

# Real-valued arrays
RealArray = Union[NDArray[Any, Integer], NDArray[Any, Floating]]
ScalarArray = Union[NDArray[ScalarShape, Integer], NDArray[ScalarShape, Floating]]
VectorArray = Union[NDArray[VectorShape, Integer], NDArray[VectorShape, Floating]]
MatrixArray = Union[NDArray[MatrixShape, Integer], NDArray[MatrixShape, Floating]]

# Real-valued array inputs
scalar = Union[int, float, ScalarArray]
vector = Union[int, float, VectorArray]
matrix = Union[int, float, MatrixArray]

# Rasters
RasterArray = MatrixArray  # alias for clarity
Raster = Union[str, Path, DatasetReader, RasterArray]
