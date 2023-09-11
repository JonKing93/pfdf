"""
_utils  Low-level utilities used throughout the package
----------
This module provides a variety of low-level functions used throughout the package.
----------
Misc:
    real            - A list of numpy dtypes considered to be real-valued numbers
    any_defined     - True if any input is not None
    classify        - Classify array values based on thresholds

Sequence conversion:
    aslist          - Returns an input as a list
    astuple         - Returns an input as a tuple
"""

from typing import Any, List, Tuple

from numpy import bool_, digitize, floating, inf, integer, isnan, nan

from pfdf import _nodata
from pfdf.typing import RealArray, VectorArray, scalar

# Combination numpy dtypes
real = [integer, floating, bool_]


def any_defined(*args: Any) -> bool:
    "any_defined  True if any input is not None. Otherwise False."
    for arg in args:
        if arg is not None:
            return True
    return False


def aslist(input: Any) -> List:
    """
    aslist  Returns an input as a list
    ----------
    aslist(input)
    Returns the input as a list. If the input is a tuple, converts to a list. If
    the input is a list, returns it unchanged. Otherwise, places the input within
    a new list.
    """
    if isinstance(input, tuple):
        input = list(input)
    elif not isinstance(input, list):
        input = [input]
    return input


def astuple(input: Any) -> Tuple:
    """
    astuple  Returns an input as a tuple
    ----------
    astuple(input)
    Returns the input as a tuple. If the input is a list, converts to a tuple. If
    the input is a tuple, returns it unchanged. Otherwise, places the input within
    a new tuple.
    """
    if isinstance(input, list):
        input = tuple(input)
    elif not isinstance(input, tuple):
        input = (input,)
    return input


def classify(
    array: RealArray,
    thresholds: VectorArray,
    nodata: scalar = nan,
    nodata_to: scalar = nan,
) -> RealArray:
    """
    classify  Classifies an array using thresholds while preserving NoData
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

    # Locate NoDatas and classify array
    nodatas = _nodata.mask(array, nodata)
    bins = [-inf] + list(thresholds) + [inf]
    classes = digitize(array, bins, right=True)

    # Classify Nodata
    if nodatas is not None:
        if isnan(nodata_to):
            classes = classes.astype(float)
        classes[nodatas] = nodata_to
    return classes
