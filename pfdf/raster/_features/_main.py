"""
Utilities to process vector features into rasters
----------
Functions:
    parse_file  - Validates feature file and computes values for raster creation
    _parse_file - Determines values from an opened feature file using validated options
"""

from __future__ import annotations

import typing

from pfdf import raster
from pfdf.projection import crs as _crs
from pfdf.raster._features import _features, _parse, _validate
from pfdf.raster._features._ffile import FeatureFile

if typing.TYPE_CHECKING:
    from typing import Any, Callable

    from numpy import dtype

    from pfdf.projection import CRS, BoundingBox
    from pfdf.raster import RasterMetadata
    from pfdf.raster._features.typing import Resolution, nodata
    from pfdf.typing.core import GeometryValues, scalar


def parse_file(
    # General
    geometry: str,
    path: Any,
    field: Any,
    # Field options
    dtype: Any,
    field_casting: Any,
    nodata: Any,
    casting: Any,
    operation: Any,
    # Spatial
    window: Any,
    resolution: Any,
    units: Any,
    # File IO
    layer: Any,
    driver: Any,
    encoding: Any,
) -> tuple[GeometryValues, RasterMetadata]:
    "Validates feature file and computes values for raster creation"

    # Validate
    if field is not None:
        dtype, field_casting, nodata = _validate.field_options(
            field, dtype, field_casting, nodata, casting, operation
        )
    window, resolution, units = _validate.spatial(window, resolution, units)
    path, layer, driver, encoding = _validate.file_io(path, layer, driver, encoding)

    # Open file. Parse feature values and geometries
    with FeatureFile(path, layer, driver, encoding) as ffile:
        features, crs, bounds, dtype, nodata = _parse_file(
            # General
            geometry,
            ffile,
            field,
            # Field options
            dtype,
            field_casting,
            nodata,
            casting,
            operation,
            # Spatial
            window,
            resolution,
            units,
        )

    # Convert resolution to axis unit. Compute shape and transform
    resolution, crs = _parse.resolution(resolution, units, crs, bounds)
    transform, shape = _parse.extent(bounds, resolution)

    # Build metadata for the output array
    metadata = raster.RasterMetadata(
        shape=shape, dtype=dtype, nodata=nodata, crs=crs, transform=transform
    )
    return features, metadata


def _parse_file(
    # General
    geometry: str,
    ffile: FeatureFile,
    field: str | None,
    # Field options
    dtype: dtype | None,
    field_casting: str,
    nodata: nodata | None,
    casting: str,
    operation: Callable | None,
    # Spatial
    window: BoundingBox | None,
    resolution: Resolution,
    units: str,
) -> tuple[GeometryValues, CRS | None, BoundingBox, dtype, scalar]:
    "Parses raster-creation values from an opened feature file"

    # Extract property schema
    properties = ffile.file.schema["properties"]

    # Validate field. Parse dtype and nodata
    _validate.field(field, properties)
    dtype = _parse.dtype(field, properties, dtype)
    nodata = _parse.nodata(nodata, casting, dtype)

    # Validate CRS and resolution units. Get window in the same CRS as the features
    crs = _crs.validate(ffile.crs)
    _validate.units(units, crs, resolution, geometry, ffile.path)

    # Load features and validate geometries
    features, bounds = _features.parse(
        geometry, ffile, field, dtype, field_casting, operation, crs, window
    )
    return features, crs, bounds, dtype, nodata
