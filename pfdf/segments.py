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

from math import inf, nan, sqrt
from typing import Any, Callable, Literal, Optional, Self

import fiona
import geojson
import numpy as np
import rasterio.features
import shapely
from affine import Affine
from geojson import Feature, FeatureCollection
from pysheds.grid import Grid
from rasterio.crs import CRS
from rasterio.transform import rowcol

from pfdf import watershed
from pfdf._utils import nodata_, real, validate
from pfdf._utils.kernel import Kernel
from pfdf.errors import RasterTransformError
from pfdf.raster import Raster, RasterInput
from pfdf.typing import (
    BasinValues,
    BooleanMask,
    FlowNumber,
    MatrixArray,
    Pathlike,
    PixelIndices,
    PropertyDict,
    RealArray,
    ScalarArray,
    SegmentIndices,
    SegmentParents,
    SegmentValues,
    TerminalValues,
    VectorArray,
    scalar,
    shape2d,
    slopes,
    vector,
)

# Type aliases
indices = list[PixelIndices]
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
    "nanvar",
]
StatFunction = Callable[[np.ndarray], ScalarArray]
OutletIndices = tuple[int, int]
FeatureType = Literal["segments", "outlets", "basins"]

# Supported statistics -- name: (function, description)
_STATS = {
    "outlet": (None, "Values at stream segment outlet pixels"),
    "min": (np.amin, "Minimum value"),
    "max": (np.amax, "Maximum value"),
    "mean": (np.mean, "Mean"),
    "median": (np.median, "Median"),
    "std": (np.std, "Standard deviation"),
    "sum": (np.sum, "Sum"),
    "var": (np.var, "Variance"),
    "nanmin": (np.nanmin, "Minimum value, ignoring NaNs"),
    "nanmax": (np.nanmax, "Maximum value, ignoring NaNs"),
    "nanmean": (np.nanmean, "Mean value, ignoring NaNs"),
    "nanmedian": (np.nanmedian, "Median value, ignoring NaNs"),
    "nanstd": (np.nanstd, "Standard deviation, ignoring NaNs"),
    "nansum": (np.nansum, "Sum, ignoring NaNs"),
    "nanvar": (np.nanvar, "Variance, ignoring NaNs"),
}


