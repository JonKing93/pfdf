"""
severity  Functions that estimate and locate burn severity
----------
The severity module is used to generate and work with rasters that record a
BARC4-like soil burn severity. The BARC4 classification is as follows:

    1 - Unburned
    2 - Low burn severity
    3 - Moderate burn severity
    4 - High burn severity

This module has two main functions: "mask" and "estimate" (see below for details).

Burn severity rasters are typically used to derive data masks used to
implement various parts of a hazard assessment. For example, the burned pixel
mask used to delineate a stream network, or the high-moderate burn mask used to
implement the M1, M2, and M3 models from Staley et al., 2017. Users can use the
"mask" function to generate these masks from a BARC4-like burn severity raster.
Note that "mask" function searches for burn-severity levels by name, and users
can inspect the supported names using the "classification" function.

We recommend using field-verified BARC4-like burn severity data when possible, 
but these maps are not always available. If this is the case, users can use the 
"estimate" function to estimate a BARC4-like burn severity raster from dNBR,
BARC256, or other burn severity measure.
----------
User Functions:
    mask                    - Returns a mask of the specified burn severities
    estimate                - Estimates burn severity from dNBR, BARC256, or burn-severity measure
    classification          - Returns a dict with the BARC4 classification scheme

Private:
    _validate_thresholds    - Checks that severity level thresholds are valid
    _validate_descriptions  - Checks that burn severity descriptions are recognized
    _compare                - Compares two severity-level thresholds
    _classify               - Locates a burn severity class using two thresholds 
"""

from typing import Any, Dict, Optional, Set

import numpy as np

from pfdf import _nodata as nodata
from pfdf import _validate as validate
from pfdf._rasters import Raster
from pfdf._utils import astuple, real
from pfdf.rasters import RasterOutput, RasterInput
from pfdf.typing import (
    Pathlike,
    RasterArray,
    ThresholdArray,
    Thresholds,
    VectorArray,
    strs,
)

# The classification scheme used in the module
_classification = {
    1: "unburned",
    2: "low",
    3: "moderate",
    4: "high",
}


#####
# User Functions
#####


def classification() -> Dict[int, str]:
    """
    classification  Returns the BARC4 burn severity classification scheme
    ----------
    classification()
    Returns a dict reporting the BARC4 burn severity classification scheme used
    by the module. Keys are the integers in the classification scheme. Each value
    is a string describing the burn severity associated with the class.
    ----------
    Outputs:
        Dict[int, str]: Maps the burn severity classification integers to their
            descriptions.
    """
    return _classification


def mask(
    severity: RasterInput,
    descriptions: strs,
    *,
    path: Optional[Pathlike] = None,
    overwrite: bool = False,
) -> RasterOutput:
    """
    mask  Generates a burn severity mask
    ----------
    mask(severity, descriptions)
    Given a burn severity raster, locates pixels that match any of the specified
    burn severity levels. Returns a Raster holding the mask of matching
    pixels. Pixels that match one of the specified burn severities will have a
    value of 1. All other pixels will be 0.

    Note that the burn severity descriptions are strings describing the appropriate
    burn severity levels. The supported strings are: "unburned", "low", "moderate",
    and "high".

    mask(..., *, path)
    mask(..., *, path, overwrite)
    Saves the burn severity mask to the indicated file. Returns the Path to the
    saved raster rather than a Raster. Set overwrite=True to allow the
    output to overwrite an existing file. Otherwise, raises a FileExistsError
    if the file already exists.
    ----------
    Inputs:
        severity: A BARC4-like burn severity raster.
        descriptions: A list of strings indicating the burn severity levels that
            should be set as True in the returned mask
        path: A path for a saved burned severity mask
        overwrite: True to allow saved output to replace existing files. Set to
            False (default) to prevent replacement.

    Outputs:
        Raster | pathlib.Path: The burn severity mask
    """

    # Validate inputs
    descriptions = _validate_descriptions(descriptions)
    path = validate.output_path(path, overwrite)
    severity = Raster.validate(severity, "burn severity raster")

    # Get the queried classes and return the severity mask
    classes = [
        number
        for number, description in _classification.items()
        if description in descriptions
    ]
    mask = np.isin(severity.values, classes)
    return Raster.output(mask, path)


