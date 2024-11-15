"""
Functions used to build Raster and RasterMetadata objects from various sources
----------
Factories:
    file        - Builds the metadata object for a file-based raster
    window      - Updates metadata and builds rasterio.Window for windowed loading
    pysheds     - Validates pysheds raster and builds metadata
    array       - Validates array. Returns metadata and values

Vector Features:
    point       - Validates and parses a Point feature file. Returns geometry-values and metadata
    polygons    - Validates and parses a Polygon feature file. Returns geometry-values and metadata
"""

from __future__ import annotations

import typing

import numpy as np
from pysheds.sview import Raster as PyshedsRaster
from rasterio import DatasetReader
from rasterio.windows import Window

import pfdf._validate.core as cvalidate
from pfdf import raster
from pfdf._utils import limits
from pfdf.projection import CRS, Transform
from pfdf.raster import _features
from pfdf.raster._utils import parse

if typing.TYPE_CHECKING:
    from typing import Any

    from pfdf.projection import BoundingBox
    from pfdf.raster import RasterMetadata
    from pfdf.typing.core import GeometryValues, MatrixArray


#####
# Standard factories
#####


def file(file: DatasetReader, band: int, name: str) -> RasterMetadata:
    "Builds the initial metadata object for a file-based raster"

    # Read file metadata
    shape = (file.height, file.width)
    dtype = file.dtypes[band - 1]
    nodata = file.nodata
    crs = file.crs
    transform = file.transform

    # Return the metadata object
    return raster.RasterMetadata(
        shape,
        dtype=dtype,
        nodata=nodata,
        casting="unsafe",
        crs=crs,
        transform=transform,
        name=name,
    )


def window(
    metadata: RasterMetadata, bounds: BoundingBox
) -> tuple[RasterMetadata, Window]:
    "Updates metadata and builds Window for windowed loading"

    # Get the window indices. Limit to pixels within the dataset
    _, rows, cols = metadata.clip(bounds, return_limits=True)
    rows = limits(rows[0], rows[1], metadata.nrows)
    cols = limits(cols[0], cols[1], metadata.ncols)

    # Require the bounds to overlap the dataset for at least one pixel
    if rows[0] >= rows[1] or cols[0] >= cols[1]:
        raise ValueError(
            f"The bounds must overlap the file dataset for at least 1 pixel.\n"
            f"    File dataset bounds: {metadata.bounds}"
        )

    # Compute the new shape and transform
    shape = (rows[1] - rows[0], cols[1] - cols[0])
    dx, dy = metadata.dx("base"), metadata.dy("base")
    left = metadata.left + dx * cols[0]
    top = metadata.top + dy * rows[0]
    transform = Transform(dx, dy, left, top)

    # Update metadata and build window
    metadata = metadata.update(shape=shape, transform=transform)
    window = Window.from_slices(rows, cols)
    return metadata, window


def pysheds(sraster: Any, name: Any) -> RasterMetadata:
    "Validates type, extracts CRS, and builds metadata"

    # Validate type and extract CRS
    cvalidate.type(
        sraster, "input raster", PyshedsRaster, "pysheds.sview.Raster object"
    )
    crs = CRS.from_wkt(sraster.crs.to_wkt())

    # Return metadata
    return raster.RasterMetadata(
        sraster.shape,
        dtype=sraster.dtype,
        nodata=sraster.nodata,
        casting="unsafe",
        crs=crs,
        transform=sraster.affine,
        name=name,
    )


def array(
    array: Any,
    name: Any,
    nodata: Any,
    casting: Any,
    crs: Any,
    transform: Any,
    bounds: Any,
    spatial: Any,
    copy: bool,
) -> tuple[RasterMetadata, MatrixArray]:
    "Returns metadata and values for an array-based raster"

    # Validate array and initialize metadata
    values = cvalidate.matrix(array, "array", copy=copy)
    metadata = raster.RasterMetadata(
        values.shape,
        dtype=values.dtype,
        nodata=nodata,
        casting=casting,
        crs=crs,
        transform=transform,
        bounds=bounds,
        name=name,
    )

    # Parse spatial template. Return metadata and array values
    metadata = parse.template(metadata, spatial, "spatial template")
    return metadata, values


#####
# Vector features
#####


def points(
    path: Any,
    field: Any,
    # Field options
    dtype: Any,
    field_casting: Any,
    nodata: Any,
    casting: Any,
    operation: Any,
    # Spatial options
    bounds: Any,
    resolution: Any,
    units: Any,
    # File IO
    layer: Any,
    driver: Any,
    encoding: Any,
) -> tuple[GeometryValues, RasterMetadata]:
    "Validates and parses a Point feature file. Returns geometry-values and metadata"

    # Parse metadata and features
    features, metadata = _features.parse_file(
        # General
        "point",
        path,
        field,
        # Field
        dtype,
        field_casting,
        nodata,
        casting,
        operation,
        # Spatial
        bounds,
        resolution,
        units,
        # File IO
        layer,
        driver,
        encoding,
    )

    # If not using a window, pad shape by 1 to include points on the edges
    if bounds is None:
        shape = (metadata.nrows + 1, metadata.ncols + 1)
        metadata = metadata.update(shape=shape, keep_bounds=False)
    return features, metadata


def polygons(
    path: Any,
    field: Any,
    # Field options
    dtype: Any,
    field_casting: Any,
    nodata: Any,
    casting: Any,
    operation: Any,
    # Spatial options
    bounds: Any,
    resolution: Any,
    units: Any,
    # File IO
    layer: Any,
    driver: Any,
    encoding: Any,
) -> tuple[GeometryValues, RasterMetadata]:
    "Validates and parses a Polygon feature file. Returns geometry-values and metadata"

    # Check that the dtype is supported
    if field is not None and dtype is not None:
        dtype = cvalidate.real_dtype(dtype, "dtype")
        allowed = [
            "bool",
            "int16",
            "int32",
            "uint8",
            "uint16",
            "uint32",
            "float32",
            "float64",
        ]
        cvalidate.option(str(dtype), "dtype", allowed)

    # Parse the features and metadata
    return _features.parse_file(
        # General
        "polygon",
        path,
        field,
        # Field
        dtype,
        field_casting,
        nodata,
        casting,
        operation,
        # Spatial
        bounds,
        resolution,
        units,
        # File IO
        layer,
        driver,
        encoding,
    )
