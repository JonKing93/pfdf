"""
Functions that implement raster watershed analyses
----------
The watershed module provides functions that implement watershed analyses using
rasters derived from a digital elevation model (DEM) raster. Note that the
functions in this module are for raster-wide analyses. Please see the "segments"
module if you are instead interested in computing values for individual stream
segments or stream segment basins.

Typical workflow is to use the "condition" function to condition a DEM. Then use
"flow" to compute flow directions. The flow directions can then be used to compute
slopes, relief, and accumulation. This module also contains the "catchment" and
"network" functions, but most users will not need these, as they are implemented
internally by the Segments class.

GEOREFERENCING:
The "slopes" function requires the input DEM to have both a CRS and affine Transform.
Most workflows will require flow slopes, so we recommend using a properly
georeferenced DEM whenever possible.

NODATA VALUES:
This module relies on the pysheds library, which will assign a default NoData
value of 0 to any raster that does not have a NoData value. This can cause
unexpected results when a DEM has valid 0 values and does not have a NoData value.

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
    catchment       - Returns the catchment mask for a watershed pixel
    network         - Returns the stream segments as a list of shapely.LineString objects

Internal:
    _to_pysheds         - Converts a raster to pysheds and returns metadata
    _geojson_to_shapely - Converts a stream network GeoJSON to a list of shapely LineStrings
    _split_segments     - Splits stream network segments longer than a specified length
    _split              - Splits a stream segment into pieces shorter than a specified length
"""

from __future__ import annotations

import typing
from math import ceil, inf, nan

import numpy as np
from pysheds.grid import Grid
from shapely import LineString
from shapely.ops import substring

import pfdf._validate.core as validate
from pfdf._utils import all_nones, real
from pfdf._utils.nodata import NodataMask
from pfdf._utils.patches import NodataPatch, RidgePatch
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import crs
from pfdf.raster import Raster

if typing.TYPE_CHECKING:
    from typing import Any, Optional

    from geojson.feature import FeatureCollection
    from pysheds.sview import Raster as PyshedsRaster

    from pfdf.typing.core import Units, scalar
    from pfdf.typing.raster import RasterInput


# Flow direction options - D8 and TauDEM style directions
_FLOW_OPTIONS = {"routing": "d8", "dirmap": (3, 2, 1, 8, 7, 6, 5, 4)}


#####
# User Functions
#####


def condition(
    dem: RasterInput,
    *,
    fill_pits: bool = True,
    fill_depressions: bool = True,
    resolve_flats: bool = True,
) -> Raster:
    """
    condition  Conditions a DEM to resolve pits, depressions, and/or flats
    ----------
    condition(dem)
    Conditions a DEM by filling pits, filling depressions, and then resolving
    flats. A pit is defined as a single cell lower than all its surrounding neighbors.
    When a pit is filled, its elevation is raised to match that of its lowest
    neighbor. A depression consists of multiple cells surrounded by higher terrain.
    When a depression is filled, the elevations of all depressed cells are raised
    to match the elevation of the lowest pixel on the border of the depression.
    Flats are sets of adjacent cells with the same elevation, and often result from
    filling pits and depressions (although they may also occur naturally). When
    a flat is resolved the elevations of the associated cells are minutely adjusted
    so that their elevations no longer match.

    condition(dem, *, fill_pits=False)
    condition(dem, *, fill_depressions=False)
    condition(dem, *, resolve_flats=False)
    Allows you to skip specific steps of the conditioning algorithm. Setting an
    option to False will disable the associated conditioning step. Raises a ValueError
    if you attempt to skip all three steps.
    ----------
    Inputs:
        dem: A digital elevation model raster
        fill_pits: True (default) to fill pits. False to disable this step
        fill_depressions: True (default) to fill depressions. False to disable this step
        resolve_flats: True (default) to resolve flats. False to disable this step

    Outputs:
        Raster: A conditioned DEM raster
    """

    # Must use at least one conditioning algorithm
    if not fill_pits and not fill_depressions and not resolve_flats:
        raise ValueError(
            "You cannot skip all three steps of the conditioning algorithm. "
            "At least one step must be implemented."
        )

    # Validate raster. Set all NoData values to -inf (other values can cause
    # edge case issues - NaNs and numeric values can be interpreted as high terrain
    # when filling pits/depressions, and numeric values are neglected for flats)
    dem = Raster(dem, "dem")
    nodatas = NodataMask(dem.values, dem.nodata)
    dem, metadata = _to_pysheds(dem)
    dem = dem.astype(float)
    nodatas.fill(dem, -inf)

    # Condition DEM
    grid = Grid.from_raster(dem, nodata=-inf)
    if fill_pits:
        dem = grid.fill_pits(dem, nodata_out=-inf)
    if fill_depressions:
        dem = grid.fill_depressions(dem, nodata_out=-inf)
    if resolve_flats:
        dem = grid.resolve_flats(dem, nodata_out=-inf)
    return Raster.from_array(dem, nodata=-inf, **metadata, copy=False)


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
    with NodataPatch():
        flow = grid.flowdir(dem, flats=0, pits=0, nodata_out=0, **_FLOW_OPTIONS)
    flow = flow.astype("int8")
    return Raster.from_array(flow, nodata=0, **metadata, copy=False)


