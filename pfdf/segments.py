"""
segments  Determine stream segments worthy of hazard assessment modeling
----------
The segments module provides the "Segments" class. This class provides various
methods for managing the stream segments in a drainage network. Common operations
include:

    * Building a stream segment network
    * Filtering the network to a set of model-worthy segments
    * Calculating values for each segment in the network, and
    * Exporting the network (and associated data value) to GeoJSON

Please see the documentation of the Segments class for details on implementing 
these procedures.
----------
Classes:
    Segments    - Builds and manages a stream segment network
"""

from copy import deepcopy
from math import inf, nan, sqrt
from typing import Any, Callable, Literal, Optional, Self

import fiona
import geojson
import numpy as np
import shapely
from affine import Affine
from geojson import Feature, FeatureCollection
from rasterio.crs import CRS
from rasterio.transform import rowcol

from pfdf import watershed
from pfdf._utils import nodata_, real, validate
from pfdf._utils.kernel import Kernel
from pfdf.errors import RasterTransformError
from pfdf.raster import Raster, RasterInput
from pfdf.typing import (
    BooleanMask,
    FlowNumber,
    Pathlike,
    PixelIndices,
    PropertyDict,
    ScalarArray,
    SegmentIDs,
    SegmentIndices,
    SegmentValues,
    scalar,
    shape2d,
    slopes,
)

# Type aliases
indices = dict[int, PixelIndices]
Statistic = Literal["min", "max", "mean", "median", "std", "sum"]
StatFunction = Callable[[np.ndarray], np.ndarray]
FlowLengths = dict[str, float]

# Supported statistics
_STATS = {
    "min": np.amin,
    "max": np.amax,
    "mean": np.mean,
    "median": np.median,
    "std": np.std,
    "sum": np.sum,
}


