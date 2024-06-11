"""
errors  Classes that define custom exceptions
----------
Numpy Arrays:
    ArrayError              - Generic class for invalid numpy arrays
    EmptyArrayError         - When a numpy array has no elements
    DimensionError          - When a numpy array has invalid nonsingleton dimensions
    ShapeError              - When a numpy axis has an invalid shape

Spatial Metadata:
    CRSError                - When a coordinate reference system is invalid
    MissingCRSError         - When a required CRS is missing
    TransformError          - When an affine transformation is invalid

Rasters:
    RasterError             - Generic class for invalid raster metadata
    RasterShapeError        - When a raster array has an invalid shape
    RasterTransformError    - When a raster has an invalid affine transformation
    RasterCRSError          - When a raster has an invalid coordinate reference system

Vector Features:
    FeaturesError           - When vector features are not valid
    FeatureFileError        - When a vector feature file cannot be read
    GeometryError           - When a feature geometry is not valid
    CoordinatesError        - When a feature's coordinates are not valid
    PolygonError            - When a polygon's coordinates are not valid
    PointError              - When a point's coordinates are not valid

Models:
    DurationsError          - When queried rainfall durations are not recognized

Internal:
    _handle_memory_error    - Detects and supplements memory errors
"""

from typing import NoReturn

#####
# Numpy Arrays
#####


class ArrayError(Exception):
    "Generic class for invalid numpy arrays"


class EmptyArrayError(ArrayError):
    "When a numpy array has no elements"


class DimensionError(ArrayError):
    "When a numpy array has invalid non-singleton dimensions"


class ShapeError(ArrayError):
    "When a numpy axis has the wrong length"


#####
# Projection Metadata
#####


class CRSError(Exception):
    "When a coordinate reference system is invalid"


class MissingCRSError(Exception):
    "When a required CRS is missing"


class TransformError(Exception):
    "When an affine transformation is invalid"


class MissingTransformError(Exception):
    "When a required transform is missing"


class MissingNoDataError(Exception):
    "When a required NoData value is missing"


#####
# Rasters
#####


class RasterError(Exception):
    "Generic class for invalid rasters"


class RasterShapeError(RasterError, ShapeError):
    "When a raster array has an invalid shape"


class RasterTransformError(RasterError, TransformError):
    "When a raster has an invalid affine transformation"


class RasterCRSError(RasterError, CRSError):
    "When a raster has an invalid coordinate reference system"


#####
# Vector Features
#####


class FeaturesError(Exception):
    "When vector features are not valid"


class FeatureFileError(FeaturesError):
    "When a vector feature file cannot be read"


class NoFeaturesError(FeaturesError):
    "When there are no vector features to convert to a raster"


class GeometryError(FeaturesError):
    "When a vector feature geometry is not valid"


class CoordinateError(GeometryError):
    "When vector feature geometry coordinates are not valid"


class PolygonError(CoordinateError):
    "When polygon feature coordinates are not valid"


class PointError(CoordinateError):
    "When point feature coordinates are not valid"


#####
# Models
#####


class DurationsError(Exception):
    "When queried rainfall durations are not reported in Table 4 of Staley et al., 2017"


#####
# Memory Errors
#####


def _handle_memory_error(error: Exception, message: str) -> NoReturn:
    "Detects and supplements memory errors"

    # Detect whether this is a memory issue
    ismemory = False
    if isinstance(error, MemoryError):
        ismemory = True
    elif isinstance(error, ValueError):
        for pattern in ["Maximum allowed dimension exceeded", "array is too big"]:
            if pattern in error.args[0]:
                ismemory = True

    # Supplement memory issues, reraise anything else
    if ismemory:
        raise MemoryError(message) from error
    else:
        raise error from None
