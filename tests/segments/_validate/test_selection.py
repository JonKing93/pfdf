import numpy as np
import pytest

from pfdf.errors import DimensionError, ShapeError
from pfdf.segments._validate import _selection


class TestCheckInNetwork:
    def test_in_network(_, segments):
        input = np.array(5).reshape(1)
        _selection._check_in_network(segments, input, "")

    def test_scalar_missing(_, segments, assert_contains):
        input = np.array(9).reshape(1)
        with pytest.raises(ValueError) as error:
            _selection._check_in_network(segments, input, "id")
        assert_contains(error, "id (value=9)")

    def test_vector_missing(_, segments, assert_contains):
        input = np.array([1, 9])
        with pytest.raises(ValueError) as error:
            _selection._check_in_network(segments, input, "ids")
        assert_contains(error, "ids[1] (value=9)")


class TestId:
    def test_valid(_, segments):
        output = _selection.id(segments, 5)
        assert output == 4

    def test_not_scalar(_, segments, assert_contains):
        with pytest.raises(DimensionError) as error:
            _selection.id(segments, [5, 2])
        assert_contains(error, "id")

    def test_not_in_network(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            _selection.id(segments, 9)
        assert_contains(error, "id (value=9)")


class TestIds:
    def test_none(_, segments):
        output = _selection.ids(segments, None)
        assert np.array_equal(output, [0, 1, 2, 3, 4, 5])

    def test_valid(_, segments):
        segments.remove(3, "ids")
        print(segments.ids)
        output = _selection.ids(segments, [5, 1, 2, 5, 4])
        assert np.array_equal(output, [3, 0, 1, 3, 2])

    def test_not_vector(_, segments, assert_contains):
        with pytest.raises(TypeError) as error:
            _selection.ids(segments, "invalid")
        assert_contains(error, "ids")

    def test_not_in_network(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            _selection.ids(segments, 22)
        assert_contains(error, "ids[0] (value=22)")


class TestSelection:
    def test_valid_ids(_, segments):
        ids = [2, 4, 5]
        expected = np.array([0, 1, 0, 1, 1, 0], dtype=bool)
        output = _selection.selection(segments, ids, "ids")
        assert np.array_equal(output, expected)

    def test_valid_indices(_, segments):
        indices = np.ones(6).astype(bool)
        output = _selection.selection(segments, indices, "indices")
        assert np.array_equal(output, indices)

    def test_duplicate_ids(_, segments):
        ids = [1, 1, 1, 1, 1]
        output = _selection.selection(segments, ids, "ids")
        expected = np.zeros(6, bool)
        expected[0] = 1
        assert np.array_equal(output, expected)

    def test_booleanish_indices(_, segments):
        indices = np.ones(6, dtype=float)
        output = _selection.selection(segments, indices, "indices")
        assert np.array_equal(output, indices.astype(bool))

    def test_not_boolean_indices(_, segments, assert_contains):
        ids = np.arange(6)
        with pytest.raises(ValueError) as error:
            _selection.selection(segments, ids, "indices")
        assert_contains(
            error,
            "The data elements of selected segment indices must be 0 or 1, ",
            "but element [2] (value=2) is not.",
        )

    def test_indices_wrong_length(_, segments, assert_contains):
        indices = np.ones(10)
        with pytest.raises(ShapeError) as error:
            _selection.selection(segments, indices, "indices")
        assert_contains(
            error,
            "selected segment indices must have 6 element(s), but it has 10 element(s) instead.",
        )

    def test_invalid_ids(_, segments, assert_contains):
        ids = [1, 2, 7]
        with pytest.raises(ValueError) as error:
            _selection.selection(segments, ids, "ids")
        assert_contains(
            error,
            "selected segment ids (value=7) is not the ID of a segment in the network",
        )

    def test_invalid_type(_, segments, assert_contains):
        indices = np.ones(6)
        with pytest.raises(ValueError) as error:
            _selection.selection(segments, indices, "invalid")
        assert_contains(
            error,
            "type (invalid) is not a recognized option. Supported options are: indices, ids",
        )
