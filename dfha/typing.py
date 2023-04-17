"""
typing  Type aliases for the post-wildfire debris-flow package
----------
The typing module contains various type aliases used throughout the package.
Note that this module does not provide *every* type alias used within the package.
Rather, it provides common aliases that are used in multiple modules. As such,
individual modules may still define aliases unique to their individual
implementations.
"""

from typing import Any, Union, Sequence, Dict, Tuple
from nptyping import NDArray, Shape, Integer, Floating
from pathlib import Path
from rasterio import DatasetReader
import numpy as np

# Singular / plural built-ins
strs = Union[str, Sequence[str]]
ints = Union[int, Sequence[int]]
floats = Union[float, Sequence[float]]

# Paths
Pathlike = Union[str, Path]
Pathdict = Dict[str, Path]

# Numpy dtypes
dtypes = Union[type, Sequence[type]]

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
vector = Union[ints, floats, VectorArray]
matrix = Union[ints, floats, MatrixArray]

# Rasters
RasterArray = MatrixArray  # alias for clarity
Raster = Union[str, Path, DatasetReader, RasterArray]
