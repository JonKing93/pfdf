import pytest

from pfdf.errors import (
    ArrayError,
    CoordinateError,
    CrsError,
    DimensionError,
    DurationsError,
    EmptyArrayError,
    FeatureFileError,
    FeaturesError,
    GeometryError,
    PointError,
    PolygonError,
    RasterCrsError,
    RasterError,
    RasterShapeError,
    RasterTransformError,
    ShapeError,
    TransformError,
)


def check(error, message, type):
    assert isinstance(error, type)
    assert error.args[0] == message


@pytest.mark.parametrize(
    "error",
    (ArrayError, CrsError, TransformError, RasterError, DurationsError, FeaturesError),
)
def test_base_error(error):
    message = "test message"
    error = error(message)
    check(error, message, Exception)


@pytest.mark.parametrize("error", (EmptyArrayError, DimensionError, ShapeError))
def test_array_error(error):
    message = "test message"
    error = error(message)
    check(error, message, ArrayError)


@pytest.mark.parametrize(
    "error, SecondaryError",
    (
        (RasterShapeError, ShapeError),
        (RasterTransformError, TransformError),
        (RasterCrsError, CrsError),
    ),
)
def test_raster_error(error, SecondaryError):
    message = "test message"
    error = error(message)
    check(error, message, RasterError)
    assert isinstance(error, SecondaryError)


@pytest.mark.parametrize(
    "error",
    (FeatureFileError, GeometryError, CoordinateError, PolygonError, PointError),
)
def test_features_error(error):
    message = "test message"
    error = error(message)
    check(error, message, FeaturesError)