class Segments:
    """
    Segments  Builds and manages a stream segment network
    ----------
    The Segments class is used to build and manage a stream segment network. Here,
    a stream segment is approximately equal to the stream bed of a catchment basin.
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
           segments. (e.g. confinement angle, slope, the proportion of burned
           upslope area)
        3. Reduce the network to the model-worthy segments using the "remove" or
           "keep" methods
        4. Use the Segments object to calculate inputs for various models
           (e.g. Gartner et al. 2014; Staley et al. 2017; Cannon et al. 2010)
        5. Use the "save" method to write the network (and associated data values)
           to file.

    The following sections provide additional details for these procedures.

    TERMINOLOGY:
    Here we define various terms that are used throughout the documentation.

    *Stream Segments*
    A stream segment approximates a stream bed in a drainage area. Each stream
    segment consists of a set of points that proceed from upstream to downstream.
    When multiple segments meet at a confluence point, then the upstream segments
    end just before the confluence, and a new segment begins at the confluence.
    Stream segments are well-represented as LineString (also known as Polyline)
    features.

    *Local Drainage Network*
    A local drainage network is a subset of stream segments that exhibit flow
    connectivity. Each segment in a local network flows directly into another
    local segment and/or has another local segment flow directly into it. It is
    common for a stream segment network to consist of multiple local drainage
    networks. Note that the distinguishing characteristic of a local network is
    connectivity, rather than flow paths. As such, it is possible for a local
    network to be downstream of another local network. So long as the segments in
    the two networks do not connect, the networks are considered distinct,
    even if one network eventually flows into the other.

    *Outlets*
    An outlet is the final, most downstream point in a stream segment. All points
    that eventually flow into the stream segment will eventually flow through the
    outlet (and the outlet is the most upstream point at which this is the case).
    When multiple segments join at a confluence, then the upstream outlets are
    *just before* the confluence point. As such, no two stream segments will share
    the same outlet point. Outlets are well-represented as point features.

    *Terminal Outlet*
    A terminal outlet is the outlet point of a local drainage network. The segment
    associated with the outlet is sometimes referred to as a "terminal segment".
    All the stream segments in a local network share the same terminal outlet.
    As such, the terminal outlets are a subset of the complete set of segment
    outlets, and the terminal outlet for a segment is not necessarily the same as
    the segment's outlet. Terminal outlets are well-represented as point features.

    *Catchment Basin*
    The catchment basin for a stream segment is the complete set of points that
    eventually drain into the segment's outlet. If a stream segment has upstream
    parents, then its catchment basin will include the (necessarily) smaller
    catchment basins of the parents. Catchment basins are well-represented as
    Polygon features.

    *Terminal Outlet Basin*
    A terminal outlet basin is the catchment basin for a terminal segment. This is
    the complete set of points that eventually drain into the terminal outlet point
    of a local drainage network. All the stream segments in a local network are
    associated with the same terminal outlet basin. As such, the terminal outlet
    basins are a subset of the complete set of segment catchment basins. Note
    that a given segment's catchment basin will be a subset of the points in its
    terminal outlet basin. Terminal outlet basins are well-represented as Polygon feautres.

    *Upstream Parents*
    A segment's upstream parents are the segments that flow immediately into the
    segment. A segment may have no parents (if it is at the top of its local drainage
    network), or multiple parents (if the segment begins at a confluence point).
    The key characteristic of a parent is immediate upstream connectivity. A upstream
    segment that flows into the current segment via intermediate segments is not
    a parent of the current segment.

    *Downstream Child*
    A segment's downstream child is the segment that it flows immediately into.
    A segment may have at most one child. A terminal segment (a segment at
    the bottom of a local drainage network) will not have a child. The key
    characteristic of a child is immediate downstream connectivity. If the current
    segment flows into a downstream segment via intermediate segments, then the
    downstream segment is not a child of the current segment.

    BUILDING A NETWORK:
    You can build an initial stream segment network by initializing a Segments
    object. There are two essential input for this procedure: (1) A D8 flow
    direction raster (see the pfdf.watershed module to produce this), and
    (2) a raster mask indicating watershed pixels that may potentially be stream
    segments. Note that the flow direction raster must have (affine) transform
    metadata.

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
    segments spatially. The "lengths" (plural) property returns the lengths of the
    individual segments as a 1D numpy array. These lengths will be in the base
    units of the coordinate reference system. (In practice, this is often meters).

    Segments objects also include two properties to faciliate working with terminal
    outlet basins. The "nlocal" property returns the number of local drainage
    networks in the network. This number is equivalent to the number of terminal
    outlet basins, which is the same as the number of terminal outlets. The "isterminus"
    property returns a boolean 1D numpy array that indicates whether each segment
    is a terminal segment. True elements indicate a terminal segment, False elements
    are not terminal segments.

    Each segment in the network is assigned a unique integer ID. These IDs are
    used to represent segments within rasters (see below), as well as to identify
    segments for various commands. The ID for a given segment is constant, so will
    not change if other segments are rmeoved from the network. The "ids" property
    returns a numpy 1D array with the ID of each segment.

    A Segment object also tracks the connectivity of segments in the network. The
    "child" property returns a numpy 1D array holding the ID of each segment's
    child. A value of 0 indicates that the segment does not have a child (equivalently,
    that the segment is a terminal segment). You can also use the "parents" property
    to return the IDs of each segment's parent segments. Parents are represented
    as a numpy array with one row per segment and multiple columns. Each column represents
    a parent. Each row will contain some combination of 0 and non-zero elements.
    Non-zero elements are the IDs of the segment's parents. Zero elements are fill
    values that accommodate different numbers of parents for different segments.

    STREAM NETWORK RASTERS:
    Although stream segments are often represented as vector features (via the
    shapely.LineString objects), it is also useful to represent the network using
    various rasters. For example, these raster representations are used to compute
    statistical summaries and physical values for the segments in a network.
    When representing the network as a raster, the output raster will always match
    the metadata of the flow direction raster used to derive the network. You can
    use the "flow" property to return this raster directly, or alternatively the
    "raster_shape", "transform", "crs", "resolution", and "pixel_area" properties
    to return specific characteristics. When relevant, the units of these properties
    will match the base units of the coordinate reference system for the network.
    (In practice, these are usually units of meters).

    The "stream raster" is a commonly used raster representation of the stream network.
    This raster consists of a 0 background, with stream segments indicated by
    non-zero values. The value of each non-zero pixel will match of the ID of the
    associated stream segment. Confluence pixels are always assigned to the most
    downstream segment. You can use the "raster" method to return this raster.
    Relatedly, the "indices" property returns the indices of each segment's pixels
    within the stream raster. The property returns a list with one element per
    stream segment. Each element holds two numpy arrays with the row and column
    indices of the segment's pixels within the stream raster.

    It is often useful to locate outlet pixels within the stream raster. You can use
    the "outlet" method to return the row and column index of a queried segment's
    outlet or terminal outlet pixel. Alternatively, use the "outlets" method to
    return a list of all outlet or terminal outlet pixel indices. Two other methods
    further support working with terminal outlets. The "terminus" method returns the
    ID of a queried segment's terminal segment, and the "termini" method returns
    a numpy array with the IDs of all terminal segments.

    It can also be useful to represent segment basins as a raster. The "terminal
    outlet basins raster" is one such representation. This raster consists of a
    0 background, with terminal outlet basins indicated by non-zero pixels. The
    value of each pixel is the ID of the terminal segment associated with the
    outlet basin. If a pixel belongs to multiple terminal outlet basins, then its
    value will match the ID of the terminal segment that is farthest upstream.
    You can return this raster by calling the "raster" method with basins=True.

    Sometimes it can be useful to return the basin mask for a specific segment.
    For example, to locate the pixels used to compute a statistical summary over
    a segment's catchment basin. Here, a basin mask is a boolean raster. True
    elements indicate pixels that belong to the segment's basin. You can return
    basin masks using the "basin_mask" method. By default, this will return the
    catchment basin mask for the queried segment. However, you can instead return
    the terminal outlet basin mask by setting terminal=True. Note that you can
    also use the "npixels" property to return the number of pixels in the catchment
    basin of each segment.

    A final (and uncommon) raster representation is the "nested drainage basin
    raster". This raster consists of a 0 background, with nested drainage basins
    indicated by non-zero pixels. The value of each non-zero pixel will match the
    ID of the *most upstream segment* that contains the pixel in its catchment basin.
    Building this raster requires a slow algorithm and takes a long time to compute.
    As such, we recommend using one of the other raster representations whenever
    possible. You can return a nested drainage basin raster by calling the "raster"
    method with both basins=True and nested=True.

    WORKING WITH INPUT RASTERS:
    Many Segments methods compute a statistical summary over an input raster.
    There are four common cases for computing segment summaries: (1) Computing
    values over the pixels in each stream segment, (2) Computing values over all
    pixels in the catchment basin of each stream segement, (3) Computing values
    over the pixels in each terminal outlet basins, and (4) Returning the values
    at the outlet or terminal outlet pixels.

    For case 1, recall that stream segment pixels can be returned using the "indices"
    property, and visualized using "raster" method. For case 2, a stream segment
    catchment basin consists of all pixels that flow into the segment's outlet
    pixel, and this can be visualized using the "basin_mask" method. For case 3,
    recall that you can return the IDs of the terminal segments using the "termini"
    method. You can also visualize terminal outlet basins using the "basin_mask"
    method with terminal=True. Finally for case 4, note that the "outlet" and
    "outlets" methods return the indices of stream segment outlet pixels.

    When providing an input raster, the raster must match the shape, crs, and
    affine transformation of the flow directions raster used to derive the stream
    segment network. You can return these values using the "raster_shape", "crs",
    and "transform" properties. You can also return the full flow directions raster
    using the "flow" property. If an input raster does not have a crs or transform,
    then it is assumed to have the same crs or transform as the flow directions
    raster.

    COMPUTING SEGMENT VALUES:
    Many Segments methods compute a statistical summary or physical value for each
    segment in the network. Currently, the class supports a number of specific
    variables commonly used for hazard assessment. These include catchment area
    (basic or masked), burned catchment area, developed catchment area, the
    proportion of burned catchment area (the burn ratio), confinement angle, mean
    catchment soil KF-factor, mean catchment dNBR / 1000, mean catchment
    soil thickness / 100, mean catchment sin(theta), the vertical relief (change
    in elevation from a segment outlet to its nearest ridge cell), topographic
    ruggedness (relief / sqrt(area), and the proportion of catchment area meeting
    a criterion (the upslope ratio).

    The class also provides two methods for calculating custom statistical
    summaries from a raster of data values. The "summary" method computes a statistic
    using the pixels in each segment. Similarly, the "basin_summary" method computes
    a statistic over all pixels in the catchment basin of each segment. Alternatively,
    use "basin_summary" with terminal=True to only compute summaries for the terminal
    outlet basions. Also note that "basin_summary" method supports masked statistical
    summaries. Both methods also allow you to return the value at each stream
    segment's outlet pixel, and "basin_mask" also allows you to return the values
    at the terminal outlet pixels. When computing values for all stream segments,
    the order of output values will be the same order as reported by the "ids"
    property. When computing values for terminal outlet basins, the order of
    output values will match the order reported by the "termini" method.

    Both functions support a variety of statistical summaries, including: max,
    min, mean, median, standard deviation, sum, and variance. The functions also
    allow you to compute these statistics while ignoring NaN and NoData values.
    You can print info about supported statistics (or return the info as a dict)
    using the "statistics" method. When computing catchment basin statistics, we
    recommend using the "outlet", "sum", or "mean" statistics whenever possible.
    The remaining statistics require a less efficient algorithm, and so often take
    a long time to compute. Alternatively, the number of terminal outlet basins is
    often much smaller than the total number of catchment basins. As such, it can
    be much faster to only compute summaries for the terminal outlet basins.

    NETWORK FILTERING:
    If is often desirable to limit a stream segment network to some subset of its
    segments. For example, to select model-worthy segments from an initial network.
    The Segments object includes 3 methods to help modify the network. The "remove"
    method will attempt to remove the indicated segments from the network. In
    the default configuration, this method will only remove segments that do not
    break network continuity. Specifically, an indicated segment will only be
    removed if it (1) does not have a nested child being retained, OR (2) does not
    have a nested parent being retained. Here, "nested" indicates that the parent/child
    does not need to be an immediate parent or child. So for example, the parent
    of a parent, or the child of a child. Users can prevent removal from the
    upstream/downstream ends of the local networks by setting upstream=False or
    downstream=False. Alternatively, you can remove all indicated segments,
    regardless of network continuity, by setting continuous=False.

    When segments are removed, they are permanently deleted from the Segments object.
    Any statistical summaries or physical variables will only be calculated for
    the remaining segments, and object properties will not contain values for the
    deleted segments. Similarly, the outputs of the "raster" method will only include
    the remaining segments. Note that a stream segment's ID is not affected by
    segment removal. Although an ID may be removed from the network, the individual
    IDs are constant, and are not renumbered when the network becomes smaller.

    The "keep" method is essentially the inverse of "remove" and will limit the
    network to the indicated segments, discarding all others. The "keep" method
    will preserve network continuity by default, but this can also be modified using
    the upstream, downstream, and continuous options. The keep and remove methods
    permanently alter a Segments object, and discarded segments cannot be recovered
    after removal. However, you can use the "copy" method to create a copy of an
    object before altering it. You can then remove segments from one copy without
    affecting the other. This can often be useful for testing different filtering
    criteria.

    Finally, note that preserving network continuity may cause the segments that
    are kept/removed from the network to differ from the inputs to the "keep" and
    "remove" commands. Essentially, the network may retain additional segments to
    preserve continuity. Because of this, both the "keep" and "remove" commands
    return a 1D boolean numpy array indicating the segments that were actually
    kept or removed, as appropriate.

    EXPORTING TO OTHER FORMATS:
    It is often useful to export a Segments object to a format for visualization.
    Specifically, as a set of vector features, optionally tagged with associated
    data values. To support this, the Segments class provides two methods that
    export a network to other formats. The "geojson" method exports a network to a
    geojson.FeatureCollection. Additionally, the "save" method allows users to
    save a network to a vector feature file.

    Both methods support several types of export. By default, both methods are
    configured to export the stream segments as a set of LineString features.
    However, you can use the "type" option to change this behavior. Setting
    type="basins" will export the terminal outlet basins as a set of Polygon
    features. Setting type="outlets" will export segment outlets as a set of
    Point features. You can also set terminal=False to instead export the nested
    drainage basins or the complete set of outlets, as appropriate. However, the
    nested drainage basins take a long time to compute, and we recommend avoiding
    this option whenever possible. (Also note that the "terminal" option is ignored
    when exporting the stream segments as LineString features).

    Both methods allow an optional properties input, which can be used to tag
    the features with associated data values. The properties input should be a
    dict whose keys are the names of data fields (as strings), and whose values
    are 1D numpy arrays with one element per exported feature. Currently, the
    class supports numeric, real-valued properties, so the array dtypes should
    be integer, floating-point, or boolean. There are no required data fields,
    so you may use any data field names supported by geojson. However, note that
    data field names may be truncated when saving to certain vector file formats
    (for example, saving to a Shapefile will truncate field names to 10 characters).
    ----------
    **FOR USERS**
    Object Creation:
        __init__            - Builds an initial stream segment network

    Properties (network):
        length              - The number of segments in the network
        nlocal              - The number of local drainage networks in the full network
        crs                 - The coordinate reference system associated with the network

    Properties (segments):
        segments            - A list of shapely.LineString objects representing the stream segments
        lengths             - The length of each segment
        ids                 - A unique integer ID associated with each stream segment
        parents             - The IDs of the upstream parents of each stream segment
        child               - The ID of the downstream child of each stream segment
        isterminus          - Whether each segment is a terminal segment
        indices             - The indices of each segment's pixels in the stream segment raster
        npixels             - The number of pixels in the catchment basin of each stream segment

    Properties (raster metadata):
        flow                - The flow direction raster used to build the network
        raster_shape        - The shape of the flow direction raster
        transform           - The affine transformation associated with the flow raster
        resolution          - The resolution of the flow raster pixels
        pixel_area          - The area of a raster pixel

    Python built-ins:
        __len__             - The number of segments in the network
        __str__             - A string representing the network

    Rasters:
        raster              - Returns a raster representation of the stream segment network
        basin_mask          - Returns the catchment or terminal outlet basin mask for the queried stream segment

    Outlets:
        terminus            - Return the ID of the queried segment's terminal segment
        termini             - Return the IDs of all terminal segments
        outlet              - Return the indices of the queried segment's outlet or terminal outlet pixel
        outlets             - Return the indices of all outlet or terminal outlet pixels

    Generic Statistics:
        statistics          - Print or return info about supported statistics
        summary             - Compute summary statistics over the pixels for each segment
        basin_summary       - Compute summary statistics over the catchment basins or terminal outlet basins

    Specific Variables:
        area                - Computes the total basin areas
        burn_ratio          - Computes the burned proportion of basins
        burned_area         - Computes the burned area of basins
        developed_area      - Computes the developed area of basins
        confinement         - Computes the confinement angle for each segment
        kf_factor           - Computes mean basin KF-factors
        scaled_dnbr         - Computes mean basin dNBR / 1000
        scaled_thickness    - Computes mean basin soil thickness / 100
        sine_theta          - Computes mean basin sin(theta)
        slope               - Computes the mean slope of each segment
        relief              - Computes the vertical relief to highest ridge cell for each segment
        ruggedness          - Computes topographic ruggedness (relief / sqrt(area)) for each segment
        upslope_ratio       - Computes the proportion of basin pixels that meet a criteria

    Filtering:
        copy                - Returns a deep copy of the Segments object
        keep                - Restricts the network to the indicated segments while optionally preserving continuity
        remove              - Removes segments from the network while optionally preserving continuity

    Export:
        geojson             - Returns the network as a geojson.FeatureCollection
        save                - Saves the network to file

    INTERNAL
    Attributes:
        _flow                   - The flow direction raster for the watershed
        _segments               - A list of shapely LineStrings representing the segments
        _ids                    - The ID for each segment
        _indices                - A list of each segment's pixel indices
        _npixels                - The number of catchment pixels for each stream segment
        _child                  - The index of each segment's downstream child
        _parents                - The indices of each segment's upstream parents
        _basins                 - Saved nested drainage basin raster values

    Utilities:
        _indices_to_ids         - Converts segment indices to (user-facing) IDs
        _preallocate            - Initializes an array to hold summary values
        _accumulation           - Computes flow accumulation values

    Validation:
        _validate               - Checks that an input raster has metadata matching the flow raster
        _check_ids              - Checks that IDs are in the network
        _validate_id            - Checks that a segment ID is valid
        _validate_selection     - Validates indices/IDs used to select segments for filtering
        _validate_properties    - Checks that a GeoJSON properties dict is valid
        _validate_export        - Checks export properties and type

    Outlets:
        _terminus               - Returns the index of the queried segment's terminus
        _termini                - Returns the indices of all terminal segments
        _outlet                 - Returns the outlet indices for the queried stream segment index

    Rasters:
        _segments_raster        - Builds a stream segment raster array
        _basins_raster          - Builds a terminal outlet or nested drainage basin array

    Confinement Angles:
        _segment_confinement    - Computes the confinement angle for a stream segment
        _pixel_slopes           - Computes confinement slopes for a pixel

    Summaries:
        _summarize              - Computes a summary statistic
        _values_at_outlets      - Returns the data values at the outlet pixels
        _accumulation_summary   - Computes basin summaries using flow accumulation
        _catchment_summary      - Computes basin summaries by iterating over catchment basins

    Removal:
        _removable              - Locates requested segments on the edges of their local flow networks
        _continuous_removal     - Locates segments that can be removed without breaking flow continuity

    Filtering Updates:
        _update_segments        - Computes updated _segments and _indices after segments are removed
        _update_family          - Updates child-parent arrays in-place after removing segments
        _update_indices         - Updates connectivity indices in-place after removing segments
        _update_connectivity    - Computes updated _child and _parents after segments are removed
        _update_basins          - Computes updated _basins after removing segments
        _update_attributes      - Updates attributes affected by filtering
        _set_attributes         - Sets the values of attributes affected by filtering

    Export:
        _outlet_segments        - Returns a list of LineString geometries for catchment or terminal outlets
        _basin_polygons         - Returns a generator of (Polygon, value) geometries
        _geojson                - Creates a GeoJSON feature collection using validated properties
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
        Note that stream segments approximate the river beds in the catchment basins,
        rather than the full catchment basins. The returned object records the
        pixels associated with each segment in the network.

        The stream segment network is determined using a TauDEM-style D8 flow direction
        raster and a raster mask (and please see the documentation of the pfdf.watershed
        module for details of this style). Note the the flow direction raster must have
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
        self._ids: SegmentValues = None
        self._indices: indices = None
        self._npixels: SegmentValues = None
        self._child: SegmentValues = None
        self._parents: SegmentParents = None
        self._basins: Raster = None

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

        # Calculate network. Assign IDs
        self._segments = watershed.network(self.flow, mask, max_length)
        self._ids = np.arange(self.length, dtype=int) + 1

        # Initialize attributes - indices, child, parents
        self._indices = []
        self._child = np.full(self.length, -1, dtype=int)
        self._parents = np.full((self.length, 2), -1, dtype=int)

        # Initialize variables used to determine connectivity and split points.
        # (A split point is where a long stream segment was split into 2 pieces)
        starts = np.empty((self.length, 2), float)
        outlets = np.empty((self.length, 2), float)
        split = False

        # Get the spatial coordinates of each segment
        for s, segment in enumerate(self.segments):
            coords = np.array(segment.coords)
            starts[s, :] = coords[0, :]
            outlets[s, :] = coords[-1, :]

            # Get the pixel indices for each segment. If the first two indices are
            # identical, then this is downstream of a split point
            rows, cols = rowcol(self.flow.transform, xs=coords[:, 0], ys=coords[:, 1])
            if rows[0] == rows[1] and cols[0] == cols[1]:
                split = True

            # If the segment is downstream of a split point, then remove the
            # first index so that split pixels are assigned to the split segment
            # that contains the majority of the pixel
            if split:
                del rows[0]
                del cols[0]
                split = False

            # If the final two indices are identical, then the next segment
            # is downstream of a split point.
            if rows[-1] == rows[-2] and cols[-1] == cols[-2]:
                split = True

            # Record pixel indices. Remove the final coordinate so that junctions
            # are assigned to the downstream segment.
            indices = (rows[:-1], cols[:-1])
            self._indices.append(indices)

        # Find upstream parents (if any)
        for s, start in enumerate(starts):
            parents = np.equal(start, outlets).all(axis=1)
            parents = np.argwhere(parents)

            # Add extra columns if there are more parents than initially expected
            nextra = parents.size - self._parents.shape[1]
            if nextra > 0:
                fill = np.full((self.length, nextra), -1, dtype=int)
                self._parents = np.concatenate((self._parents, fill), axis=1)

            # Record child-parent relationships
            self._child[parents] = s
            self._parents[s, 0 : parents.size] = parents.flatten()

        # Compute flow accumulation
        self._npixels = self._accumulation()

    def __len__(self) -> int:
        "The number of stream segments in a Segments object"
        return len(self._indices)

    def __str__(self) -> str:
        "String representation of the object"
        return f"A network of {self.length} stream segments."

    #####
    # Properties
    #####

    ##### Network

    @property
    def length(self) -> int:
        "The number of stream segments in the network"
        return len(self._segments)

    @property
    def nlocal(self) -> int:
        "The number of local drainage networks"
        ntermini = np.sum(self.isterminus)
        return int(ntermini)

    @property
    def crs(self) -> CRS:
        "The coordinate reference system of the stream segment network"
        return self._flow.crs

    ##### Segments

    @property
    def segments(self) -> list[shapely.LineString]:
        "A list of shapely LineStrings representing the stream segments"
        return self._segments.copy()

    @property
    def lengths(self) -> SegmentValues:
        "The length of each stream segment in the units of the CRS"
        return np.array([segment.length for segment in self._segments])

    @property
    def ids(self) -> SegmentValues:
        "The ID of each stream segment"
        return self._ids.copy()

    @property
    def parents(self) -> SegmentParents:
        "The IDs of the upstream parents of each stream segment"
        return self._indices_to_ids(self._parents)

    @property
    def child(self) -> SegmentValues:
        "The ID of the downstream child of each stream segment"
        return self._indices_to_ids(self._child)

    @property
    def isterminus(self) -> SegmentIndices:
        "Whether each segment is a terminal segment"
        return self._child == -1

    @property
    def indices(self) -> indices:
        "The row and column indices of the stream raster pixels for each segment"
        return self._indices.copy()

    @property
    def npixels(self) -> SegmentValues:
        "The number of pixels in the catchment basin of each stream segment"
        return self._npixels.copy()

    ##### Raster metadata

    @property
    def flow(self) -> Raster:
        "The flow direction raster used to build the network"
        return self._flow

    @property
    def raster_shape(self) -> shape2d:
        "The shape of the stream segment raster"
        return self._flow.shape

    @property
    def transform(self) -> Affine:
        "The (affine) transform of the stream segment raster"
        return self._flow.transform

    @property
    def resolution(self) -> float:
        "The resolution of the stream segment raster pixels"
        return self._flow.resolution

    @property
    def pixel_area(self) -> float:
        "The area of the stream segment raster pixels in the units of the transform"
        return self._flow.pixel_area

    #####
    # Utilities
    #####

    def _indices_to_ids(self, indices: RealArray) -> RealArray:
        "Converts segment indices to (user-facing) IDs"
        ids = np.zeros(indices.shape)
        valid = indices != -1
        ids[valid] = self._ids[indices[valid]]
        return ids

    def _basin_npixels(self, terminal: bool) -> BasinValues:
        "Returns the number of pixels in catchment or terminal outlet basins"
        if terminal:
            return self._npixels[self.isterminus]
        else:
            return self._npixels

    def _nbasins(self, terminal: bool) -> int:
        "Returns the number of catchment or terminal outlet basins"
        if terminal:
            return self.nlocal
        else:
            return self.length

    def _preallocate(self, terminal: bool = False) -> BasinValues:
        "Preallocates an array to hold summary values"
        length = self._nbasins(terminal)
        return np.empty(length, dtype=float)

    def _accumulation(
        self,
        weights: Optional[RasterInput] = None,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        "Computes flow accumulation values"

        # Default case is just npixels
        if (weights is None) and (mask is None) and (self._npixels is not None):
            return self._basin_npixels(terminal).copy()

        # Otherwise, compute the accumulation at each outlet
        accumulation = watershed.accumulation(self.flow, weights, mask)
        return self._values_at_outlets(accumulation, terminal=terminal)

    #####
    # Validation
    #####

    def _validate(self, raster: Any, name: str) -> Raster:
        "Checks that an input raster has metadata matching the flow raster"
        return self.flow._validate(raster, name)

    def _check_ids(self, ids: VectorArray, name: str) -> None:
        "Checks that segment IDs are in the network"

        validate.integers(ids, name)
        for i, id in enumerate(ids):
            if id not in self._ids:
                if name == "ids":
                    name = f"{name}[{i}]"
                raise ValueError(
                    f"{name} (value={id}) is not the ID of a segment in the network. "
                    "See the '.ids' property for a list of current segment IDs."
                )

    def _validate_id(self, id: Any) -> int:
        "Checks that a segment ID is valid and returns index"
        id = validate.scalar(id, "id", dtype=real)
        self._check_ids(id, "id")
        return int(np.argwhere(self._ids == id))

    def _validate_selection(self, ids: Any, indices: Any) -> SegmentIndices:
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
            self._check_ids(ids, "ids")

            # Convert IDs to logical indices. Return union of IDs and indices
            ids = np.isin(self._ids, ids)
        return ids | indices

    def _validate_properties(
        self,
        properties: Any,
        terminal: bool,
    ) -> PropertyDict:
        "Validates a GeoJSON property dict for export"

        # Properties are optional, use an empty dict if None
        if properties is None:
            return {}

        # Get the required vector length
        length = self._nbasins(terminal)

        # Require a dict with string keys
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
                properties[key], name, length=length, dtype=real
            ).astype(float, copy=False)
        return properties

    def _validate_export(
        self, properties: Any, type: Any, terminal: bool
    ) -> tuple[PropertyDict, str, bool]:
        "Validates export type and properties"

        type = validate.option(type, "type", allowed=["segments", "outlets", "basins"])
        if type == "segments":
            terminal = False
        properties = self._validate_properties(properties, terminal)
        return properties, type, terminal

    #####
    # Outlets
    #####

    def _terminus(self, index: ScalarArray) -> ScalarArray:
        "Returns the index of the queried segment's terminal segment"
        while self._child[index] != -1:
            index = self._child[index]
        return index

    def terminus(self, id: scalar) -> int:
        """
        terminus  Returns the ID of a queried segment's terminal segment
        ----------
        self.terminus(id)
        Returns the ID of the queried segment's terminal segment. The terminal
        segment is the final segment in the queried segment's local drainage
        network. The input should be the ID associated with the queried segment.
        ----------
        Inputs:
            id: The ID of the segment being queried

        Outputs:
            int: The ID of the queried segment's terminal segment
        """
        segment = self._validate_id(id)
        terminus = self._terminus(segment)
        return int(self._indices_to_ids(terminus))

    def _termini(self) -> TerminalValues:
        "Returns the indices of all terminal segments"
        (indices,) = np.nonzero(self._child == -1)
        return indices

    def termini(self) -> TerminalValues:
        """
        termini  Returns the IDs of all terminal segments
        ----------
        self.termini()
        Returns a numpy 1D array with the IDs of all terminal segments in the
        network. A terminal segment is a segment at the bottom of its local
        drainage network.
        ----------
        Outputs:
            numpy 1D array: The IDs of the terminal segments in the network
        """
        termini = self._termini()
        return self._indices_to_ids(termini)

    def _outlet(self, index: int) -> OutletIndices:
        "Returns the outlet indices for the queried stream segment index"
        pixels = self._indices[index]
        row = pixels[0][-1]
        column = pixels[1][-1]
        return row, column

    def outlet(self, id, terminal: bool = False) -> OutletIndices:
        """
        outlet  Return the indices of the queried segment's outlet pixel
        ----------
        self.outlet(id)
        Returns the indices of the queried segment's outlet pixel in the stream
        segment raster. The outlet pixel is the segment's most downstream pixel.
        The first output is the row index, second output is the column index.

        self.outlet(id, terminal=True)
        Returns the indices of the queried segment's terminal outlet pixel. The
        terminal outlet is the final pixel in the segment's local drainage network.
        ----------
        Inputs:
            id: The ID of the queried segment
            terminal: True to return the indices of the terminal outlet pixel.
                False (default) to return the indices of the outlet pixel.

        Outputs:
            int: The row index of the outlet pixel
            int: The column index of the outlet pixel
        """
        segment = self._validate_id(id)
        if terminal:
            segment = self._terminus(segment)
        return self._outlet(segment)

    def outlets(self, terminal: bool = False) -> list[OutletIndices]:
        """
        outlets  Returns the row and column indices of all outlet or terminal outlet pixels
        ----------
        self.outlets()
        Returns a list of outlet pixel indices for the network. The output has one
        element per stream segment. Each element is a tuple with the outlet indices
        for the associated segment. The first element of the tuple is the row index,
        and the second element is the column index.

        self.outlets(terminal=True)
        Returns the indices of all terminal outlet pixels in the network. Terminal
        outlets are outlets at the bottom of their local drainage network. The
        output list will have one element per terminal outlet.
        ----------
        Inputs:
            terminal: True to return the indices of the terminal outlet pixels.
                False (default) to return the indices of all output pixels.

        Outputs:
            list[tuple[int, int]]: A list of outlet pixel indices
        """

        if terminal:
            segments = self._termini()
        else:
            segments = np.arange(self.length)
        return [self._outlet(segment) for segment in segments]

    #####
    # Rasters
    #####

    def basin_mask(self, id: scalar, terminal: bool = False) -> Raster:
        """
        basin_mask  Return a mask of the queried segment's catchment or terminal outlet basin
        ----------
        self.basin_mask(id)
        Returns the catchment basin mask for the queried segment. The catchment
        basin consists of all pixels that drain into the segment. The output will
        be a boolean raster whose True elements indicate pixels that are in the
        catchment basin.

        self.basin_mask(id, terminal=True)
        Returns the mask of the queried segment's terminal outlet basin. The
        terminal outlet basin is the catchment basin for the segment's local
        drainage network. This basin is a superset of the segment's catchment
        basin. The output will be a boolean raster whose True elements indicate
        pixels that are in the local drainage basin.
        ----------
        Inputs:
            id: The ID of the stream segment whose basin mask should be determined
            terminal: True to return the terminal outlet basin mask for the segment.
                False (default) to return the catchment mask.

        Outputs:
            Raster: The boolean raster mask for the basin. True elements indicate
                pixels that belong to the basin.
        """

        row, column = self.outlet(id, terminal)
        return watershed.catchment(self.flow, row, column)

    def raster(self, basins=False, nested=False) -> Raster:
        """
        raster  Return a raster representation of the stream network
        ----------
        self.raster()
        Returns the stream segment raster for the network. This raster has a 0
        background. Non-zero pixels indicate stream segment pixels. The value of
        each pixel is the ID of the associated stream segment.

        self.raster(basins=True)
        Returns the terminal outlet basin raster for the network. This raster has
        a 0 background. Non-zero pixels indicate terminal outlet basin pixels. The
        value of each pixel is the ID of the terminal segment associated with the
        basin. If a pixel is in multiple basins, then its value to assigned to
        the ID of the terminal segment that is farthest upstream.

        self.raster(basins=True, nested=True)
        Returns the nested drainage basin raster for the network. The raster has
        a 0 background. Non-zero pixels indicated nested drainage basin pixels.
        The value of each pixel is the ID of the most upstream segment containing
        the pixel in its catchment basin. We recommend avoiding this raster when
        possible, as it is slow to compute. Also note that the "nested" option
        is ignored when basins=False.
        ----------
        Inputs:
            basins: False (default) to return the stream segment raster. True to
                return a terminal outlet or nested drainage basin raster.
            nested: False (default) to return the terminal outlet basin raster.
                True to return a nested drainage basin raster. Has no effect if
                basins = False.

        Outputs:
            Raster: A stream segment, terminal outlet basin, or nested drainage
                basin raster.
        """

        if basins:
            raster = self._basins_raster(nested)
        else:
            raster = self._segments_raster()
        return Raster.from_array(raster, nodata=0, spatial=self.flow)

    def _segments_raster(self) -> MatrixArray:
        "Builds a stream segment raster array"
        raster = np.zeros(self._flow.shape, dtype="int32")
        for id, (rows, cols) in zip(self._ids, self._indices):
            raster[rows, cols] = id
        return raster

    def _basins_raster(self, nested: bool) -> MatrixArray:
        "Builds a terminal outlet or nested drainage basin raster array"

        # If building nested basins, use saved values when possible
        if nested and self._basins is not None:
            return self._basins

        # Initialize raster and prepare pysheds objects
        raster = np.zeros(self._flow.shape, dtype="int32")
        flow = self._flow.as_pysheds()
        grid = Grid.from_raster(flow)

        # Get segment outlets sorted from downstream to upstream
        outlets = self.outlets()
        indices = np.argsort(self._npixels)
        indices = np.flip(indices)

        # Iterate through outlets in sorted order. Either use all outlets
        # (for nested basins), or terminal outlets (for terminal basins)
        for k in indices:
            if nested or self._child[k] == -1:
                row, col = outlets[k]

                # Get catchment mask and assign pixel values as the segment ID
                catchment = grid.catchment(
                    fdir=flow, x=col, y=row, xytype="index", **watershed._FLOW_OPTIONS
                )
                raster[catchment] = self._ids[k]

        # Nested basins are slow, so save after building
        if nested:
            self._basins = raster
        return raster

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
        for i, pixels in enumerate(self._indices):
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
    # Generic summaries
    #####

    @staticmethod
    def statistics(asdict: bool = False) -> dict[str, str] | None:
        """
        statistics  Prints or returns info about supported statistics
        ----------
        Segments.statistics()
        Prints information about supported statistics to the console. The printed
        text is a table with two columns. The first column holds the names of
        statistics that can be used with the "summary" and "basin_summary" methods.
        The second column is a description of each statistic.

        Segments.statistics(asdict=True)
        Returns info as a dict, rather than printing to console. The keys of the
        dict are the names of the statistics. The values are the descriptions.
        ----------
        Inputs:
            asdict: True to return info as a dict. False (default) to print info
                to the console.

        Outputs:
            None | dict[str,str]: None if printing to console. Otherwise a dict
                whose keys are statistic names, and values are descriptions.
        """

        if asdict:
            return {name: values[1] for name, values in _STATS.items()}
        else:
            print("Statistic | Description\n" "--------- | -----------")
            for name, values in _STATS.items():
                description = values[1]
                print(f"{name:9} | {description}")

    @staticmethod
    def _summarize(
        statistic: StatFunction, raster: Raster, indices: PixelIndices | BooleanMask
    ) -> ScalarArray:
        """Compute a summary statistic over indicated pixels. Converts NoData elements
        to NaN. Returns NaN if no data elements are selected or all elements are NaN"""

        # Get the values. Require float with at least 1 dimension
        values = raster.values[indices].astype(float)
        values = np.atleast_1d(values)

        # Set NoData values to NaN
        if raster.nodata is not None:
            nodatas = nodata_.mask(values, raster.nodata)
            values[nodatas] = nan

        # Return NaN if there's no data, or if everything is already NaN.
        # Otherwise, compute the statistic
        if (values.size == 0) or np.isnan(values).all():
            return nan
        else:
            return statistic(values)

    def _values_at_outlets(self, raster: Raster, terminal: bool = False) -> BasinValues:
        "Returns the values at segment outlets. Returns NoData values as NaN"

        identity = lambda input: input
        values = self._preallocate(terminal)
        outlets = self.outlets(terminal)
        for k, outlet in enumerate(outlets):
            values[k] = self._summarize(identity, raster, indices=outlet)
        return values

    def summary(self, statistic: Statistic, values: RasterInput) -> SegmentValues:
        """
        summary  Computes a summary value for each stream segment
        ----------
        self.summary(statistic, values)
        Computes a summary statistic for each stream segment. Each summary
        value is computed over the associated stream segment pixels. Returns
        the statistical summaries as a numpy 1D array with one element per segment.

        Note that NoData values are converted to NaN before computing statistics.
        If using one of the statistics that ignores NaN values (e.g. nanmean),
        a segment's summary value will still be NaN if every pixel in the stream
        segment is NaN.
        ----------
        Inputs:
            statistic: A string naming the requested statistic. See Segments.statistics()
                for info on supported statistics
            values: A raster of data values over which to compute stream segment
                summary values.

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = self._validate(values, "values raster")

        # Either get outlet values...
        if statistic == "outlet":
            return self._values_at_outlets(values)

        # ...or compute a statistical summary
        statistic = _STATS[statistic][0]
        summary = self._preallocate()
        for i, pixels in enumerate(self._indices):
            summary[i] = self._summarize(statistic, values, pixels)
        return summary

    def basin_summary(
        self,
        statistic: Statistic,
        values: RasterInput,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        """
        basin_summary  Computes a summary statistic over each catchment or terminal outlet basin
        ----------
        self.basin_summary(statistic, values)
        Computes the indicated statistic over the catchment basin pixels for each
        stream segment. Uses the input values raster as the data value for each pixel.
        Returns a numpy 1D array with one element per stream segment.

        Note that NoData values are converted to NaN before computing statistics.
        If using one of the statistics that ignores NaN values (e.g. nanmean),
        a basin's summary value will still be NaN if every pixel in the basin
        basin is NaN.

        When possible, we recommend only using the "outlet", "mean", and "sum"
        statistics when computing summaries for every catchment basin. The remaining
        statistic require a less efficient algorithm, and so are much slower to
        compute. Alternatively, see below for an option to ony compute statistics
        for terminal outlet basins - this is typically a faster operation, and
        more suitable for other statistics.

        self.basin_summary(statistic, values, mask)
        Computes masked statistics over the catchment basins. True elements in the
        mask indicate pixels that should be included in statistics. False elements
        are ignored. If a catchment does not contain any True pixels, then its
        summary statistic is set to NaN. Note that a mask will have no effect
        on the "outlet" statistic.

        self.basin_summary(..., terminal=True)
        Only computes statistics for the terminal outlet basins. The output will
        have one element per terminal segment. The order of values will match the
        order of IDs reported by the "Segments.termini" method. The number of
        terminal outlet basins is often much smaller than the total number of
        segments. As such, this option presents a faster alternative and is
        particularly suitable when computing statistics other than "outlet",
        "mean", or "sum".
        ----------
        Inputs:
            statistic: A string naming the requested statistic. See Segments.statistics()
                for info on supported statistics.
            values: A raster of data values over which to compute basin summaries
            mask: An optional raster mask for the data values. True elements
                are used to compute basin statistics. False elements are ignored.
            terminal: True to only compute statistics for terminal outlet basins.
                False (default) to compute statistics for every catchment basin.

        Outputs:
            numpy 1D array: The summary statistic for each basin
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = self._validate(values, "values raster")
        if mask is not None:
            mask = self._validate(mask, "mask")
            mask = validate.boolean(mask.values, mask.name, nodata=mask.nodata)

        # Outlet values
        if statistic == "outlet":
            return self._values_at_outlets(values, terminal)

        # Sum or mean are derived from accumulation
        elif statistic in ["sum", "mean"]:
            return self._accumulation_summary(statistic, values, mask, terminal)

        # Anything else needs to iterate through catchment basins
        else:
            return self._catchment_summary(statistic, values, mask, terminal)

    def _accumulation_summary(
        self, statistic: Statistic, values: Raster, mask: Raster | None, terminal: bool
    ) -> BasinValues:
        "Uses flow accumulation to compute basin summaries"

        # Compute sums and pixels counts. If there are no pixels, the statistic is NaN
        sums = self._accumulation(values, mask=mask, terminal=terminal)
        npixels = self._accumulation(mask=mask, terminal=terminal)
        sums[npixels == 0] = nan

        # Return the sum or mean, as appropriate
        if statistic == "sum":
            return sums
        else:
            return sums / npixels

    def _catchment_summary(
        self,
        statistic: Statistic,
        values: Raster,
        mask: Raster | None,
        terminal: bool,
    ) -> BasinValues:
        "Iterates through catchment basins to compute basin summaries"

        # Get statistic, preallocate, and locate catchment outlets
        statistic = _STATS[statistic][0]
        summary = self._preallocate(terminal=terminal)
        outlets = self.outlets(terminal)

        # Iterate through catchment basins and compute summaries
        for k, outlet in enumerate(outlets):
            catchment = watershed.catchment(self.flow, *outlet).values
            if mask is not None:
                catchment = catchment & mask
            summary[k] = self._summarize(statistic, values, catchment)
        return summary

    #####
    # Earth system variables
    #####

    def area(
        self, mask: Optional[RasterInput] = None, terminal: bool = False
    ) -> BasinValues:
        """
        area  Returns the areas of basins
        ----------
        self.area()
        Computes the total area of the catchment basin for each stream segment.
        The returned area will be in the same units as the pixel_area property.

        self.area(mask)
        Computes masked areas for the basins. True elements in the mask indicate
        pixels that should be included in the calculation of areas. False pixels
        are ignored and given an area of 0.

        self.area(..., *, terminal=True)
        Only returns values for the terminal outlet basins.
        ----------
        Inputs:
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute upslope areas.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The catchment area for each stream segment
        """

        if mask is None:
            N = self._basin_npixels(terminal)
        else:
            N = self._accumulation(mask=mask, terminal=terminal)
        return N * self.pixel_area

    def burn_ratio(self, isburned: RasterInput, terminal: bool = False) -> BasinValues:
        """
        burn_ratio  Returns the proportion of burned pixels in basins
        ----------
        self.burn_ratio(isburned)
        Given a mask of burned pixel locations, determines the proportion of
        burned pixels in the catchment basin of each stream segment. Returns a numpy
        1D array with the ratio for each segment. Ratios are on the interval from
        0 to 1.

        self.burn_ratio(isburned, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations
                of burned pixels in the watershed.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The proportion of burned pixels in each basin
        """
        return self.upslope_ratio(isburned, terminal)

    def burned_area(self, isburned: RasterInput, terminal: bool = False) -> BasinValues:
        """
        burned_area  Returns the total burned area of basins
        ----------
        self.burned_area(isburned)
        Given a mask of burned pixel locations, returns the total burned area in
        the catchment of each stream segment. Returns a numpy 1D array with the
        burned area for each segment. The returned areas will be in the same
        units as the "pixel_area" property.

        self.burned_area(isburned, terminal=True)
        Only computes areas for the terminal outlet basins.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations of
                burned pixels within the watershed
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The burned catchment area for the basins
        """
        return self.area(isburned, terminal=terminal)

    def developed_area(
        self, isdeveloped: RasterInput, terminal: bool = False
    ) -> BasinValues:
        """
        developed_area  Returns the total developed area of basins
        ----------
        self.developed_area(isdeveloped)
        Given a mask of developed pixel locations, returns the total developed
        area in the catchment of each stream segment. Returns a numpy 1D array
        with the developed area for each segment.

        self.developed_area(isdeveloped, terminal)
        Only computes areas for the terminal outlet basins.
        ----------
        Inputs:
            isdeveloped: A raster mask whose True elements indicate the locations
                of developed pixels within the watershed.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The developed catchment area for each basin
        """
        return self.area(isdeveloped, terminal)

    def kf_factor(
        self,
        kf_factor: RasterInput,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        """
        kf_factor  Computes mean soil KF-factor for basins
        ----------
        self.kf_factor(kf_factor)
        Computes the mean catchment KF-factor for each stream segment in the
        network. Note that the KF-Factor raster must have all positive values.

        self.kf_factor(kf_factor, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean KF-Factors. False elements are ignored. If a
        catchment only contains False elements, then its mean Kf-factor is set
        to NaN.

        self.kf_factor(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            kf_factor: A raster of soil KF-factor values. Cannot contain negative
                elements.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute mean KF-factors
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment KF-Factor for each basin
        """
        kf_factor = self._validate(kf_factor, "kf_factor")
        validate.positive(kf_factor.values, "kf_factor", nodata=kf_factor.nodata)
        return self.basin_summary("mean", kf_factor, mask, terminal)

    def scaled_dnbr(
        self,
        dnbr: RasterInput,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        """
        scaled_dnbr  Computes mean catchment dNBR / 1000 for basins
        ----------
        self.scaled_dnbr(dnbr)
        Computes mean catchment dNBR for each stream segment in the network.
        These mean dNBR values are then divided by 1000 to place dNBR values
        roughly on the interval from 0 to 1. Returns the scaled dNBR values as a
        numpy 1D array.

        self.scaled_dnbr(dnbr, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute scaled dNBR values. False elements are ignored. If a
        catchment only contains False elements, then its scaled dNBR value is set
        to NaN.

        self.scaled_dnbr(..., terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            dnbr: A dNBR raster for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled dNBR
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment dNBR/1000 for the basins
        """
        dnbr = self.basin_summary("mean", dnbr, mask, terminal)
        return dnbr / 1000

    def scaled_thickness(
        self,
        soil_thickness: RasterInput,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        """
        scaled_thickness  Computes mean catchment soil thickness / 100 for basins
        ----------
        self.scaled_thickness(soil_thickness)
        Computes mean catchment soil-thickness for each segment in the network.
        Then divides these values by 100 to place soil thicknesses approximately
        on the interval from 0 to 1. Returns a numpy 1D array with the scaled soil
        thickness values for each segment. Note that the soil thickness raster
        must have all positive values.

        self.scaled_thickness(soil_thickness, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean soil thicknesses. False elements are ignored. If
        a catchment only contains False elements, then its scaled soil thickness
        is set to NaN.

        self.scaled_thickness(..., terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            soil_thickess: A raster with soil thickness values for the watershed.
                Cannot contain negative values.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled soil thicknesses
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment soil thickness / 100 for each basin
        """
        soil_thickness = self._validate(soil_thickness, "soil_thickness")
        validate.positive(
            soil_thickness.values, "soil_thickness", nodata=soil_thickness.nodata
        )
        soil_thickness = self.basin_summary("mean", soil_thickness, mask, terminal)
        return soil_thickness / 100

    def sine_theta(
        self,
        sine_thetas,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> BasinValues:
        """
        sine_theta  Computes the mean sin(theta) value for each segment's catchment
        ----------
        self.sine_theta(sine_thetas)
        Given a raster of watershed sin(theta) values, computes the mean sin(theta)
        value for each stream segment catchment. Here, theta is the slope angle. Note
        that the pfdf.utils.slope module provides utilities for converting from
        slope gradients (rise/run) to other slope measurements, including
        sin(theta) values. All sin(theta) values should be on the interval from
        0 to 1. Returns a numpy 1D array with the sin(theta) values for each segment.

        self.sine_theta(sine_thetas, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean sin(theta) values. False elements are ignored.
        If a catchment only contains False elements, then its sin(theta) value
        is set to NaN.

        self.sine_theta(..., terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            sine_thetas: A raster of sin(theta) values for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute sin(theta) values
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean sin(theta) value for each basin
        """

        sine_thetas = self._validate(sine_thetas, "sine_thetas")
        validate.inrange(
            sine_thetas.values,
            sine_thetas.name,
            min=0,
            max=1,
            nodata=sine_thetas.nodata,
        )
        return self.basin_summary("mean", sine_thetas, mask, terminal)

    def slope(self, slopes: RasterInput) -> SegmentValues:
        """
        slope  Returns the mean slope (rise/run) for basins
        ----------
        self.slope(slopes)
        Given a raster of slopes (rise/run), returns the mean slope for each
        segment as a numpy 1D array.
        ----------
        Inputs:
            slopes: A slope (rise/run) raster for the watershed

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

        relief = self._validate(relief, "relief")
        return self._values_at_outlets(relief)

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

    def upslope_ratio(self, mask: RasterInput, terminal: bool = False) -> BasinValues:
        """
        upslope_ratio  Returns the proportion of basin pixels that meet a criteria
        ----------
        self.upslope_ratio(mask)
        Given a raster mask, computes the proportion of True pixels in the
        catchment basin for each stream segment. Returns the ratios as a numpy 1D
        array with one element per stream segment. Ratios will be on the interval
        from 0 to 1.

        self.upslope_ratio(mask, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            mask: A raster mask for the watershed. The method will compute the
                proportion of True elements in each catchment
            terminal: True to only compute values for the terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The proportion of True values in each basin
        """
        counts = self._accumulation(mask=mask, terminal=terminal)
        npixels = self._basin_npixels(terminal)
        return counts / npixels

    #####
    # Filtering
    #####

    @staticmethod
    def _removable(
        requested: SegmentIndices,
        child: SegmentValues,
        parents: SegmentParents,
        upstream: bool,
        downstream: bool,
    ) -> SegmentIndices:
        "Returns the indices of requested segments on the edges of their local networks"

        edge = False
        if downstream:
            edge = edge | (child == -1)
        if upstream:
            edge = edge | (parents == -1).all(axis=1)
        return requested & edge

    def _continuous_removal(
        self, requested: SegmentIndices, upstream: bool, downstream: bool
    ) -> SegmentIndices:
        """Locates stream segments that are both (1) requested for removal,
        and (2) would not break flow continuity in the network"""

        # Initialize segments actually being removed. Get working copies of
        # parent-child relationships.
        remove = np.zeros(self.length, bool)
        child = self._child.copy()
        parents = self._parents.copy()

        # Iteratively select requested segments on the edges of their local networks.
        # Update child-parent segments and repeat for new edge segments
        removable = self._removable(requested, child, parents, upstream, downstream)
        while np.any(removable):
            remove[removable] = True
            requested[removable] = False
            self._update_family(child, parents, removable)
            removable = self._removable(requested, child, parents, upstream, downstream)
        return remove

    def remove(
        self,
        *,
        ids: Optional[vector] = None,
        indices: Optional[SegmentIndices] = None,
        continuous: bool = True,
        upstream: bool = True,
        downstream: bool = True,
    ) -> None:
        """
        remove  Removes segments from the network while optionally preserving continuity
        ----------
        self.remove(*, ids)
        self.remove(*, indices)
        Attempts to remove the indicated segments, but prioritizes the continuity
        of the stream network. An indicated segment will not be removed if it is
        between two segments being retained. Equivalently, segments are only removed
        from the upstream and downstream ends of a local network. Conceptually,
        this algorithm first marches upstream, and removes segments until it reaches
        a segment that was not indicated as input. The algorithm then marches
        downstream, and again removes segments until it reaches a segment that was
        not indicated as input. As such, the total number of removed segments may
        be less than the number of input segments.

        If using "ids", the input should be a list or numpy 1D array whose elements
        are the IDs of the segments that may potentially be removed from the network.
        If using "indices" the input should be a boolean numpy 1D array with one
        element per segment in the network. True elements indicate the stream segments
        that may potentially be removed. False elements will always be retained.
        If you provide both inputs, segments indicated by either input are potentially
        removed from the network.

        Returns the indices of the segments that were removed from the network as
        a boolean numpy 1D array. The output indices will have one element per
        segment in the original network. True elements indicate segments that were
        removed. False elements are segments that were retained. These indices are
        often useful for filtering values computed for the original network.

        self.remove(*, ..., continuous=False)
        Removes all indicates segments, regardless of the continuity of the
        stream network.

        self.remove(*, continuous=True, upstream=False)
        self.remove(*, continuous=True, downstream=False)
        Further customizes the removal of segments when prioritizing the continuity
        of the stream network. When upstream=False, segments will not be removed
        from the upstream end of a local network. Equivalently, a segment will not
        be removed if it flows into a segment retained in the network. When
        downstream=False, segments will not be removed from the downstream end
        of a local network. So a segment will not be removed if a retained segment
        flow into it. These options are ignored when continuous=False.
        ----------
        Inputs:
            ids: A list or numpy 1D array listing the IDs of segments that may
                be removed from the network
            indices: A boolean numpy 1D array with one element per stream segment.
                True elements indicate segments that may be removed from the
                network.
            continuous: If True (default), segments will only be removed if they
                do not break the continuity of the stream network. If False, all
                indicated segments are removed.
            upstream: Set to False to prevent segments from being removed from the
                upstream end of a local network. Ignored if continuous=False.
            downstream: Set to False to prevent segments from being removed from
                the downstream end of a local network. Ignored if continuous=False.

        Outputs:
            boolean numpy 1D array: The indices of the segments that were removed
                from the network. Has one element per segment in the initial network.
                True elements indicate removed segments.
        """

        # Validate and determine the segments actually being removed
        requested = self._validate_selection(ids, indices)
        if continuous:
            remove = self._continuous_removal(requested, upstream, downstream)
        else:
            remove = requested
        keep = ~remove

        # Update attributes
        new = {}
        new["segments"], new["indices"] = self._update_segments(remove)
        new["ids"] = self.ids[keep]
        new["npixels"] = self.npixels[keep]
        new["child"], new["parents"] = self._update_connectivity(remove)
        new["basins"] = self._update_basins(remove)
        self._update_attributes(new)

        # Return the indices that were actually removed
        return remove

    def keep(
        self,
        *,
        ids: Optional[vector] = None,
        indices: Optional[SegmentIndices] = None,
        continuous: bool = True,
        upstream: bool = True,
        downstream: bool = True,
    ) -> None:
        """
        keep  Restricts the network to the indicated segments
        ----------
        self.keep(*, ids)
        self.keep(*, indices)
        Attempts to restrict the network to the indicated segments, but prioritizes
        the continuity of the stream network. A segment will be retained if it is
        an indicated input, or if it falls between two segments being retained.
        Equivalently, segments are only removed from the upstream and downstream
        ends of a local network. Conceptually, this algorithm first marches upstream
        and removes segments until it reaches a segment that was indicated as input.
        The algorithm then marches downstream, and again removes segments until
        reaching a segment that was indicated as input. As such, the total number
        of retained segments may be greater than the number of input segments.

        If using "ids", the input should be a list or numpy 1D array whose elements
        are the IDs of the segments to definitely retain in the network. If using
        "indices" the input should be a boolean numpy 1D array with one element
        per segment in the network. True elements indicate stream segments that
        should definitely be retained. False elements may potentially be removed.
        If you provide both inputs, segments indicated by either input are definitely
        retained in the network.

        Returns the indices of the retained segments as a boolean 1D numpy array.
        The output indices will have one element per segment in the original network.
        True elements indicate segments that were retained. False elements are
        segments that were remove. These indices are often useful for filtering values
        computed from the original network.

        self.keep(*, ..., continuous=False)
        Only keeps the indicated segments, regardless of network continuity. All
        segments not indicated by the "ids" or "indices" inputs will be removed.

        self.keep(*, continuous=True, upstream=False)
        self.keep(*, continuous=True, downstream=False)
        Further customizes the removal of segments when prioritizing the continuity
        of the stream network. When upstream=False, segments will not be removed
        from the upstream end of a local network. Equivalently, a segment will not
        be removed if it flows into a segment retained in the network. When
        downstream=False, segments will not be removed from the downstream end
        of a local network. So a segment will not be removed if a retained segment
        flow into it. These options are ignored when continuous=False.
        ----------
        Inputs:
            ids: A list or numpy 1D array listing the IDs of segments that should
                always be retained in the network
            indices: A boolean numpy 1D array with one element per stream segment.
                True elements indicate segments that should always be retained
                in the network.
            continuous: If True (default), segments will only be removed if they
                do not break the continuity of the stream network. If False, all
                non-indicated segments are removed.
            upstream: Set to False to prevent segments from being removed from the
                upstream end of a local network. Ignored if continuous=False.
            downstream: Set to False to prevent segments from being removed from
                the downstream end of a local network. Ignored if continuous=False.

        Outputs:
            boolean numpy 1D array: The indices of the segments that remained in
                the network. Has one element per segment in the initial network.
                True elements indicate retained segments.
        """

        keep = self._validate_selection(ids, indices)
        removed = self.remove(
            indices=~keep,
            continuous=continuous,
            upstream=upstream,
            downstream=downstream,
        )
        return ~removed

    def copy(self) -> Self:
        """
        copy  Returns a copy of a Segments object
        ----------
        self.copy()
        Returns a copy of the current Segments object. Stream segments can be
        removed from the new/old objects without affecting one another. Note that
        the flow direction raster is not duplicated in memory. Instead, both
        objects reference the same underlying raster.
        ----------
        Outputs:
            Segments: A copy of the current Segments object.
        """

        copy = super().__new__(Segments)
        copy._flow = self._flow
        copy._segments = self._segments.copy()
        copy._ids = self._ids.copy()
        copy._indices = self._indices.copy()
        copy._child = self._child.copy()
        copy._parents = self._parents.copy()
        copy._basins = None
        if self._basins is not None:
            copy._basins = self._basins.copy()
        return copy

    #####
    # Filtering Updates
    #####

    def _update_segments(
        self, remove: SegmentIndices
    ) -> tuple[list[shapely.LineString], indices]:
        "Computes updated linestrings and pixel indices after segments are removed"

        # Initialize new attributes
        segments = self.segments
        indices = self.indices

        # Delete items from lists
        (removed,) = np.nonzero(remove)
        for k in reversed(removed):
            del segments[k]
            del indices[k]
        return segments, indices

    @staticmethod
    def _update_family(
        child: SegmentValues, parents: SegmentParents, remove: SegmentIndices
    ) -> None:
        "Updates child-parent relationships in-place after segments are removed"

        indices = np.nonzero(remove)
        removed = np.isin(child, indices)
        child[removed] = -1
        removed = np.isin(parents, indices)
        parents[removed] = -1

    @staticmethod
    def _update_indices(family: RealArray, nremoved: VectorArray) -> None:
        "Updates connectivity indices in-place after segments are removed"

        adjust = family != -1
        indices = family[adjust]
        family[adjust] = indices - nremoved[indices]

    def _update_connectivity(
        self, remove: SegmentIndices
    ) -> tuple[SegmentValues, SegmentParents]:
        "Computes updated child and parents after segments are removed"

        # Initialize new attributes
        child = self._child.copy()
        parents = self._parents.copy()

        # Limit arrays to retained segments
        keep = ~remove
        child = child[keep]
        parents = parents[keep]

        # Update connectivity relationships and reindex as necessary
        self._update_family(child, parents, remove)
        nremoved = np.cumsum(remove)
        self._update_indices(child, nremoved)
        self._update_indices(parents, nremoved)
        return child, parents

    def _update_basins(self, remove: SegmentIndices) -> MatrixArray | None:
        "Computes an updated nested drainage basin raster after segments are removed"

        # If there aren't any basins, then leave them as None
        if self._basins is None:
            return None

        # Initialize basins. Track indices of segments being removed and updated
        basins = self._basins.copy()
        (removed,) = np.nonzero(remove)
        outdated = removed.copy()

        # Iterate through outdated (removed) segments until all are updated.
        # Do a recursive downstream search for the new nested basin end
        while outdated.size > 0:
            update = [outdated[0]]
            child = self._child[outdated[0]]
            while child != -1 and child in removed:
                update.append(child)
                child = self._child[child]

            # Get the final set up updated indices and IDs
            update = np.array(update)
            update_ids = self._indices_to_ids(update)

            # Update the basin IDs. Mark that the segments have been updated
            where = np.nonzero(np.isin(self._basins, update_ids))
            basins[where] = self._indices_to_ids(child)
            unchanged = ~np.isin(outdated, update)
            outdated = outdated[unchanged]
        return basins

    def _update_attributes(self, new: dict[str, Any]) -> None:
        "Updates filtering attributes to new values"

        # Collect the original attributes. (This way we can restore the object if
        # an error occurs mid-update)
        old = {
            "segments": self._segments,
            "ids": self._ids,
            "indices": self._indices,
            "npixels": self._npixels,
            "child": self._child,
            "parents": self._parents,
            "basins": self._basins,
        }

        # Update the attributes, but restore the original state if anything fails
        try:
            incomplete = True
            self._set_attributes(new)
            incomplete = False
        finally:
            if incomplete:
                self._set_attributes(old)

    def _set_attributes(self, atts: dict[str, Any]) -> None:
        "Sets the values of attributes affected by filtering"

        self._segments = atts["segments"]
        self._ids = atts["ids"]
        self._indices = atts["indices"]
        self._npixels = atts["npixels"]
        self._child = atts["child"]
        self._parents = atts["parents"]
        self._basins = atts["basins"]

    #####
    # Export
    #####

    def _outlet_segments(self, terminal: bool) -> list[shapely.LineString]:
        "Returns the shapely.linestring list for the requested outlets"

        if terminal:
            return [
                segment
                for keep, segment in zip(self.isterminus, self._segments)
                if keep
            ]
        else:
            return self._segments

    def _basin_polygons(self, terminal: bool):
        "Returns a generator of drainage basin (Polygon, ID value) tuples"

        basins = self.raster(basins=True, nested=not terminal).values
        mask = basins.astype(bool)
        return rasterio.features.shapes(
            basins, mask, connectivity=8, transform=self.transform
        )

    def _geojson(
        self,
        properties: PropertyDict,
        type: FeatureType,
        terminal: bool,
    ) -> FeatureCollection:
        "Builds a geojson Feature collection using validated properties"

        # Get the appropriate geometry iterable
        if type == "segments":
            geometries = self._segments
        elif type == "outlets":
            geometries = self._outlet_segments(terminal)
        else:
            geometries = self._basin_polygons(terminal)

        # Build each feature and group into a FeatureCollection. Start by getting
        # the properties for each feature
        features = []
        for g, geometry in enumerate(geometries):
            data = {field: vector[g] for field, vector in properties.items()}

            # Get the geometry
            if type == "segments":
                geometry = geojson.LineString(geometry.coords)
            elif type == "outlets":
                outlet = geometry.coords[-1]
                geometry = geojson.Point(outlet)
            else:
                geometry = geometry[0]

            # Build feature and add to collection
            feature = Feature(geometry=geometry, properties=data)
            features.append(feature)
        return FeatureCollection(features)

    def geojson(
        self,
        properties: Optional[PropertyDict] = None,
        *,
        type: FeatureType = "segments",
        terminal: bool = True,
    ) -> FeatureCollection:
        """
        geosjon  Exports the network to a geojson.FeatureCollection object
        ----------
        self.geojson()
        self.geojson(type='segments')
        Exports the network to a geojson.FeatureCollection object. The individual
        Features have LineString geometries whose coordinates proceed from upstream
        to downstream. Will have one feature per stream segment.

        self.geojson(properties)
        Specifies properties for the GeoJSON Features. The "properties" input should
        be a dict. Each key should be the (string) name of the associated property
        field. Each value should be a numpy 1D array with one element per exported
        feature. The arrays must have an integer, floating-point, or boolean dtype.
        All properties in the output GeoJSON Features will have a floating-point type.

        self.geojson(..., *, type='outlets')
        self.geojson(..., *, type='basins')
        If type='outlets', exports the terminal outlet points as a collection of Point
        features. If type='basins', exports the terminal outlet basins as a collection
        of Polygon features. The output geojson will have one feature per local
        drainage network.

        self.geojson(..., *, type='outlets', terminal=False)
        self.geojson(..., *, type='basins', terminal=False)
        Exports an outlet or basin for every segment in the network, rather than
        just the terminal segments. If type='outlets', exports the outlet point
        for each segment in the network. If type='basins', exports the nested
        drainage basins as Polygon features. We recommend avoiding the nested
        drainage basins when possible, as these features are slow to generate.
        Note that the "terminal" option is ignored when exporting segments.
        ----------
        Inputs:
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with an integer,
                floating-point, or boolean dtype. Each array should have one
                element per segment, unless exporting terminal outlet basins.
                In this case, each array should have one element per terminal
                segment.
            type: A string indicating the type of feature to export. Options are
                'segments', 'outlets', and 'basins'.
            terminal: Customizes the export of outlet Points and basin Polygons.
                If True (default), exports the terminal outlet points or terminal
                outlet basins. If False, exports all outlet points or the nested
                drainage basins. Ignored if type='segments'.

        Outputs:
            geojson.FeatureCollection: The collection of stream network features
        """

        properties, type, terminal = self._validate_export(properties, type, terminal)
        return self._geojson(properties, type, terminal)

    def save(
        self,
        path: Pathlike,
        properties: Optional[PropertyDict] = None,
        *,
        type: FeatureType = "segments",
        terminal: bool = True,
        driver: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        """
        save  Saves the network to a vector feature file
        ----------
        save(path)
        save(path, *, overwrite=True)
        Saves the network to the indicated path. Each segment is saved as a vector
        feature with a LineString geometry whose coordinates proceed from upstream
        to downstream. The vector features will not have any data properties. In
        the default state, the method will raise a FileExistsError if the file
        already exists. Set overwrite=True to enable the replacement of existing
        files.

        By default, the method will attempt to guess the intended file format based
        on the path extensions, and will raise an Exception if the file format
        cannot be guessed. However, see below for a syntax to specify the driver,
        regardless of extension. You can use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions. We note that pfdf is tested using the "GeoJSON" driver (.geojson
        extension), and so this format is likely the most robust.

        save(path, properties)
        Specifies data properties for the saved features. The "properties" input should
        be a dict. Each key should be the (string) name of the associated property
        field. Each value should be a numpy 1D array with one element per segment
        in the network. The arrays must have an integer, floating-point, or
        boolean dtype. Note that all properties will be converted to a floating-point
        type in the saved file.

        self.save(..., *, type='outlets')
        self.save(..., *, type='basins')
        If type='outlets', saves the terminal outlet points as a collection of Point
        features. If type='basins', saves the terminal outlet basins as a collection
        of Polygon features.

        self.save(..., *, type='outlets', terminal=False)
        self.save(..., *, type='basins', terminal=False)
        Saves an outlet or basin for every segment in the network, rather than
        just the terminal segments. If type='outlets', saves the outlet point
        for each segment in the network. If type='basins', saves the nested
        drainage basins as Polygon features. We recommend avoiding the nested
        drainage basins when possible, as these features are slow to generate.
        Note that the "terminal" option is ignored when exporting segments.

        save(..., *, driver)
        Specifies the file format driver to used to write the vector feature file.
        Uses this format regardless of the file extension. You can call:
            >>> pfdf.utils.driver.vectors()
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR)
        to write vector files, and so additional drivers may work if their
        associated build requirements are met. You can call:
            >>> fiona.drvsupport.vector_driver_extensions()
        to summarize the drivers currently supported by fiona, and a complete
        list of driver build requirements is available here:
        https://gdal.org/drivers/vector/index.html
        ----------
        Inputs:
            path: The path to the output file
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with one element per
                segment. Each array should have an integer, floating-point, or
                boolean dtype.
            basins: Set to True to export drainage basin polygons. If False (default),
                exports stream segment LineString features.
            nested: Set to True to export nested drainage basins. If False (default),
                exports outlet basins. Ignored if basins = False.
            overwrite: True to allow replacement of existing files. False (default)
                to prevent overwriting.
            driver: The name of the file-format driver to use when writing the
                vector feature file. Uses this driver regardless of file extension.
        """

        # Validate and get the features as geojson
        validate.output_path(path, overwrite)
        properties, type, terminal = self._validate_export(properties, type, terminal)
        collection = self._geojson(properties, type, terminal)

        # Build the schema
        geometries = {"segments": "LineString", "outlets": "Point", "basins": "Polygon"}
        schema = {
            "geometry": geometries[type],
            "properties": {key: "float" for key in properties.keys()},
        }

        # Write file
        records = collection["features"]
        with fiona.open(path, "w", driver=driver, crs=self.crs, schema=schema) as file:
            file.writerecords(records)
