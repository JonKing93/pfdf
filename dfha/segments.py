"""
segments  Filter stream segments to model-worthy basins
----------
The segments module is used to compute values for each stream segment in a
network. These computed values can then be used to filter the stream network to
a final set of model-worthy segments. Filtering values include
    
    * Slope
    * Confinement Angle
    * Total upslope area
    * Total developed upslope area
    * Number of upslope debris-retention basins

Operational users will likely be most interested in the "filter" function, which
implements a number of filters for standard hazard assessment and returns a final
set of stream segments.

Other users may be interested in build custom filtering routines. The workflow
for this is as follows: First, run the "locate" command on a stream link raster.
This command returns a Segments object, which defines a set of stream segments
for a DEM - the object's "indices" property maps segment IDs to the locations of
the segment's pixels in the DEM. You can then use the "slope", "area", 
"confinement", "basins", and/or "development" functions to return the values
associated with the stream segments. For example, the "slope" command returns
the mean slope for each segment in the dict. 
then use these values to implement custom filtering routines. See also the "remove"
command to remove segments from the set.

Advanced users may want to implement filters beyond the 5 filters explicitly
provided by this module. The "summarize" function provides support for this for
basic calculations. Given an input raster of data values, the function returns 
a summary statistic for each segment in the dict. The summary statistic for each
segment is computed using the raster values for the segment's pixels. Options 
include the min, max, mean, median, and standard deviation of the pixel values.



Summary statistics are calculated
from the 





    * min


We provide limited support for other using the
"summarize" function. This function takes an input raster and returns a summary




    * Next, use this dict to run the "slope", "area", "confinement", "basins",
      and "development commands

Other users may be interested in designing custom filters. This can be implemented
using the "slope", "confinement", "area", "development", and "basins" functions.
These functions return the values associated with a set of stream segments. Users
can then use these values to implement custom filtering routines. Before using
these functions, you should first use the "locate" function to locate the stream
segments within the DEM. This command returns a dict that defines a set of stream
segments. The dict maps stream segment IDs to pixel locations in the DEM, and is
used as input to the aforementioned functions.






The output of this command is a used as input to the
aforementioned functions. Users may also be interested in the "remove" command,
which can be used to remove 




for a set of stream segments. Users can then use 
the returned values to implement custom filtering routines. Before using these


Note that most users
will want to use the "locate

Other users may be interested in the "slope", "confinement", "area", "development",

    * Location below debris-retention basins
    * Whether a segment is below a debris-retention basin, and
    * Whether a segment is below a developed area

Note that these values are summarized
----------
Operational Users:
    filter      - Filters a stream network to model-worthy segments

User Functions:
    locate      - Locates stream segments within a stream link raster
    slope       - Returns the mean slope (rise/run) of stream segments
    confinement - Returns the mean confinement angle of stream segments
    area        - Returns the total upslope area of stream segments
    development - Returns the total upslope developed area of stream segments
    basins      - Returns the number of upslope debris basins for stream segments


"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from math import sqrt

# Type aliases
segments = Dict[int, np.ndarray]


class Segments:
    @property
    def raster_shape(self) -> Tuple[int, int]:
        return self._raster_shape

    @property
    def indices(self) -> Dict[str, np.ndarray]:
        return self._indices

    def __len__(self) -> int:
        return len(self._indices)

    def __str__(self) -> str:
        ids = self._indices.keys()
        ids = [str(id) for id in ids]
        return ", ".join(ids)

    def __init__(self, stream_raster: np.ndarray) -> None:

        # Get the indices of stream segment pixels. Organize as column vectors
        (rows, cols) = np.nonzero(stream_raster)
        rows = rows.reshape(-1, 1)
        cols = cols.reshape(-1, 1)

        # Reduce the stream link raster to just the segment pixels. Get the segment IDs
        pixels = stream_raster[rows, cols].reshape(-1)
        ids = np.unique(pixels)

        # Store a dict mapping segment IDs to the indices of their pixels
        segments = {id: None for id in ids}
        for id in ids:
            segment = np.nonzero(segments == id)
            indices = (rows[segment], cols[segment])
            segments[id] = np.hstack(indices)

        # Record the segment map and the indices dict
        self._raster_shape = stream_raster.shape
        self._indices = segments

    def ids(self):
        return self._indices.keys()

    def remove(self, ids):
        for id in ids:
            self._indices.pop(id)
        return self

    def basins(self, upslope_basins: np.ndarray) -> np.ndarray:
        """
        Segments.basins  Returns the maximum number of upslope basins for each stream segment
        ----------
        self.basins(upslope_basins)
        Computes the maximum number of upslope debris retention basins for each
        stream segment. Returns this count as a numpy 1D array. The order of slopes
        in the output array will match the order of IDs in the Segments object.
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
        self.validate_raster(upslope_basins, "upslope_basins")
        return self._summary(upslope_basins, np.amax)

    def validate_raster(self, raster: np.ndarray, name: Optional[str] = None) -> None:

        # Default name
        if name is None:
            name = "input raster"

        # Require 2D numpy array matching the stream raster shape
        if not isinstance(raster, np.ndarray):
            raise TypeError(f"{name} must be a numpy.ndarray")
        elif raster.ndim != 2:
            raise ValueError(f"{name} must have 2 dimensions")
        elif raster.shape != self._raster_shape:
            raise ValueError(
                f"The shape of the {name} raster {raster.shape} does "
                f"not match the shape of the stream link raster used "
                f"to define the stream segments {self._raster_shape}."
            )


