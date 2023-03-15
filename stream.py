"""
stream  Functions that delineate the stream network.
----------
This module contains functions that delineate an initial hazard assessment
stream network. This network is defined by drainages that are both (1) large
enough for debris-flows to occur, and (2) below a sufficient amount of burned
area. Note that this network is only the initial estimate of potentially 
hazardous drainages. Many users will want to apply additional screenings to
obtain a final set of stream segments for hazard modeling.

We recommend that most users start with the "network" function, which conducts
the stream network delineation from start to finish. See its documentation for
usage details.

Advanced users may also be interested in the low-level "links", "split",
"raster", and "search_radius" functions, which can be used to implement custom
stream network delineation routines.

This module requires upslope area, upslope burned area, and flow direction
rasters computed from a DEM. Users may wish to see the "taudem" module for
functions that compute these raster. The following is a suggested workflow 
outline for hazard assessment users:
    * Acquire DEM Data
    * Use "taudem" module to compute upslope areas and flow directions
    *** Use this module to delineate a stream network
    * Screen the stream network to a final set of drainage basins

REQUIREMENTS:
Running this module requires:
    * The ArcPy package and base Python environment shipped with ArcGIS Pro 3.0
      (Build Number 36056))
----------
User functions:
    network             - Delineates a stream network

Low-level functions:
    links               - Creates a feature layer holding links of a stream network
    split               - Split stream links longer than a maximum length
    search_radius       - Return a recommended search radius for splitting stream links
    raster              - Converts stream link polylines into a raster

Utilities:
    raster_size         - Returns the resolution of a raster as a float
    check_split_paths   - Error checking for optional splitting inputs
"""

from typing import Dict, Optional, Literal, Any
import arcpy
from os import path


def network(
    total_area: str,
    min_basin_area: float,
    burned_area: str,
    min_burned_area: float,
    flow_direction: str,
    stream_links: str,
    stream_raster: str,
    max_segment_length: Optional[float] = None,
    split_points: Optional[str] = None,
    split_links: Optional[str] = None,
) -> Dict[str, str]:
    """
    network  Delineates the stream network
    ----------
    network(total_area, min_basin_area, burned_area, min_burned_area,
            flow_direction, stream_links, stream_raster)
    Uses input rasters to delineate the links of the stream network. Saves the
    network as both a raster and feature layer. Returns a dict with the absolute
    paths to the final feature and raster layers. (In this case, the
    stream_raster and stream_links layers).

    Drainage streams are defined as raster pixels that exceed both (1) a minimum
    upslope area threshold, and (2) a minimum burned upslope area threshold.
    These drainage streams are then classified into individual stream links. The
    output feature layer represents these stream links as a set of polylines. In
    the output raster layer, the values of stream link pixels are set as the
    OBJECTID of the coresponding polyline.

    network(..., max_segment_length, split_points, split_links)
    Also restricts the stream links to a maximum length. Stream links exceeding
    this length will be split into multiple segments that respect the maximum
    allowed length. In this case, the value of the "feature" key in the output
    dict will be the path to the "split_links" layer. When using this option,
    arcpy should be set to return raster resolutions in units of meters.
    ----------
    Inputs:
        total_area (str): The path to an arcpy raster layer holding the total
            upslope area of each pixel in the extent box, as computed using a
            D8 flow model.
        min_basin_area (float): The minimum upslope area required to qualify
            as a drainage stream. Units are meters^2
        burned_area (str): The path to an arcpy raster layer holding the total
            burned upslope area of each pixel in the extent box, as computed
            using a D8 flow model. The raster grid and projection should match
            that of the total_area raster.
        min_burned_area (float): The minimum burned upslope area required to
            qualify as a drainage stream. Units are meters^2.
        flow_direction (str): The path to an arcpy raster layer holding the flow
            direction of each pixel in the extent box, as computed using a D8
            flow model. Flow direction integers should follow the arcpy
            convention. The raster grid and projection should match that of the
            total_area raster.
        stream_links (str): The path to the arcpy feature layer that should
            hold the initial (unsplit) stream link polylines.
        stream_raster (str): The path to the arcpy feature layer that should
            hold the stream link raster.
        max_segment_length (float): The maximum allowed stream link length
            (units are meters). If specified, the split_points and split_streams
            inputs must also be set.
        split_points (str): The path to the arcpy feature layer holding the
            output points used to split the stream segments. Must be set when
            providing a max_segment_length.
        split_links (str): The path to the arcpy feature layer holding the split
            stream link polylines. Must be set when providing a max_segment_length.

    Outputs:
        A dict mapping str keys to the paths of the final feature and raster layers
        for the stream network.

        feature (str): The absolute path to the final arcpy feature layer
            representing the stream links as a set of polylines.
        raster (str): The absolute path to the final arcpy layer representing
            the stream links as a raster. The value of stream link pixels will
            match the OBJECTID of the associated polyline in the feature layer.
            All other pixels are set as NoData.
    """

    # Note if splitting and get final feature layer. Check for splitting paths
    # if required
    if max_segment_length is None:
        splitting = False
        final_features = stream_links
    else:
        splitting = True
        final_features = split_links
        check_split_paths(split_points, split_links)

    # Create dict of final stream paths
    output = {
        "feature": path.abspath(final_features),
        "raster": path.abspath(stream_raster),
    }

    # Get stream link polylines. Optionally split by length
    links(
        total_area,
        min_basin_area,
        burned_area,
        min_burned_area,
        flow_direction,
        stream_links,
    )
    if splitting:
        radius = search_radius(total_area)
        split(stream_links, max_segment_length, radius, split_points, split_links)

    # Convert final links to raster and return dict of output layer paths
    raster(output["feature"], stream_raster)
    return output


