"""
errors  Classes that define custom exceptions
----------
Numpy Arrays:
    ArrayError              - Generic class for invalid numpy arrays
    EmptyArrayError         - When a numpy array has no elements
    DimensionError          - When a numpy array has invalid nonsingleton dimensions
    ShapeError              - When a numpy axis has an invalid shape

Spatial Metadata:
    CrsError                - When a coordinate reference system is invalid
    TransformError          - When an affine transformation is invalid

Rasters:
    RasterError             - Generic class for invalid raster metadata
    RasterShapeError        - When a raster array has an invalid shape
    RasterTransformError    - When a raster has an invalid affine transformation
    RasterCrsError          - When a raster has an invalid coordinate reference system

Vector Features:
    FeaturesError           - When vector features are not valid
    FeatureFileError        - When a vector feature file cannot be read
    GeometryError           - When a feature geometry is not valid
    CoordinatesError        - When a feature's coordinates are not valid
    PolygonError            - When a polygon's coordinates are not valid
    PointError              - When a point's coordinates are not valid

Models:
    DurationsError          - When queried rainfall durations are not recognized
"""


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
# Raster Metadata
#####


class CrsError(Exception):
    "When a coordinate reference system is invalid"


class TransformError(Exception):
    "When an affine transformation is invalid"


#####
# Rasters
#####


class RasterError(Exception):
    "Generic class for invalid rasters"


class RasterShapeError(RasterError, ShapeError):
    "When a raster array has an invalid shape"


class RasterTransformError(RasterError, TransformError):
    "When a raster has an invalid affine transformation"


class RasterCrsError(RasterError, CrsError):
    "When a raster has an invalid coordinate reference system"


#####
# Vector Features
#####


class FeaturesError(Exception):
    "When vector features are not valid"


class FeatureFileError(FeaturesError):
    "When a vector feature file cannot be read"


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
