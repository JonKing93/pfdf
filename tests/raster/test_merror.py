import pytest

from pfdf.raster import _merror


class TestFeatures:
    def test_memory(_, assert_contains):
        a = MemoryError("test")
        with pytest.raises(MemoryError) as error:
            _merror.features(a, "polygon")
        assert_contains(
            error,
            "Cannot create the polygon raster because the requested array is too large for your computer's memory.",
            'Try changing the "resolution" input to a coarser resolution, or use the "bounds" option to load a smaller subset of polygon data',
        )

    def test_other(_, assert_contains):
        a = TypeError("some other error")
        with pytest.raises(TypeError) as error:
            _merror.features(a, "polygon")
        assert_contains(error, "some other error")


class TestSupplement:
    def test_memory(_, assert_contains):
        a = MemoryError("test")
        message = "more info"
        with pytest.raises(MemoryError) as error:
            _merror.supplement(a, message)
        assert_contains(error, message)

    def test_value(_, assert_contains):
        a = ValueError("Maximum allowed dimension exceeded")
        message = "more info"
        with pytest.raises(MemoryError) as error:
            _merror.supplement(a, message)
        assert_contains(error, message)

    def test_unrecognized_value(_, assert_contains):
        a = ValueError("Some other issue")
        with pytest.raises(ValueError) as error:
            _merror.supplement(a, "memory info")
        assert_contains(error, "Some other issue")

    def test_other(_, assert_contains):
        a = TypeError("Some other issue")
        with pytest.raises(TypeError) as error:
            _merror.supplement(a, "memory info")
        assert_contains(error, "Some other issue")
