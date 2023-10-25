from math import nan

import numpy as np

from pfdf._utils.classify import classify


class TestClassify:
    def test_default(_):
        a = np.array([1, 2, 3, 4, nan, 5, 6, 7, nan, 8, 9, 10])
        thresholds = [3, 7]
        output = classify(a, thresholds)
        expected = np.array([1, 1, 1, 2, nan, 2, 2, 2, nan, 3, 3, 3])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nan(_):
        a = np.array([1, 2, 3, 4, 5, 6, 7])
        thresholds = [3.5]
        output = classify(a, thresholds, nodata=4)
        expected = np.array([1, 1, 1, nan, 2, 2, 2])
        assert np.array_equal(output, expected, equal_nan=True)

    def test_nan_to(_):
        a = np.array([1, 2, 3, 4, 5, 6, 7])
        thresholds = [3.5]
        output = classify(a, thresholds, nodata=4, nodata_to=-999)
        expected = np.array([1, 1, 1, -999, 2, 2, 2])
        assert np.array_equal(output, expected)
