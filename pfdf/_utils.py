"""
_utils  Low-level utilities used throughout the package
----------
This module provides a variety of low-level functions used throughout the package.
Broadly, these include functions for basic input parsing.
----------
Misc:
    real            - A list of numpy dtypes considered to be real-valued numbers
    any_defined     - True if any input is not None

Sequence conversion:
    aslist          - Returns an input as a list
    astuple         - Returns an input as a tuple
"""

from typing import Any, List, Tuple

from numpy import bool_, floating, integer

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
