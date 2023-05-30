"""
segments  Determine stream segments worthy of hazard assessment modeling
----------
The segments module uses various filtering criteria to reduce an initial stream
segment network (produced by the stream module) to a final set of segments worthy
of hazard assessment modeling. Common filtering criteria include:
    
    * Slope
    * Confinement Angle
    * Total upslope area
    * Total developed upslope area
    * Number of upslope debris-retention basins

The workflow for this module proceeds via the "Segments" class. This class provides
a variety of methods that calculate values for each stream segment in a network.
Users can use these values to screen stream segments and reduce the network as
desired. Please see the documentation of the "Segments" class for detailed
instructions on this workflow.

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
Classes:
    Segments            - Defines a stream segment network and calculates values for the segments

Internal Classes:
    _Kernel             - Locates raster pixels required for confinement angle focal statistics
"""

import numpy as np
from math import sqrt
from copy import deepcopy
from dfha import validate, dem
from dfha.utils import load_raster, real, isdata, has_nodata
from dfha.errors import ShapeError, RasterShapeError
from typing import Any, Dict, Tuple, Literal, Union, Callable, Optional, List
from dfha.typing import (
    Raster,
    ValidatedRaster,
    RasterArray,
    scalar,
    ints,
    ScalarArray,
    VectorShape,
    SegmentsShape,
    SegmentValues,
    nodata,
)
from nptyping import NDArray, Shape, Integer, Floating, Bool


# Type aliases
PixelIndices = NDArray[Shape["Pixels"], Integer]
PixelIndices = Tuple[PixelIndices, PixelIndices]
indices = Dict[int, PixelIndices]
Statistic = Literal["min", "max", "mean", "median", "std"]
StatFunction = Callable[[np.ndarray], np.ndarray]
IDs = Union[ints, NDArray[VectorShape, Integer], NDArray[SegmentsShape, Bool]]
FlowNumber = Literal[1, 2, 3, 4, 5, 6, 7, 8]
KernelIndices = Tuple[List[int], List[int]]


