"""
watershed  Functions that implement raster watershed analyses
----------
The watershed module provides functions that implement watershed analyses using
rasters derived from a digital elevation model (DEM) raster. Note that the 
functions in this module are for raster-wide analyses. Please see the "segments"
module if you are instead interested in computing values for individual stream
segments or stream segment basins.

The typical workflow for using the watershed module is to first use the "condition"
function to condition a DEM (i.e. filling pits and resolving flats). Then, use the
"flow" function to compute D8 flow directions from a DEM. These flow directions are
an essential input to all other watershed functions. With the flow directions, users
can compute flow accumulation (also referred to as upslope area), D8 flow slopes, 
and the vertical relief of watershed pixels. We note that the accumulation function 
essentially counts the number of upslope pixels in its base configuration.
However, it can also be set to compute weighted and masked sums over upslope areas.

The module also contains the "catchment" and "network" functions, which can be
used to extract stream segment networks and catchment basins. However, most
users will not need to use these functions and should instead use the
pfdf.segments.Segments class to build and manage the stream segments in a drainage
network.

FLOW DIRECTION SCHEME:
All functions in this module produce/expect D8 flow directions that conform to
the TauDEM style. For a given raster cell, the TauDEM style is as follows:

    4 3 2
    5 X 1
    6 7 8

where X represents the raster cell, and the numbers represent flow to the 
adjacent neighbor.
----------
Functions:
    condition       - Conditions a DEM by filling pit, filling depressions, and/or resolving flats
    flow            - Computes D8 flow directions from a conditioned DEM
    slopes          - Computes D8 flow slopes
    relief          - Computes vertical relief to the nearest ridge cell
    accumulation    - Computes basic, weighted, or masked flow accumulation
    catchment       - Returns the catchment mask for a DEM pixel
    network         - Builds a stream segment raster

Internal:
    _to_pysheds     - Converts a raster to pysheds and returns metadata
"""
from math import ceil
from typing import Any, Optional

import numpy as np
from geojson.feature import FeatureCollection
from numpy import nan
from pysheds.grid import Grid
from pysheds.sview import Raster as pysheds_raster
from shapely import LineString
from shapely.ops import substring

from pfdf._utils import nodata_, real, validate
from pfdf.raster import Raster, RasterInput
from pfdf.typing import scalar

# Flow direction options - D8 and TauDEM style directions
_FLOW_OPTIONS = {"routing": "d8", "dirmap": (3, 2, 1, 8, 7, 6, 5, 4)}


#####
# User Functions
#####

def condition(
        dem: RasterInput,
        *,
        fill_pits: bool = True, 
        fill_depressions: bool = False, 
        resolve_flats: bool = True
    ) -> Raster:
    """
    condition  Conditions a DEM to resolve pits, depressions, and/or flats
    ----------
    condition(dem)
    Conditions a DEM to fill pits and resolve flats. A pit is defined as a single
    cell lower than all its surrounding neighbors. When a pit is filled, its
    elevation is raised to match that of its lowest neighbor. Flats are sets of
    adjacent cells with the same elevation, such that there are multiple possible
    flow directions. When a flat is resolved, the elevations of the associated
    cells are minutely adjusted so that their elevations no longer match.

    condition(dem, *, fill_pits=False)
    condition(dem, *, fill_depressions=True)
    condition(dem, *, resolve_flats=False)
    Allows you to specify which steps should be implemented to condition the DEM.
    By default, fills pits and resolves flats. Set these options to False to disable
    these steps. If all options are enabled, fills pits first, then fills depressions,
    then resolves flats.

    A depression is a set of multiple adjacent cells that are all lower than their 
    surrounding neighbors. When a depression is filled, the elevations of all the 
    low cells are set to match the elevation of the lowest cell surrounding the 
    depression. Note that filling depressions can result in unrealistically large 
    flat areas that adversely affect the calculation of flow directions (even after
    resolving flats). As such, depression filling is disabled by default.
    ----------
    Inputs:
        dem: A digital elevation model raster
        fill_pits: Set to True (default) to fill pits. Set to False to disable this step
        fill_depressions: Set to True to fill depressions. Set to False (default)
            to disable this step
        resolve_flats: Set to True (default) to resolve flats. Set to False to
            disable this step.

    Outputs:
        Raster: A conditioned DEM raster
    """

    # Validate. Get metadata and convert to pysheds
    dem = Raster(dem, "dem")
    dem, metadata = _to_pysheds(dem)

    # Condition DEM
    grid = Grid.from_raster(dem, nodata=nan)
    if fill_pits:
        dem = grid.fill_pits(dem, nodata_out=nan)
    if fill_depressions:
        dem = grid.fill_depressions(dem, nodata_out=nan)
    if resolve_flats:
        dem = grid.resolve_flats(dem, nodata_out=nan)
    return Raster.from_array(dem, nodata=nan, **metadata)


