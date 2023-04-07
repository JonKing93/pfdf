"""
segments  Computes values for stream segments
----------
The segments module is used to compute values for each stream segment in a
network. These computed values can then be used to filter the stream network to
a final set of model-worthy segments. Filtering values include
    * Slope
    * Confinement Angle
    * Total upslope area
    * Whether a segment is below a debris-retention basin, and
    * Whether a segment is below a developed area

Note that these values are summarized
----------
User functions:
    filter      - Filters a stream network for a standard hazard assessment
    locate      - Locates individual segments within a stream link raster
    slope       - Returns the mean slope (rise/run) of stream segments
    confinement - Returns the mean confinement angle of stream segments
    area        - Returns 


"""

import numpy as np
from typing import Dict, List
from math import sqrt

# Type aliases
segments = Dict[int, np.ndarray]


def filter(
        stream_raster: np.ndarray,
        *,
        slopes: np.ndarray,
        minimum_slope: float,
        upslope_area: np.ndarray,
        maximum_area: float,
        upslope_development: np.ndarray,
        maximum_development: float,
        dem: np.ndarray,
        flow_directions: np.ndarray,
        N: int,
        resolution: float,
        maximum_confinement: float,
        upslope_basins: Optional[np.ndarray] = None,
        maximum_basins: Optional[int] = None,
) -> List[int]:
    
    # Get the segments
    segments = locate(stream_raster)

    # Remove segments below developed areas
    if _any_args(upslope_development, maximum_development):
        upslope_development = development(segments, upslope_development)
        segments = _remove(segments, upslope_development, '>', maximum_development)

    # Remove watch streams (area too large)
    if _any_args(upslope_area, maximum_area):
        upslope_area = area(segments, upslope_area)
        segments = _remove(segments, upslope_area, '>' maximum_area)

    # Remove segments below debris basins
    if _any_args(upslope_basins, maximum_basins):
        upslope_basins = basins(segments, upslope_basins)
        segments = _remove(segments, upslope_basins, '>', maximum_basins)

    # Remove low angle slopes (not steep enough)
    if _any_args(slopes, minimum_slope):
        slopes = slope(segments, slopes)
        segments = _remove(segments, slopes, '<', minimum_slope)

    # Remove high confinement
    if _any_args(dem, flow_directions, N, resolution, maximum_confinement):
        angles = confinement(segments, dem, flow_directions, N, resolution)
        segments = _remove(segments, angles, '>', maximum_confinement)
        

def locate(stream_raster: np.ndarray) -> segments:
    """
    locate  Locates stream segment pixels within a stream link raster
    ----------
    locate(stream_raster)
    Returns a dict that maps stream segment IDs to their associated pixels. The
    input "segments" should be a numpy 2D int array representing the pixels of a
    stream link raster. The values of stream segment pixels should be the ID of the
    associated stream segment. All other pixels should be 0. (Essentially, each
    group of non-zero pixels with the same value constitutes one stream segment).
    The output dict will have a key for each stream segment ID (the unique non-zero
    values in the input raster). The value of each key will be an Nx2 int ndarray.
    This array records the indices of the stream segment's pixels within the
    stream link raster. The first column holds row indices, and the second column
    holds column indices.
    ----------
    Inputs:
        stream_raster (2D int numpy.ndarray): A numpy.ndarray representing the
            pixels of a stream link raster. Should be a 2D int array. Stream
            segment pixels should have a value matching the ID of the associated
            stream segment. All other pixels should be 0.

    Outputs:
        Dict[int, numpy.ndarray]: The dict of stream segment pixels. Has one key
            per stream segment ID (these are the unique non-zero values in the
            stream link raster). Each key maps to a Nx2 numpy.ndarray. This array
            holds the indices of the stream segment's pixels within the stream
            link raster. Each row holds the indices for one pixel. First column
            is the row index, second column is the column index.
    """

    # Get the indices of stream segment pixels. Organize as column vectors
    (rows, cols) = np.nonzero(stream_raster)
    rows = rows.reshape(-1, 1)
    cols = cols.reshape(-1, 1)

    # Reduce the stream link raster to just the segments. Get the segment IDs
    segments = stream_raster[rows, cols].reshape(-1)
    ids = np.unique(segments)

    # Return a dict mapping segment IDs to the indices of the pixels associated
    # with each segment
    output = {id: None for id in ids}
    for id in output.keys():
        segment = np.nonzero(segments == id)
        pixels = (rows[segment], cols[segment])
        output[id] = np.hstack(pixels)
    return output


