import pytest

from pfdf.errors import (
    ArrayError,
    CoordinateError,
    CRSError,
    DimensionError,
    DurationsError,
    EmptyArrayError,
    FeatureFileError,
    FeaturesError,
    GeometryError,
    NoFeaturesError,
    PointError,
    PolygonError,
    RasterCRSError,
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
    (ArrayError, CRSError, TransformError, RasterError, DurationsError, FeaturesError),
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
        (RasterCRSError, CRSError),
    ),
)
def test_raster_error(error, SecondaryError):
    message = "test message"
    error = error(message)
    check(error, message, RasterError)
    assert isinstance(error, SecondaryError)


@pytest.mark.parametrize(
    "error",
    (
        FeatureFileError,
        NoFeaturesError,
        GeometryError,
        CoordinateError,
        PolygonError,
        PointError,
    ),
)
def test_features_error(error):
    message = "test message"
    error = error(message)
    check(error, message, FeaturesError)
