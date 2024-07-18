import pytest

import pfdf._validate._buffers as validate
from pfdf.errors import DimensionError


class TestDistance:
    def test_valid(_):
        assert validate._distance(5, "distance") == 5

    def test_negative(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate._distance(-5, "distance")
        assert_contains(error, "distance")

    def test_vector(_, assert_contains):
        with pytest.raises(DimensionError) as error:
            validate._distance([1, 2, 3], "distance")
        assert_contains(error, "distance")


class TestBuffers:
    def test_all_default(_):
        buffers = validate.buffers(
            distance=5, left=None, right=None, top=None, bottom=None
        )
        assert buffers == {"left": 5, "right": 5, "top": 5, "bottom": 5}

    def test_no_default(_):
        buffers = validate.buffers(distance=None, left=1, right=2, top=3, bottom=4)
        assert buffers == {"left": 1, "right": 2, "top": 3, "bottom": 4}

    def test_mixed(_):
        buffers = validate.buffers(distance=5, left=None, right=2, top=3, bottom=None)
        assert buffers == {"left": 5, "right": 2, "top": 3, "bottom": 5}

    def test_all_0(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.buffers(distance=0, left=None, right=None, top=None, bottom=None)
        assert_contains(error, "cannot all be 0")

    def test_no_buffers(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.buffers(None, None, None, None, None)
        assert_contains(error, "must specify at least one buffer")

    def test_negative_buffer(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.buffers(distance=5, left=-1, right=None, top=None, bottom=None)
        assert_contains(error, "left")
