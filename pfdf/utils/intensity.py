"""
Functions for converting between rainfall accumulations and intensities
----------
This module contains functions that convert between rainfall accumulations
and intensities. In pfdf, the models.staley2017 (s17) module works strictly with
rainfall accumulations, defined as millimeters accumulated over a duration (typically
15, 30, or 60 minutes). However, many users find it useful to instead work with
rainfall intensities, which are typically represented as mm/hour. The functions
in this module help convert between these two formats.

These functions are specifically designed to support the s17 module. The
"to_accumulation" function converts a vector rainfall intensities to a vector of
accumulations. By contrast, the "from_accumulation" function is intended
to convert the output of the s17.accumulation fuction to intensities. This function
broadcasts a vector of durations along an accumulation array in order to convert the
array values to intensities.
----------
Functions:
    to_accumulation     - Converts rainfall intensities to accumulations
    from_accumulation   - Converts rainfall accumulations to intensities
"""

from __future__ import annotations

import typing

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import ShapeError

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import RealArray, VectorArray, scalar, vector


def to_accumulation(I: vector, durations: vector) -> VectorArray:
    """
    Converts rainfall intensities to accumulations
    ----------
    to_accumulation(I, durations)
    Converts the input rainfall intensities (in mm/hour) to rainfall accumulations
    (mm accumulated over a duration). The input intensities should be a vector in
    mm/hour. The input durations should be in minutes. The durations may either
    be scalar, or a vector with one element per intensity.
    ----------
    Inputs:
        I: Rainfall intensities (mm/hour)
        durations: Number of minutes per duration

    Outputs:
        numpy array: The converted rainfall accumulations
    """

    # Intensities should be a vector
    Iname = "rainfall intensities (I)"
    I = validate.vector(I, Iname, dtype=real)

    # Durations should be a vector with a broadcastable number of elements
    durations = validate.vector(durations, "durations", dtype=real)
    if durations.size not in [1, I.size]:
        raise ShapeError(
            f"The length of the durations vector must either be 1, or the number "
            f"of rainfall intensities ({I.size})."
        )
    return I * durations / 60


def from_accumulation(
    R: RealArray, durations: vector, *, dim: Optional[scalar] = None
) -> RealArray:
    """
    Converts rainfall accumulations to intensities
    ----------
    from_accumulation(R, durations)
    Converts the input rainfall accumulations from mm over a duration to rainfall
    intensities in mm/hour. R should be an array of values representing millimeters
    of accumulation over one or more durations. The input durations should be in minutes.
    By default, the durations are broadcast across the final dimension of R, so the
    length of `durations` should either be 1, or the final value in R.shape.

    from_accumulation(..., *, dim)
    Specifies the dimension of R that durations should be broadcast over. Here, `dim` is
    the *index* of a dimension of R. So for example, use 0 to broadcast durations over
    the first dimension, 1 to broadcast along the second dimension, etc. The `dim` input
    must be a scalar positive index. If None, broadcasts along the final dimension. When
    using the `dim` option, the length of the durations vector should either be 1, or
    R.shape[dim].
    ----------
    Inputs:
        R: An array of rainfall accumulations in millimeters over durations
        durations: Rainfall durations in minutes.
        dim: The index of the dimension of R over which to broadcast durations

    Outputs:
        numpy array: The converted rainfall intensities (mm/hour)
    """

    # Validate the broadcasting dimension
    if dim is None:
        dim = -1
    else:
        dim = validate.scalar(dim, "dim", dtype=real)
        validate.positive(dim, "dim", allow_zero=True)
        validate.integers(dim, "dim")
        dim = int(dim)

    # Check R is an array. Ensure shape has at least dim dimensions
    name = "rainfall accumulations (R)"
    R = validate.array(R, name, dtype=real)
    if dim != -1:
        nmissing = (dim + 1) - R.ndim
        if nmissing > 0:
            shape = R.shape + (1,) * nmissing
            R = R.reshape(shape)

    # Durations should be a vector that can be broadcasted along the indicated dimension
    durations = validate.vector(durations, "durations", dtype=real)
    if durations.size not in (1, R.shape[dim]):
        raise ShapeError(
            f"The length of the durations vector must either be 1 or {R.shape[dim]} "
            f"(scalar or R.shape[{dim}])"
        )

    # Shape durations for broadcasting and convert accumulations
    shape = [1] * R.ndim
    shape[dim] = durations.size
    durations = durations.reshape(shape)
    return R * 60 / durations
