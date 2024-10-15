"""
Utilities to process vector features into rasters
----------
Functions:
    parse_file  - Validates feature file and computes values for raster creation
    _parse_file - Determines values from an opened feature file using validated options
"""

from typing import Any, Callable

from numpy import dtype

from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.raster._features import _features, _parse, _validate
from pfdf.raster._features._ffile import FeatureFile
from pfdf.raster._features.typing import GeometryValues, Resolution, nodata
from pfdf.typing.core import scalar, shape2d


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
    bounds: Any,
    resolution: Any,
    units: Any,
    # File IO
    layer: Any,
    driver: Any,
    encoding: Any,
) -> tuple[GeometryValues, CRS, Transform, shape2d, dtype, nodata]:
    "Validates feature file and computes values for raster creation"

    # Validate
    if field is not None:
        dtype, field_casting, nodata = _validate.field_options(
            field, dtype, field_casting, nodata, casting, operation
        )
    bounds, resolution, units = _validate.spatial(bounds, resolution, units)
    path, layer, driver, encoding = _validate.file_io(path, layer, driver, encoding)

    # Open file. Read and parse properties
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
            bounds,
            resolution,
            units,
        )

    # Convert resolution to axis unit. Then compute transform and shape
    resolution, crs = _parse.resolution(resolution, units, crs, bounds)
    transform, shape = _parse.extent(bounds, resolution)
    return features, crs, transform, shape, dtype, nodata


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
    bounds: BoundingBox | None,
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

    # Validate CRS and resolution units
    crs = _crs.validate(ffile.crs)
    _validate.units(units, crs, resolution, geometry, ffile.path)

    # Load features and validate geometries
    features, bounds = _features.parse(
        geometry, ffile, field, dtype, field_casting, operation, crs, bounds
    )
    return features, crs, bounds, dtype, nodata
