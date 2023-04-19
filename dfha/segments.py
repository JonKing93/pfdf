"""
segments  Determine stream segments worthy of hazard assessment modeling
----------
The segments module uses various filtering criteria to reduce an initial stream
segment network (produced by the stream module) to a final set of segments worthy
of hazard assessment modeling. Filtering criteria can include:
    
    * Slope
    * Confinement Angle
    * Total upslope area
    * Total developed upslope area
    * Number of upslope debris-retention basins

This module provides two main workflows for filtering stream segments: 
    1. The "filter" function, and
    2. The "Segments" class
The "filter" function is intended for operational users. This function implements
a number of standard filters, and returns the IDs of stream segments deemed 
worthy of hazard assessment modeling. 

By contrast, the "Segments" class is intended for users interested in designing 
custom filtering routines. The class includes a variety of methods that calculate
values for each stream segment in a network - users can use these values to screen
the stream segments as desired. Please see the documention of the "Segments"
class for instructions on this workflow.

Most of the commands in this module operate on raster datasets, and so the module
allows users to provide rasters in a variety of ways. When calling commands, 
users may provide rasters as:
    * A string indicating a raster file path,
    * A pathlib.Path object to a raster file,
    * A rasterio.DatasetReader object, or
    * A 2D numpy array (real-valued)
Note that file-based rasters are loaded using rasterio, and so support nearly all
common raster file formats. You can find a complete list of supported formats
here: https://gdal.org/drivers/raster/index.html
----------
Functions:
    filter              - Filters a network of stream segments

Classes:
    Segments            - Defines a stream segment network and calculates values for the segments

Custom Exceptions:
    RasterShapeError    - When a values raster does not match the shape of the stream segment raster

Internal:
    _Kernel             - Locates raster pixels required for confinement angle focal statistics
    _validate_raster    - Validates a raster for a filter
"""

import numpy as np
from math import sqrt
from copy import deepcopy
from dfha import validate
from dfha.utils import any_defined, load_raster, real
from typing import Any, Dict, Tuple, Literal, Union, Callable, Optional, List
from dfha.typing import (
    shape,
    Raster,
    RasterArray,
    scalar,
    ints,
    ScalarArray,
    VectorShape,
)
from nptyping import NDArray, Shape, Integer, Number, Bool


# Type aliases
PixelValues = NDArray[Shape["Pixels"], Integer]
indices = Dict[int, Tuple[PixelValues, PixelValues]]
SegmentValues = NDArray[Shape["Segments"], Number]
Statistic = Literal["min", "max", "mean", "median", "std"]
StatFunction = Callable[[np.ndarray], np.ndarray]
IDs = Union[ints, NDArray[VectorShape, Integer], NDArray[Shape["Segments"], Bool]]
FlowNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8]
KernelIndices = Tuple[List[int], List[int]]