def filter(
    stream_raster: np.ndarray,
    *,
    slopes: Optional[np.ndarray] = None,
    minimum_slope: Optional[float] = None,
    upslope_area: Optional[np.ndarray] = None,
    maximum_area: Optional[float] = None,
    upslope_development: Optional[np.ndarray] = None,
    maximum_development: Optional[float] = None,
    dem: Optional[np.ndarray] = None,
    flow_directions: Optional[np.ndarray] = None,
    N: Optional[int] = None,
    resolution: Optional[float] = None,
    maximum_confinement: Optional[float] = None,
    upslope_basins: Optional[np.ndarray] = None,
    maximum_basins: Optional[int] = None,
) -> List[int]:
    """
    filter  Filters an initial stream network to a set of model-worthy stream segments
    ----------
    filter(stream_raster, *, ...)
    Filters the stream segments in a network to a set of segments worthy of
    hazard-assessment modeling. Searches a stream network raster for non-zero
    pixels. The unique set of non-zero pixels are taken as the IDs of the stream
    segments. Each segment is associated with the pixels matching its ID.

    Once the stream segments are located, applies various optional filters to
    the stream segment network. Returns the IDs of the stream segments that
    passed all the filters. These are the IDs of stream segments appropriate for
    hazard assessment modeling.

    Individual filters are described below. All filters are optional and require
    several inputs. If any of a filter's inputs are provided, then the filter
    will attempt to run. However, the filter will raise an expection if any of
    its inputs are missing.

    filter(..., *, minimum_slope, slopes, ...)
    Removes stream segments whose mean slopes are below a minimum threshold.
    Slopes below the threshold should be too flat to support a debris flow.
    Requires the slopes of the DEM pixels as input. Segment slopes are set as
    the mean slope from all associated pixels.

    filter(..., *, maximum_area, upslope_area, ...)
    Removes stream segments whose upslope area is above a maximum threshold.
    Segments with an upslope area over the threshold should exhibit flood-like
    behavior, and are often tagged as watchstreams. Requires the upslope areas
    of the DEM pixels as input. Segment areas are set as the area from the most
    downstream pixel.

    filter(..., *, maximum_development, upslope_development, ...)
    Removes stream segments whose upslope development is above a maximum threshold.
    Segments with upslope development over the threshold should be too altered
    by human development to support standard debris flow behavior. Requires the
    upslope developed areas of the DEM pixels as input. Segment areas are set as
    the upslope developed area from the most downstream pixel.

    filter(..., *, maximum_confinement, dem, resolution, flow_directions, N, ...)
    removes stream segments whose confinement angle is above a maximum threshold.
    Segments with angles above the threshold should be too confined to support
    the flow of debris. Segment confinement is set as the mean confinement of
    all associated pixels. Requires the DEM, DEM resolution, and D8 flow
    directions as input. D8 flow directions should follow the TauDEM convention,
    wherein flow directions are numbered from 1 to 8, traveling clockwise from right.

    This filter also requires N, which specifies the number of pixels from the
    processing pixel to search when calculating confinement slopes (the slopes
    in the directions perpendicular to flow). For example, for a pixel flowing
    east with N=4, the function will calculate confinement slopes using the
    maximum DEM height from the 4 pixels north and the 4 pixels south.

    filter(..., *, maximum_basins, upslope_basins, ...)
    Removes stream segments whose number of upslope debris-retention basins
    exceeds a maximum threshold. (This threshold is often set to 1). Segments
    with an upslope debris basin should have debris flows contained by the
    basin. Requires the upslope basins of the DEM pixels as input. The upslope
    basins for a segment is set as the number of basins from the most downstream
    pixel.
    ----------
    Inputs:
        stream_raster (2D int numpy.ndarray): A numpy.ndarray representing the
            pixels of a stream link raster. Should be a 2D int array. Stream
            segment pixels should have a value matching the ID of the associated
            stream segment. All other pixels should be 0.
        minimum_slope: A minimum slope. Segments with slopes below this threshold
            will be removed.
        slopes: A numpy 2D array holding the slopes of the DEM pixels
        maximum_area: A maximum upslope area. Segments with upslope areas above
            this threshold will be removed.
        upslope_area: A numpy 2D array holding the total upslope area (also known
            as contributing area or flow accumulation) for the DEM pixels.
        maximum_developement: A maximum amount of upslope development. Segments
            with upslope development above this threshold will be removed.
        upslope_development: A numpy 2D array holding the developed upslope area
            fot the DEM pixels.
        maximum_basins: A maximum number of upslope debris basins. Segments with
            a number of debris basins exceeding this threshold will be removed.
        upslope_basins: A numpy 2D array holding the number of upslope debris basins
            for the DEM pixels.
        maximum_confinement: A maximum confinement angle. Segments with a mean
            confinement angle above this threshold will be removed.
        dem: A numpy 2D array holding the DEM data
        resolution: The resolution of the DEM
        flow_directions: A numpy 2D array holding the flow directions for the
            DEM pixels
        N: The number of raster pixels to search for maximum heights when
            calculating confinement slopes perpendicular to flow.

    Outputs:
        List[int]: The IDs of the stream segments that passed all applied
            filters. These is often the set of stream segments worthy of hazard
            assessment modeling.
    """

    # Find the segments
    segments = locate(stream_raster)

    # Filter
    segments = _filter(
        segments, development, ">", maximum_development, upslope_development
    )
    segments = _filter(segments, area, ">", maximum_area, upslope_area)
    segments = _filter(segments, basins, ">", maximum_basins, upslope_basins)
    segments = _filter(segments, slope, "<", minimum_slope, slopes)
    segments = _filter(
        segments,
        confinement,
        ">",
        maximum_confinement,
        dem,
        flow_directions,
        N,
        resolution,
    )

    # Return the IDs of model-worthy segments
    return segments.keys()


