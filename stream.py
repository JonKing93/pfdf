"""
stream  Functions that delineate the stream network.
"""

from typing import Dict, Optional
import arcpy
from os import path

def network(total_area: str,     min_basin_area: float,
            burned_area: str,    min_burned_area: float,
            flow_direction: str,
            stream_features: str, stream_raster: str,
            max_segment_length: Optional[float] = None,
            split_points: Optional[str] = None,
            split_streams: Optional[str] = None) -> Dict[str, str]:
    """
    stream.network  Delineates the stream network
    ----------
    network(total_area, min_basin_area, burned_area, min_burned_area,
            flow_direction, stream_features, stream_raster)
    Uses input rasters to delineate the stream network. Saves the stream network
    as both a raster layer and feature layer. Returns a dict with the absolute
    paths to the final feature and raster layer (in this case, the
    stream_features and stream_raster layers).

    Drainage streams are defined as raster pixels that exceed both (1) a minimum
    upslope area threshold, and (2) a minimum burned upslope area threshold.
    These drainage streams are then classified into individual stream links. The
    output feature layer represents these stream links as a set of polylines. In
    the output raster layer, the values of stream link pixels are set as the
    OBJECTID of the coresponding polyline.

    network(..., max_segment_length, split_points, split_streams)
    Also restricts the stream links to a maximum length. Stream links exceeding
    this length will be split into multiple links. In this case, the value of
    the "feature" key in the output dict be the split_streams layer.
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
        stream_features (str): The path to the arcpy feature layer that should
            hold the (unsplit) stream link polylines.
        stream_raster (str): The path to the arcpy feature layer that should
            hold the stream link raster.
        max_segment_length (float): The maximum allowed stream link length
            (units are meters). If specified, the split_points and split_streams
            inputs must also be set.
        split_points (str): The absolute path to the arcpy feature layer holding
            the output points used to split the stream segments. Must be set
            when providing a max_segment_length.
        split_streams (str): The absolute path to the arcpy feature layer holding
            the split stream link polylines. Must be set when providing a max_segment_length.

    Outputs:
        A dict mapping keys to the final feature and raster layers of the stream
        network. (All keys are strings)

        feature (str): The absolute path to the final arcpy feature layer
            representing the stream links as a set of polylines.
        raster (str): The absolute path to the final arcpy raster layer
            representing the stream links as a raster. The value of stream link
            pixels match the OBJECTID of the associated polyline in the feature
            layer. All other pixels are set as NoData.
    """

    # Note if splitting segments over the maximum length
    if max_segment_length is None:
        splitting = False
    else:
        splitting = True

        # If splitting, check for additional arcpy paths
        if split_points is None:
            missing = "split_points"
        elif split_streams is None:
            missing = "split_streams"
        else:
            missing = None

        # Informative error if missing paths
        if missing is not None:
            MissingPathError = TypeError(f"You must provide the '{missing}' input when enforcing a maximum stream segment length.")
            raise MissingPathError

    # Get absolute paths
    output_feature = path.abspath(stream_features)
    output_raster = path.abspath(stream_raster)
    if splitting:
        split_points = path.abspath(split_points)
        split_streams = path.abspath(split_streams)

    # Initialize output dict of stream layer paths
    output = {'feature': stream_features, 'raster': stream_raster}

    # Locate drainage streams
    total_area = arcpy.Raster(total_area)
    burned_area = arcpy.Raster(burned_area)
    streams = (total_area >= min_basin_area) & (burned_area >= min_burned_area)
    streams = arcpy.sa.Con(streams, 1)

    # Convert streams to polyline features
    arcpy.sa.StreamToFeature(streams, flow_direction, stream_features, "NO_SIMPLIFY")

    # Optionally split long segments
    # TODO: Research effects of search_radius before code review.
    if splitting:
        arcpy.management.GeneratePointsAlongLines(stream_features, split_points, "DISTANCE", max_segment_length)
        arcpy.management.SplitLineAtPoint(stream_features, split_points, split_streams, search_radius="2")
        output['feature'] = split_streams

    # Create stream link raster and return output paths
    arcpy.conversion.PolylineToRaster(output['feature'], "OBJECTID", stream_raster)
    return output
