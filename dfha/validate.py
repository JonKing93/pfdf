"""
validate  Functions that validate user inputs
"""

import numpy as np
from typing import Any, Union, List, Optional, Tuple, NoReturn

# Type aliases
dtype = Union[np.dtype, str]
dtypes = Union[dtype, List[dtype]]
shape2d = Tuple[int, int]


def ndarray(input, name):
    """
    ndarray  Checks that an input is a numpy ndarray
    ----------
    ndarray(input)
    Checks that the input is an numpy ndarray. Raises a TypeError if not.
    ----------
    Inputs:
        input: The input being checked

    Raises:
        TypeError: If the input is not a numpy ndarray
    """

    if not isinstance(input, np.ndarray):
        raise TypeError(f"{name} must be a numpy ndarray")


def _dtype(input, name, dtypes):
    if dtypes is not None:
        if input.dtype not in list(dtypes):
            raise TypeError(f"{name} is not an allowed dtype")


def _shape(input, name, axes, required):
    if required is not None:
        for axis, required, actual in zip(axes, required, input.shape):
            if required != -1 and required != actual:
                raise ValueError(
                    f"{name} must have {required} {axis}, but it has {actual} {axis} instead."
                )


def _ndim(input, name, N):
    if input.ndim != N:
        raise ValueError(f"{name} must have {N} dimensions")


def matrix(
    input: Any,
    name: str,
    *,
    dtype: Optional[dtypes] = None,
    shape: Optional[shape2d] = None,
):
    """
    matrix  Validates an input numpy 2D array
    ----------
    matrix(input)
    Checks that an input is a numpy ndarray with two dimensions.

    matrix(..., *, dtype, ...)
    Also checks that the ndarray has one of the specified dtypes.

    matrix(..., *, shape, ...)
    Also checks that the ndarray has the specified shape.
    """

    ndarray(input, name)
    _ndim(input, name, 2)
    _dtype(input, name, dtype)
    _shape(input, name, ["rows", "columns"], shape)
