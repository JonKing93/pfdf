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
    _handle_memory_error,
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


class TestHandleMemoryError:
    def test_memory(_, assert_contains):
        a = MemoryError("test")
        message = "more info"
        with pytest.raises(MemoryError) as error:
            _handle_memory_error(a, message)
        assert_contains(error, message)

    def test_value(_, assert_contains):
        a = ValueError("Maximum allowed dimension exceeded")
        message = "more info"
        with pytest.raises(MemoryError) as error:
            _handle_memory_error(a, message)
        assert_contains(error, message)

    def test_unrecognized_value(_, assert_contains):
        a = ValueError("Some other issue")
        with pytest.raises(ValueError) as error:
            _handle_memory_error(a, "memory info")
        assert_contains(error, "Some other issue")

    def test_other(_, assert_contains):
        a = TypeError("Some other issue")
        with pytest.raises(TypeError) as error:
            _handle_memory_error(a, "memory info")
        assert_contains(error, "Some other issue")
