"""
kernel  A class to facilitate irregular neighborhood focal statistics
----------
This module contains the Kernel class, which facilitates the computation of
focal statistics with irregular neighborhoods. The main purpose of this class
is to compute confinement angle slopes.
----------
Class:
    Kernel  - Locate data values for confinement angle focal statistics
"""

from math import nan

import numpy as np

from pfdf._utils import nodata
from pfdf.raster import Raster
from pfdf.typing import FlowNumber, ScalarArray, scalar, slopes

# Type aliases
KernelIndices = tuple[list[int], list[int]]


class Kernel:
    """Kernel  Locate data values for irregular focal statistics
    ----------
    The Kernel class helps determine the indices of raster pixels needed to
    implement irregular focal statistics (which are needed to calculate stream
    segment confinement angles). Each Kernel object represents a focal
    statistics environment - the properties of the object describe the raster,
    kernel size, and current processing cell.

    The class provides functions that return the indices of raster pixels needed
    to calculate irregular focal statistics for the current processing cell. These
    functions are left, right, up, down, upleft, upright, downleft, and downright.
    These functions will only return indices within the bounds of the raster.
    The "directions" property provides a reference for these directional functions,
    and lists the functions in the same order as D8 flow direction numbers.

    The "orthogonal_slopes" function then uses these directional indices to
    calculate slopes perpendicular to the direction of flow. These slopes are
    typically used to compute confinement angles. Note that this class assumes
    that flow direction numbers follow the TauDEM D8 flow number style.
    ----------
    PROPERTIES:
        Focal Statistics Environment:
            neighborhood    - The size of the kernel neighborhood
            nRows           - The number of raster rows
            nCols           - The number of raster columns
            row             - The row index of the processing cell
            col             - The column index of the processing cell

        Reference:
            directions      - Lists kernel direction functions in the same order as Taudem D8 flow directions

    METHODS:
        Creation:
            __init__        - Create a _Kernel object
            update          - Update the processing cell

        Directions:
            (These methods return the indices for a particular direction)
            left, right, up, down, upleft, upright, downleft, downright

        Direction types:
            vertical        - Indices for up or down
            horizontal      - Indices for left or right
            identity        - Indices for upleft or downright (derived from the diagonal of an identity matrix)
            exchange        - Indices for upright or downleft (derived from the counter-diagonal of an exchange matrix)

        Index utilities:
            lateral         - Returns indices for lateral directions (up, down, left, right)
            diagonal        - Returns indices for diagonal directions (upleft, upright, downleft, downright)
            indices         - Returns the N indices preceding or following a processing cell index
            limit           - Limits indices to the N values closest to the processing cell index

        Confinement Slopes:
            orthogonal_slopes   - Returns the slopes perpendicular to the flow direction
            max_height          - Returns the maximum DEM height in a particular direction
    """

    # Focal statistics environment
    def __init__(self, neighborhood: int, nRows: int, nCols: int) -> None:
        """
        neighborhood: The kernel size. Sometimes called the kernel half-step. (May be even)
        nRows: The number of raster rows
        nCols: The number of raster columns
        """

        self.neighborhood = neighborhood
        self.nRows = nRows
        self.nCols = nCols
        self.row = None
        self.col = None

    def update(self, row: int, col: int) -> None:
        """
        row: The row index of the processing cell
        col: The column index of the processing cell
        """
        self.row = row
        self.col = col

    # Directions: Lateral
    def up(self) -> KernelIndices:
        return self.vertical(True)

    def down(self) -> KernelIndices:
        return self.vertical(False)

    def left(self) -> KernelIndices:
        return self.horizontal(True)

    def right(self) -> KernelIndices:
        return self.horizontal(False)

    # Directions: Diagonal
    def upleft(self) -> KernelIndices:
        return self.identity(True)

    def downright(self) -> KernelIndices:
        return self.identity(False)

    def upright(self) -> KernelIndices:
        return self.exchange(True)

    def downleft(self) -> KernelIndices:
        return self.exchange(False)

    # Direction reference
    directions = [right, upright, up, upleft, left, downleft, down, downright]

    # Direction types
    def vertical(self, before: bool) -> KernelIndices:
        "before: True for up, False for down"
        return self.lateral(self.row, self.nRows, self.col, before, False)

    def horizontal(self, before: bool) -> KernelIndices:
        "before: True for left, False for right"
        return self.lateral(self.col, self.nCols, self.row, before, True)

    def identity(self, before: bool) -> KernelIndices:
        "before: True for upleft, False for downright"
        return self.diagonal(before, before)

    def exchange(self, before_rows: bool) -> KernelIndices:
        "before_rows: True for upright, False for downleft"
        (rows, cols) = self.diagonal(before_rows, not before_rows)
        cols = list(reversed(cols))
        return (rows, cols)

    # Utilities
    def diagonal(self, before_rows: bool, before_cols: bool) -> KernelIndices:
        """
        before_rows: True for up, False for down
        before_cols: True for left, False for right
        """
        rows = self.indices(self.row, self.nRows, before_rows)
        cols = self.indices(self.col, self.nCols, before_cols)
        N = min(len(rows), len(cols))
        rows = self.limit(N, rows, before_rows)
        cols = self.limit(N, cols, before_cols)
        return (rows, cols)

    def lateral(
        self, changing: int, nMax: int, fixed: int, before: bool, fixed_rows: bool
    ) -> KernelIndices:
        """
        changing: The processing index of the changing direction. (up/down: row, left/right: col)
        nMax: The raster size in the changing direction (up/down: nRows, left/right: nCols)
        fixed: The processing index of the unchanging direction (up/down: col, left/right: row)
        before: True for left/up, False for right/down
        fixed_rows: True for left/right, False for up/down
        """
        changing = self.indices(changing, nMax, before)
        fixed = [fixed] * len(changing)
        if fixed_rows:
            return (fixed, changing)
        else:
            return (changing, fixed)

    def indices(self, index: int, nMax: int, before: bool) -> list[int]:
        """Returns indices adjacent to a processing cell
        index: An index of the processing cell (row or col)
        nMax: The raster size in the index direction (nRows or nCols)
        before: True for up/left, False for down/right
        """
        if before:
            start = max(0, index - self.neighborhood)
            stop = index
        else:
            start = index + 1
            stop = min(nMax, index + self.neighborhood + 1)
        return list(range(start, stop))

    @staticmethod
    def limit(N: int, indices: list[int], are_before: bool) -> list[int]:
        """Restricts indices to N values adjacent to the processing cell
        N: The number of indices to keep
        indices: The current set of indices
        are_before: True if these are indices before the processing cell (up/left)
        """
        if are_before:
            return indices[-N:]
        else:
            return indices[0:N]

    # Confinement angle slopes
    def max_height(self, flow: int, dem: Raster) -> ScalarArray:
        """Returns the maximum height in a particular direction or NaN if there
        are NoData values.
        flow: Flow direction *index* (flow number - 1)
        dem: DEM raster"""

        direction = self.directions[flow]
        heights = dem.values[direction(self)]
        if nodata.isin(heights, dem.nodata):
            return nan
        else:
            return np.amax(heights)

    def orthogonal_slopes(
        self, flow: FlowNumber, length: scalar, dem: Raster
    ) -> slopes:
        """Returns the slopes perpendicular to flow for the current pixel
        flow: TauDEM style D8 flow direction number
        length: The lateral or diagonal flow length across 1 pixel
        dem: The DEM Raster"""

        # Return NaN if the centering pixel is NoData
        center = dem.values[self.row, self.col]
        if nodata.isin(center, dem.nodata):
            return np.array([nan, nan]).reshape(1, 2)

        # Get maximum heights in orthogonal directions
        clockwise = self.max_height(flow - 3, dem)
        counterclock = self.max_height(flow - 7, dem)
        heights = np.array([clockwise, counterclock]).reshape(1, 2)

        # Compute slopes
        rise = heights - center
        slopes = rise / length
        return slopes