def _filter(segments, function, type, threshold, *args):

    # Only run if at least one of the filter's arguments were given
    if _any_args(threshold, *args):

        # Get segment values and find invalid segments
        values = function(segments, *args)
        if type == ">":
            remove = values > threshold
        elif type == "<":
            remove = values < threshold

        # Remove invalid segments from future filtering
        ids = segments.keys()
        for id in ids[remove]:
            segments.pop(id)
    return segments


def _any_args(*args: Any) -> bool:
    for arg in args:
        if arg is not None:
            return True
    return False


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


def area(segments: segments, upslope_area: np.ndarray) -> np.ndarray:
    """
    area  Returns the maximum upslope area for each stream segment
    ----------
    area(segments, upslope_area)
    Computes the maximum upslope area for each stream segment. Returns the areas
    as a numpy 1D array. Te order of slopes in the output array will match the
    order of keys in the input segments dict.
    ----------
    Inputs:
        segments: A dict mapping stream segment IDs to the indices of the
            associated DEM pixels.
        upslope_area: A numpy 2D array holding the total upslope area (also known
            as contributing area or flow accumulation) for the DEM pixels.

    Outputs:
        numpy 1D array: The maximum upslope area of each stream segment. The
            order of values matches the order of ID keys in the input segments dict.
    """
    return _segment_summary(segments, upslope_area, np.amax)


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