def area(segments: segments, upslope_areas: np.ndarray) -> np.ndarray:
    """
    area  Returns the maximum upslope area for each stream segment
    ----------
    area(segments, upslope_areas)
    Computes the maximum upslope area for each stream segment. Returns the areas
    as a numpy 1D array. Te order of slopes in the output array will match the
    order of keys in the input segments dict.
    ----------
    Inputs:
        segments: A dict mapping stream segment IDs to the indices of the
            associated DEM pixels.
        upslope_areas: A numpy 2D array holding the total upslope area (also known
            as contributing area or flow accumulation) for the DEM pixels.

    Outputs:
        numpy 1D array: The maximum upslope area of each stream segment. The
            order of values matches the order of ID keys in the input segments dict.
    """
    return _segment_summary(segments, upslope_areas, np.amax)


def slope(segments: segments, slopes: np.ndarray) -> np.ndarray:
    """
    slope  Returns the mean slope (rise/run) for each stream segment
    ----------
    slope(segments, slopes)
    Computes the mean slope (rise/run) for each stream segment. Returns the slopes
    as a numpy 1D array. The order of slopes in the output array will match the
    order of keys in the input segments dict.
    ----------
    Inputs:
        segments: A dict mapping stream segment IDs to the indices of the
            associated DEM pixels.
        slopes: A numpy 2D array holding the slopes of the DEM pixels

    Outputs:
        numpy 1D array: The mean slope (rise/run) of each stream segment. The order
            of values matches the order of ID keys in the input segments dict.
    """
    return _segment_summary(segments, slopes, np.mean)


def basins(segments: segments, upslope_basins: np.ndarray) -> np.ndarray:
    """
    basins  Returns the maximum number of upslope basins for each stream segment
    ----------
    basins(segments, upslope_basins)
    Computes the maximum number of upslope debris retention basins for each
    stream segment. Returns this count as a numpy 1D array. The order of slopes
    in the output array will match the order of IDs in the input segments dict.
    ----------
    Inputs:
        segments: A dict mapping stream segment IDs to the indices of the
            associated DEM pixels.
        upslope_basins: A numpy 2D array holding the number of upslope debris basins
            for the DEM pixels.

    Outputs:
        numpy 1D array: The maximum number of upslope debris basins for each
            stream segment. The order of values matches the order of ID keys in
            the input segments dict.
    """
    return _segment_summary(segments, upslope_basins, np.amax)


def development(segments: segments, upslope_development: np.ndarray) -> np.ndarray:
    """
    development  Returns the mean upslope developed area for each stream segments
    ----------
    development(segments, upslope_development)
    Computes the mean developed upslope area for each stream segment. Returns
    these areas as a numpy 1D array. The order of slopes in the output array will
    match the order of IDs in the input segments dict.
    ----------
    Inputs:
        segments: A dict mapping stream segment IDs to the indices of the
            associated DEM pixels.
        upslope_development: A numpy 2D array holding the developed upslope area
            fot the DEM pixels.

    Outputs:
        numpy 1D array: The mean developed upslope area of each stream segment.
            The order of values matches the order of ID keys in the input
            segments dict.
    """
    return _segment_summary(segments, upslope_development, np.amean)


def _segment_summary(segments, raster, statistic):

    # Preallocate
    ids = segments.keys()
    summary = np.empty(len(ids))

    # Get summary statistic for each segment
    for i, id in enumerate(ids):
        pixels = segments[id]
        summary[i] = statistic(raster[pixels])
    return summary


