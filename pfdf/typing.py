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
from typing import Any, Literal, Sequence

from nptyping import Bool, Floating, Integer, NDArray, Shape

# Singular / plural
strs = str | Sequence[str]
ints = int | Sequence[int]
floats = float | Sequence[float]
dtypes = type | Sequence[type]

# Paths
Pathlike = str | Path
OutputPath = Path | None

# Inputs that are literally shapes
shape = ints
shape2d = tuple[int, int]

# Generic array shapes
ScalarShape = Shape["1"]
VectorShape = Shape["Elements"]
MatrixShape = Shape["Rows, Columns"]

# Generic real-valued arrays
RealArray = NDArray[Any, Floating]
ScalarArray = NDArray[ScalarShape, Floating]
VectorArray = NDArray[VectorShape, Floating]
MatrixArray = NDArray[MatrixShape, Floating]

# Real-valued array inputs
scalar = int | float | ScalarArray
vector = ints | floats | VectorArray
matrix = ints | floats | MatrixArray

# NoDatas and masks
ignore = None | scalar | Sequence[scalar]
Casting = Literal["no", "equiv", "safe", "same_kind", "unsafe"]
BooleanArray = NDArray[Any, Bool]
BooleanMatrix = NDArray[MatrixShape, Bool]

# Segment summaries
SegmentsShape = Shape["Segments"]
SegmentValues = NDArray[SegmentsShape, Floating]
TerminalValues = NDArray[Shape["Outlets"], Floating]
BasinValues = SegmentValues | TerminalValues

# Misc segments
OutletIndices = tuple[int, int]
Outlets = list[OutletIndices]
SegmentIndices = NDArray[SegmentsShape, Bool]
SegmentParents = NDArray[Shape["Segments, Parents"], Integer]
PixelIndices = NDArray[Shape["Pixels"], Integer]
PixelIndices = tuple[PixelIndices, PixelIndices]
PropertyDict = dict[str, SegmentValues]

# Confinement Angles
FlowNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8]
slopes = NDArray[Shape["1 pixel, 2 rotations"], Floating]

# Burn severities
ThresholdSequence = Sequence[scalar]
ThresholdArray = NDArray[Shape["3 thresholds"], Floating]
Thresholds = ThresholdSequence | ThresholdArray

# Generic Models
Variables = NDArray[Shape["Segments, Runs"], Floating]
Parameters = NDArray[Shape["Runs"], Floating]

# Staley 2017
Durations = NDArray[Shape["Durations"], Floating]
DurationValues = Durations  # same shape, but different name for clarity
Pvalues = NDArray[Shape["Pvalues"], Floating]
SegmentPvalues = NDArray[Shape["Segments, Runs, Accumulations"], Floating]
Accumulations = NDArray[Shape["Accumulations"], Floating]
SegmentAccumulations = NDArray[Shape["Segments, Runs, Pvalues"], Floating]
S17ModelVariables = tuple[SegmentValues, SegmentValues, SegmentValues]
S17ModelParameters = tuple[
    DurationValues, DurationValues, DurationValues, DurationValues
]

# Gartner 2014
Volumes = NDArray[Shape["Segments, Runs"], Floating]

# Projections
Quadrant = Literal[1, 2, 3, 4]