class Segments:
    """
    Segments  Builds and manages a stream segment network
    ----------
    The Segments class is used to build and manage a stream segment network. Here,
    a stream segment is approximately equal to the river bed of a drainage basin.
    The class provides a number of functions that compute summary values for each
    stream segment in the set. (For example, the confinement angle of each segment,
    or the mean slope in each segment's catchment basin). These calculations are
    designed with a stream segment network in mind, and so only operate on a small
    fraction of a raster dataset. As such, calculations via a "Segments" object
    are typically faster than computing values over an entire raster dataset.

    WORKFLOW:
    Typical workflow for the "Segments" class is as follows:

        1. Build a stream segment network by initializing a Segments object
        2. Compute data values needed to reduce the network to a set of model-worthy
           segments. (e.g. confinement angle, mean catchment slope, the proportion
           of burned upslope area)
        3. Remove unworthy segments via the "remove" method
        4. Use the Segments object to calculate inputs for various models
           (e.g. Gartner et al. 2014; Staley et al. 2017; Cannon et al. 2010)
        5. Use the "export" method to write the network (and associated data values)
           to a GeoJSON file.

    The following sections provide additional details for these procedures.

    BUILDING A NETWORK:
    You can build an initial stream segment network by initializing a Segments
    object. There are two essential input for this procedure: (1) A D8 flow
    directions raster (see the pfdf.watershed module to produce this), and
    (2) a raster mask indicating watershed pixels that may potentially be stream
    segments. Note that the flow direction raster must have (affine) transform
    metadata. The raster is also required to have square pixels - rectangular
    pixels are currently unsupported.

    In part, the mask is used to limit stream segments to watershed pixels that
    likely represent a physical stream bed. To do so, the mask will typically
    limit the stream segments to pixels that exceed some minimum flow accumulation.
    The mask might also remove certain areas from the hazard modeling process.
    For example, a mask might screen out pixels in large bodies of water, or
    below human development in order to prevent hazard modeling in these areas.

    When building a stream segment network, you may also provide an optional
    maxmimum length. In this case, any stream segments exceeding the indicated
    length will be split into multiple pieces in the Segments object.

    BASIC PROPERTIES:
    A Segments object includes a number of properties with information about the
    stream segment network. The "length" property returns the total number of
    segments in the network, and "segments" returns a list of shapely.LineString
    objects representing the segments. The coordinates in the LineStrings are ordered
    from upstream to downstream. The "crs" property reports the coordinate reference
    system associated with the LineString coordinates, and can be used to locate the
    segments spatially. "npixels" indicates the total number of pixels in the
    catchment of each segment. Each segment in the network is assigned a unique
    integer ID. The ID for a given segment is constant, so will not change if other
    segments are removed from the netwokr. You can return the list of current
    segment IDS using "ids".

    STREAM SEGMENT RASTER:
    Although the stream segments are often represented as vector features (via the
    shapely.LineString objects), the network can also be represented as a raster.
    This raster consists of a 0 background, with stream segments indicated by
    non-zero values. The value of each non-zero pixel will match the ID of the
    associated stream segment. Junction points (pixels where multiple segments
    meet) are always assigned to the most downstream segment. You can use the
    "raster" method to return this raster.

    Several properties/methods also return information about this raster. The
    "indices" property returns a dict mapping stream segment IDs to the row and
    column indices of the associated pixels, and the "outlets" method returns the
    row and column index of the most downstream pixel for each segment. Separately,
    the "resolution" and "pixel_area" properties return the cell spacing and area
    of a single pixel. The units of these measurements will be in the base units
    of the coordinate reference system associated with the network. In practice,
    these are almost always units of meters.

    WORKING WITH INPUT RASTERS:
    Many Segments methods compute a statistical summary over an input raster.
    There are two common cases for computing statistical summaries: (1) Computing
    values over the pixels in a stream segment, or (2) Computing values over all
    pixels in the catchment area of a stream segment. For case 1, recall that stream
    segment pixels can be returned using the "indices" property, and visualized
    using the output of the "raster" method. For case 2, stream segment catchment
    basins are defined as all pixels that eventually flow into the most downstream
    pixel in the stream segment. Recall that the "outlets" method can be used to
    return the most downstream pixel for each segment, and note that the watershed
    module includes the catchment function, which can be used to return the catchment
    mask for a given pixel.

    When providing an input raster, the raster must match the shape, crs, and
    affine transformation of the flow directions raster used to derive the stream
    segment network. You can return these values using the "raster_shape", "crs",
    and "transform" properties. You can also return the full flow directions raster
    using the "flow" property. If an input raster does not have a crs or transform,
    then it is assumed to have the same crs or transform as the flow directions
    raster used to derive the stream segment network.

    COMPUTING SEGMENT VALUES:
    Many Segments methods return a statistical summary or physical value for each
    segment in the network. Currently, the class supports a number of specific
    variables commonly used for hazard assessment. These include the upslope
    area (basic or masked), burned upslope area, the proportion of burned upslope
    ratio (the burn ratio), confinement angle, mean catchment soil KF-factor, mean
    catchment dNBR / 1000, mean catchment soil thickness / 100, mean catchment
    sin(theta), the vertical relief (change in elevation from a segment outlet to
    its nearest ridge cell), topographic ruggedness (relief / sqrt(area), and the
    proportion of catchment area meeting a criterion (the upslope ratio).

    The class also provides two generic methods for calculating custom statistical
    summaries from a raster of data values. The "summary" method computes a statistic
    over the pixels in each segment, and the "catchment" method computes a statistic
    over all the pixels in the catchment basin of each segment. (And note that the
    catchment method also supports masked statistical summaries). Both functions
    allow you to calculate the sum, mean, median, min, max, or standard deviation
    of the relevant pixels. When computing catchment statistics, we recommend
    using catchment means or sums whenever possible, as these values are typically
    efficient to compute. The remaining catchment statistics require a less efficient
    algorithm, and so often take a long time to calculate.

    NETWORK FILTERING:
    If is sometimes desirable to limit a stream segment network to some subset of its
    segments. For example, to select model-worthy segments from an initial network.
    The Segments object includes 3 methods to help modify the network. The "remove"
    method will remove the indicated segments from the network. After calling
    remove, the removed segments are deleted from the object. Any statistical
    summaries or physical variables will only be calculated for the remaining
    segments, and object properties will not contain values for the
    deleted segments. Similarly, the "raster" method will return a raster that
    only contains the remaining segments. Note that a stream segment's ID is not
    affected by segment removal. Although an ID may be removed from the network,
    the individual IDs are constant, and are not renumbered when the network
    becomes smaller.

    The "keep" method is essentially the inverse of "remove" and will limit the
    network to the indicated segments, discarding all others. The keep and remove
    methods permanently alter a Segments object, and discarded segments cannot
    be recovered after removal. However, you can use the "copy" method to create
    a copy of an object before altering it. This method creates a deep copy of the
    network (rather than a view), so you can remove segments from one copy without
    affecting the other.

    EXPORTING TO GEOJSON:
    It is often useful to export a Segments object to a format for visualization.
    Specifically, as a set of vector features, optionally tagged with associated
    data values. To support this, the Segments class provides two methods that
    export a network to GeoJSON. The "geojson" method exports a network to a
    geojson.FeatureCollection whose individual Features are LineStrings. Similarly,
    the "save" method saves the network to a geojson file.

    Both methods allow an optional properties input, which can be used to tag
    the LineStrings with relevant data values. The properties input should be a
    dict whose keys are the names of data fields (as strings), and whose values
    are 1D numpy arrays with one element per segment in the network. Currently,
    the class supports numeric, real-valued properties, so the array dtypes should
    be integer, floating-point, or boolean. There are no required data fields,
    so you may use any names supported by geojson.
    ----------
    **FOR USERS**
    Object Creation:
        __init__            - Builds an initial stream segment network

    Properties (stream segments):
        segments            - A list of shapely.LineString objects representing the stream segments
        length              - The number of segments in the network
        ids                 - A unique integer ID associated with each stream segment
        indices             - A dict mapping each segment ID to its associated pixels in the stream raster
        crs                 - The coordinate reference system associated with the network
        npixels             - The number of pixels in the catchment basin of each stream segment

    Properties (flow raster):
        flow                - The flow direction raster used to build the network
        raster_shape        - The shape of the flow direction raster
        transform           - The affine transformation associated with the flow raster
        resolution          - The resolution of the flow raster pixels
        pixel_area          - The area of a raster pixel

    Python built-ins:
        __len__             - The number of segments in the network
        __str__             - A string representing the network

    Stream Raster:
        raster              - Returns the stream raster associated with the network
        outlets             - Returns the indices of the outlet pixel for each stream segment

    Generic Statistics:
        summary             - Computes a summary statistic over the pixels for each segment
        catchment           - Computes a summary statistc over the catchment pixels for each segment

    Specific Variables:
        area                - Returns the total upslope area for each segment
        burn_ratio          - Returns the proportion of burned area in each segment's catchment
        burned_area         - Returns the burned upslope area for each segment
        confinement         - Returns the confinement angle for each segment
        kf_factor           - Returns mean catchment KF-factor for each segment
        scaled_dnbr         - Mean catchment dNBR / 1000 for each segment
        scaled_thickness    - Mean catchment soil thickness / 100 for each segment
        sine_theta          - Mean catchment sin(theta) for each segment
        slope               - Mean catchment slope for each segment
        relief              - Vertical relief to highest ridge cell for each segment
        ruggedness          - Topographic ruggedness (relief / sqrt(area)) for each segment
        upslope_ratio       - The proportion of catchment pixels that meet a criteria for each segment

    Filtering:
        copy                - Returns a deep copy of the Segments object
        keep                - Restricts the network to the indicated segments
        remove              - Removes indicated segments from the network

    Export:
        geojson             - Returns the network as a geojson.FeatureCollection
        save                - Saves the network to a GeoJSON file.

    INTERNAL
    Attributes:
        _flow                   - The flow direction raster for the watershed
        _segments               - A list of shapely LineStrings representing the segments
        _indices                - A dict mapping segment IDs to raster pixels
        _npixels                - The number of upslope pixels for each stream segment

    Validation:
        _validate               - Checks that a value raster's metadata matches that of the flow raster
        _validate_resolution    - Checks that pixels are square and returns resolution
        _validate_properties    - Checks that a GeoJSON properties dict is valid

    Utilities:
        _preallocate            - Initializes an array to hold segment summary values
        _accumulation           - Computes flow accumulation for each segment
        _outlet_values          - Returns the values at the outlet pixels

    Statistics:
        _summarize              - Computes a generic summary statistic
        _catchment_summary      - Computes statistical summaries by iterating over catchment basins

    Confinement Angles:
        _segment_confinement    - Computes the confinement angle for a stream segment
        _pixel_slopes           - Computes confinement slopes for a pixel
    """

    #####
    # Dunders
    #####
    def __init__(
        self,
        flow: RasterInput,
        mask: RasterInput,
        max_length: scalar = inf,
    ) -> None:
        """
        __init__  Creates a new Segments object
        ----------
        Segments(flow, mask)
        Builds a Segments object to manage the stream segments in a drainage network.
        Note that stream segments approximate the river beds in the drainage basin,
        rather than the full catchment basins. The returned object records the
        pixels associated with each segment in the network.

        The stream segment network is determined using a (TauDEM-style) D8 flow direction
        raster and a raster mask. Note the the flow direction raster must have
        (affine) transform metadata. The mask is used to indicate the pixels under
        consideration as stream segments. True pixels may possibly be assigned to a
        stream segment, False pixels will never be assiged to a stream segment. The
        mask typically screens out pixels with low flow accumulations, and may include
        other screenings - for example, to remove pixels in large bodies of water, or
        pixels below developed areas.

        Segments(flow, mask, max_length)
        Also specifies a maximum length for the segments in the network. Any segment
        longer than this length will be split into multiple pieces. The split pieces
        will all have the same length, which will be <= max_length. The units of
        max_length should be the base units of the (affine) transform associated
        with the flow raster. In practice, this is usually units of meters. The
        maximum length must be at least as long as the diagonal of the raster pixels.
        ----------
        Inputs:
            flow: A TauDEM-style D8 flow direction raster
            mask: A raster whose True values indicate the pixels that may potentially
                belong to a stream segment.
            max_length: A maximum allowed length for segments in the network. Units
                should be the same as the units of the (affine) transform for the
                flow raster.

        Outputs:
            Segments: A Segments object recording the stream segments in the network.
        """

        # Initialize attributes
        self._flow: Raster = None
        self._segments: list[shapely.LineString] = None
        self._indices: indices = {}
        self._npixels: SegmentValues = None

        # Validate and record flow raster
        flow = Raster(flow, "flow directions")
        if flow.transform is None:
            raise RasterTransformError(
                "The flow direction raster must have (affine) transform metadata."
            )
        self._flow = flow

        # max length cannot be shorter than a pixel diagonal
        max_length = validate.scalar(max_length, "max_length", dtype=real)
        if max_length < flow.pixel_diagonal:
            raise ValueError(
                f"max_length (value={max_length}) must be at least as long as the "
                f"diagonals of the pixels in the flow direction raster (length={flow.pixel_diagonal})."
            )

        # Calculate network
        self._segments = watershed.network(self.flow, mask, max_length)

        # Locate pixel indices for each segment. If the first two indices are
        # identical, then this is downstream of a split point
        split = False
        for s, segment in enumerate(self.segments):
            coords = np.array(segment.coords)
            rows, cols = rowcol(flow.transform, xs=coords[:, 0], ys=coords[:, 1])
            if rows[0] == rows[1] and cols[0] == cols[1]:
                split = True

            # If the segment is downstream of a split point, then remove the
            # first index so that raster pixels are assigned to the correct
            # portion of the split segment
            if split:
                del rows[0]
                del cols[0]
                split = False

            # If the final two indices are identical, then the next segment
            # is downstream of a split point.
            if rows[-1] == rows[-2] and cols[-1] == cols[-2]:
                split = True

            # Record pixel indices. Remove the final coordinate so that junctions
            # are assigned to the downstream segment. Also compute flow accumulation
            self._indices[s + 1] = (rows[:-1], cols[:-1])
        self._npixels = self._accumulation()

    def __len__(self) -> int:
        "The number of stream segments in a Segments object"
        return len(self.indices)

    def __str__(self) -> str:
        "String representation of the object"
        return f"A network of {self.length} stream segments."

    #####
    # Properties
    #####

    ##### Vector-derived properties

    @property
    def segments(self) -> list[shapely.LineString]:
        "A list of shapely LineStrings representing the stream segments"
        return self._segments

    @property
    def length(self) -> int:
        "The number of stream segments in the network"
        return len(self.segments)

    @property
    def indices(self) -> indices:
        """
        A dict mapping each stream segment ID to the indices of its associated
        pixels. The value of each key is a 2-tuple whose elements are numpy 1D
        arrays. The first array lists the row indices of the pixels, and the
        second array lists the column indices.
        """
        return self._indices

    @property
    def ids(self) -> SegmentValues:
        "A numpy 1D array listing the stream segment IDs for the object."
        # (Uses a numpy array so user can apply logical indexing when filtering)
        ids = list(self.indices.keys())
        return np.array(ids)

    ##### Raster-derived properties

    @property
    def flow(self) -> Raster:
        "The flow direction raster used to build the network"
        return self._flow

    @property
    def raster_shape(self) -> shape2d:
        "The shape of the stream segment raster"
        return self.flow.shape

    @property
    def crs(self) -> CRS:
        "The coordinate reference system of the stream segment raster"
        return self.flow.crs

    @property
    def transform(self) -> Affine:
        "The affine transformation of the stream segment raster"
        return self.flow.transform

    @property
    def resolution(self) -> float:
        "The resolution of the stream segment raster pixels"
        return self.flow.resolution

    @property
    def pixel_area(self) -> float:
        "The area of the stream segment raster pixels in the units of the transform"
        return self.flow.pixel_area

    @property
    def npixels(self) -> SegmentValues:
        "The number of pixels in the catchment basin of each stream segment"
        return self._npixels

    #####
    # Stream raster
    #####

    def raster(self) -> Raster:
        """
        raster  Returns the stream segment raster for the network
        ----------
        self.raster()
        Builds a stream segment raster for the segments in the drainage network.
        Non-zero pixels indicate stream segments. The value of a stream segment
        pixel is the ID of the associated stream segment. Note that pixels at
        junction points are always assigned to the most downstream segment.
        ----------
        Outputs:
            Raster: A raster representing the stream segment network.
        """

        raster = np.zeros(self.raster_shape, dtype=int)
        for id, (rows, cols) in self.indices.items():
            raster[rows, cols] = id
        return Raster.from_array(
            raster, nodata=0, transform=self.transform, crs=self.crs
        )

    def outlets(self) -> list[tuple[int, int]]:
        """
        outlets  Returns the indices of the drainage basin outlets
        ----------
        self.outlets()
        Returns the row and column indices of the drainage basin outlets in the
        stream segment raster. There is one outlet per segment in the network.
        Each outlet is the most downstream pixel for the associated
        segment. Returns a list of 2-tuples with one element per stream
        segment. Each 2-tuple holds the row index and the column index (in that
        order) of the outlet pixel for the associated stream segment.
        ----------
        Outputs:
            list[tuple[int, int]]: A list of outlet pixel indices. Each element
                is a 2-tuple with the row index and column index of an outlet pixel
        """

        outlets = []
        for pixels in self.indices.values():
            row = pixels[0][-1]
            col = pixels[1][-1]
            outlets.append((row, col))
        return outlets

    #####
    # Validation
    #####

    def _validate(self, raster: Any, name: str) -> Raster:
        "Checks that an input raster has metadata matching the flow raster"
        return self.flow._validate(raster, name)

    def _validate_indices(self, ids: Any, indices: Any) -> SegmentIndices:
        "Validates IDs and/or logical indices and returns them as logical indices"

        # Default or validate logical indices
        if indices is None:
            indices = np.zeros(self.length, bool)
        else:
            indices = validate.vector(
                indices, "indices", dtype=real, length=self.length
            )
            indices = validate.boolean(indices, "indices")

        # Default or validate IDs.
        if ids is None:
            ids = np.zeros(self.length, bool)
        else:
            ids = validate.vector(ids, "ids", dtype=real)
            validate.integers(ids, "ids")

            # Ensure IDs exists
            ids = np.unique(ids)
            all_ids = self.ids
            for i, id in enumerate(ids):
                if id not in all_ids:
                    raise KeyError(
                        f"Input ID {i} (value={id}) is not the ID of a segment in the network. "
                        "See self.ids for a list of current segment IDs."
                    )

            # Convert IDs to logical indices. Return union of IDs and indices
            ids = np.isin(all_ids, ids)
        return ids | indices

    def _validate_properties(self, properties: Any) -> PropertyDict:
        "Checks that a GeoJSON properties dict is valid"

        # Properties are optional, use an empty dict if None
        if properties is None:
            return {}

        # Otherwise, require a dict with string keys
        if not isinstance(properties, dict):
            raise TypeError("properties must be a dict")
        for k, key in enumerate(properties.keys()):
            if not isinstance(key, str):
                raise ValueError(
                    f'The keys of "properties" must all be strings, but key {k} is not.'
                )

            # Values must be floating-point numpy 1D arrays with one element per segment
            name = f"properties['{key}']"
            properties[key] = validate.vector(
                properties[key], name, length=self.length, dtype=real
            ).astype(float)
        return properties

    #####
    # Variable Utilties
    #####

    def _preallocate(self, dtype: type = float) -> SegmentValues:
        "Preallocates an array to hold segment summary values"
        return np.empty(self.length, dtype)

    def _accumulation(
        self, weights: Optional[RasterInput] = None, mask: Optional[RasterInput] = None
    ) -> SegmentValues:
        "Computes flow accumulation values for the segments."

        # Default case is just npixels
        if (weights is None) and (mask is None) and (self._npixels is not None):
            return self.npixels

        # Otherwise, compute the accumulation at each outlet
        accumulation = watershed.accumulation(self.flow, weights, mask)
        return self._outlet_values(accumulation)

    def _outlet_values(self, raster: Raster) -> SegmentValues:
        "Returns the values at the segment outlets"
        values = self._preallocate()
        for k, outlet in enumerate(self.outlets()):
            values[k] = raster.values[outlet]
        return values

    #####
    # Confinement angles
    #####

    def confinement(
        self,
        dem: RasterInput,
        neighborhood: scalar,
        factor: scalar = 1,
    ) -> SegmentValues:
        """
        confinement  Returns the mean confinement angle of each stream segment
        ----------
        self.confinement(dem, neighborhood)
        Computes the mean confinement angle for each stream segment. Returns these
        angles as a numpy 1D array. The order of angles matches the order of
        segment IDs in the object.

        The confinement angle for a given pixel is calculated using the slopes in the
        two directions perpendicular to stream flow. A given slope is calculated using
        the maximum DEM height within N pixels of the processing pixel in the
        associated direction. Here, the number of pixels searched in each direction
        (N) is equivalent to the "neighborhood" input. The slope equation is thus:

            slope = max height(N pixels) / (N * length)

        where length is one of the following:
            * X axis resolution (for flow along the Y axis)
            * Y axis resolution (for flow along the X axis)
            * length of a raster cell diagonal (for diagonal flow)
        Recall that slopes are computed perpendicular to the flow direction,
        hence the use X axis resolution for Y axis flow and vice versa.

        The confinment angle is then calculated using:

            theta = 180 - tan^-1(slope1) - tan^-1(slope2)

        and the mean confinement angle is calculated over all the pixels in the
        stream segment.

        Example:
        Consider a pixel flowing east with neighborhood=4. (East here indicates
        that the pixel is flowing to the next pixel on its right - it is not an
        indication of actual geospatial directions). Confinement angles are then
        calculated using slopes to the north and south. The north slope is
        determined using the maximum DEM height in the 4 pixels north of the
        stream segment pixel, such that:

            slope = max height(4 pixels north) / (4 * Y axis resolution)

        and the south slope is computed similarly. The two slopes are used to
        compute the confinement angle for the pixel, and this process is then
        repeated for all pixels in the stream segment. The final value for the
        stream segment will be the mean of these values.

        Important!
        This syntax requires that the units of the DEM are the same as the units
        of the stream segment resolution (which you can return using the ".resolution"
        property). Use the following syntax if this is not the case.

        self.confinement(dem, neighborhood, factor)
        Also specifies a multiplicative constant needed to scale the stream segment
        raster resolution to the same units as the DEM. If the raster resolution
        uses different units than the DEM data, then confinement slopes will be
        calculated incorrectly. Use this syntax to correct for this.
        ----------
        Inputs:
            dem: A raster of digital elevation model (DEM) data. Should have
                square pixels.
            neighborhood: The number of raster pixels to search for maximum heights.
                Must be a positive integer.
            factor: A multiplicative constant used to scale the stream segment raster
                resolution to the same units as the DEM data.

        Outputs:
            numpy 1D array: The mean confinement angle for each stream segment.
        """

        # Validate
        neighborhood = validate.scalar(neighborhood, "neighborhood", real)
        validate.positive(neighborhood, "neighborhood")
        validate.integers(neighborhood, "neighborhood")
        factor = validate.scalar(factor, "factor", real)
        validate.positive(factor, "factor")
        dem = self._validate(dem, "dem")

        # Preallocate. Initialize kernel
        theta = self._preallocate()
        kernel = Kernel(neighborhood[0], *self.raster_shape)

        # Determine flow lengths
        width, height = self.resolution
        scale = neighborhood * factor
        lengths = {
            "horizontal": width * scale,
            "vertical": height * scale,
            "diagonal": sqrt(width**2 + height**2) * scale,
        }

        # Get the mean confinement angle for each stream segment
        for i, pixels in enumerate(self.indices.values()):
            theta[i] = self._segment_confinement(pixels, lengths, kernel, dem)
        return theta

    def _segment_confinement(
        self,
        pixels: PixelIndices,
        lengths: dict[str, float],
        kernel: Kernel,
        dem: Raster,
    ) -> ScalarArray:
        "Computes the mean confinement angle for a stream segment"

        # Get the flow directions. If any are NoData, set confinement to NaN
        flows = self.flow.values[pixels]
        if nodata_.isin(flows, self.flow.nodata):
            return nan

        # Group indices by pixel. Preallocate slopes
        pixels = np.stack(pixels, axis=-1)
        npixels = pixels.shape[0]
        slopes = np.empty((npixels, 2), dtype=float)

        # Get the slopes for each pixel
        for p, flow, rowcol in zip(range(npixels), flows, pixels):
            slopes[p, :] = self._pixel_slopes(flow, lengths, rowcol, kernel, dem)

        # Compute the mean confinement angle
        theta = np.arctan(slopes)
        theta = np.mean(theta, axis=0)
        theta = np.sum(theta)
        return 180 - np.degrees(theta)

    @staticmethod
    def _pixel_slopes(
        flow: FlowNumber,
        lengths: dict[str, float],
        rowcol: tuple[int, int],
        kernel: Kernel,
        dem: Raster,
    ) -> slopes:
        "Computes the slopes perpendicular to flow for a pixel"

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

    #####
    # Generic statistical summaries
    #####

    @staticmethod
    def _summarize(
        statistic: StatFunction, raster: Raster, indices: PixelIndices | BooleanMask
    ) -> ScalarArray:
        """Compute a summary statistic over indicated pixels. Sets to NaN if Nodata
        is present, or if no data elements are selected."""

        values = raster.values[indices]
        if values.size == 0 or nodata_.isin(values, raster.nodata):
            return nan
        else:
            return statistic(values)

    def summary(self, statistic: Statistic, values: RasterInput) -> SegmentValues:
        """
        summary  Computes a summary statistic for each stream segment
        ----------
        self.summary(statistic, values)
        Computes a generic summary statistic for each stream segment. Each summary
        value is computed over the associated stream segment pixels. Statistic
        options include: sum, mean, median, min, max, and standard deviation.
        ----------
        Inputs:
            statistic: 'sum', 'mean', 'median', 'min', 'max', or 'std'
            values: A raster of data values over which to compute stream segment
                summary values

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        statistic = _STATS[statistic]
        values = self._validate(values, "values raster")

        # Compute the summary
        summary = self._preallocate()
        for i, pixels in enumerate(self.indices.values()):
            summary[i] = self._summarize(statistic, values, pixels)
        return summary

    def catchment(
        self,
        statistic: Statistic,
        values: RasterInput,
        mask: Optional[RasterInput] = None,
    ) -> SegmentValues:
        """
        catchment  Compute a generic summary statistic over stream segment catchment basins
        ----------
        self.catchment(statistic, values)
        Computes the indicated statistic over the catchment basin of each stream
        segment using the input data values. Returns a numpy 1D array with one
        element per stream segment. Supported statistics include: sum, mean,
        median, min, max, and standard deviation. Note that the sum and mean
        statistics usually compute much faster than the other statistics.

        self.catchment(statistic, values, mask)
        Computes masked statistics over the catchment basins. True elements in the
        mask indicate pixels that should be included in statistics. False elements
        are ignored. If a catchment does not contain any True pixels, then its
        summary statistic is set to NaN.
        ----------
        Inputs:
            statistic: 'sum', 'mean', 'median', 'min', 'max', or 'std'
            values: A raster of data values over which to compute stream segment
                summary values
            mask: An optional Raster that masks the values raster. True elements
                are used to compute summary statistics. False elements are ignored.

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = self._validate(values, "values raster")
        if mask is not None:
            mask = self._validate(mask, "mask")
            mask = validate.boolean(mask.values, mask.name, nodata=mask.nodata)

        # Sum
        if statistic == "sum":
            sums = self._accumulation(values, mask=mask)
            npixels = self._accumulation(mask=mask)
            sums[npixels == 0] = nan
            return sums

        # Mean
        elif statistic == "mean":
            sums = self._accumulation(values, mask=mask)
            npixels = self._accumulation(mask=mask)
            npixels[npixels == 0] = nan
            return sums / npixels

        # Anything else needs to iterate through catchment basins
        else:
            return self._catchment_summary(_STATS[statistic], values, mask)

    def _catchment_summary(
        self, statistic: StatFunction, values: Raster, mask: BooleanMask | None
    ) -> SegmentValues:
        "Computes catchment summary statistics by iterating through catchment basins"

        summary = self._preallocate()
        for k, outlet in enumerate(self.outlets()):
            catchment = watershed.catchment(self.flow, *outlet).values
            if mask is not None:
                catchment = catchment & mask
            summary[k] = self._summarize(statistic, values, catchment)
        return summary

    #####
    # Variables
    #####

    def area(self, mask: Optional[RasterInput] = None) -> SegmentValues:
        """
        area  Returns the upslope (contributing) area for each stream segment
        ----------
        self.area()
        Computes the total upslope (contributing) area for each stream segment.
        The returned area will be in the same units as the pixel area property.

        self.area(mask)
        Computes a masked upslope area for each stream segment. True elements in
        the mask indicate pixels that should be included in the calculation of
        upslope areas. False elements are ignored.
        ----------
        Inputs:
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute upslope areas.

        Outputs:
            numpy 1D array: The upslope (contributing) area for each stream segment
        """

        if mask is None:
            N = self.npixels
        else:
            N = self._accumulation(mask=mask)
        return N * self.pixel_area

    def burn_ratio(self, isburned: RasterInput) -> SegmentValues:
        """
        burn_ratio  Returns the proportion of burned pixels in each segment's catchment
        ----------
        self.burn_ratio(isburned)
        Given a mask of burned pixel locations, determines the proportion of
        burned pixels in the catchment of each stream segment. Returns a numpy
        1D array with the ratio for each segment. Ratios are on the interval from
        0 to 1.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations
                of burned pixels in the watershed

        Outputs:
            numpy 1D array: The proportion of burned pixels for each stream segment
        """
        return self.upslope_ratio(isburned)

    def burned_area(self, isburned: RasterInput) -> SegmentValues:
        """
        burned_area  Returns the total burned area for each segment's catchment
        ----------
        self.burned_area(isburned)
        Given a mask of burned pixel locations, returns the total burned area in
        the catchment of each stream segment. Returns a numpy 1D array with the
        burned area for each segment.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations of
                burned pixels within the watershed

        Outputs:
            numpy 1D array: The burned upslope area for each segment
        """

        nburned = self._accumulation(mask=isburned)
        return nburned * self.pixel_area

    def kf_factor(
        self, kf_factor: RasterInput, mask: Optional[RasterInput] = None
    ) -> SegmentValues:
        """
        kf_factor  Computes mean soil KF-factor for each stream segment catchment basin
        ----------
        self.kf_factor(kf_factor)
        Computes the mean catchment KF-factor for each stream segment in the
        network. Note that the KF-Factor raster cannot contain negative values.

        self.kf_factor(kf_factor, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean KF-Factors. False elements are ignored. If a
        catchment only contains False elements, then its mean Kf-factor is set
        to NaN.
        ----------
        Inputs:
            kf_factor: A raster of soil KF-factor values. Cannot contain negative
                elements.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute mean KF-factors

        Outputs:
            numpy 1D array: The mean catchment KF-Factor for each stream segment
        """
        return self.catchment("mean", kf_factor, mask)

    def scaled_dnbr(
        self, dnbr: RasterInput, mask: Optional[RasterInput] = None
    ) -> SegmentValues:
        """
        scaled_dnbr  Computes mean catchment dNBR / 1000 for each stream segment
        ----------
        self.scaled_dnbr(dnbr)
        Computes mean catchment dNBR for each stream segment in the network.
        These mean dNBR values are then divided by 1000 to place dNBR values
        roughly on the interval from 0 to 1. Returns the scaled dNBR values.

        self.scaled_dnbr(dnbr, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute scaled dNBR values. False elements are ignored. If a
        catchment only contains False elements, then its scaled dNBR value is set
        to NaN.
        ----------
        Inputs:
            dnbr: A dNBR raster for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled dNBR

        Outputs:
            numpy 1D array: The mean catchment dNBR/1000 for each stream segment
        """

        dnbr = self.catchment("mean", dnbr, mask)
        return dnbr / 1000

    def scaled_thickness(
        self, soil_thickness: RasterInput, mask: Optional[RasterInput] = None
    ) -> SegmentValues:
        """
        scaled_thickness  Computes mean catchment soil thickness / 100 for each stream segment
        ----------
        self.scaled_thickness(soil_thickness)
        First, computes the mean catchment soil thickness for each segment in the
        network. Then, divides these values by 100 to place soil thicknesses
        approximately on the interval from 0 to 1. Returns a numpy 1D array with
        the scaled soil thickness values for each segment. Note that the soil
        thickness raster cannot contain negative values.

        self.scaled_thickness(soil_thickness, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean soil thicknesses. False elements are ignored. If
        a catchment only contains False elements, then its scaled soil thickness
        is set to NaN.
        ----------
        Inputs:
            soil_thickess: A raster with soil thickness values for the watershed.
                Cannot contain negative values.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled soil thicknesses

        Outputs:
            numpy 1D array: The mean catchment soil thickness / 100 for each segment
        """

        soil_thickness = self.catchment("mean", soil_thickness, mask)
        return soil_thickness / 100

    def sine_theta(
        self, sine_thetas, mask: Optional[RasterInput] = None
    ) -> SegmentValues:
        """
        sine_theta  Computes the mean sin(theta) value for each segment's catchment
        ----------
        self.sine_theta(sine_thetas)
        Given a raster of watershed sin(theta) values, sin(theta) value for the
        catchment of each stream segment. Here, theta is the slope angle. Note
        that the pfdf.utils.slope module provides utilities for converting from
        slope gradients (rise/run) to other slope measurements, including
        sin(theta) values. All sin(theta) values should be on the interval from
        0 to 1. Returns a numpy 1D array with the sin(theta) values for each segment.

        self.sine_theta(sine_thetas, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean sin(theta) values. False elements are ignored.
        If a catchment only contains False elements, then its sin(theta) value
        is set to NaN.
        ----------
        Inputs:
            sine_thetas: A raster of sin(theta) values for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute sin(theta) values

        Outputs:
            numpy 1D array: The mean sin(theta) value for the catchment of each
                stream segment in the network
        """

        sine_thetas = self._validate(sine_thetas, "sine_thetas")
        validate.inrange(
            sine_thetas.values,
            sine_thetas.name,
            min=0,
            max=1,
            nodata=sine_thetas.nodata,
        )
        return self.catchment("mean", sine_thetas, mask)

    def slope(self, slopes: RasterInput):
        """
        slope  Returns the mean slope (rise/run) for each stream segment
        ----------
        self.slope(slopes)
        Given a raster of slopes (rise/run), returns the mean slope for each
        segment as a numpy 1D array. The order of slopes will match the order of
        segment IDs for the object. Any stream segment with NoData values in the
        associated pixels will be given a slope of NaN.
        ----------
        Inputs:
            slopes: Slopes (rise/run) for the watershed

        Outputs:
            numpy 1D array: The mean slope for each stream segment.
        """
        return self.summary("mean", slopes)

    def relief(self, relief: RasterInput) -> SegmentValues:
        """
        relief  Returns the vertical relief for each segment
        ----------
        self.relief(relief)
        Returns the vertical relief between each stream segment's outlet and the
        nearest ridge cell as a numpy 1D array.
        ----------
        Inputs:
            relief: A vertical relief raster for the watershed

        Outputs:
            numpy 1D array: The vertical relief for each segment
        """

        # Validate raster and record nodata
        relief = self._validate(relief, "relief")
        nodata = relief.nodata

        # Compute outlet values and convert NoData to NaN
        relief = self._outlet_values(relief)
        nodatas = nodata_.mask(relief, nodata)
        relief[nodatas] = nan
        return relief

    def ruggedness(self, relief: RasterInput) -> SegmentValues:
        """
        ruggedness  Returns the ruggedness of each stream segment catchment
        ----------
        self.ruggedness(relief)
        Returns the ruggedness of the catchment for each stream segment in the
        network. Ruggedness is defined as a stream segment's vertical relief,
        divided by the square root of its catchment area. Returns ruggedness
        values as a numpy 1D array with one element per stream segment.
        ----------
        Inputs:
            relif: A vertical relief raster for the watershed

        Outputs:
            numpy 1D array: The topographic ruggedness of each stream segment
        """
        area = self.area()
        relief = self.relief(relief)
        return relief / np.sqrt(area)

    def upslope_ratio(self, mask: RasterInput) -> SegmentValues:
        """
        upslope_ratio  Returns the proportion of catchment pixels that meet a criteria
        ----------
        self.upslope_ratio(mask)
        Given a raster mask, computes the proportion of True pixels in the
        catchment area for each stream segment. Returns the ratios as a numpy 1D
        array with one element per stream segment. Ratios will be on the interval
        from 0 to 1.
        ----------
        Inputs:
            mask: A raster mask for the watershed. The method will compute the
                proportion of True elements in each catchment

        Outputs:
            numpy 1D array: The proportion of True values on the catchment for
                each stream segment
        """
        counts = self._accumulation(mask=mask)
        return counts / self.npixels

    #####
    # Filtering
    #####

    def copy(self) -> Self:
        """
        copy  Returns a deep copy of a Segments object
        ----------
        self.copy()
        Returns a deep copy of the current Segments object. The new/old objects
        can be altered without affecting one another.
        ----------
        Outputs:
            Segments: A deep copy of the Segments object.
        """
        return deepcopy(self)

    def keep(
        self,
        *,
        ids: Optional[SegmentIDs] = None,
        indices: Optional[SegmentIndices] = None,
    ) -> None:
        """
        keep  Restricts the network to the indicated segments
        ----------
        self.keep(*, ids)
        self.keep(*, indices)
        Restricts the network to the indicated segments. All other segments are
        discarded. If using "ids", the input should be a list or numpy 1D array
        whose elements are the IDs of the segments to retain in the network. If
        using "indices" the input should be a boolean numpy 1D array with one
        element per segment in the network. True elements indicate stream segments
        that should be retained. False elements will be removed. If you provide
        both inputs, segments indicated by either input are retained in the network.
        ----------
        Inputs:
            ids: A list or numpy 1D array listing the IDs of segments that should
                be retained in the network
            indices: A boolean numpy 1D array with one element per stream segment.
                True elements indicate segments that should be retained in the
                network.
        """

        keep = self._validate_indices(ids, indices)
        self.remove(indices=~keep)

    def remove(
        self,
        *,
        ids: Optional[SegmentIDs] = None,
        indices: Optional[SegmentIndices] = None,
    ) -> None:
        """
        remove  Removes segments from a Segments object
        ----------
        self.remove(*, ids)
        self.remove(*, indices)
        Removes the indicated segments from the network. If using "ids", the input
        should be a list or numpy 1D array whose elements are the IDs of the segments
        that should be removed from the network. If using "indices" the input should
        be a boolean numpy 1D array with one element per segment in the network.
        True elements indicate the stream segments that should be discarded. False
        elements will be retained. If you provide both inputs, segments indicated
        by either input are removed from the network.
        ----------
        Inputs:
            ids: A list or numpy 1D array listing the IDs of segments that should
                be removed from the network
            indices: A boolean numpy 1D array with one element per stream segment.
                True elements indicate segments that should be removed from the
                network.
        """

        remove = self._validate_indices(ids, indices)
        ids = self.ids
        for k in reversed(range(0, self.length)):
            if remove[k]:
                id = ids[k]
                del self._indices[id]
                del self._segments[k]
        self._npixels = self._npixels[~remove]

    #####
    # Export
    #####

    def geojson(self, properties: Optional[PropertyDict] = None):
        """
        geosjon  Exports the network to a geojson.FeatureCollection object
        ----------
        self.geojson()
        Exports the network to a geojson.FeatureCollection object. The individual
        Features have LineString geometries whose coordinates proceed from upstream
        to downstream. The Features will not have any properties.

        self.geojson(properties)
        Specifies properties for the GeoJSON Features. The "properties" input should
        be a dict. Each key should be the (string) name of the associated property
        field. Each value should be a numpy 1D array with one element per segment
        in the network. The arrays must have an integer, floating-point, or
        boolean dtype - all properties in the output GeoJSON Features will have
        a floating-point type.
        ----------
        Inputs:
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with one element per
                segment. Each array should have an integer, floating-point, or
                boolean dtype.

        Outputs:
            geojson.FeatureCollection: The network of stream segments represented
                as geojson
        """

        properties = self._validate_properties(properties)
        segments = []
        for s, segment in enumerate(self.segments):
            geometry = geojson.LineString(segment.coords)
            data = {field: vector[s] for field, vector in properties.items()}
            segment = Feature(geometry=geometry, properties=data)
            segments.append(segment)
        return FeatureCollection(segments)

    def save(
        self,
        path: Pathlike,
        properties: Optional[PropertyDict] = None,
        *,
        overwrite: bool = False,
    ) -> None:
        """
        save  Saves the network to a GeoJSON file
        ----------
        save(path)
        save(path, *, overwrite=True)
        Saves the network to the indicated path as a GeoJSON file. Each stream
        segment is a Feature with a LineString geometry whose coordinates proceed
        from upstream to downstream. The Features will not have any properties.
        In the default state, the method will raise a FileExistsError if the file
        already exists. Set overwrite=True to enable the replacement of existing
        files.

        save(path, properties)
        Specifies properties for the GeoJSON feature. The "properties" input should
        be a dict. Each key should be the (string) name of the associated property
        field. Each value should be a numpy 1D array with one element per segment
        in the network. The arrays must have an integer, floating-point, or
        boolean dtype. Note that all properties will be converted to a floating-point
        type in the saved file.
        ----------
        Inputs:
            path: The path to the output file
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with one element per
                segment. Each array should have an integer, floating-point, or
                boolean dtype.
            overwrite: True to allow replacement of existing files. False (default)
                to prevent overwriting.
        """

        # Validate
        validate.output_path(path, overwrite)
        properties = self._validate_properties(properties)

        # Build the schema
        schema = {
            "geometry": "LineString",
            "properties": {key: "float" for key in properties.keys()},
        }

        # Build the record for each segment. Start with geometry
        segments = []
        for s, segment in enumerate(self.segments):
            geometry = {"type": "LineString", "coordinates": segment.coords}

            # Build the properties and add the record to the list
            props = {}
            for field, vector in properties.items():
                props[field] = vector[s]
            record = {"geometry": geometry, "properties": props}
            segments.append(record)

        # Write file
        with fiona.open(
            path, "w", driver="GeoJSON", crs=self.crs, schema=schema
        ) as file:
            file.writerecords(segments)