def flow(dem: RasterInput) -> Raster:
    """
    flow  Compute D8 flow directions from a conditioned DEM
    ----------
    flow(dem)
    Computes D8 flow directions for a conditioned DEM. Flow direction numbers
    follow the TauDEM style, as follows:

        4 3 2
        5 X 1
        6 7 8

    Values of 0 indicate NoData - these may results from NoData values in the
    original DEM, as well as any unresolved pits, depressions, or flats.
    ----------
    Inputs:
        dem: A conditioned digital elevation model raster

    Outputs:
        Raster: The D8 flow directions for the DEM
    """

    # Validate. Get metadata and convert to pysheds
    dem = Raster(dem, "dem")
    dem, metadata = _to_pysheds(dem)

    # Compute flow directions
    grid = Grid.from_raster(dem, nodata=nan)
    flow = grid.flowdir(dem, flats=0, pits=0, nodata_out=0, **_FLOW_OPTIONS)
    return Raster.from_array(flow, nodata=0, **metadata)


def slopes(dem: RasterInput, flow: RasterInput) -> Raster:
    """
    slopes  Computes D8 flow slopes for a watershed
    ----------
    slopes(dem, flow)
    Returns D8 flow slopes for a watershed. Computes these slopes using a DEM
    raster, and TauDEM-style D8 flow directions. Note that the DEM should be a
    raw DEM - it does not need to resolve pits and flats.
    ----------
    Inputs:
        dem: A digital elevation model raster
        flow: A raster with TauDEM-style D8 flow directions

    Outputs:
        slopes: The computed D8 flow slopes for the watershed
    """

    # Validate
    dem = Raster(dem, "dem")
    flow = dem._validate(flow, "flow directions")
    validate.flow(flow.values, flow.name, nodata=flow.nodata)

    # Get metadata and convert to pysheds
    dem, metadata = _to_pysheds(dem)
    flow = flow.as_pysheds()

    # Compute slopes
    grid = Grid.from_raster(flow, nodata=nan)
    slopes = grid.cell_slopes(dem, flow, nodata_out=nan, **_FLOW_OPTIONS)
    return Raster.from_array(slopes, nodata=nan, **metadata)


def relief(dem: RasterInput, flow: RasterInput) -> Raster:
    """
    relief  Computes vertical relief to the highest ridge cell
    ----------
    relief(dem, flow)
    Computes the vertical relief for each watershed pixel. Here, vertical relief
    is defined as the change in elevation between each pixel and its nearest
    ridge cell. (A ridge cell is an upslope cell with no contributing flow from
    other pixels). Computes these slopes using a DEM raster, and TauDEM-style D8
    flow directions. Note that the DEM should be a raw DEM - it does not need to
    resolve pits and flats.
    ----------
    Inputs:
        dem: A digital elevation model raster
        flow: A TauDEM-style D8 flow direction raster

    Outputs:
        Raster: The vertical relief of the nearest ridge cell.
    """

    # Validate
    dem = Raster(dem, "dem")
    flow = dem._validate(flow, "flow directions")
    validate.flow(flow.values, flow.name, nodata=flow.nodata)

    # Get metadata and convert to pysheds
    dem, metadata = _to_pysheds(dem)
    flow = flow.as_pysheds()

    # Locate ridge cells. Fix any NoData elements treated as ridges
    grid = Grid.from_raster(flow, nodata=nan)
    ridge_distance = grid.distance_to_ridge(flow, nodata_out=nan, **_FLOW_OPTIONS)
    nodatas = nodata_.mask(flow, flow.nodata)
    ridge_distance[nodatas] = nan
    isridge = ridge_distance == 0

    # Get the height of the ridge cell associated with each pixel
    ridge_height = dem.copy()
    ridge_height[~isridge] = 0
    ridge_height = grid.accumulation(
        flow, ridge_height, nodata_out=nan, **_FLOW_OPTIONS
    )
    ridge_height[nodatas] = nan

    # Compute vertical relief
    relief = ridge_height - dem
    return Raster.from_array(relief, nodata=nan, **metadata)