def links(
    total_area: str,
    min_basin_area: float,
    burned_area: str,
    min_burned_area: float,
    flow_direction: str,
    links: str,
) -> None:
    """
    links  Creates a feature layer holding links of the stream network
    ----------
    links(total_area, min_basin_area, burned_area, min_burned_area, flow_direction, links)
    Uses upslope area, upslope burned area, and flow direction rasters to
    delineate the links of a stream network. Saves the stream links as a feature
    layer of polylines. (Each link is a separate polyline).

    Drainage streams are defined as raster pixels that exceed both (1) a minimum
    upslope area threshold, and (2) a minimum burned upslope area threshold.
    These drainage streams are then classified into individual stream links
    using a flow direction raster.
    ----------
    Inputs:
        total_area (str): The path to an arcpy raster layer holding the total
            upslope area of each pixel in the extent box, as computed using a
            D8 flow model.
        min_basin_area (float): The minimum upslope area required to qualify
            as a drainage stream. Units are meters^2
        burned_area (str): The path to an arcpy raster layer holding the total
            burned upslope area of each pixel in the extent box, as computed
            using a D8 flow model. The raster grid and projection should match
            that of the total_area raster.
        min_burned_area (float): The minimum burned upslope area required to
            qualify as a drainage stream. Units are meters^2.
        flow_direction (str): The path to an arcpy raster layer holding the flow
            direction of each pixel in the extent box, as computed using a D8
            flow model. Flow direction integers should follow the arcpy
            convention. The raster grid and projection should match that of the
            total_area raster.
        links (str): The path to the arcpy feature layer that should hold the
            computed stream link polylines.

    Saves:
        An arcpy feature layer holding the stream link polylines. The name of
        the layer will match the "links" input.

    Outputs: None
    """

    # Locate drainage streams
    total_area = arcpy.Raster(total_area)
    burned_area = arcpy.Raster(burned_area)
    streams = (total_area >= min_basin_area) & (burned_area >= min_burned_area)
    streams = arcpy.sa.Con(streams, 1)

    # Convert streams to polyline features
    arcpy.sa.StreamToFeature(streams, flow_direction, links, "NO_SIMPLIFY")


