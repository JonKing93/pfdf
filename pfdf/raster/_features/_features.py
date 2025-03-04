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

from pfdf.errors import NoFeaturesError, NoOverlappingFeaturesError
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
    geotype = geotype.capitalize()
    geometries = [geotype, f"Multi{geotype}"]

    # If there's no window, track the bounds of the file's features. Otherwise, convert
    # the load window to a shapely box
    if window is None:
        bounds = _bounds.unbounded(crs)
    else:
        window = window.match_crs(crs)
        bounds = window.todict()
        window = window.orient().tolist(crs=False)
        window = shapely.geometry.box(*window)

    # Get the value for each feature. Validate geometry and convert to multicoordinate
    geometry_values = []
    for f, feature in enumerate(ffile.file):
        value = _parse_value(f, feature, field, dtype, casting, operation)
        geometry = feature["geometry"]
        multicoordinates = _validate.geometry(f, geometry, geometries)

        # Validate geometry coordinates. Track bounds if there's no window. Otherwise,
        # skip any geometries that don't intersect the window
        for c, coordinates in enumerate(multicoordinates):
            shape = validate_coordinates(f, c, coordinates)
            if window is None:
                _bounds.add_geometry(geotype, coordinates, bounds)
            elif not window.intersects(shape):
                continue

            # Record the geometry-value tuple
            geometry = {"type": geotype, "coordinates": coordinates}
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
            raise NoOverlappingFeaturesError(
                f"None of the {geometry} features intersect the input bounds.\n"
                f"File: {path}"
            )