class Segments:
    """
    Segments  Defines and calculates summary values for set of stream segments
    ----------
    The Segments class is used to manage a set of stream segments derived from a
    stream link raster. The class provides a number of functions that compute
    a summary statistic for each stream segment in the set. For example, the
    mean slope of each stream segment, or the segment's confinement angles.
    Note that summary statistics are only calculated using stream segment
    pixels (roughly, the river bed), and NOT using all the pixels in the segment's
    catchment area.

    These summary values can then be used to filter an initial stream segment
    network to a final set of segments for hazard assessment modeling. A
    typical workflow is to:
        1. Define an initial set of segments by calling Segments() on a stream
           segment raster.*
        2. Use the "area", "basins", "confinement", "development", "slope",
           and/or "summary" methods to return summary values for the segments.
        3. Use the "remove" method to filter out segments whose value don't meet
           the criteria for hazard assessment modeling.
        4. Inspect the "ids" property to get a list of final stream segments

    *See the help for Segments.__init__ for instructions on creating a Segments object

    The "area", "basins", "confinement", "development", and "slope" represent
    standard filters for hazard assessment analysis. However, some users may be
    interested in computing other values for the stream segments. The "summary"
    method is intended for such users. Given a raster of data values, this
    function allows users to calculate common statistical values for the stream
    segments in the network.

    It is worth noting that most methods require input rasters with the same shape
    as the stream segment raster used to derive the initial set of stream segments
    (and will raise an exception when this criterion is not met). Users can 
    retrieve this shape by inspecting the 'raster_shape' property. Separately, 
    users may find the "copy" method useful for testing out different filtering 
    criteria.
    ----------
    PROPERTIES:
        ids             - The list of stream segment IDs remaining in the set
        indices         - A dict mapping each segment ID to the locations of its pixels
        raster_shape    - The shape of the raster used to derive the stream segments.

    METHODS:
    Python built-ins:
        __len__         - Returns the number of segments in the set
        __str__         - Returns a string listing the segment IDs

    Object Creation:
        __init__        - Defines a set of stream segments from a stream segment raster
        copy            - Returns a deep copy of the current object

    Summary Values:
        area            - Returns the maximum upslope area of each segment
        basins          - Returns the maximum number of upslope debris basins of each segment
        confinement     - Returns the mean confinement angle of each segment
        development     - Returns the mean upslope developed area for each segment
        slope           - Returns the mean slope for each segment
        summary         - Returns a generic statistical summary value for each segment

    Filtering:
        remove          - Removes the indicated segments from the Segments object
    """

    # The statistical function for each type of summary value
    _stats = {
        "area": np.amax,
        "basins": np.amax,
        "confinement": np.mean,
        "development": np.mean,
        "slope": np.mean,
    }

    #####
    # Properties
    #####
    @property
    def ids(self) -> SegmentValues:
        "A numpy 1D array listing the stream segment IDs for the object."
        # (Use a numpy array so user can apply logical indexing when filtering)
        ids = list(self.indices.keys())
        return np.array(ids)

    @property
    def indices(self) -> indices:
        """
        A dict mapping each stream segment ID to the indices of its associated
        pixels in the stream segment raster. The value of each key is a 2-tuple
        whose elements are numpy 1D arrays. The first array lists the row indices
        of the pixels, and the second array lists the column indices.
        """
        return self._indices

    @property
    def raster_shape(self) -> Tuple[int, int]:
        "The shape of the stream link raster used to define the stream segments"
        return self._raster_shape

    #####
    # Dunders
    #####
    def __init__(self, stream_raster: Raster) -> None:
        """
        Segments  Returns an object defining a set of stream segments
        ----------
        Segments(stream_raster)
        Given a stream segment raster, builds and returns a Segments object defining
        the set of stream segments in the raster. The stream segment raster should
        consist of integers. The values of the stream segment pixels should be the ID
        of the associated stream segment. All other pixels should be 0.

        Each group of pixels with the same (non-zero) value is interpreted as one
        stream segment. The "ids" property of the returned object lists the stream
        segment IDs in the set. The "indices" property is a dict that maps each
        ID to the indices of associated pixels in the stream segment raster.
        ----------
        Inputs:
            stream_raster: A stream segment raster used to define the set of stream
                segments. May be a path to a raster file, a rasterio.DatasetReader
                or a numpy ndarray. If a raster file or rasterio.DatasetReader object,
                then the raster will be read from the first band. If a numpy array,
                should have 2 dimensions.

                The data in the raster should consist of integers. The value of
                each stream segment pixel should be a positive integer matching
                the ID of the associated strea segment. All other pixels should
                be 0. If reading data from a raster file or a rasterio.DatasetReader,
                NoData values will be converted to 0 before processing.

        Outputs:
            Segments: A Segments object defining a set of stream segments
        """

        # Get raster array. Check values are valid
        name = "stream_raster"
        stream_raster = validate.raster(stream_raster, name, nodata=0)
        validate.positive(stream_raster, name, allow_zero=True)
        validate.integers(stream_raster, name)

        # Get the indices of stream segment pixels. Organize as column vectors
        (rows, cols) = np.nonzero(stream_raster)
        rows = rows.reshape(-1, 1)
        cols = cols.reshape(-1, 1)

        # Reduce the stream link raster to just the segments. Get the segment IDs
        segments = stream_raster[rows, cols].reshape(-1)
        ids = np.unique(segments)

        # Record a dict mapping segments IDs to the indices of their pixels
        # Also record the raster shape
        self._indices = {id: None for id in ids}
        for id in ids:
            pixels = np.nonzero(segments == id)
            indices = (rows[pixels], cols[pixels])
            self._indices[id] = np.hstack(indices)
        self._raster_shape = stream_raster.shape

    def __len__(self) -> int:
        "The number of stream segments in a Segments object"
        return len(self.indices)

    def __str__(self) -> str:
        "A string listing the stream segment IDs in a Segments object"
        ids = self.ids
        ids = [str(id) for id in ids]
        return "Stream Segments: " + ", ".join(ids)

    #####
    # Validation methods
    #####
    def _validate(self, raster: Any, name: str) -> RasterArray:
        """
        _validate  Check input raster if compatible with stream segment pixel indices
        ----------
        self._validate(raster, name)
        Validates the input raster and returns it as a numpy 2D array. A valid
        raster must meet the criteria described in validate.raster AND must have
        a shape matching the shape of the raster used to define the stream segments.
        ----------
        Inputs:
            raster: The input raster being checked
            name: A name for the raster for use in error messages

        Outputs:
            numpy 2D array: The raster as a numpy array
        """

        try:
            return validate.raster(raster, name, shape=self.raster_shape)
        except validate.ShapeError as error:
            raise RasterShapeError(name, error)

    @staticmethod
    def _validate_confinement_args(
        N: Any, resolution: Any
    ) -> Tuple[ScalarArray, ScalarArray]:
        """Validates the kernel size (N) and DEM resolution for confinement angles
        Returns the values as scalar numpy arrays"""
        N = validate.scalar(N, "N", real)
        validate.positive(N, "N")
        validate.integers(N, "N")
        resolution = validate.scalar(resolution, "resolution", real)
        validate.positive(resolution)
        return (N, resolution)

    @staticmethod
    def _validate_flow(flow_directions) -> None:
        "Checks that flow directions conform to the TauDEM style"
        validate.inrange(flow_directions, "flow_directions", min=1, max=8)
        validate.integers(flow_directions, "flow_directions")

    #####
    # Confinement angle calculations
    #####
    @staticmethod
    def _confinement_angle(
        slopes: NDArray[Shape["Pixels, 2 rotations"], Number]
    ) -> ScalarArray:
        """Returns mean confinement angle for a set of pixels
        slopes: (Nx2) ndarray. One column each for clockwise/counterclockwise slopes
            Each row holds the values for one pixel"""
        theta = np.arctan(slopes)
        theta = np.mean(theta, axis=0)
        theta = 180 - np.sum(theta)

    @staticmethod
    def _flow_length(
        flow_direction: FlowNumber, lateral_length: scalar, diagonal_length: scalar
    ) -> scalar:
        """Returns the flow length for a given flow direction
        flow_direction: TauDEM style D8 flow number
        lateral_length: Flow length up/down/right/left
        diagonal_length: Flow length upleft/upright/downleft/downright"""
        if flow_direction % 2 == 0:
            length = diagonal_length
        else:
            length = lateral_length
        return length

    #####
    # Low-level summary values (no error checking)
    #####
    def _confinement(
        self,
        dem: RasterArray,
        flow_directions: RasterArray,
        N: ScalarArray,
        resolution: ScalarArray,
    ) -> SegmentValues:
        """Computes mean confinement angle. Assumes that all inputs are valid
        numpy arrays. Please see the documention of Segments.confinement for 
        additional details on the inputs and computation.
        """

        # Preallocate. Initialize kernel. Get flow lengths
        theta = np.empty(len(self))
        kernel = _Kernel(N, *self.raster_shape)
        lateral_length = resolution * N
        diagonal_length = lateral_length * sqrt(2)

        # Get pixels for each stream segment. Preallocate orthogonal slopes
        for i, id in enumerate(self.ids):
            pixels = self.indices[id]
            nPixels = pixels.shape[0]
            slopes = np.empty((nPixels, 2), dem.dtype)

            # Iterate through pixels as processing cells. Update kernel
            for p, [row, col] in enumerate(pixels):
                kernel.update(row, col)

                # Get flow direction and length. Compute orthogonal slopes
                flow = flow_directions[row, col]
                length = self._flow_length(flow, lateral_length, diagonal_length)
                slopes[p, :] = kernel.orthogonal_slopes(flow, dem, length)

            # Compute and return mean confinement angles
            theta[i] = self._confinement_angle(slopes)
        return theta

    def _filter(
        self,
        method: Callable[["Segments", Tuple[Any, ...]], SegmentValues],
        type: Literal["<", ">"],
        threshold: scalar,
        *args: Any,
    ) -> None:
        """
        _filter  Applies a filter to a set of stream segments
        ----------
        self._filter(method, type, threshold, *args)
        Applies a filter to a set of stream segments and removes segments that
        do not pass the filter. Uses the indicated method to return a set of
        stream segment values, and compares the values to a threshold value.
        If a stream segment's value does not pass the comparison, then the
        segment is removed from the Segments object.
        ----------
        Inputs:
            method: A Segments method that returns a set of segment values
            type:
                '>': Removes segments greater than the threshold
                '<': Removes segments less than the threshold
            threshold: A comparison value for the segment values
            *args: The inputs to the Segments method
        """

        # Only run if at least one of the filter's arguments were given
        if any_defined(threshold, *args):

            # Get segment values and find invalid segments
            values = method(self, *args)
            if type == ">":
                failed = values > threshold
            elif type == "<":
                failed = values < threshold
            self.remove(failed)

    def _summary(self, raster: RasterArray, statistic: StatFunction) -> SegmentValues:
        """
        _summary  Returns a summary value for each stream segment
        ----------
        self._summary(raster, statistic)
        Given a raster of data values, computes a summary statistic for each
        stream segment.
        ----------
        Inputs:
            raster: A raster of data values. Should have the same size as the
                raster used to derive the stream segments
            statistic: A numpy function used to compute a statistic over an array.
                Options are amin, amax, mean, median, and std

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        summary = np.empty(len(self))
        for i, id in enumerate(self.ids):
            pixels = self.indices[id]
            summary[i] = statistic(raster[pixels])
        return summary

    #####
    # User Methods
    #####
    def area(self, upslope_area: Raster) -> SegmentValues:
        """
        area  Returns the maximum upslope area for each stream segment
        ----------
        self.area(upslope_area)
        Computes the maximum upslope area for each stream segment. Returns the areas
        as a numpy 1D array. The order of slopes in the output array will match the
        order of segment IDs in the object.
        ----------
        Inputs:
            upslope_area: The total upslope area (also known as contributing area
                or flow accumulation) for the DEM pixels.

        Outputs:
            numpy 1D array: The maximum upslope area of each stream segment.
        """
        upslope_area = self._validate(upslope_area, "upslope_area")
        return self._summary(upslope_area, self._stats["area"])

    def basins(self, upslope_basins: Raster) -> SegmentValues:
        """
        basins  Returns the maximum number of upslope basins for each stream segment
        ----------
        self.basins(upslope_basins)
        Computes the maximum number of upslope debris retention basins for each
        stream segment. Returns this count as a numpy 1D array. The order of slopes
        in the output array will match the order of segment IDs for the object.
        ----------
        Inputs:
            upslope_basins: The number of upslope debris basins for the DEM pixels

        Outputs:
            numpy 1D array: The maximum number of upslope debris basins for each
                stream segment.
        """
        upslope_basins = self._validate(upslope_basins, "upslope_basins")
        return self._summary(upslope_basins, self._stats["basins"])

    def confinement(
        self,
        dem: Raster,
        flow_directions: Raster,
        N: scalar,
        resolution: scalar,
    ) -> SegmentValues:
        """
        confinement  Returns the mean confinement angle of each stream segment
        ----------
        self.confinement(segments, dem, flow_directions, N, resolution)
        Computes the mean confinement angle for each stream segment. Returns these
        angles as a numpy 1D array. The order of angles matches the order of
        segment IDs in the object.

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
            dem: The digital elevation model (DEM) data
            flow_directions: TauDEM-style D8 flow directions for the DEM pixels
            N: The number of raster pixels to search for maximum heights
            resolution: The resolution of the DEM

        Outputs:
            numpy 1D array: The mean confinement angle for each stream segment.
        """

        # Check user inputs
        (N, resolution) = self._validate_confinement_args(N, resolution)
        flow_directions = self._validate(flow_directions, "flow_directions")
        self._validate_flow(flow_directions)
        dem = self._validate(dem, "dem")

        # Compute mean confinement angle
        return self._confinement(dem, flow_directions, N, resolution)

    def copy(self) -> "Segments":
        """
        copy  Returns a deep copy of a Segments object
        ----------
        self.copy()
        Returns a deep copy of the current Segments object. The new/old objects
        can be altered without affecting one another. This can be useful for
        testing different filtering criteria.
        ----------
        Outputs:
            Segments: A deep copy of the Segments object.
        """
        return deepcopy(self)

    def development(self, upslope_development: Raster) -> SegmentValues:
        """
        development  Returns the mean upslope developed area for each stream segments
        ----------
        self.development(upslope_development)
        Computes the mean developed upslope area for each stream segment. Returns
        these areas as a numpy 1D array. The order of slopes in the output array will
        match the order of segment IDs in the object.
        ----------
        Inputs:
            upslope_development: A numpy 2D array holding the developed upslope area
                fot the DEM pixels.

        Outputs:
            numpy 1D array: The mean developed upslope area of each stream segment.
        """
        upslope_development = self._validate(upslope_development, "upslope_development")
        return self._summary(upslope_development, self._stats["development"])

    def remove(self, ids: IDs) -> None:
        """
        remove  Removes segments from a Segments object
        ----------
        self.remove(segments)
        Removes segments with the indicated IDs from the Segments object. The
        input may either be a numpy 1D integer array-like, or a numpy 1D integer
        array-like with one element per stream segment in the object.

        If using integers, the values indicate the IDs of the segments that should
        be removed. Raises a KeyError if an ID is not in the segments object.

        If using bools, the elements correspond to the IDs returned by the ".ids"
        property. Removes segments corresponding to True elements of the bool array.
        Raises a ShapeError if the bool array-like has a different number of
        elements than the number of segments.
        ----------
        Inputs:
            segments: Indicates which stream segments to remove from the object.
                May use either an integer or boolean syntax. Integers denote
                the IDs of the segments to remove. If booleans, removes the
                segments corresponding to True elements.

        Raises:
            KeyError: If an integer is not a segment ID
            ShapeError: If a boolean array-like does not have exactly one element
                per stream segment in the object.
        """

        # Require numeric or bool vector
        segments = validate.vector(
            segments, "segments", dtype=[np.integer, np.floating, np.bool_]
        )

        # If boolean, require 1 element per segment. Convert to IDs
        if segments.dtype == bool:
            validate.shape_(
                "segments", "element(s)", required=len(self), actual=segments.shape
            )
            segments = self.ids[np.argwhere(segments)].reshape(-1)

        # If not boolean, get the unique inputs and the list of ID keys
        else:
            ids = self.ids
            segments = set(segments)

            # Check each key is in the object
            for i, id in enumerate(segments):
                if id not in ids:
                    raise KeyError(
                        f"Input ID {i} ({id}) is not the ID of a segment in the network. "
                        "See self.ids for a list of current segment IDs."
                    )

        # Remove the IDs
        for id in segments:
            del self.indices[id]

    def slope(self, slopes: Raster) -> SegmentValues:
        """
        slope  Returns the mean slope (rise/run) for each stream segment
        ----------
        self.slope(slopes)
        Computes the mean slope (rise/run) for each stream segment. Returns the slopes
        as a numpy 1D array. The order of slopes in the output array will match the
        order of segment IDs in the object.
        ----------
        Inputs:
            slopes: A numpy 2D array holding the slopes of the DEM pixels

        Outputs:
            numpy 1D array: The mean slope (rise/run) of each stream segment.
        """
        slopes = self._validate(slopes, "slopes")
        return self._summary(slopes, self._stats["slope"])

    def summary(self, raster: Raster, statistic: Statistic) -> SegmentValues:
        """
        summary  Computes a summary statistic for each stream segment
        ----------
        self.summary(raster, statistic)
        Given a raster of data values, computes a generic summary statistic
        for each stream segment. This function can be used to extend filtering
        beyond the built-in summary values. Statistic options include: mean,
        median, std, min, and max.
        ----------
        Inputs:
            raster: A raster of data values over which to compute stream segment
                summary values
            statistic: 'mean', 'median', 'std', 'min', or 'max'

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Supported statistics
        stat_functions = {
            "min": np.amin,
            "max": np.amax,
            "mean": np.mean,
            "median": np.median,
            "std": np.std,
        }

        # Validate user statistic
        statistic = statistic.lower()
        if statistic not in stat_functions:
            supported = ", ".join(stat_functions.keys())
            raise ValueError(
                f"Unsupported statistic ({statistic}). Allowed values are: {supported}"
            )

        # Calculate the summary statistic
        raster = self._validate(raster, "input raster")
        statistic = stat_functions[statistic]
        return self._summary(raster, statistic)