def accumulation(
    flow: RasterInput,
    weights: Optional[RasterInput] = None,
    mask: Optional[RasterInput] = None,
) -> Raster:
    """
    accumulation  Computes basic, weighted, or masked flow accumulation
    ----------
    accumulation(flow)
    Uses D8 flow directions to compute basic flow accumulation. In this setup,
    each pixel is given a value of 1, so the accumulation for each pixel indicates
    the number of upslope pixels. Note that each pixel is included in its own
    accumulation, so the minimum valid accumulation is 1. NoData values are
    indicated by NaN. Flow directions should follow the TauDEM style (see the
    documentation of watershed.flow for details).

    accumulation(flow, weights)
    Computes weighted accumulations. Here, the value of each pixel is set by the
    input "weights" raster, so the accumulation for each pixel is a sum over
    itself and all upslope pixels. The weights raster must have the same shape,
    transform, and crs as the flow raster.

    accumulation(flow, mask)
    accumulation(flow, weights, mask)
    Computes a masked accumulation. In this syntax, only the True elements of
    the mask are included in accumulations. All False elements are given a weight
    of 0. The accumulation for each pixel is thus the sum over all upslope pixels
    included in the mask. If weights are not specified, then all included pixels
    are given a weight of 1. Note that the mask raster must have the same shape,
    transform, and crs as the flow raster.
    ----------
    Inputs:
        flow: A D8 flow direction raster in the TauDEM style
        weights: A raster indicating the value of each pixel
        mask: A raster whose True elements indicate pixels that should be included
            in the accumulation.

    Outputs:
        Raster: The computed flow accumulation
    """

    # Initial validation
    flow = Raster(flow, "flow directions")
    if weights is not None:
        weights = flow._validate(weights, "weights")
    if mask is not None:
        mask = flow._validate(mask, "mask")

    # Initialize NoData masks for optional rasters
    weights_nodata = None
    mask_nodata = None

    # Locate NoDatas and validate array elements
    flow_nodata = nodata_.mask(flow.values, flow.nodata)
    validate.flow(flow.values, flow.name, nodata=flow.nodata)
    if mask is not None:
        mask_nodata = nodata_.mask(mask.values, mask.nodata)
        mask = validate.boolean(mask.values, mask.name, isdata=mask.nodata)
    if weights is not None:
        weights_nodata = nodata_.mask(weights.values, weights.nodata)

    # Create default weights or mask as needed
    if weights is None and mask is None:
        weights = np.ones(flow.shape, dtype=float)
    elif mask is None:
        weights = weights.values
    elif weights is None:
        weights = mask
    else:
        weights = mask * weights.values

    # Get the weights as a float array, and then set NoData elements to NaN.
    # This is to prevent numeric NoData values from propagating through the
    # pysheds accumulation algorithm.
    weights = weights.astype(float)
    masks = (flow_nodata, weights_nodata, mask_nodata)
    weights = nodata_.fill(weights, masks, nan)

    # Get metadata and convert to pysheds
    flow, metadata = _to_pysheds(flow)
    weights = Raster.from_array(weights, nodata=nan, **metadata).as_pysheds()

    # Compute accumulation
    grid = Grid.from_raster(flow)
    accumulation = grid.accumulation(flow, weights, nodata_out=nan, **_FLOW_OPTIONS)
    return Raster.from_array(accumulation, nodata=nan, **metadata)


def catchment(flow: RasterInput, row: scalar, column: scalar) -> Raster:
    """
    catchment  Returns the catchment mask for a DEM pixel
    ----------
    catchment(flow, row, column)
    Determines the catchment area for the DEM pixel at the indicated row and
    column. Returns a mask for the catchment area. The mask will have the same
    shape as the input flow directions raster - True values indicated pixels
    that are in the catchment area, False values are outside of the catchment.
    Any NoData values in the flow directions will become False values in the
    catchment mask.
    ----------
    Inputs:
        flow: D8 flow directions for the DEM (in the TauDEM style)
        row: The row index of the queried pixel in the DEM
        column: The column index of the queried pixel in the DEM

    Outputs:
        Raster: The catchment mask for the queried pixel
    """

    # Validate
    row = validate.scalar(row, "row", dtype=real)
    validate.integers(row, "row")
    validate.inrange(row, "row", min=1, max=flow.shape[0])
    column = validate.scalar(column, "column")
    validate.integers(column, "column")
    validate.inrange(column, "column", min=1, max=flow.shape[1])
    flow = Raster(flow, "flow directions")
    validate.flow(flow.values, flow.name, nodata=flow.nodata)

    # Get metadata and convert to pysheds
    flow, metadata = _to_pysheds(flow)
    column = column[0]
    row = row[0]

    # Get the catchment mask
    grid = Grid.from_raster(flow)
    catchment = grid.catchment(
        fdir=flow, x=column, y=row, xytype="index", **_FLOW_OPTIONS
    )
    return Raster.from_array(catchment, **metadata)


