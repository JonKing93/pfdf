"""
Type aliases for the post-wildfire debris-flow package
----------
The typing module contains various type aliases used throughout the package.
Note that this module does not provide *every* type alias used within the package.
Rather, it provides common aliases that are used in multiple modules. As such,
individual modules may still define aliases unique to their implementations.
"""

from pathlib import Path
from typing import Literal, Sequence

from numpy import ndarray

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

# Segment summaries
SegmentValues = ndarray
TerminalValues = ndarray  # One value per outlet
BasinValues = SegmentValues | TerminalValues

# Misc segments
OutletIndices = tuple[int, int]
Outlets = list[OutletIndices]
SegmentIndices = ndarray  # Boolean indices
SegmentParents = ndarray  # nSegments x nParents

# Linestring indices
PixelIndices = tuple[ndarray, ndarray]  # Row and column indices
NetworkIndices = list[tuple[ndarray, ndarray]]

# Segment Export
ExportType = Literal["segments", "segment outlets", "outlets", "basins"]
PropertySchema = dict[str, str]
PropertyDict = dict[str, SegmentValues]

# Confinement Angles
FlowNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8]
slopes = ndarray  # 1 pixel x 2 rotations

# Burn severities
ThresholdSequence = Sequence[scalar]
ThresholdArray = ndarray  # 3 thresholds
Thresholds = ThresholdSequence | ThresholdArray

# Generic Models
Variables = ndarray  # Segments x Runs
Parameters = ndarray  # Runs vector

# Staley 2017
Durations = ndarray  # Durations vector
DurationValues = Durations  # same shape, but different name for clarity
Pvalues = ndarray  # P-value vector
SegmentPvalues = ndarray  # Segments x Runs x Accumulations
Accumulations = ndarray  # Accumulation vector
SegmentAccumulations = ndarray  # Segments x Runs x P-values
S17ModelVariables = tuple[SegmentValues, SegmentValues, SegmentValues]
S17ModelParameters = tuple[
    DurationValues, DurationValues, DurationValues, DurationValues
]

# Gartner 2014
Volume = ndarray  # Segments x Runs
Volumes = tuple[Volume, Volume, Volume]

# Projections
Quadrant = Literal[1, 2, 3, 4]
XY = Literal["x", "y"]
Units = Literal["base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"]
BufferUnits = Literal[
    "pixels", "base", "meters", "metres", "kilometers", "kilometres", "feet", "miles"
]