def split(
    links: str,
    max_segment_length: float,
    search_radius: float,
    split_points: str,
    split_links: str,
) -> None:
    """
    split  Splits stream links longer than a maximum length
    ----------
    split(links, max_segment_length, search_radius, split_points, split_streams)
    Splits stream links longer than a maximum allowed length into segments that
    do not exceed this length. Stream links less than the maximum length are not
    affected. Note that a single stream link may be split into multiple
    segments, depending on its length.

    This method proceeds by determining a set of splitting points for the
    stream links. The split points for each stream link are the points along the
    link whose distance from the start of the link is a multiple of the maximum
    allowed length. The links are then split into segments at these points.
    ----------
    Inputs:
        links (str): The path to the arcpy feature layer holding the initial
            stream link polylines.
        max_segment_length (float): The maximum allowed length (in meters)
        search_radius (float): The search radius used to enable multiple
            splitting for the stream links (in meters). Must be greater than 0.
            We recommend using a value smaller than the minimum resolution of
            the raster used to derive the stream links, as this reduces the
            likelihood of incorrectly applying a split point to multiple links.
        split_points (str): The path to the output arcpy feature layer holding
            the points used to split the stream links.
        split_links (str): The path to the output arcpy feature layer holding
            the split stream link polylines.

    Saves:
        Arcpy feature layers whose names match the "split_points" and
        "split_links" inputs.

    Outputs: None
    """

    max_length = f"{max_segment_length} meters"
    arcpy.management.GeneratePointsAlongLines(
        links, split_points, "DISTANCE", max_length
    )
    arcpy.management.SplitLineAtPoint(links, split_points, split_links, search_radius)


def raster(link_features: str, raster: str) -> None:
    """
    raster  Converts a stream link feature layer to raster
    ----------
    raster(link_features, raster)
    Converts a feature layer of stream links to a raster. The feature layer
    should consist of a set of polylines, each denoting a link in the stream
    network. The value of stream link pixels in the output raster will match the
    OBJECTID of the links in the feature layer. All other pixels are set
    to NoData.
    ----------
    Inputs:
        link_features (str): The path to the arcpy feature layer holding the
            stream link polylines.
        raster (str): The path to the arcpy layer that should hold the output
            stream link raster.

    Saves:
        Saves an arcpy raster layer matching the name of the "raster" input.

    Outputs: None
    """

    arcpy.conversion.PolylineToRaster(link_features, "OBJECTID", raster)


def search_radius(raster: str, divisor=5) -> float:
    """
    search_radius  Returns a search radius for splitting stream links
    ----------
    search_radius(raster)
    Returns a recommended search radius to use when splitting stream link
    polylines derived from the input raster. The returned radius will be the
    minimum XY resolution of the input raster, divided by 5. The use of 5 as
    a divisor is somewhat arbitrary, as any value >= 1 is probably fine. Here
    we use 5 as a default to conform with the original codebase, which used a
    2 meter search radius for stream links derived from a 10 meter DEM.

    search_radius(raster, divisor)
    Also specifies the divisor to apply to the minimum XY resolution.
    ----------
    Inputs:
        raster (str): The path to an arcpy raster layer used to derive the links
            in a stream network.
        divisor (float): The divisor to apply to the minimum XY resolution of
            the input raster. Should be a value >= 1.

    Outputs:
        float: A recommended search radius to use for splitting stream links
            derived from the input raster.
    """

    # Get the minimum raster resolution
    height = raster_size(raster, "CELLSIZEX")
    width = raster_size(raster, "CELLSIZEY")
    resolution = min(height, width)

    # Return scaled resolution
    return resolution / divisor


def raster_size(raster: str, field: Literal["CELLSIZEX", "CELLSIZEY"]) -> float:
    """
    raster_size  Returns a raster resolution as a float
    ----------
    raster_size(raster, field)
    Returns the X or Y resolution of an arcpy raster layer as a float.
    ----------
    Inputs:
        raster (str): The path to the arcpy raster layer being queried
        field ("CELLSIZEX" | "CELLSIZEY"): The resolution field to query

    Outputs:
        float: The queried resolution
    """

    resolution = arcpy.management.GetRasterProperties(raster, field)
    resolution = resolution.getOutput(0)
    return float(resolution)


def check_split_paths(split_points: Any, split_links: Any) -> None:
    """
    check_split_paths  Informative error checking for optional splitting inputs
    ----------
    check_split_paths(split_points, split_links)
    Raises an informative error if either split_points or split_links is None.
    ----------
    Inputs:
        split_points (Any): The split_points input
        split_links (Any): The split_links input

    Outputs: None

    Raises:
        ValueError if either split_points or split_links is None.
    """

    # Check for missing inputs
    if split_points is None:
        missing = "split_points"
    elif split_links is None:
        missing = "split_links"
    else:
        missing = None

    # Informative error if missing inputs
    if missing is not None:
        message = f"You must provide the {missing} input when enforcing a maximum stream segment length."
        MissingPathError = ValueError(message)
        raise MissingPathError
