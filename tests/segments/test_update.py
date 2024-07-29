import numpy as np

from pfdf.segments import Segments, _update


class TestSegments:
    def test(_, segments, linestrings245, indices245):
        remove = np.array([1, 0, 1, 0, 0, 1], bool)
        out1, out2 = _update.segments(segments, remove)
        assert out1 == linestrings245
        assert out2 == indices245


class TestFamily:
    def test(_):
        child = np.array([1, 2, 3, 4, 5, 6, 7]) - 1
        parents = np.array([[0, 0], [2, 0], [2, 6], [6, 2], [2, 5], [5, 2], [4, 5]]) - 1
        remove = np.array([0, 1, 0, 0, 1, 0], bool)

        expected_child = np.array([1, 0, 3, 4, 0, 6, 7]) - 1
        expected_parents = (
            np.array([[0, 0], [0, 0], [0, 6], [6, 0], [0, 0], [0, 0], [4, 0]]) - 1
        )
        _update.family(child, parents, remove)

        assert np.array_equal(child, expected_child)
        assert np.array_equal(parents, expected_parents)


class TestIndices:
    def test(_):
        family = np.array(
            [
                [-1, -1],
                [-1, -1],
                [1, 4],
                [4, 6],
                [7, -1],
                [-1, 7],
            ]
        )
        nremoved = np.array([1, 1, 2, 2, 2, 3, 3, 3, 3])
        expected = np.array(
            [
                [-1, -1],
                [-1, -1],
                [0, 2],
                [2, 3],
                [4, -1],
                [-1, 4],
            ]
        )
        _update.indices(family, nremoved)
        assert np.array_equal(family, expected)


class TestConnectivity:
    def test(_, segments, child245, parents245):
        remove = np.array([1, 0, 1, 0, 0, 1], bool)
        out1, out2 = _update.connectivity(segments, remove)
        assert np.array_equal(out1, child245)
        assert np.array_equal(out2, parents245)


class TestBasins:
    def test_none(_, bsegments):
        assert bsegments._basins is None
        remove = np.array([0, 0, 0, 0, 0, 0], bool)
        output = _update.basins(bsegments, remove)
        assert output is None

    def test_unaltered(_, bsegments, basins):
        bsegments.locate_basins()
        original = bsegments._basins
        assert np.array_equal(original, basins)

        remove = np.array([1, 1, 0, 0, 0, 0], bool)
        output = _update.basins(bsegments, remove)
        assert output is original

    def test_reset(_, bsegments, basins):
        bsegments.locate_basins()
        original = bsegments._basins
        assert np.array_equal(original, basins)

        remove = np.array([0, 0, 1, 0, 0, 0], bool)
        output = _update.basins(bsegments, remove)
        assert output is None
