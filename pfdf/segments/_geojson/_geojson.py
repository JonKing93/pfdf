"""
Functions that build GeoJSON features for segments, outlets, and basins
----------
Functions:
    features        - Main function to export a FeatureCollection
    _basins         - Builds features for basin polygons
    _from_shapely   - Builds segment or outlet features derived from shapely linestrings
    _values         - Builds the property value dict for a feature
"""

from typing import Any, Callable

import numpy as np
import rasterio.features
from geojson import Feature, FeatureCollection, LineString, Point

import pfdf.segments._validate as validate
from pfdf.projection import CRS, _crs
from pfdf.segments._geojson import _reproject
from pfdf.typing.segments import ExportType, PropertySchema, SegmentValues

PropertyConvert = dict[str, tuple[SegmentValues, Callable]]


def _values(properties: PropertyConvert, index: int) -> dict:
    "Builds the property value dict for a feature"
    values = {}
    for field, (vector, as_builtin) in properties.items():
        value = vector[index]
        values[field] = as_builtin(value)
    return values


def _basins(segments, properties: PropertyConvert, crs: CRS) -> list[Feature]:
    "Returns features for basin polygons"

    # Build (geometry, ID) tuples. Reproject as needed
    basins = segments._locate_basins()
    mask = basins.astype(bool)
    basins = rasterio.features.shapes(
        basins, mask, connectivity=8, transform=segments.transform.affine
    )
    basins = list(basins)
    _reproject.geometries(basins, "basins", segments.crs, crs)

    # Convert basins to geojson Features. Track basin IDs when determining property
    # values as basins are unordered
    ids = segments.terminal_ids
    for b, (geometry, id) in enumerate(basins):
        index = np.argwhere(id == ids)
        index = int(index[0, 0])
        values = _values(properties, index)
        basins[b] = Feature(geometry=geometry, properties=values)
    return basins


def _from_shapely(
    segments, type: ExportType, properties: PropertyConvert, crs: CRS
) -> list[Feature]:
    "Returns segments or outlets derived from the shapely linestrings"

    # Get the linestring geometries. Limit to terminal segments as needed.
    features = [list(linestring.coords) for linestring in segments._segments]
    if type == "outlets":
        features = [
            feature for keep, feature in zip(segments.isterminal(), features) if keep
        ]

    # Extract final point for outlets. Get GeoJSON geometry type and reproject
    if "outlets" in type:
        features = [coords[-1] for coords in features]
        to_geojson = Point
    else:
        to_geojson = LineString
    _reproject.geometries(features, type, segments.crs, crs)

    # Get values and build each feature
    for g, geometry in enumerate(features):
        values = _values(properties, g)
        geometry = to_geojson(geometry)
        features[g] = Feature(geometry=geometry, properties=values)
    return features


def features(
    segments, type: Any, properties: Any, crs: Any
) -> tuple[FeatureCollection, PropertySchema, CRS]:
    "Returns a GeoJSON feature collection for export"

    # Validate. Get final CRS
    type, properties, schema = validate.export(segments, properties, type)
    if crs is None:
        crs = segments.crs
    else:
        crs = _crs.validate(crs)

    # Add built-in converters to properties
    builtins = {"float": float, "int": int, "str": str}
    for field, value in properties.items():
        dtype = schema[field].split(":")[0]
        properties[field] = (value, builtins[dtype])

    # Get Features and group in a FeatureCollection
    if type == "basins":
        features = _basins(segments, properties, crs)
    else:
        features = _from_shapely(segments, type, properties, crs)
    return FeatureCollection(features), schema, crs
