"""
validate  Functions that validate user inputs
----------
Key functions:
    ndarray     - Check that an input is a numpy ndarray
    matrix      - Check an input is a 2D numpy array. Optionally check dtype and shape

Custom Errors:
    NDimError   - Raised when an input has an incorrect number of dimensions
    ShapeError  - Raised when an input has an incorrect shape
"""

import numpy as np
from typing import Any, Union, List, Optional, Tuple
from dfha import utils

# Type aliases
dtype = Union[np.dtype, str, object]
dtypes = Union[dtype, List[dtype]]
shape2d = Tuple[int, int]


def _dtype(input: Any, name: str, dtypes: dtypes) -> None:
    "Check a numpy dtype is valid"
    if dtypes is not None:
        dtypes = utils.aslist(dtypes)
        if input.dtype not in dtypes:
            allowed = ", ".join([str(np.dtype(type)) for type in dtypes])
            raise TypeError(
                f"The dtype of {name} ({input.dtype}) is not allowed. Allowed dtypes are: {allowed}"
            )


def _shape(input: Any, name: str, axes: List[str], shape: shape2d) -> None:
    "Check that the shape of each axis is correct"
    if shape is not None:
        for axis, required, actual in zip(axes, shape, input.shape):
            if required != -1 and required != actual:
                raise ShapeError(name, axis, required, actual)


def _ndim(input: Any, name: str, N: int) -> None:
    "Check that the number of dimensions are correct"
    if input.ndim != N:
        raise NDimError(name, N, input.ndim)


def matrix(
    input: Any,
    name: str,
    *,
    dtypes: Optional[dtypes] = None,
    shape: Optional[shape2d] = None,
) -> None:
    """
    matrix  Validates an input numpy 2D array
    ----------
    matrix(input, name)
    Checks that an input is a numpy ndarray with two dimensions. Raises a
    TypeError if not an ndarray. Raises a NDimError if the number of dimensions
    is not 2.

    matrix(..., *, dtypes, ...)
    Also checks that the ndarray has one of the specified dtypes. Raises a
    TypeError if not.

    matrix(..., *, shape, ...)
    Also checks that the ndarray has the specified shape. Raises a ShapeError
    if not.
    ----------
    Inputs:
        input: The input being checked
        name: The name of the input (for use in error messages)
        dtypes: The set of allowed dtypes. May be a single dtype, or a list. A
            dtype may be any value accepted by the numpy.dtype constructor.
        shape: A required shape for the matrix. Use -1 to not check the shape
            of an axis.

    Raises:
        TypeError: If the input is not a numpy ndarray
        NDimError: If the input does not have 2 dimensions
        TypeError: If the input is not an allowed dtype
        ShapeError: If the input does not have the required shape
    """

    ndarray(input, name)
    _ndim(input, name, 2)
    _dtype(input, name, dtypes)
    _shape(input, name, ["row(s)", "column(s)"], shape)


def ndarray(input: Any, name: str) -> None:
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


class NDimError(Exception):
    "When a numpy array has the wrong number of dimensions"

    def __init__(self, name: str, nrequired: int, nactual: int) -> None:
        message = (
            f"{name} must have {nrequired} dimension(s), but it has {nactual} instead."
        )
        super().__init__(message)


class ShapeError(Exception):
    "When a numpy axis has the wrong shape"

    def __init__(self, name: str, axis: str, required: int, actual: int) -> None:
        message = (
            f"{name} must have {required} {axis}, but it has {actual} {axis} instead."
        )
        super().__init__(message)