def slopes(
    dem: RasterInput,
    flow: RasterInput,
    dem_per_m: Optional[scalar] = None,
    check_flow: bool = True,
) -> Raster:
    """
    slopes  Computes D8 flow slopes for a watershed
    ----------
    slopes(dem, flow)
    slopes(dem, flow, dem_per_m)
    Returns D8 flow slopes for a watershed. Computes these slopes using a DEM
    raster, and TauDEM-style D8 flow directions. The DEM must have both a CRS and
    an affine Transform. Note that the DEM may be a raw DEM - it does not need to
    resolve pits and flats, although you may wish to use a resolved DEM for
    consistency across your analysis.  The returned slopes will be unitless
    gradients. The rise is determined using the DEM, and the run is determined
    from the CRS and transform. If the CRS base unit is not meters, converts the
    run to meters before computing slope gradients.

    By default, this routine assumes that the DEM is in units of meters. If this
    is not the case, use the "dem_per_m" to specify a conversion factor (number
    of DEM units per meter).

    slopes(..., check_flow=False)
    Disables validation checking of the flow directions raster. Validation is not
    necessary for flow directions directly output by the "watershed.flow" function,
    and disabling the validation can improve runtimes for large rasters. However,
    be warned that this option may produce unexpected results if the flow directions
    raster contains invalid values.
    ----------
    Inputs:
        dem: A digital elevation model raster
        flow: A raster with TauDEM-style D8 flow directions
        dem_per_m: A conversion factor from DEM units to meters
        check_flow: True (default) to validate the flow directions raster.
            False to disable validation checks.

    Outputs:
        slopes: The computed D8 flow slopes for the watershed
    """

    # Validate DEM metadata
    dem = Raster(dem, "dem")
    if dem.crs is None:
        raise MissingCRSError(
            "In order to compute flow slopes, the conditioned DEM must have a CRS."
        )
    if dem.transform is None:
        raise MissingTransformError(
            "In order to compute flow slopes, the conditioned DEM must have an affine transform."
        )

    # Validate flow and conversion factor
    dem_per_m = validate.conversion(dem_per_m, "dem_per_m")
    flow = dem.validate(flow, "flow directions")
    if check_flow:
        validate.flow(flow.values, flow.name, ignore=flow.nodata)

    # Get metadata and convert to pysheds. Compute slopes
    demsheds, metadata = _to_pysheds(dem)
    flow = flow.as_pysheds()
    grid = Grid.from_raster(flow, nodata=nan)
    with NodataPatch():
        slopes = grid.cell_slopes(demsheds, flow, nodata_out=nan, **_FLOW_OPTIONS)

    # Ensure slopes are unitless gradients and return raster
    if dem_per_m is not None:
        slopes = slopes / dem_per_m
    if dem.crs_units[1] != "metre":
        crs_per_m = crs.y_units_per_m(dem.crs)
        slopes = slopes * crs_per_m
    return Raster.from_array(slopes, nodata=nan, **metadata, copy=False)


