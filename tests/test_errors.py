"""
test_errors  Unit tests for the errors module
"""

from dfha import errors


class TestShapeError:
    def test(_):
        error = errors.ShapeError("array", "columns", 1, (2, 5), (2, 6))
        assert isinstance(error, Exception)
        assert error.index == 1
        assert error.required == (2, 5)
        assert error.actual == (2, 6)
        assert (
            error.args[0] == "array must have 5 columns, but it has 6 columns instead."
        )


class TestDimensionError:
    def test(_):
        message = "test message"
        error = errors.DimensionError(message)
        assert isinstance(error, Exception)
        assert error.args[0] == message


class TestRasterShapeError:
    def test(_):
        name = "test"
        cause = errors.ShapeError(name, "rows", 0, required=(10, 10), actual=(9, 10))
        error = errors.RasterShapeError(name, cause)

        assert isinstance(error, Exception)
        assert error.args[0] == (
            "The shape of the test raster (9, 10) does not match the shape of the "
            "stream segment raster used to derive the segments (10, 10)."
        )
