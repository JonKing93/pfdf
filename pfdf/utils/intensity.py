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
"to_accumulation" function converts from an input vector rainfall intensities to 
a vector of accumulations. By contrast, the "from_accumulation" function is intended 
to convert the output of the s17.likelihood fuction to intensities. This function
broadcasts a vector of durations along the second dimension of an accumulation
array in order to convert the array values to intensities.
----------
Functions:
    to_accumulation     - Converts rainfall intensities to accumulations
    from_accumulation   - Converts rainfall accumulations to intensities
"""

import numpy as np

import pfdf._validate as validate
from pfdf._utils import real
from pfdf.errors import ShapeError
from pfdf.typing import RealArray, VectorArray, vector


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


def from_accumulation(R: RealArray, durations: vector) -> RealArray:
    """
    Converts rainfall accumulations to intensities
    ----------
    from_accumulation(R, durations)
    Converts the input rainfall accumulations from mm over a duration to rainfall
    intensities in mm/hour. R should be an array of values representing millimeters
    of accumulation over one or more durations. The array is assumed to originate
    from the s17.accumulation function, so durations are broadcast across the
    second dimension. The input durations should be in minutes and may either be
    scalar or a vector with one element per column in R.
    ----------
    Inputs:
        R: An array of rainfall accumulations in millimeters over durations
        durations: Rainfall durations in minutes. Either scalar, or a vector
            with one element per column of R

    Outputs:
        numpy array: The converted rainfall intensities (mm/hour)
    """

    # Validate R is an array. Ensure at least 2 dimensions
    Rname = "rainfall accumulations (R)"
    R = validate.array(R, Rname, dtype=real)
    if len(R.shape) == 1:
        R = R.reshape(-1, 1)

    # Durations should be a vector that is broadcastable along the second dimension
    durations = validate.vector(durations, "durations", dtype=real)
    if durations.size not in [1, R.shape[1]]:
        raise ShapeError(
            f"The length of the durations vector must either be 1, or the number "
            f"of elements along the second dimension of R ({R.shape[1]})."
        )

    # Shape durations for broadcasting and convert accumulations
    shape = np.ones(len(R.shape), int)
    shape[1] = durations.size
    durations = durations.reshape(shape)
    return R * 60 / durations
