"""
_utils  Low-level utilities used throughout the package
----------
Type hint:
    real        - A list of numpy dtypes considered to be real-valued numbers

Functions:
    aslist      - Returns an input as a list
    astuple     - Returns an input as a tuple
    clean_dims  - Optionally removes trailing singleton dimensions from an array
    all_nones   - True if every input is None
    no_nones    - True if every input is not None
    limits      - Trims limits to valid indices

Modules:
    classify    - Function for classifying arrays using thresholds
    nodata      - Utilities for working with NoData values
"""

from typing import Any

import numpy as np

from pfdf.typing.core import RealArray

# Combination numpy dtype for real-valued data
real = [np.integer, np.floating, np.bool_]


def aslist(input: Any) -> list:
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


def astuple(input: Any) -> tuple:
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


def clean_dims(X: RealArray, keepdims: bool) -> RealArray:
    "Optionally removes trailing singleton dimensions"
    if not keepdims:
        X = np.atleast_1d(np.squeeze(X))
    return X


def all_nones(*args: Any) -> bool:
    "True if every input is None. Otherwise False"
    for arg in args:
        if arg is not None:
            return False
    return True


def no_nones(*args: Any) -> bool:
    "True if none of the inputs are None. Otherwise False"

    for arg in args:
        if arg is None:
            return False
    return True


def limits(start, stop, length):
    start = max(start, 0)
    stop = min(stop, length)
    return (start, stop)