def estimate(
    raster: RasterInput,
    thresholds: Thresholds = [125, 250, 500],
    *,
    path: Optional[Pathlike] = None,
    overwrite: bool = False,
) -> RasterOutput:
    """
    estimate  Estimates a BARC4-like burn severity raster from dNBR, BARC256, or other burn-severity measure
    ----------
    estimate(raster)
    Estimates a BARC4 burn severity from a raster assumed to be (raw dNBR * 1000).
    (See the following syntax if you instead have raw dNBR, BARC256, or another
    burn-severity measure). This process classifies the burn severity of each
    raster pixel using an integer from 1 to 4. The classification scheme is as follows:

        Classification - Interpretation: dNBR Range
        1 - unburned:  [-Inf, 125)
        2 - low:       [ 125, 250)
        3 - moderate:  [ 250, 500)
        4 - high:      [ 500, Inf]

    NoData values are set to 0. Returns a Raster object holding the estimated
    BARC4 burn severity raster.

    estimate(raster, thresholds)
    Specifies the thresholds to use to distinguish between burn severity classes
    in the input raster. This syntax should be used whenever the input raster is
    not (raw dNBR * 1000), and also supports custom thresholds for the (raw dNBR * 1000)
    case. Note that the function does not check the intervals of raster values
    when thresholds are specified.

    The "thresholds" input should have 3 elements. In order, these should
    be the thresholds between (1) unburned and low severity, (2) low and moderate
    severity, and (3) moderate and high severity. Each threshold defines the
    upper bound (exclusive) of the less-burned class, and the lower bound (inclusive)
    of the more-burned class. The thresholds must be in increasing order.

    estimate(..., *, path)
    estimate(..., *, path, overwrite)
    Saves the estimated BARC4 severity to the indicated path. Returns the Path
    to the saved raster. By default, the function will raise an exception if the
    saved raster would replace an existing file. Set overwrite=True to allow
    saved output to replace files.
    ----------
    Inputs:
        dNBR: A raster holding dNBR data
        thresholds: The 3 thresholds to use to distinguish between burn severity classes
        path: A file in which to save the estimated BARC4 burn severity.
        overwrite: True to allow saved burn severities to replace existing files.
            False to prevent replacement.

    Outputs:
        Raster | pathlib.Path: The BARC4 burn severity estimate or the
            Path to a saved estimate.
    """

    # Validate inputs
    thresholds = _validate_thresholds(thresholds)
    path = validate.output_path(path, overwrite)
    raster = Raster.validate(raster, "input raster")

    # Preallocate. Get nodata mask
    severity = np.empty(raster.shape, dtype="int8")
    nodatas = nodata.mask(raster.values, raster.nodata)
    raster = raster.values

    # Get the burn severity classes
    severity[raster < thresholds[0]] = 1
    _classify(severity, raster, thresholds[0:2], 2)
    _classify(severity, raster, thresholds[1:3], 3)
    severity[raster >= thresholds[2]] = 4

    # Fill NoData
    if nodatas is not None:
        severity[nodatas] = 0
    return Raster.output(severity, path, nodata=0)


#####
# Utilities
#####


def _validate_descriptions(descriptions: Any) -> Set[str]:
    "Checks that burn severity descriptions are recognized"
    descriptions = astuple(descriptions)
    allowed = tuple(_classification.values())
    for d, description in enumerate(descriptions):
        if not isinstance(description, str):
            raise TypeError("Description {d} is not a string.")
        elif description not in allowed:
            allowed = ", ".join(allowed)
            raise ValueError(
                f"Description {d} ({description}) is not a recognized burn severity level. "
                f"Recognized values are: {allowed}"
            )
    return set(descriptions)


def _validate_thresholds(thresholds: Any) -> ThresholdArray:
    "Checks that thresholds are sorted and not NaN"
    thresholds = validate.vector(thresholds, "thresholds", dtype=real, length=3)
    nans = np.isnan(thresholds)
    if np.any(nans):
        bad = np.argwhere(nans)[0]
        raise ValueError(f"thresholds cannot be NaN, but threshold {bad} is NaN.")
    names = ["unburned-low", "low-moderate", "moderate-high"]
    _compare(thresholds[0:2], names[0:2])
    _compare(thresholds[1:], names[1:])
    return thresholds


def _compare(thresholds: VectorArray, names: strs) -> None:
    "Checks that the second threshold is >= the first threshold"
    if thresholds[1] < thresholds[0]:
        raise ValueError(
            f"The {names[1]} threshold ({thresholds[1]}) is less than the {names[0]} threshold ({thresholds[0]})."
        )


def _classify(
    severity: RasterArray, raster: RasterArray, thresholds: ThresholdArray, value: int
) -> None:
    "Locates a severity class using 2 thresholds"
    mask = (raster >= thresholds[0]) & (raster < thresholds[1])
    severity[mask] = value
