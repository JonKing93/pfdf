"""
Type hints for Segments object inputs and outputs
"""

from typing import Callable, Literal

from numpy import ndarray

from pfdf.typing.core import ScalarArray, vector

# Various indices
OutletIndices = tuple[int, int]
Outlets = list[OutletIndices]
PixelIndices = tuple[ndarray, ndarray]  # Row and column indices
NetworkIndices = list[tuple[ndarray, ndarray]]
SegmentParents = ndarray  # nSegments x nParents

# Statistics
Statistic = Literal[
    "outlet",
    "min",
    "max",
    "mean",
    "median",
    "std",
    "sum",
    "var",
    "nanmin",
    "nanmax",
    "nanmean",
    "nanmedian",
    "nanstd",
    "nansum",
    "nanvar",
]
StatFunction = Callable[[ndarray], ScalarArray]

# Confinement angles
FlowNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8]
ConfinementSlopes = ndarray  # 1 pixel x 2 rotations

# Summaries
SegmentValues = ndarray  # vector
CatchmentValues = ndarray  # vector
TerminalValues = ndarray  # vector with one element per terminal segment

# Selection
IDs = vector
BooleanIndices = ndarray
Selection = IDs | BooleanIndices
SelectionType = Literal["indices", "ids"]

# Export
ExportType = Literal["segments", "segment outlets", "outlets", "basins"]
PropertySchema = dict[str, str]
PropertyDict = dict[str, SegmentValues]