class Segments:
    """
    Segments  Defines and calculates summary values for set of stream segments
    ----------
    The Segments class is used to manage a set of stream segments derived from a
    stream link raster. The class provides a number of functions that compute
    a summary statistic for each stream segment in the set. For example, the
    mean slope of each stream segment, or each segment's confinement angle.
    Note that summary statistics are only calculated using stream segment
    pixels (roughly, the river bed), and NOT using all the pixels in the segment's
    catchment area. The one exception is the "catchment_mean" method, which does
    operate over a catchment area.

    These summary values can then be used to filter an initial stream segment
    network to a final set of segments for hazard assessment modeling. A
    typical workflow is to:
        1. Define an initial set of segments by calling Segments() on a stream
           segment raster.*
        2. Use the "basins", "confinement", "development", "pixels", "slope",
           and/or "summary", and "catchment_mean" methods to return summary values
           for the segments.
        3. Use the "remove" method to filter out segments whose values don't meet
           the criteria for hazard assessment modeling.

    *See the help for Segments.__init__ for instructions on creating a Segments object

    The "basins", "confinement", "development", and "slope" methods represent
    standard filters for hazard assessment. The "pixels" method can be used to
    determine total upslope area (another standard filter) by multiplying pixel
    counts by the area of each DEM pixel. Some users may also be interested in
    computing other values for the stream segments. The "summary"
    method is intended for this case. Given a raster of data values, this
    function allows users to calculate common statistical values for the stream
    segments in the network. For example, the mean value of the raster values in
    each segment, or the maximum value from the raster in each segment. See also
    the "catchment_mean" method for computing generic mean values over the pixels
    in each stream segment's catchment area.

    It is worth noting that most methods require input rasters with the same shape
    as the stream segment raster used to derive the initial set of stream segments
    (and will raise an exception when this condition is not met). Users can
    retrieve this shape by inspecting the 'raster_shape' property.

    Separately, users may find the "copy" method useful for testing out different
    filtering criteria.
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

    Specific Values:
        basins          - Returns the maximum number of upslope debris basins of each segment
        confinement     - Returns the mean confinement angle of each segment
        development     - Returns the mean upslope developed area for each segment
        pixels          - Returns the maximum number of upslope pixels for each stream segment
        slope           - Returns the mean slope for each segment

    Generic Values:
        summary         - Returns a statistical summary value for each segment
        catchment_mean  - Returns a mean computed over the catchment area for each segment

    Filtering:
        remove          - Removes the indicated segments from the Segments object

    INTERNAL:
    Class Variables:
        _stats                      - Dict mapping standard filters to statistical functions

    Object Variables:
        _raster_shape               - The shape of the stream segment raster
        _indices                    - Dict mapping segment IDs to pixel indices

    Validation:
        _validate                   - Validates an input raster
        _validate_area              - Validates the area of DEM pixels
        _validate_confinement_args  - Validate kernel size (N) and DEM resolution

    Confinement:
        _confinement                - Computes mean confinement angles for a set of stream segments
        _confinement_angle          - Computes confinement from a set of pixel slopes
        _flow_length                - Returns flow length in a given direction

    Statistics:
        _summary                    - Computes a summary statistic for a set of stream segments
    """

    # The statistical function for each type of summary value
    _stats = {
        "basins": np.amax,
        "confinement": np.mean,
        "development": np.mean,
        "pixels": np.amax,
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
    def __init__(self, stream_raster: Raster, nodata: Optional[scalar] = None) -> None:
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

        Segments(stream_raster, nodata)
        Specifies a NoData value for when the stream raster is a numpy array.
        If the stream raster is a file-based raster, this option is ignored and
        the NoData value is instead determined from the file metadata.
        ----------
        Inputs:
            stream_raster: A stream segment raster used to define the set of stream
                segments. May be a path to a raster file, a rasterio.DatasetReader
                or a numpy ndarray. If a raster file or rasterio.DatasetReader object,
                then the raster will be read from the first band. If a numpy array,
                should have 2 dimensions.

                The data in the raster should consist of integers. The value of
                each stream segment pixel should be a positive integer matching
                the ID of the associated strea segment. All other data pixels
                should be 0. NoData pixels are also treated as 0.
            nodata: A NoData value for when the stream raster is a numpy array.

        Outputs:
            Segments: A Segments object defining a set of stream segments
        """

        # Validate
        name = "stream_raster"
        stream_raster, nodata = validate.raster(
            stream_raster, name, numpy_nodata=nodata
        )
        data_mask = isdata(stream_raster, nodata)
        validate.positive(stream_raster, name, allow_zero=True, isdata=data_mask)
        validate.integers(stream_raster, name, isdata=data_mask)

        # Locate stream segment pixels
        pixels = stream_raster != 0
        if data_mask is not None:
            pixels = pixels & data_mask

        # Get pixel indices for each dimension. Set as 1D arrays
        (rows, cols) = np.nonzero(pixels)
        rows = rows.reshape(-1)
        cols = cols.reshape(-1)

        # Reduce the raster to just the segment pixels. Get the segments IDs
        segments = stream_raster[rows, cols].reshape(-1)
        ids = np.unique(segments)

        # Map each segment ID to its pixels. Also record the raster shape
        self._indices = {id: None for id in ids}
        for id in ids:
            pixels = np.nonzero(segments == id)
            self._indices[id] = (rows[pixels], cols[pixels])
        self._raster_shape = stream_raster.shape

    def __len__(self) -> int:
        "The number of stream segments in a Segments object"
        return len(self.indices)

    def __str__(self) -> str:
        "A string listing the stream segment IDs in a Segments object"
        if len(self) == 0:
            list = "None"
        else:
            list = ", ".join([str(id) for id in self.ids])
        return f"Stream Segments: {list}"

    #####
    # Raster Validation
    #####
    def _validate(
        self,
        raster: Any,
        name: str,
        nodata: Any,
        nodata_name: str = "nodata",
        *,
        load: bool = True,
    ) -> Tuple[ValidatedRaster, nodata]:
        """
        _validate  Check input raster if compatible with stream segment pixel indices
        ----------
        self._validate(raster, name, nodata, nodata_name)
        Validates the input raster. If the raster is a numpy array, also validates
        the NoData value. Returns a 2-tuple whose first element is the raster as
        numpy 2D array. The second element is the NoData value for the array (which
        may either derive from the input nodata option, or from file-based raster
        metadata). Note that a valid raster must both (1) meet the criteria
        described in validate.raster, and (2) have a shape matching the shape of
        the raster used to define the stream segments. Raises a RasterShapeError
        if the shape criterion is not met. Note that "nodata_name" is optional
        and default to "nodata" if not set.

        self._validate(..., *, load=False)
        Returns the Path for file-based rasters, rather than loading and returning
        as a numpy 2D array. Will still return a numpy array when a numpy array
        is provided as the raster input.
        ----------
        Inputs:
            raster: The input raster being checked
            name: A name for the raster for use in error messages
            nodata: A NoData value for when the raster is a numpy array
            nodata_name: An optional name for the NoData value for use in error
                messages. Defaults to "nodata"
            load: True (default) if file-based rasters should be loaded and returned
                as a numpy array. False to return the Path to file-based rasters.

        Outputs:
            numpy 2D array | pathlib.Path: The raster as a numpy array or Path
                to a file-based raster.
            numpy 1D array: The NoData value for a loaded array.

        Raises:
            RasterShapeError: If the shape of the input raster does not match
                the shape of the stream raster used to derive the segments.
        """

        try:
            return validate.raster(
                raster,
                name,
                shape=self._raster_shape,
                load=load,
                numpy_nodata=nodata,
                nodata_name=nodata_name,
            )
        except ShapeError as error:
            raise RasterShapeError(name, error)

    #####
    # Confinement angle calculations
    #####
    @staticmethod
    def _confinement_angle(
        slopes: NDArray[Shape["Pixels, 2 rotations"], Floating]
    ) -> ScalarArray:
        """Returns mean confinement angle given slopes for a set of pixels.
        Slopes should be rise/run - output angle is in degrees.
        slopes: (Nx2) ndarray. One column each for clockwise/counterclockwise
            slopes. Each row holds the values for one pixel"""
        theta = np.arctan(slopes)
        theta = np.mean(theta, axis=0)
        theta = np.sum(theta)
        return 180 - np.degrees(theta)

    @staticmethod
    def _flow_length(
        flow_direction: FlowNumber, lateral_length: scalar, diagonal_length: scalar
    ) -> scalar:
        """Returns the flow length for a given flow direction
        flow_direction: TauDEM style D8 flow number
        lateral_length: Flow length up/down/right/left
        diagonal_length: Flow length upleft/upright/downleft/downright"""
        if flow_direction % 2 == 0:
            return diagonal_length
        else:
            return lateral_length

    #####
    # Low-level summary values (no error checking)
    #####
    def _confinement(
        self,
        dem: RasterArray,
        dem_nodata: nodata,
        flow_directions: RasterArray,
        flow_nodata: nodata,
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

        # Get pixels for each stream segment.
        for i, id in enumerate(self.ids):
            pixels = self.indices[id]

            # Get flow-directions. If any are NoData, set confinement to NaN
            flows = flow_directions[pixels]
            if has_nodata(flows, flow_nodata):
                theta[i] = np.nan
                continue

            # Group indices by pixel. Preallocate slopes
            pixels = np.stack(pixels, axis=-1)
            npixels = pixels.shape[0]
            slopes = np.empty((npixels, 2), dem.dtype)

            # Iterate through pixels and compute confinement slopes
            for p, [row, col], flow in zip(range(0, npixels), pixels, flows):
                kernel.update(row, col)
                length = self._flow_length(flow, lateral_length, diagonal_length)
                slopes[p, :] = kernel.orthogonal_slopes(flow, length, dem, dem_nodata)

            # Compute and return mean confinement angles
            theta[i] = self._confinement_angle(slopes)
        return theta

    def _summary(
        self, raster: RasterArray, statistic: StatFunction, nodata: nodata
    ) -> SegmentValues:
        """
        _summary  Returns a summary value for each stream segment
        ----------
        self._summary(raster, statistic, nodata)
        Given a raster of data values, computes a summary statistic for each
        stream segment. If a stream segment contains NoData values, then the
        statistic for the stream segment is set to NaN.
        ----------
        Inputs:
            raster: A raster of data values. Should have the same size as the
                raster used to derive the stream segments
            statistic: A numpy function used to compute a statistic over an array.
                Options are amin, amax, mean, median, and std
            nodata: A NoData value for the raster. Segments that contain this
                value will receive a NaN value.

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Preallocate. Get the pixel values for each segment
        summary = np.empty(len(self))
        for i, id in enumerate(self.ids):
            pixels = self.indices[id]
            values = raster[pixels]

            # Compute statistic or set to NaN if NoData is present
            if has_nodata(values, nodata):
                summary[i] = np.nan
            else:
                summary[i] = statistic(raster[pixels])
        return summary

    #####
    # User Methods
    #####
    def basins(
        self, upslope_basins: Raster, nodata: Optional[scalar] = None
    ) -> SegmentValues:
        """
        basins  Returns the maximum number of upslope basins for each stream segment
        ----------
        self.basins(upslope_basins)
        Computes the maximum number of upslope debris retention basins for each
        stream segment. Returns this count as a numpy 1D array. The order of
        basin counts in the output array will match the order of segment IDs for
        the object.

        self.basins(upslope_basins, nodata)
        Specifies a NoData value for when the input raster is a numpy array.
        Without this option, all elements of an input numpy array are treated as
        valid. If upslope_basins is a file-based raster, this option is ignored
        and the NoData value is instead determined from the file metadata.
        ----------
        Inputs:
            upslope_basins: A raster holding the number of upslope debris basins
                for the DEM pixels.
            nodata: A NoData value for when the upslope_basins raster is a numpy array.

        Outputs:
            numpy 1D array: The maximum number of upslope debris basins for each
                stream segment.
        """

        upslope_basins, nodata = self._validate(
            upslope_basins, "upslope_basins", nodata
        )
        return self._summary(upslope_basins, self._stats["basins"], nodata)

    def catchment_mean(
        self,
        flow_directions: Raster,
        values: Raster,
        *,
        mask: Optional[Raster] = None,
        npixels: Optional[SegmentValues] = None,
        flow_nodata: Optional[scalar] = None,
        values_nodata: Optional[scalar] = None,
        mask_nodata: Optional[scalar] = None,
        check: bool = True,
    ) -> SegmentValues:
        """
        catchment_mean  Computes mean values over all pixels in stream segment catchment areas
        ----------
        self.catchment_mean(flow_directions, values)
        Computes the mean value over all pixels in the catchment (upslope) area
        for each stream segment. Calculates mean values over an input values raster.
        and returns the mean values as a numpy 1D array. The order of mean values
        matches the order of segment IDs in the object. Note that the values raster
        cannot include negative values.

        Note that this syntax requires computing (1) upslope sums, and (2) pixel
        counts for each stream segment. However, many workflows already use pixel
        counts to filter the stream network and implement other processing. If
        you are using pixel counts for multiple purposes, see below for a more
        efficient sytnax.

        self.catchment_mean(flow_directions, values, *, npixels)
        Specifies the number of pixels for each stream segment. This syntax only
        requires computing upslope sums, so is more efficient when pixels counts
        are already known. If a pixel count is 0, the mean for the associated
        segment is set to NaN.

        self.catchment_mean(flow_directions, values, *, mask)
        Computes a catchment means using only the pixels indicated by a valid
        data mask. True pixels in the mask are included in the means. False
        pixels are excluded. This procedure computes (1) masked upslope sums, and
        (2) masked pixel counts for each stream segment. If there are no valid
        pixels in a stream segment's catchment area, then the mean value for the
        stream segment is set to NaN.

        self.catchment_mean(flow_directions, values, *, mask, npixels)
        Specifies the number of masked pixels for each stream segment. Note that
        these masked pixel counts are not the same as the total pixel counts
        often used to filter stream segments. Rather, they are the number of valid
        pixels in the data mask for each stream segment catchment. If the masked
        pixel count for a stream segment is 0, then the mean value for the segment
        is set to NaN.

        Masked pixel counts can be generated via:

            >>> npixels = dem.upslope_sum(flow_directions, values=mask)
            >>> npixels = self.pixels(npixels)

        However, these masked pixel counts are often less reusable than total
        pixel counts, so this syntax may not be necessary for many cases.
        If you are not reusing the masked pixel counts for a later computation,
        we recommend using the previous syntax instead.

        self.catchment_mean(..., *, flow_nodata)
        self.catchment_mean(..., *, values_nodata)
        self.catchment_mean(..., *, mask_nodata)
        Specify NoData values for when an input raster is a numpy array. Otherwise,
        all elements of input arrays are treated as valid. Ignored if an input
        raster is file-based.

        self.catchment_mean(..., *, check=False)
        Disables validation checks of input rasters. This can speed up the
        processing of large rasters, but may produce unexpected results if any
        of the input rasters contain invalid values.
        ----------
        Inputs:
            flow_directions: A raster with TauDEM-style D8 flow directions for
                the DEM pixels.
            values: A raster of data values for the DEM pixels over which to
                calculate catchment means. All values must be positive.
            npixels: The number of upslope pixels for each stream segment. Values
                must be positive.
            mask: An optional valid data mask used to include/exclude pixels from
                the catchment means. True pixels are included, False are excluded.
            flow_nodata: A NoData value for when flow directions are a numpy array
            values_nodata: A NoData value for when the values are a numpy array
            mask_nodata: A NoData value for when the mask is a numpy array
            check: True (default) to validate input rasters before processing.
                False to disable these checks.

        Outputs:
            numpy 1D array: The catchment mean for each stream segment.
        """

        # Initial validation
        if npixels is not None:
            npixels = validate.vector(npixels, "npixels", dtype=real, length=len(self))
            validate.positive(npixels, "npixels", allow_zero=True)
        flow, flow_nodata = self._validate(
            flow_directions,
            "flow_directions",
            nodata=flow_nodata,
            nodata_name="flow_nodata",
            load=False,
        )
        values, values_nodata = self._validate(
            values,
            "values",
            nodata=values_nodata,
            nodata_name="values_nodata",
            load=False,
        )
        if mask is not None:
            mask, mask_nodata = validate.raster(
                mask,
                "mask",
                numpy_nodata=mask_nodata,
                nodata_name="mask_nodata",
                load=False,
            )

        # Optionally validate array elements
        if check:
            flow_array = load_raster(flow_directions)
            validate.flow(flow_array, "flow_directions", nodata=flow_nodata)
            values_array = load_raster(values)
            validate.positive(
                values_array, "values", allow_zero=True, nodata=values_nodata
            )
            if mask is not None:
                mask = load_raster(mask)
                mask = validate.mask(mask, "mask", nodata="mask_nodata")
                values = values_array  # Loaded array is required for a masked mean

        # Compute the number of pixels if not provided
        if npixels is None:
            if mask is None:
                npixels = dem.upslope_pixels(flow, nodata=flow_nodata, check=False)
            else:
                npixels = dem.upslope_sum(
                    flow,
                    values=mask,
                    flow_nodata=flow_nodata,
                    values_nodata=values_nodata,
                    check=False,
                )
            print(npixels)
            assert False
            npixels = self._summary(npixels, np.amax, values_nodata)
        npixels[npixels == 0] = np.nan
        print(npixels)
        assert False

        # Compute mean values. (Note that since values are positive, np.amax
        # gives the sum from the most downstream pixel).
        upslope_sums = dem.upslope_sum(
            flow,
            values,
            mask,
            flow_nodata=flow_nodata,
            values_nodata=values_nodata,
            mask_nodata=mask_nodata,
            check=False,
        )
        segment_sums = self._summary(upslope_sums, np.amax, values_nodata)
        return segment_sums / npixels

    def confinement(
        self,
        dem: Raster,
        flow_directions: Raster,
        N: scalar,
        resolution: scalar,
        *,
        dem_nodata: Optional[scalar] = None,
        flow_nodata: Optional[scalar] = None,
    ) -> SegmentValues:
        """
        confinement  Returns the mean confinement angle of each stream segment
        ----------
        self.confinement(segments, dem, flow_directions, N, resolution)
        Computes the mean confinement angle for each stream segment. Returns these
        angles as a numpy 1D array. The order of angles matches the order of
        segment IDs in the object.

        This method requires the resolution of the DEM as input. Note that this
        resolution should be provided in the same units as the DEM data. For example,
        if the DEM records elevations in meters, then the DEM resolution should
        also be in meters. Also note that the DEM should be a raw DEM, and not
        a pitfilled version.

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

        self.confinement(..., *, dem_nodata)
        self.confinement(..., *, flow_nodata)
        Specify NoData values for when the DEM and/or flow-directions are a numpy
        array. If these options are not set, all values in an input numpy array
        are treated as valid. If an input raster is file-based, the associated
        NoData option is ignored and the NoData value is instead determined from
        the file metadata.
        ----------
        Inputs:
            dem: A raster of digital elevation model (DEM) data.
            flow_directions: A raster with TauDEM-style D8 flow directions for
                the DEM pixels
            N: The number of raster pixels to search for maximum heights
            resolution: The resolution of the DEM. Should use the same units as
                the DEM data.
            dem_nodata: A NoData value for when the DEM is a numpy array
            flow_nodata: A NoData value for when the flow-directions are a numpy array

        Outputs:
            numpy 1D array: The mean confinement angle for each stream segment.
        """

        # Validate N and resolution
        N = validate.scalar(N, "N", real)
        validate.positive(N, "N")
        validate.integers(N, "N")
        resolution = validate.scalar(resolution, "resolution", real)
        validate.positive(resolution, "resolution")

        # Validate rasters
        flow, flow_nodata = self._validate(
            flow_directions,
            "flow_directions",
            nodata=flow_nodata,
            nodata_name="flow_nodata",
        )
        validate.flow(flow, "flow_directions", nodata=flow_nodata)
        dem = self._validate(dem, "dem", nodata=dem_nodata, nodata_name="dem_nodata")

        # Compute mean confinement angles
        return self._confinement(
            dem, dem_nodata, flow_directions, flow_nodata, N, resolution
        )

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

    def development(
        self, upslope_development: Raster, nodata: Optional[scalar] = None
    ) -> SegmentValues:
        """
        development  Returns the mean number of developed upslope pixels for each stream segment
        ----------
        self.development(upslope_development)
        Computes the mean number of developed upslope pixels for each stream segment.
        Returns these counts as a numpy 1D array. The pixel counts in the output
        array will match the order of segment IDs in the object.

        self.development(upslope_development, nodata)
        Specifies a NoData value for when the upslope_developement raster is a
        numpy array. If not provided, all elements of an input array are treated
        as valid. If upslope_development is file-based, this option is ignored
        and the NoData value is instead determined from the file metadata.
        ----------
        Inputs:
            upslope_development: A raster indicating the number of developed
                upslope pixels for the DEM pixels.
            nodata: A NoData value for when the raster is a numpy array.

        Outputs:
            numpy 1D array: The mean number of developed upslope pixels for each
                stream segment.
        """
        upslope_development, nodata = self._validate(
            upslope_development, "upslope_development", nodata
        )
        return self._summary(upslope_development, self._stats["development"], nodata)

    def pixels(
        self, upslope_pixels: Raster, nodata: Optional[scalar] = None
    ) -> SegmentValues:
        """
        pixels  Returns the maximum number of upslope pixels for each stream segment
        ----------
        self.pixels(upslope_pixels)
        Computes the maximum number of upslope pixels for each stream segment.
        Stream segments with NoData values are given a value of NaN. Returns the
        pixel counts as a numpy 1D array. The order of pixel counts in the output
        array will match the order of segment IDs in the object.

        Note that you can use pixel counts to determine the total upslope area
        (contributing area) for each stream segment by multiplying pixel counts
        by the area of a DEM pixel.

        self.pixels(upslope_pixels, nodata)
        Specifies a NoData value for when the upslope_pixels raster is a numpy
        array. Without this option, all values of an input numpy array are treated
        as valid. If upslope_pixels is a file-based raster, this value is ignored
        and the NoData value is instead determined from file metadata.
        ----------
        Inputs:
            upslope_pixels: A raster holding the number of upslope pixels for
                the DEM pixels.
            nodata: A NoData value for when upslope_pixels is a numpy array.

        Outputs:
            numpy 1D array: The maximum number of upslope pixels for each stream segment.
        """
        upslope_pixels, nodata = self._validate(
            upslope_pixels, "upslope_pixels", nodata
        )
        return self._summary(upslope_pixels, self._stats["pixels"], nodata)

    def remove(self, segments: IDs) -> None:
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
        segments = validate.vector(segments, "segments", dtype=real)

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

    def slope(self, slopes: Raster, nodata: Optional[scalar] = None) -> SegmentValues:
        """
        slope  Returns the mean slope for each stream segment
        ----------
        self.slope(slopes)
        Computes the mean slope for each stream segment. Returns the slopes
        as a numpy 1D array. The order of slopes in the output array will match the
        order of segment IDs in the object.

        self.slope(slopes, nodata)
        Specifies a NoData value for when the slopes raster is a numpy array.
        Without this option, all values of an input numpy array are treated as
        valid. If slopes is a file-based raster, this option is ignored and the
        NoData value is instead determined from the file metadata.
        ----------
        Inputs:
            slopes: A raster holding the slopes of the DEM pixels
            nodata: A NoData value for when slopes is a numpy array

        Outputs:
            numpy 1D array: The mean slope of each stream segment.
        """
        slopes, nodata = self._validate(slopes, "slopes", nodata)
        return self._summary(slopes, self._stats["slope"], nodata)

    def summary(
        self, statistic: Statistic, raster: Raster, nodata: Optional[scalar] = None
    ) -> SegmentValues:
        """
        summary  Computes a summary statistic for each stream segment
        ----------
        self.summary(statistic, raster)
        Given a raster of data values, computes a generic summary statistic
        for each stream segment. This function can be used to extend filtering
        beyond the built-in summary values. Statistic options include: mean,
        median, std, min, and max.

        self.summary(statistic, raster, nodata)
        Specifies a NoData value when the raster is a numpy array. Without the
        nodata option, all elements of an input numpy array are treated
        ----------
        Inputs:
            statistic: 'mean', 'median', 'std', 'min', or 'max'
            raster: A raster of data values over which to compute stream segment
                summary values

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
        if not isinstance(statistic, str):
            raise TypeError("statistic must be a string.")
        statistic = statistic.lower()
        if statistic not in stat_functions:
            supported = ", ".join(stat_functions.keys())
            raise ValueError(
                f"Unsupported statistic ({statistic}). Allowed values are: {supported}"
            )

        # Calculate the summary statistic
        raster, nodata = self._validate(raster, "input raster", nodata)
        statistic = stat_functions[statistic]
        return self._summary(raster, statistic, nodata)


class _Kernel:
    """_Kernel  Locate data values for irregular focal statistics
    ----------
    The _Kernel class helps determine the indices of raster pixels needed to
    implement irregular focal statistics (which are needed to calculate stream
    segment confinement angles). Each _Kernel object represents a focal
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
    def max_height(self, flow: int, dem: RasterArray, nodata: nodata) -> ScalarArray:
        """Returns the maximum height in a particular direction or NaN if there
        are NoData values.
        flow: Flow direction *index* (flow number - 1)
        dem: DEM raster
        nodata: NoData value for the DEM"""
        direction = self.directions[flow]
        heights = dem[direction(self)]
        if has_nodata(heights, nodata):
            return np.nan
        else:
            return np.amax(heights)

    def orthogonal_slopes(
        self, flow: FlowNumber, length: scalar, dem: RasterArray, nodata: nodata
    ) -> NDArray[Shape["1 pixel, 2 rotations"], Floating]:
        """Returns the slopes perpendicular to flow for the current pixel
        flow: TauDEM style D8 flow direction number
        length: The lateral or diagonal flow length across 1 pixel
        nodata: NoData value for the DEM"""
        clockwise = self.max_height(flow - 3, dem, nodata)
        counterclock = self.max_height(flow - 7, dem, nodata)
        heights = np.array([clockwise, counterclock]).reshape(1, 2)
        rise = heights - dem[self.row, self.col]
        slopes = rise / length
        return slopes