def relief(
    dem: RasterInput,
    flow: RasterInput,
    check_flow: bool = True,
) -> Raster:
    """
    Computes vertical relief to the highest ridge cell
    ----------
    relief(dem, flow)
    Computes the vertical relief for each watershed pixel. Here, vertical relief
    is defined as the change in elevation between each pixel and its nearest
    ridge cell. (A ridge cell is an upslope cell with no contributing flow from
    other pixels). Computes these slopes using a DEM raster, and TauDEM-style D8
    flow directions. Note that the DEM should be a raw DEM - it does not need to
    resolve pits and flats.

    relief(..., check_flow=False)
    Disables validation checking of the flow directions raster. Validation is not
    necessary for flow directions directly output by the "watershed.flow" function,
    and disabling the validation can improve runtimes for large rasters. However,
    be warned that this option may produce unexpected results if the flow directions
    raster contains invalid values.
    ----------
    Inputs:
        dem: A digital elevation model raster
        flow: A TauDEM-style D8 flow direction raster
        check_flow: True (default) to validate the flow directions raster.
            False to disable validation checks.

    Outputs:
        Raster: The vertical relief of the nearest ridge cell.
    """

    # Validate
    dem = Raster(dem, "dem")
    flow = dem.validate(flow, "flow directions")
    if check_flow:
        validate.flow(flow.values, flow.name, ignore=flow.nodata)

    # Mark Nodatas in the DEM or flow directions as NaN.
    nodatas = NodataMask(dem.values, dem.nodata)
    nodatas = nodatas | NodataMask(flow.values, flow.nodata)

    # Get metadata and convert to pysheds
    dem, metadata = _to_pysheds(dem)
    flow = flow.as_pysheds()

    # Compute vertical drops. Relief is the vertical distance to the ridge cells
    # Preserve NoData pixels (sometimes distance_to_ridge neglects them)
    grid = Grid.from_raster(flow, nodata=nan)
    with RidgePatch():
        with NodataPatch():
            drops = grid.cell_dh(dem, flow, nodata_out=nan, **_FLOW_OPTIONS)
            relief = grid.distance_to_ridge(
                flow, weights=drops, nodata_out=nan, **_FLOW_OPTIONS
            )
    nodatas.fill(relief, nan)
    return Raster.from_array(relief, nodata=nan, **metadata, copy=False)