def confinement(
    segments: segments,
    dem: np.ndarray,
    flow_directions: np.ndarray,
    N: int,
    resolution: float,
):
    """
    confinement  Returns the mean confinement angle of each stream segment
    ----------
    confinement(segments, dem, flow_directions, N, resolution)
    Computes the mean confinement angle for each stream segment. Returns these
    angles as a numpt 1D array. The order of angles matches the order of ID keys
    in the input segments dict.

    The confinement angle for a given pixel is calculated using the slopes in the
    two directions perpendicular to stream flow. A given slope is calculated using
    the maximum DEM height within N pixels of the processing pixel in the
    associated direction. For example, consider a pixel flowing east with N=4.
    Confinement angles are calculated using slopes to the north and south. The
    north slope is determined using the maximum DEM height in the 4 pixels north
    of the stream segment pixel via:

        slope = max height / (N * DEM resolution * scale)

    where scale = 1 or sqrt(2) for lateral/diagonal flow across raster cells.
    The south slope is computed similarly. Next, confinement angles are
    calculated using:

        theta = 180 - tan^-1(slope1) - tan^-1(slope2)

    and the mean confinement angle is taken over the pixels in each stream segment.
    ----------
    Inputs:
        segments: A dict mapping stream segment IDs to the indices of the
            associated DEM pixels.
        dem: A numpy 2D array holding the DEM data
        flow_directions: A numpy 2D array holding the flow directions for the
            DEM pixels
        N: The number of raster pixels to search for maximum heights
        resolution: The resolution of the DEM

    Outputs:
        numpy 1D array: The mean confinement angle for each stream segment. The
            order of values matches the order of keys in the input segments dict.
    """

    # Preallocate
    ids = segments.keys()
    theta = np.empty(len(ids))

    # Initialize kernel and get flow lengths
    (nRows, nCols) = dem.shape
    kernel = _Kernel(N, nRows, nCols)
    lateral_length = resolution * N
    diagonal_length = lateral_length * sqrt(2)

    # Get pixels for each stream segment. Preallocate orthogonal slopes
    for i, id in enumerate(ids):
        pixels = segments[id]
        nPixels = pixels.shape[0]
        slopes = np.empty((nPixels, 2), dem.dtype)

        # Iterate through pixels as processing cells. Update kernel
        for p, [row, col] in enumerate(pixels):
            kernel.update(row, col)

            # Get flow direction and length. Use to compute orthogonal slopes
            flow = flow_directions[row, col]
            length = _flow_length(flow, lateral_length, diagonal_length)
            slopes[p, :] = _orthogonal_slopes(flow, dem, kernel, length)

        # Compute and return mean confinement angles
        theta[i] = _confinement_angle(slopes)
    return theta


def _confinement_angle(slopes):
    theta = np.arctan(slopes)
    theta = np.mean(theta, 0)
    theta = 180 - np.sum(theta)


def _orthogonal_slopes(flow, dem, kernel, length):
    slopes = np.empty((1, 2))
    slopes[0] = _max_height(flow - 7, dem, kernel)
    slopes[1] = _max_height(flow - 3, dem, kernel)
    slopes = slopes - dem[kernel.row, kernel.col]
    slopes = slopes / length
    return slopes


def _flow_length(flow_direction, lateral_length, diagonal_length):
    if flow_direction % 2 == 0:
        length = diagonal_length
    else:
        length = lateral_length
    return length


