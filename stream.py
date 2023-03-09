"""
stream  Functions that delineate the stream network.
----------
This module delineates an initial hazard assessment stream network. This network
consists of drainages that are both (1) large enough for debris-flows to occur,
and (2) below a sufficient amount of burned area. This network is only an
initial estimate of potentially hazardous drainages. Hazard assessment users
may want to apply additional screenings to filter this initial network to a
final network of drainage basins.

This module requires flow directions and upslope areas computed using a D8 flow
model. A potential workflow for hazard assessment users is as follows:

    * Acquire DEM data
    * Calculate flow directions and upslope areas
    *** Run this module
    * Screen the initial network
    * Apply a hazard assessment model to the final network
----------
Key functions:
    network     - Delineates the stream network

Utilities:
    raster_size - Returns the resolution of a raster as a float
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
    network  Delineates the stream network
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
        A dict mapping str keys to the paths of the final feature and raster layers
        for the stream network.

        feature (str): The absolute path to the final arcpy feature layer
            representing the stream links as a set of polylines.
        raster (str): The absolute path to the final arcpy raster layer
            representing the stream links as a raster. The value of stream link
            pixels match the OBJECTID of the associated polyline in the feature
            layer. All other pixels are set as NoData.
    """

    # Note if splitting segments and the corresponding the final feature layer
    if max_segment_length is None:
        splitting = False
        final_features = stream_features
    else:
        splitting = True
        final_features = split_streams

        # If splitting, check for additional required arcpy paths
        if split_points is None:
            missing = "split_points"
        elif split_streams is None:
            missing = "split_streams"
        else:
            missing = None

        # Informative error if missing paths
        if missing is not None:
            MissingPathError = TypeError(
                f"You must provide the '{missing}' input when enforcing a "
                 "maximum stream segment length.")
            raise MissingPathError
        
    # Create output dict of stream paths
    output = {'feature': path.abspath(final_features),
              'raster': path.abspath(stream_raster)}

    # Locate drainage streams
    total_area = arcpy.Raster(total_area)
    burned_area = arcpy.Raster(burned_area)
    streams = (total_area >= min_basin_area) & (burned_area >= min_burned_area)
    streams = arcpy.sa.Con(streams, 1)

    # Convert streams to polyline features
    arcpy.sa.StreamToFeature(streams, flow_direction, stream_features, "NO_SIMPLIFY")

    # If splitting long segments, get a search radius smaller than the raster
    # resolution. (Enables multiple splitting without searching too far)
    if splitting:
        width = raster_size(total_area, "CELLSIZEX")
        height = raster_size(total_area, "CELLSIZEY")
        min_resolution = min(height, width)
        radius = min_resolution / 5  # 5 is arbitrary, anything > 1 should be fine

        # Split the long segments
        max_length = f"{max_segment_length} meters"
        arcpy.management.GeneratePointsAlongLines(stream_features, split_points, "DISTANCE", max_length)
        arcpy.management.SplitLineAtPoint(stream_features, split_points, split_streams, radius)

    # Create stream link raster and return output paths
    arcpy.conversion.PolylineToRaster(output['feature'], "OBJECTID", stream_raster)
    return output

def raster_size(raster, field):
    """
    raster_size  Returns a raster resolution as a float
    ----------
    raster_size(raster, field)
    Returns the X or Y resolution of a raster layer as a float.
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