def accumulation(
    flow: RasterInput,
    weights: Optional[RasterInput] = None,
    mask: Optional[RasterInput] = None,
    *,
    times: Optional[scalar] = None,
    omitnan: bool = False,
    check_flow: bool = True,
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
    accumulation(flow, weights, *, omitnan=True)
    Computes weighted accumulations. Here, the value of each pixel is set by the
    input "weights" raster, so the accumulation for each pixel is a sum over
    itself and all upslope pixels. The weights raster must have the same shape,
    transform, and crs as the flow raster.

    In the default case, NaN and NoData values in the weights raster are set to
    propagate through the accumulation. So any pixel that is downstream of a NaN
    or a NoData weight will have its accumulation set to NaN. Setting omitnan=True
    will change this behavior to instead ignore NaN and NoData values. Effectively,
    NaN and NoData pixels will be given weights of 0.

    accumulation(..., mask)
    Computes a masked accumulation. In this syntax, only the True elements of
    the mask are included in accumulations. All False elements are given a weight
    of 0. NoData elements in the mask are interpreted as False. The accumulation
    for each pixel is thus the sum over all catchment pixels included in the mask.
    If weights are not specified, then all included pixels are given a weight of
    1. Note that the mask raster must have the same shape, transform, and crs as
    the flow raster.

    accumulation(..., *, times)
    Returns accumulation multiplied by the indicated scalar value. This option is
    often set to the area of a raster pixel in order to return accumulation in
    specific units, rather than pixel counts.

    accumulation(..., *, check_flow=False)
    Disables validation checking of the flow directions raster. Validation is not
    necessary for flow directions directly output by the "watershed.flow" function,
    and disabling the validation can improve runtimes for large rasters. However,
    be warned that this option may produce unexpected results if the flow directions
    raster contains invalid values.
    ----------
    Inputs:
        flow: A D8 flow direction raster in the TauDEM style
        weights: A raster indicating the value of each pixel
        omitnan: True to ignore NaN and NoData values in the weights raster.
            False (default) propagates these values as NaN to all downstream pixels.
        mask: A raster whose True elements indicate pixels that should be included
            in the accumulation.
        times: A multiplicative constant applied to the computed accumulation.
        check_flow: True (default) to validate the flow directions raster.
            False to disable validation checks.

    Outputs:
        Raster: The computed flow accumulation
    """

    # Validate
    if times is not None:
        times = validate.scalar(times, "times", dtype=real)
    flow = Raster(flow, "flow directions")
    if weights is not None:
        weights = flow.validate(weights, "weights")
    if mask is not None:
        mask = flow.validate(mask, "mask")
        mask = validate.boolean(mask.values, mask.name, ignore=mask.nodata)
    if check_flow:
        validate.flow(flow.values, flow.name, ignore=flow.nodata)

    # Locate weights NoDatas and optionally NaNs
    nodatas = NodataMask(flow.values, None)
    if weights is not None:
        if not nodatas.isnan(weights.nodata):
            nodatas = nodatas | NodataMask(weights.values, weights.nodata)
        if omitnan:
            nodatas = nodatas | np.isnan(weights.values)

    # Create default weights, or mask weights as needed
    if all_nones(weights, mask):
        weights = np.ones(flow.shape, dtype=float)
    elif mask is None:
        weights = weights.values
    elif weights is None:
        weights = mask
    else:
        weights = mask * weights.values

    # Ensure weights have floating dtype. Then adjust NoData and NaN values to
    # prevent propagation through the pysheds accumulation algorithm
    weights = weights.astype(float)
    if omitnan:
        fill = 0
    else:
        fill = nan
    nodatas.fill(weights, fill)

    # Always set flow Nodata elements to NaN
    nodatas = NodataMask(flow.values, flow.nodata)
    nodatas.fill(weights, nan)

    # Get metadata and convert to pysheds. Note that weights.nodata should be NaN
    # to prevent the algorithm from stopping at 0s when ignoring NaNs
    flow, metadata = _to_pysheds(flow)
    weights = Raster.from_array(weights, nodata=nan, **metadata, copy=False)
    weights = weights.as_pysheds()

    # Compute accumulation
    grid = Grid.from_raster(flow)
    with NodataPatch():
        accumulation = grid.accumulation(flow, weights, nodata_out=nan, **_FLOW_OPTIONS)

    # Apply multiplicative factor if provided
    if times is not None and times != 1:
        accumulation = accumulation * times
    return Raster.from_array(accumulation, nodata=nan, **metadata, copy=False)


def catchment(
    flow: RasterInput, row: scalar, column: scalar, check_flow: bool = True
) -> Raster:
    """
    catchment  Returns the catchment mask for a DEM pixel
    ----------
    catchment(flow, row, column)
    Determines the extent of the catchment upstream of the DEM pixel at the
    indicated row and column. Returns a mask for this catchment extent. The mask
    will have the same shape as the input flow directions raster - True values
    indicated pixels that are in the upstream catchment extent, False values are
    outside of the catchment. Any NoData values in the flow directions will become
    False values in the catchment mask.

    catchment(..., check_flow=False)
    Disables validation checking of the flow directions raster. Validation is not
    necessary for flow directions directly output by the "watershed.flow" function,
    and disabling the validation can improve runtimes for large rasters. However,
    be warned that this option may produce unexpected results if the flow directions
    raster contains invalid values.
    ----------
    Inputs:
        flow: D8 flow directions for the DEM (in the TauDEM style)
        row: The row index of the queried pixel in the DEM
        column: The column index of the queried pixel in the DEM
        check_flow: True (default) to validate the flow directions raster.
            False to disable validation checks.

    Outputs:
        Raster: The upstream catchment mask for the queried pixel
    """

    # Validate
    row = validate.scalar(row, "row", dtype=real)
    validate.integers(row, "row")
    validate.inrange(row, "row", min=0, max=flow.shape[0] - 1)
    column = validate.scalar(column, "column")
    validate.integers(column, "column")
    validate.inrange(column, "column", min=0, max=flow.shape[1] - 1)
    flow = Raster(flow, "flow directions")
    if check_flow:
        validate.flow(flow.values, flow.name, ignore=flow.nodata)

    # Get the catchment mask
    flow, metadata = _to_pysheds(flow)
    grid = Grid.from_raster(flow)
    with NodataPatch():
        catchment = grid.catchment(
            fdir=flow, x=column, y=row, xytype="index", **_FLOW_OPTIONS
        )
    return Raster.from_array(catchment, nodata=False, **metadata, copy=False)


def network(
    flow: RasterInput,
    mask: RasterInput,
    max_length: Optional[scalar] = None,
    units: Units = "meters",
    check_flow: bool = True,
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
    stream segment, False pixels will never be assigned to a stream segment. The
    mask typically screens out pixels with low flow accumulations, and may include
    other screenings - for example, to remove pixels in large bodies of water, or
    pixels below developed areas.

    network(..., max_length)
    network(..., max_length, units)
    Also specifies a maximum length for the segments in the network. Any segment
    longer than this length will be split into multiple pieces. The split pieces
    will all have the same length, which will be <= max_length. By default, the
    command interprets the units of max_length as meters. Use the "units" option
    to specify max_length in different units instead. Unit options include:
    "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet",
    and "miles". Note that the meters/kilometers/feet/miles options all require
    the flow raster to have a CRS. The units="base" option relaxes this requirement.

    network(..., check_flow=False)
    Disables validation checking of the flow directions raster. Validation is not
    necessary for flow directions directly output by the "watershed.flow" function,
    and disabling the validation can improve runtimes for large rasters. However,
    be warned that this option may produce unexpected results if the flow directions
    raster contains invalid values.
    ----------
    Inputs:
        flow: A TauDEM-style D8 flow direction raster
        mask: A raster whose True values indicate the pixels that may potentially
            belong to a stream segment.
        max_length: A maximum allowed length for segments in the network.
        units: Indicates the units of the max_length input. Options include:
            "base" (CRS/Transform base unit), "meters" (default), "kilometers",
            "feet", and "meters.
        check_flow: True (default) to validate the flow directions raster.
            False to disable validation checks.

    Outputs:
        list[shapely.LineString]: The stream segments in the network, represented
            by shapely.LineString objects. The coordinates of each LineString
            proceed from upstream to downstream. Coordinates are relative to the
            flow raster CRS (rather than raster pixel indices).
    """

    # Initial Validation
    flow = Raster(flow, "flow directions")
    if max_length is not None:
        max_length = validate.scalar(max_length, "max_length", dtype=real)
        validate.positive(max_length, "max_length")
        units = validate.units(units)

        # Get max_length in base axis units. Require a CRS for unit conversion
        if units != "base":
            if flow.crs is None:
                raise MissingCRSError(
                    f"Cannot convert max_length from {units} because the flow raster "
                    "does not have a CRS."
                )
            else:
                max_length = crs.units_to_base(flow.crs, "y", max_length, units)
                max_length = float(max_length[0])

    # Validate mask and flow values
    mask = flow.validate(mask, "mask")
    validate.boolean(mask.values, mask.name, ignore=mask.nodata)
    if check_flow:
        validate.flow(flow.values, flow.name, ignore=flow.nodata)

    # Convert to pysheds
    flow = flow.as_pysheds()
    mask = mask.as_pysheds()

    # Get the geojson river network. Shift coordinates to pixel centers and
    # convert to shapely linestrings
    grid = Grid.from_raster(flow)
    with NodataPatch():
        segments = grid.extract_river_network(flow, mask, **_FLOW_OPTIONS)
    segments = _geojson_to_shapely(flow, segments)

    # Optionally enforce a max length
    if max_length is not None:
        segments = _split_segments(segments, max_length)
    return segments


#####
# Internal
#####


def _to_pysheds(raster: Raster) -> tuple[PyshedsRaster, dict[str, Any]]:
    "Converts a raster to pysheds and returns a dict of transform and crs metadata"
    metadata = {"transform": raster.transform, "crs": raster.crs}
    raster = raster.as_pysheds()
    return raster, metadata


def _geojson_to_shapely(
    flow: PyshedsRaster, segments: FeatureCollection
) -> list[LineString]:
    """Converts a stream network GeoJSON to a list of shapely Linestrings.
    Also shifts linestring coordinates from the top-left corner to pixel centers"""

    # Get the step size for the center shift
    dx = flow.affine[0] / 2
    dy = flow.affine[4] / 2

    # Get the initial coordinates for each segment
    segments = segments["features"]
    for s, segment in enumerate(segments):
        coords = segment["geometry"]["coordinates"]

        # Shift coordinates to pixel centers and save as LineStrings
        coords = [(x + dx, y + dy) for x, y in coords]
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
