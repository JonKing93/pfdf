"""
typing  Type aliases for the post-wildfire debris-flow package
"""

from typing import Union, Sequence, Dict, Tuple
from nptyping import NDArray, Shape, Integer, Floating
from pathlib import Path
from rasterio import DatasetReader

# Singular / plural built-ins
strs = Union[str, Sequence[str]]

# Paths
Pathlike = Union[str, Path]
Pathdict = Dict[str, Path]

# Numpy shapes
shape = Union[int, Sequence[int]]
shape1d = Union[int, Tuple[int]]
shape2d = Tuple[int, int]

# Numpy dtypes
dtypes = Union[type, Sequence[type]]
Real = Union[Integer, Floating]
Reallike = Union[int, float, Real]

# Numerical arrays
scalar = Union[int, float, NDArray[Shape["1"], Real]]

# Rasters
RasterArray = NDArray[Shape["Rows", "Columns"], Real]
Raster = Union[str, Path, DatasetReader, RasterArray]