def network(
    flow: RasterInput, mask: RasterInput, max_length: Optional[scalar] = None
) -> list[LineString]:
    """
    network  Returns a list of stream segment LineStrings
    ----------
    network(flow, mask)
    Calculates a stream segment network and returns the segments as a list of
    shapely.LineString objects. These stream segments approximate the river beds
    in a drainage basin - they are not the full catchment basin.

    The stream segment network is determined using a (TauDEM-style) D8 flow direction
    raster and a raster mask. The mask is used to indicate the pixels under
    consideration as stream segments. True pixels may possibly be assigned to a
    stream segment, False pixels will never be assiged to a stream segment. The
    mask typically screens out pixels with low flow accumulations, and may include
    other screenings - for example, to remove pixels in large bodies of water, or
    pixels below developed areas.

    network(flow, mask, max_length)
    Also specifies a maximum length for the segments in the network. Any segment
    longer than this length will be split into multiple pieces. The split pieces
    will all have the same length, which will be <= max_length. The units of
    max_length should be the base units of the coordinate reference system associated
    with the flow raster. In practice, this is almost always units of meters.
    ----------
    Inputs:
        flow: A TauDEM-style D8 flow direction raster
        mask: A raster whose True values indicate the pixels that may potentially
            belong to a stream segment.
        max_length: A maximum allowed length for segments in the network. Units
            should be the same as the base units of the flow raster CRS (usually meters)

    Outputs:
        list[shapely.LineString]: The stream segments in the network, represented
            by shapely.LineString objects. The coordinates of each LineString
            proceed from upstream to downstream. Coordinates are relative to the
            flow raster CRS (rather than raster pixel indices).
    """

    # Validate
    if max_length is not None:
        max_length = validate.scalar(max_length, "max_length", dtype=real)
        validate.positive(max_length, "max_length")
    flow = Raster(flow, "flow directions")
    mask = flow._validate(mask, "mask")
    validate.flow(flow.values, flow.name, nodata=flow.nodata)
    validate.boolean(mask.values, mask.name, nodata=mask.nodata)

    # Convert to pysheds
    flow = flow.as_pysheds()
    mask = mask.as_pysheds()

    # Get the geojson river network, convert to shapely linestrings
    grid = Grid.from_raster(flow)
    segments = grid.extract_river_network(flow, mask, **_FLOW_OPTIONS)
    segments = _geojson_to_shapely(segments)

    # Optionally enforce a max length
    if max_length is not None:
        segments = _split_segments(segments, max_length[0])
    return segments


#####
# Internal
#####


def _to_pysheds(raster: Raster) -> tuple[pysheds_raster, dict[str, Any]]:
    "Converts a raster to pysheds and returns a dict of transform and crs metadata"
    metadata = {"transform": raster.transform, "crs": raster.crs}
    raster = raster.as_pysheds()
    return raster, metadata


def _geojson_to_shapely(segments: FeatureCollection) -> list[LineString]:
    "Converts a stream network GeoJSON to a list of shapely Linestrings"
    segments = segments["features"]
    for s, segment in enumerate(segments):
        coords = segment["geometry"]["coordinates"]
        segments[s] = LineString(coords)
    return segments


def _split_segments(segments: list[LineString], max_length: float) -> list[LineString]:
    "Splits stream network segments longer than a maximum length"
    split_segments = []
    for segment in segments:
        pieces = _split(segment, max_length)
        split_segments += pieces
    return split_segments


def _split(segment: LineString, max_length: float) -> list[LineString]:
    "Splits a stream segment into pieces shorter than a maximum length"

    # If under the max length, just return the segment
    if segment.length <= max_length:
        return [segment]

    # Determine the length of each substring and initialize list of pieces
    npieces = ceil(segment.length / max_length)
    length = segment.length / npieces
    pieces = [None] * npieces

    # Collect the substrings
    start = 0
    for k in range(npieces):
        end = (k + 1) * length
        pieces[k] = substring(segment, start, end)
        start = end
    return pieces