def filter(
    stream_raster: Raster,
    *,
    slopes: Optional[Raster] = None,
    minimum_slope: Optional[scalar] = None,
    upslope_area: Optional[Raster] = None,
    maximum_area: Optional[scalar] = None,
    upslope_development: Optional[Raster] = None,
    maximum_development: Optional[scalar] = None,
    dem: Optional[Raster] = None,
    flow_directions: Optional[Raster] = None,
    N: Optional[scalar] = None,
    resolution: Optional[scalar] = None,
    maximum_confinement: Optional[scalar] = None,
    upslope_basins: Optional[Raster] = None,
    maximum_basins: Optional[scalar] = None,
) -> NDArray[Shape["IDs"], Integer]:
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
        maximum_development: A maximum amount of upslope development. Segments
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

    # Map each filter to its args. Arg order must be threshold, raster, *args
    # Note that the confinement filter should be first. This allows flow
    # direction validation to occur before any computations.
    filters = {
        "confinement": {
            "maximum_confinement": maximum_confinement,
            "dem": dem,
            "flow_directions": flow_directions,
            "N": N,
            "resolution": resolution,
        },
        "area": {"maximum_area": maximum_area, "upslope_area": upslope_area},
        "basins": {"maximum_basins": maximum_basins, "upslope_basins": upslope_basins},

        "development": {
            "maximum_development": maximum_development,
            "upslope_development": upslope_development,
        },
        "slope": {"minimum_slope": minimum_slope, "slopes": slopes},
    }

    # Remove filters with no args
    for filter, args in filters.items():
        if not any_defined(*args.values()):
            del filters[filter]

    # Validate non-raster inputs.
    for filter, input_args in filters.items():
        saved = filters[filter]
        inputs = list(args.items())
        (threshold, value) = inputs[0]
        saved[threshold] = validate.scalar(value, threshold, real)
        if filter == "confinement":
            (N, N_value), (resolution, res_value) = inputs[3:5]
            saved[N], saved[resolution] = segments._validate_confinement_args(N_value, res_value)

    # Build the initial set of stream segments
    segments = Segments(stream_raster)

    # Validate the rasters, but don't load file rasters into memory yet
    for filter, args in filters.items():
        args = list(args.items())
        _validate_raster(filters, filter, segments, args[1])
        if filter == "confinement":
            _validate_raster(filters, filter, segments, args[2])

    # Iterate through filters. Get the comparison type
    for filter, args in filters.item():
        threshold = list(args.keys)[0]
        if threshold.startswith("max"):
            type = ">"
        elif threshold.startswith("min"):
            type = "<"

        # Get threshold and load raster into memory
        args = list(args.values())
        threshold, raster = args[0:2]
        raster = load_raster(raster)

        # Run the confinement filter (which should be first).
        # Delete (possibly large) flow raster when finished
        if filter == 'confinement':
            flow, N, resolution = args[2:]
            segments._validate_flow(flow)
            segments._filter(segments._confinement, type, threshold, raster, flow, N, resolution)
            del flow

        # Run a standard statistical filter
        else:
            statistic = segments._stats[filter]
            segments._filter(segments._summary, type, threshold, raster, statistic)

    # Return the IDs of the segments that passed the filters
    return segments.ids


