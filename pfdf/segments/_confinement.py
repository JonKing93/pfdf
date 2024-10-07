"""
A module to compute confinement angles for a stream segment network
----------
This module contains utility functions and the Kernel class, which are used to
compute confinement angles. The utility functions validate user inputs, and extract
many of the inputs needed to compute the angle for each segment. The Kernel class
implements the irregular focal statistics environment used to compute confinement
angle slopes for each segment.
----------
Functions:
    angles          - Computes confinement angles for a stream segment network
    angle           - Computes the angle for a given stream segment
    pixel_slopes    - Computes the two slopes perpendicular to flow for a pixel

Class:
    Kernel          - Implements irregular focal statistics for confinement angle slopes
"""

from math import nan, sqrt

import numpy as np

import pfdf._validate.core as validate
from pfdf._utils import limits, nodata, real
from pfdf.raster import Raster
from pfdf.segments._validate import raster as validate_raster
from pfdf.typing.core import ScalarArray, scalar
from pfdf.typing.segments import (
    ConfinementSlopes,
    FlowNumber,
    NetworkIndices,
    SegmentValues,
)

# Type aliases
KernelIndices = tuple[list[int], list[int]]


def angles(
    segments, dem: Raster, neighborhood: int, dem_per_m: scalar
) -> SegmentValues:
    "Computes confinement angles for a stream segment network"

    # Validate
    neighborhood = validate.scalar(neighborhood, "neighborhood", real)
    validate.positive(neighborhood, "neighborhood")
    validate.integers(neighborhood, "neighborhood")
    dem_per_m = validate.conversion(dem_per_m, "dem_per_m")
    dem = validate_raster(segments, dem, "dem")

    # Preallocate. Initialize kernel
    theta = segments._preallocate()
    kernel = Kernel(neighborhood, *segments.raster_shape)

    # Get the pixel length scaling factor
    scale = neighborhood
    if dem_per_m is not None:
        scale = scale * dem_per_m

    # Determine flow lengths in the units of the DEM
    width, height = segments.transform.resolution("meters")
    lengths = {
        "horizontal": width * scale,
        "vertical": height * scale,
        "diagonal": sqrt(width**2 + height**2) * scale,
    }

    # Get the mean confinement angle for each stream segment
    for i, pixels in enumerate(segments._indices):
        theta[i] = angle(segments, pixels, lengths, kernel, dem)
    return theta


def angle(
    segments, pixels: NetworkIndices, lengths: dict, kernel: "Kernel", dem: Raster
) -> ScalarArray:
    "Computes the confinement angle for a single stream segment"

    # Get the flow directions. If any are NoData, set confinement to NaN
    flows = segments.flow.values[pixels]
    if nodata.isin(flows, segments.flow.nodata):
        return nan

    # Group indices by pixel. Preallocate slopes
    pixels = np.stack(pixels, axis=-1)
    npixels = pixels.shape[0]
    slopes = np.empty((npixels, 2), dtype=float)

    # Get the slopes for each pixel
    for p, flow, rowcol in zip(range(npixels), flows, pixels):
        slopes[p, :] = pixel_slopes(flow, lengths, rowcol, kernel, dem)

    # Compute the mean confinement angle
    theta = np.arctan(slopes)
    theta = np.mean(theta, axis=0)
    theta = np.sum(theta)
    return 180 - np.degrees(theta)


def pixel_slopes(
    flow: int, lengths: dict, rowcol: tuple[int, int], kernel: "Kernel", dem: Raster
) -> ConfinementSlopes:
    "Computes the two slopes perpendicular to flow for a pixel"

    # Get the perpendicular flow length
    if flow in [1, 5]:
        length = lengths["vertical"]
    elif flow in [3, 7]:
        length = lengths["horizontal"]
    else:
        length = lengths["diagonal"]

    # Update the kernel and compute slopes
    kernel.update(*rowcol)
    return kernel.orthogonal_slopes(flow, length, dem)


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

    def indices(self, index: int, length: int, before: bool) -> list[int]:
        """Returns indices adjacent to a processing cell
        index: An index of the processing cell (row or col)
        length: The raster size in the index direction (nRows or nCols)
        before: True for up/left, False for down/right
        """
        if before:
            start, stop = limits(index - self.neighborhood, index, index)
        else:
            start, stop = limits(index + 1, index + self.neighborhood + 1, length)
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
    ) -> ConfinementSlopes:
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
