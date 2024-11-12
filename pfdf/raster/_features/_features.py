"""
Functions used to read and validate feature geometries and values
----------
Functions:
    parse               - Validates and parses features geometries and values
    _parse_value        - Determines the value for a feature
    _require_features   - Raises an error if there are no features
"""

from __future__ import annotations

import typing

import shapely.geometry

from pfdf.errors import NoFeaturesError
from pfdf.projection import BoundingBox
from pfdf.raster._features import _bounds, _validate

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import Callable

    from numpy import dtype

    from pfdf.projection import CRS
    from pfdf.raster._features._ffile import FeatureFile
    from pfdf.typing.core import GeometryValues, value


def parse(
    # General
    geotype: str,
    ffile: FeatureFile,
    field: str | None,
    # Field options
    dtype: dtype,
    casting: str,
    operation: Callable | None,
    # Spatial
    crs: CRS | None,
    window: BoundingBox | None,
) -> tuple[GeometryValues, BoundingBox]:
    """
    Checks that input features have valid geometries. Returns features as
    (geometry, value) tuples. Also returns the spatial bounds of the final data array.
    """

    # Get the allowed geometries and coordinate array validator
    validate_coordinates = getattr(_validate, geotype)
    geometries = geotype.capitalize()
    geometries = [geometries, f"Multi{geometries}"]

    # If there's no window, track the bounds of the file's features
    if window is None:
        track_bounds = True
        bounds = _bounds.unbounded(crs)

    # Otherwise, build a shapely box from the load window
    else:
        track_bounds = False
        window = window.match_crs(crs)
        bounds = window.todict()
        window = window.orient().tolist(crs=False)
        window = shapely.geometry.box(*window)

    # Validate each feature's geometry and get the coordinate array
    geometry_values = []
    for f, feature in enumerate(list(ffile.file)):
        geometry = feature["geometry"]
        multicoordinates = _validate.geometry(f, geometry, geometries)

        # Record feature bounds, and track whether to keep. By default, keep
        # everything. But if a window is provided, only keep intersecting features
        fbounds = _bounds.unbounded()
        keep = window is None

        # Validate geometry coordinates. Check if the feature should be kept and
        # record the bounds
        for c, coordinates in enumerate(multicoordinates):
            shape = validate_coordinates(f, c, coordinates)
            if (not keep) and window.intersects(shape):
                keep = True
            _bounds.add_geometry(geotype, coordinates, fbounds)

        # Skip the feature if not being kept. Update final bounds if tracking
        if not keep:
            continue
        if track_bounds:
            _bounds.update(bounds, **fbounds)

        # Associate each geometry with a value, and record the geometry-value tuple
        value = _parse_value(f, feature, field, dtype, casting, operation)
        geometry_values.append((geometry, value))

    # Require at least one feature. Return geometry-value tuples and feature array bounds
    _require_features(geotype, geometry_values, window, ffile.path)
    return geometry_values, BoundingBox.from_dict(bounds)


def _parse_value(
    f: int,
    feature: dict,
    field: str | None,
    dtype: dtype,
    casting: str,
    operation: Callable | None,
) -> value:
    "Determines the feature value"

    # Just use True if there isn't a field
    if field is None:
        return True

    # Extract the value and apply any operations
    value = feature["properties"][field]
    if operation is not None:
        try:
            value = operation(value)
        except Exception as error:
            raise RuntimeError('The "operation" function caused an error.') from error

    # Check the value is a numeric scalar that can be casted to the raster dtype
    name = f"the value for feature {f}"
    if operation is not None:
        name = name + ' output by "operation"'
    value = _validate.value(value, name, dtype, casting)
    return value


def _require_features(
    geometry: str, features: list | None, window: BoundingBox | None, path: Path
) -> None:
    "Provides informative errors if there are no features"

    if len(features) == 0:
        if window is None:
            raise NoFeaturesError(
                f"The {geometry} feature file is empty and does not have any "
                f"{geometry} features.\nFile: {path}"
            )
        else:
            raise NoFeaturesError(
                f"None of the {geometry} features intersect the input bounds.\n"
                f"File: {path}"
            )