class _Kernel:
    """_Kernel  Locate data values for irregular focal statistics
    ----------
    The _Kernel class helps determine the indices of raster pixels needed to
    implement irregular focal statistics. Each _Kernel object represents a focal
    statistics environment - the properties of the object describe the raster,
    kernel size, and current processing cell.

    The class provides functions that return the indices of raster pixels needed
    to calculate irregular focal statistics for the current processing cell. These
    functions are left, right, up, down, upleft, upright, downleft, and downright.
    These functions will only return indices within the bounds of the raster.
    The "directions" property provides a reference for these directional functions,
    and lists the functions in the same order as D8 flow direction numbers.
    ----------
    PROPERTIES:
        Focal Statistics Environment:
            N           - The size of the kernel
            nRows       - The number of raster rows
            nCols       - The number of raster columns
            row         - The row index of the processing cell
            col         - The column index of the processing cell

        Reference:
            directions  - Lists kernel direction functions in the same order as D8 flow directions

    METHODS:
        Creation:
            __init__    - Create a _Kernel object
            update      - Update the processing cell

        Directions:
            (These methods return the indices for a particular direction)
            left, right, up, down, upleft, upright, downleft, downright

        Direction types:
            vertical    - Indices for up or down
            horizontal  - Indices for left or right
            identity    - Indices for upleft or downright (derived from the diagonal of an identity matrix)
            exchange    - Indices for upright or downleft (derived from the counter-diagonal of an exchange matrix)

        Utilities:
            lateral     - Returns indices for lateral directions (up, down, left, right)
            diagonal    - Returns indices for diagonal directions (upleft, upright, downleft, downright)
            indices     - Returns the N indices preceding or following a processing cell index
            limit       - Limits indices to the N values closest to the processing cell index
    """

    # Focal statistics environment
    def __init__(self, N: int, nRows: int, nCols: int) -> None:
        """
        N: The kernel size. Sometimes called the kernel half-step. (May be even)
        nRows: The number of raster rows
        nCols: The number of raster columns
        """
        self.N = N
        self.nRows = nRows
        self.nCols = nCols
        self.row = None
        self.col = None

    def update(self, row: int, col: int):
        """
        row: The row index of the processing cell
        col: The column index of the processing cell
        """
        self.row = row
        self.col = col

    # Directions: Lateral
    def up(self):
        return self.vertical(True)

    def down(self):
        return self.vertical(False)

    def left(self):
        return self.horizontal(True)

    def right(self):
        return self.horizontal(False)

    # Directions: Diagonal
    def upleft(self):
        return self.identity(True)

    def downright(self):
        return self.identity(False)

    def upright(self):
        return self.exchange(True)

    def downleft(self):
        return self.exchange(False)

    # Direction reference
    directions = [right, downright, down, downleft, left, upleft, up, upright]

    # Direction types
    def vertical(self, before: bool):
        "before: True for up, False for down"
        return self.lateral(self.row, self.nRows, self.col, before, False)

    def horizontal(self, before: bool):
        "before: True for left, False for right"
        return self.lateral(self.col, self.nCols, self.row, before, True)

    def identity(self, before: bool):
        "before: True for upleft, False for downright"
        return self.diagonal(before, before)

    def exchange(self, before_rows: bool):
        "before_rows: True for downleft, False for upright"
        return self.diagonal(before_rows, not before_rows)

    # Utilities
    def diagonal(self, before_rows: bool, before_cols: bool):
        """
        before_rows: True for left, False for right
        before_cols: True for up, False for down
        """
        rows = self.indices(self.row, self.nRows, before_rows)
        cols = self.indices(self.col, self.nCols, before_cols)
        N = min(len(rows), len(cols))
        rows = self.limit(N, rows, before_rows)
        cols = self.limit(N, cols, before_cols)
        return (rows, cols)

    def lateral(
        self, changing: int, nMax: int, fixed: int, before: bool, fixed_rows: bool
    ):
        """
        changing: The processing index of the changing direction. (up/down: row, left/right: col)
        nMax: The raster size in the changing direction (up/down: nRows, left/right: nCols)
        fixed: The processing index of the unchanging direction (up/down: col, left/right: row)
        before: True for left/up, False for right/down
        fixed_rows: True for left/right, False for up/down
        """
        changing = self.indices(changing, nMax, before)
        fixed = np.full(len(changing), fixed)
        if fixed_rows:
            return (fixed, changing)
        else:
            return (changing, fixed)

    def indices(self, index: int, nMax: int, before: bool):
        """
        index: An index of the processing cell (row or col)
        nMax: The raster size in the index direction (nRows or nCols)
        before: True for up/left, False for down/right
        """
        if before:
            start = max(0, index - self.N)
            stop = index
            return np.arange(start, index)
        else:
            start = index + 1
            stop = min(nMax, index + self.N + 1)
        return np.arange(start, stop)

    @staticmethod
    def limit(N: int, indices: np.ndarray, before: bool):
        """
        N: The number of indices to keep
        indices: The current set of indices
        before: True if these are indices before the processing cell (up/left)
        """
        if before:
            return indices[-N:]
        else:
            return indices[0:N]


def _max_height(flow_index, dem, kernel):
    direction = _Kernel.directions(flow_index)
    heights = dem[direction(kernel)]
    return np.amax(heights)
