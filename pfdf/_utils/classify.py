"""
classify  A function for classifying an array using thresholds
----------
Functions:
    classify    - Classify array values based on thresholds
"""

from numpy import digitize, inf, nan

from pfdf._utils.nodata import NodataMask
from pfdf.typing import RealArray, VectorArray, scalar


def classify(
    array: RealArray,
    thresholds: VectorArray,
    nodata: scalar = nan,
    nodata_to: scalar = nan,
) -> RealArray:
    """
    classify  Classifies an array using thresholds while optionally preserving NoData
    ----------
    classify(array, thresholds)
    Classifies the elements of an array based on their relationships to a set
    of thresholds. Elements are classified from 1 to N+1, where N is the number
    of thresholds. NaN elements are classified as NaN. Thresholds specify an
    inclusive upper bound, and exclusive lower bound. The edge bins are searched
    between a threshold and the relevant infinity.

    classify(..., nodata)
    Specifies the NoData value for the array. Defaults to NaN.

    classify(..., nodata, nodata_to)
    Specify the value that NoData elements should be classified as. Defaults to NaN.
    ----------
    Inputs:
        array: The array whose elements are being classified
        thresholds: The thresholds used to classify the array
        nodata: The Nodata value for the array
        nodata_to: The value that NoData elements should be classified as

    Outputs:
        numpy array: The classification values for the array
    """

    bins = [-inf] + list(thresholds) + [inf]
    classes = digitize(array, bins, right=True)
    nodatas = NodataMask(array, nodata)
    return nodatas.fill(classes, nodata_to)
