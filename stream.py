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

Advanced users may also be interested in the lower level "links", "split",
"raster", and "search_radius" functions, which can be used to implement custom
stream network delineation routines.

This module requires upslope area, upslope burned area, and flow direction
rasters computed from a DEM. Users may wish to see the "taudem" module for
functions that compute these raster. The following is a suggested workflow 
outline for hazard assessment users:
    * Acquire DEM Data
    * Use dem module to compute upslope areas and flow directions
    *** Use this module to delineate a stream network
    * Screen the stream network to a final set of drainage basins

REQUIREMENTS:
Running this module requires:
    * The ArcPy package and base Python environment shipped with ArcGIS Pro 3.0
      (Build Number 36056)
----------
User functions:
    network             - Delineates a stream network

Advanced user functions:
    links               - Creates a feature layer holding links of a stream network
    split               - Split stream links longer than a maximum length
    search_radius       - Return a recommended search radius for splitting stream links
    raster              - Converts stream link polylines into a raster

Utilities:
    _raster_size         - Returns the resolution of a raster as a float
    _check_split_paths   - Error checking for optional splitting inputs
"""

from typing import Dict, Optional, Literal, Any
import arcpy
from pathlib import Path


def links(
    total_area_path: str,
    min_basin_area: float,
    burned_area_path: str,
    min_burned_area: float,
    flow_direction_path: str,
    links_path: str,
) -> None:
    """
    links  Creates a feature layer holding links of the stream network
    ----------
    links(total_area_path, min_basin_area, burned_area_path, min_burned_area,
          flow_direction_path, links_path)
    Uses upslope area, upslope burned area, and flow direction rasters to
    delineate the links of a stream network. Saves the stream links as a feature
    layer of polylines. (Each link is a separate polyline).

    Drainage streams are defined as raster pixels that exceed both (1) a minimum
    upslope area threshold, and (2) a minimum burned upslope area threshold.
    These drainage streams are then classified into individual stream links
    using a flow direction raster.
    ----------
    Inputs:
        total_area_path (str): The path to an arcpy raster layer holding the total
            upslope area of each pixel in the extent box, as computed using a
            D8 flow model.
        min_basin_area (float): The minimum upslope area required to qualify
            as a drainage stream. Units are meters^2
        burned_area_path (str): The path to an arcpy raster layer holding the total
            burned upslope area of each pixel in the extent box, as computed
            using a D8 flow model. The raster grid and projection should match
            that of the total_area raster.
        min_burned_area (float): The minimum burned upslope area required to
            qualify as a drainage stream. Units are meters^2.
        flow_direction_path (str): The path to an arcpy raster layer holding the flow
            direction of each pixel in the extent box, as computed using a D8
            flow model. Flow direction integers should follow the arcpy
            convention. The raster grid and projection should match that of the
            total_area raster.
        links_path (str): The path to the arcpy feature layer that should hold the
            computed stream link polylines.

    Saves:
        An arcpy feature layer holding the stream link polylines. The name of
        the layer will match the "links_path" input.

    Outputs: None
    """

    # Locate drainage streams
    total_area = arcpy.Raster(total_area_path)
    burned_area = arcpy.Raster(burned_area_path)
    streams = (total_area >= min_basin_area) & (burned_area >= min_burned_area)
    streams = arcpy.sa.Con(streams, 1)

    # Convert streams to polyline features
    arcpy.sa.StreamToFeature(streams, flow_direction_path, links_path, "NO_SIMPLIFY")


def network(
    total_area_path: str,
    min_basin_area: float,
    burned_area_path: str,
    min_burned_area: float,
    flow_direction_path: str,
    stream_links_path: str,
    stream_raster_path: str,
    max_segment_length: Optional[float] = None,
    split_points_path: Optional[str] = None,
    split_links_path: Optional[str] = None,
) -> Dict[Path, Path]:
    """
    network  Delineates the stream network
    ----------
    network(total_area_path, min_basin_area, burned_area_path, min_burned_area,
            flow_direction_path, stream_links_path, stream_raster_path)
    Uses input rasters to delineate the links of the stream network. Saves the
    network as both a raster and feature layer. Returns a dict with the absolute
    paths to the final feature and raster layers. (In this case, the
    stream_raster_path and stream_links_path).

    Drainage streams are defined as raster pixels that exceed both (1) a minimum
    upslope area threshold, and (2) a minimum burned upslope area threshold.
    These drainage streams are then classified into individual stream links. The
    output feature layer represents these stream links as a set of polylines. In
    the output raster layer, the values of stream link pixels are set as the
    OBJECTID of the coresponding polyline.

    network(..., max_segment_length, split_points_path, split_links_path)
    Also restricts the stream links to a maximum length. Stream links exceeding
    this length will be split into multiple segments that respect the maximum
    allowed length. In this case, the value of the "feature" key in the output
    dict will be the split_links_path. When using this option, arcpy should be
    set to return raster resolutions in units of meters.
    ----------
    Inputs:
        total_area_path (str): The path to an arcpy raster layer holding the total
            upslope area of each pixel in the extent box, as computed using a
            D8 flow model.
        min_basin_area (float): The minimum upslope area required to qualify
            as a drainage stream. Units are meters^2
        burned_area_path (str): The path to an arcpy raster layer holding the total
            burned upslope area of each pixel in the extent box, as computed
            using a D8 flow model. The raster grid and projection should match
            that of the total_area raster.
        min_burned_area (float): The minimum burned upslope area required to
            qualify as a drainage stream. Units are meters^2.
        flow_direction_path (str): The path to an arcpy raster layer holding the flow
            direction of each pixel in the extent box, as computed using a D8
            flow model. Flow direction integers should follow the arcpy
            convention. The raster grid and projection should match that of the
            total_area raster.
        stream_links_path (str): The path to the arcpy feature layer that should
            hold the initial (unsplit) stream link polylines.
        stream_raster_path (str): The path to the arcpy feature layer that should
            hold the stream link raster.
        max_segment_length (float): The maximum allowed stream link length
            (units are meters). If specified, the split_points and split_streams
            inputs must also be set.
        split_points_path (str): The path to the arcpy feature layer holding the
            output points used to split the stream segments. Must be set when
            providing a max_segment_length.
        split_links_path (str): The path to the arcpy feature layer holding the split
            stream link polylines. Must be set when providing a max_segment_length.

    Outputs:
        A dict mapping str keys to the paths of the final feature and raster layers
        for the stream network.

        feature (pathlib.Path): The absolute path to the final arcpy feature layer
            representing the stream links as a set of polylines.
        raster (pathlib.Path): The absolute path to the final arcpy layer representing
            the stream links as a raster. The value of stream link pixels will
            match the OBJECTID of the associated polyline in the feature layer.
            All other pixels are set as NoData.
    """

    # Note if splitting and get final feature layer. Check for splitting paths
    # if required
    if max_segment_length is None:
        splitting = False
        final_features = stream_links_path
    else:
        splitting = True
        _check_split_paths(split_points_path, split_links_path)
        final_features = split_links_path

    # Create dict of final stream paths
    output = {
        "feature": Path(final_features).absolute(),
        "raster": Path(stream_raster_path).absolute(),
    }

    # Get stream link polylines. Optionally split by length
    links(
        total_area_path,
        min_basin_area,
        burned_area_path,
        min_burned_area,
        flow_direction_path,
        stream_links_path,
    )
    if splitting:
        radius = search_radius(total_area_path)
        split(
            stream_links_path,
            max_segment_length,
            radius,
            split_points_path,
            split_links_path,
        )

    # Convert final links to raster and return dict of output layer paths
    raster(output["feature"], stream_raster_path)
    return output


def raster(link_features_path: str, raster_path: str) -> None:
    """
    raster  Converts a stream link feature layer to raster
    ----------
    raster(link_features_path, raster_path)
    Converts a feature layer of stream links to a raster. The feature layer
    should consist of a set of polylines, each denoting a link in the stream
    network. The value of stream link pixels in the output raster will match the
    OBJECTID of the links in the feature layer. All other pixels are set
    to NoData.
    ----------
    Inputs:
        link_features_path (str): The path to the arcpy feature layer holding the
            stream link polylines.
        raster_path (str): The path to the arcpy layer that should hold the output
            stream link raster.

    Saves:
        Saves an arcpy raster layer matching the raster_path input.

    Outputs: None
    """

    arcpy.conversion.PolylineToRaster(link_features_path, "OBJECTID", raster_path)


def search_radius(raster_path: str, divisor=5) -> float:
    """
    search_radius  Returns a search radius for splitting stream links
    ----------
    search_radius(raster_path)
    Returns a recommended search radius to use when splitting stream link
    polylines derived from the input raster. The returned radius will be the
    minimum XY resolution of the input raster, divided by 5. The use of 5 as
    a divisor is somewhat arbitrary, as any value >= 1 is probably fine. Here
    we use 5 as a default to conform with the original codebase, which used a
    2 meter search radius for stream links derived from a 10 meter DEM.

    search_radius(raster_path, divisor)
    Also specifies the divisor to apply to the minimum XY resolution.
    ----------
    Inputs:
        raster_path (str): The path to an arcpy raster layer used to derive the links
            in a stream network.
        divisor (float): The divisor to apply to the minimum XY resolution of
            the input raster. Should be a value >= 1.

    Outputs:
        float: A recommended search radius to use for splitting stream links
            derived from the input raster.
    """

    # Get the minimum raster resolution
    height = _raster_size(raster_path, "CELLSIZEX")
    width = _raster_size(raster_path, "CELLSIZEY")
    resolution = min(height, width)

    # Return scaled resolution
    return resolution / divisor


def split(
    links_path: str,
    max_segment_length: float,
    search_radius: float,
    split_points_path: str,
    split_links_path: str,
) -> None:
    """
    split  Splits stream links longer than a maximum length
    ----------
    split(links_path, max_segment_length, search_radius, split_points_path, split_streams_path)
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
        links_path (str): The path to the arcpy feature layer holding the initial
            stream link polylines.
        max_segment_length (float): The maximum allowed length (in meters)
        search_radius (float): The search radius used to enable multiple
            splitting for the stream links (in meters). Must be greater than 0.
            We recommend using a value smaller than the minimum resolution of
            the raster used to derive the stream links, as this reduces the
            likelihood of incorrectly applying a split point to multiple links.
        split_points_path (str): The path to the output arcpy feature layer holding
            the points used to split the stream links.
        split_links_path (str): The path to the output arcpy feature layer holding
            the split stream link polylines.

    Saves:
        Arcpy feature layers whose names match the split_points_path and
        split_links_path inputs.

    Outputs: None
    """

    max_length = f"{max_segment_length} meters"
    arcpy.management.GeneratePointsAlongLines(
        links_path, split_points_path, "DISTANCE", max_length
    )
    arcpy.management.SplitLineAtPoint(
        links_path, split_points_path, split_links_path, search_radius
    )


def _check_split_paths(split_points_path: Any, split_links_path: Any) -> None:
    """
    _check_split_paths  Informative error checking for optional splitting inputs
    ----------
    _check_split_paths(split_points_path, split_links_path)
    Raises an informative error if either split_points_path or split_links_path
    is None.
    ----------
    Inputs:
        split_points_path (Any): The split_points_path input
        split_links_path (Any): The split_links_path input

    Outputs: None

    Raises:
        ValueError if either split_points_path or split_links_path is None.
    """

    # Check for missing inputs
    if split_points_path is None:
        missing = "split_points_path"
    elif split_links_path is None:
        missing = "split_links_path"
    else:
        missing = None

    # Informative error if missing inputs
    if missing is not None:
        message = f"You must provide the {missing} input when enforcing a maximum stream segment length."
        MissingPathError = ValueError(message)
        raise MissingPathError


def _raster_size(raster_path: str, field: Literal["CELLSIZEX", "CELLSIZEY"]) -> float:
    """
    _raster_size  Returns a raster resolution as a float
    ----------
    _raster_size(raster_path, field)
    Returns the X or Y resolution of an arcpy raster layer as a float.
    ----------
    Inputs:
        raster_path (str): The path to the arcpy raster layer being queried
        field ("CELLSIZEX" | "CELLSIZEY"): The resolution field to query

    Outputs:
        float: The queried resolution
    """

    resolution = arcpy.management.GetRasterProperties(raster_path, field)
    resolution = resolution.getOutput(0)
    return float(resolution)