def _validate_raster(
    filters: Dict[str, Dict], filter: str, segments: Segments, args: Tuple[str, Any]
) -> None:
    'Validates a raster for a filter. Does not read raster files into memory'
    (name, raster) = args
    filters[filter][name] = segments._validate(raster, name, load=False)


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

    The "orthogonal_slopes" function then uses these directional indices to
    calculate slopes perpendicular to the direction of flow. These slopes are
    typically used to compute confinement angles. Note that this class assumes
    that flow direction numbers follow the TauDEM D8 flow number style.
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

        Index utilities:
            lateral     - Returns indices for lateral directions (up, down, left, right)
            diagonal    - Returns indices for diagonal directions (upleft, upright, downleft, downright)
            indices     - Returns the N indices preceding or following a processing cell index
            limit       - Limits indices to the N values closest to the processing cell index

        Confinement Slopes:
            orthogonal_slopes   - Returns the slopes perpendicular to the flow direction
            max_height          - Returns the maximum DEM height in a particular direction
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
    directions = [right, downright, down, downleft, left, upleft, up, upright]

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

    def indices(self, index: int, nMax: int, before: bool) -> List[int]:
        """Returns indices adjacent to a processing cell
        index: An index of the processing cell (row or col)
        nMax: The raster size in the index direction (nRows or nCols)
        before: True for up/left, False for down/right
        """
        if before:
            start = max(0, index - self.N)
            stop = index
        else:
            start = index + 1
            stop = min(nMax, index + self.N + 1)
        return list(range(start, stop))

    @staticmethod
    def limit(N: int, indices: List[int], are_before: bool) -> List[int]:
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
    def max_height(self, flow: int, dem: RasterArray) -> ScalarArray:
        """Returns the maximum height in a particular direction
        flow: Flow direction index
        dem: DEM raster"""
        direction = self.directions[flow]
        heights = dem[direction(self)]
        return np.amax(heights)

    def orthogonal_slopes(
        self, flow: FlowNumber, dem: RasterArray, length: scalar
    ) -> NDArray[Shape["1 pixel, 2 rotations"], Number]:
        """Returns the slopes perpendicular to flow for the current pixel
        flow: TauDEM style D8 flow direction number
        dem: DEM raster
        length: The lateral or diagonal flow length across 1 pixel"""
        clockwise = self.max_height(flow - 7, dem)
        counterclock = self.max_height(flow - 3, dem)
        slopes = np.array([clockwise, counterclock]).reshape(1, 2)
        slopes = slopes - dem[self.row, self.col]
        slopes = slopes / length
        return slopes


class RasterShapeError(Exception):
    "When the shape of a values raster does not match the shape of the stream segment raster"

    def __init__(self, name: str, cause: validate.ShapeError) -> None:
        message = (
            f"The shape of the {name} raster {cause.actual} does not match the "
            f"shape of the stream segment raster used to derive the segments {cause.required}."
        )
        super().__init__(message)
