"""
Type hints used throughout the pfdf package
"""

from pathlib import Path
from typing import Any, Callable, Literal, Sequence

from numpy import dtype, ndarray
from pyproj import CRS

# Paths
Pathlike = str | Path
OutputPath = Path | None

# Singular / plural
strs = str | Sequence[str]
ints = int | Sequence[int]
floats = float | Sequence[float]
_dtype = dtype | type
dtypes = _dtype | Sequence[_dtype]

# Inputs that are literally shapes
shape = ints
shape2d = tuple[int, int]

# Generic real-valued arrays
RealArray = ndarray
ScalarArray = ndarray
VectorArray = ndarray
MatrixArray = ndarray

# Real-valued array inputs
scalar = int | float | ScalarArray
vector = ints | floats | VectorArray
matrix = ints | floats | MatrixArray

# NoDatas and masks
ignore = None | scalar | Sequence[scalar]
Casting = Literal["no", "equiv", "safe", "same_kind", "unsafe"]
BooleanArray = ndarray
BooleanMatrix = ndarray

# Projections
CRSlike = CRS | Any
Quadrant = Literal[1, 2, 3, 4]
XY = Literal["x", "y"]
Units = Literal["base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"]

# Buffers
EdgeDict = dict[str, float]
BufferUnits = Literal[
    "pixels", "base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"
]

# Features
operation = Callable[[scalar], scalar]
value = float | int | bool
geometry = dict[str, Any]
GeometryValues = list[tuple[geometry, value]]

# URLs
url = str
timeout = None | scalar | tuple[scalar, scalar]
