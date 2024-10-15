"""
Type hints used throughout the pfdf package
"""

from pathlib import Path
from typing import Literal, Sequence

from numpy import dtype, ndarray

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
Quadrant = Literal[1, 2, 3, 4]
XY = Literal["x", "y"]
Units = Literal["base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"]
BufferUnits = Literal[
    "pixels", "base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"
]
