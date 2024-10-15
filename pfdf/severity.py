"""
Functions that estimate and locate burn severity
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

Internal:
    _validate_descriptions  - Checks that burn severity descriptions are recognized
"""

from typing import Any

import numpy as np

import pfdf._validate.core as validate
from pfdf._utils import aslist, real
from pfdf._utils.classify import classify
from pfdf.raster import Raster
from pfdf.typing.core import strs, vector
from pfdf.typing.raster import RasterInput

# Type hints
Thresholds = tuple[float, float, float] | vector

# The classification scheme used in the module
_classification = {
    "unburned": 1,
    "low": 2,
    "moderate": 3,
    "high": 4,
    "burned": [2, 3, 4],
}


#####
# User Functions
#####


def classification() -> dict[str, int | list[int]]:
    """
    classification  Returns the BARC4 burn severity classification scheme
    ----------
    classification()
    Returns a dict reporting the BARC4 burn severity classification scheme used
    by the module. Keys are the strings "unburned", "low", "moderate", "high", and
    "burned". Values are the integers associated with each burn severity level in
    the classification scheme.
    ----------
    Outputs:
        dict[str, int | list[int]]: Maps burn severity levels to their integers
            in the classification scheme
    """
    return _classification


def mask(severity: RasterInput, descriptions: strs) -> Raster:
    """
    mask  Generates a burn severity mask
    ----------
    mask(severity, descriptions)
    Given a burn severity raster, locates pixels that match any of the specified
    burn severity levels. Returns a Raster holding the mask of matching
    pixels. Pixels that match one of the specified burn severities will have a
    value of 1. All other pixels will be 0.

    Note that the burn severity descriptions are strings describing the appropriate
    burn severity levels. The supported strings are: "unburned", "burned", "low",
    "moderate", and "high".
    ----------
    Inputs:
        severity: A BARC4-like burn severity raster.
        descriptions: A list of strings indicating the burn severity levels that
            should be set as True in the returned mask

    Outputs:
        Raster: The burn severity mask
    """

    # Validate
    descriptions = _validate_descriptions(descriptions)
    severity = Raster(severity, "burn severity raster")

    # Get the integers of the queried severity levels
    classes = [
        aslist(classes)
        for description, classes in _classification.items()
        if description in descriptions
    ]
    classes = sum(classes, [])  # Concatenates lists, is not summing integers

    # Return the severity mask
    mask = np.isin(severity.values, classes)
    return Raster.from_array(
        mask, nodata=False, crs=severity.crs, transform=severity.transform, copy=False
    )


def estimate(raster: RasterInput, thresholds: Thresholds = [125, 250, 500]) -> Raster:
    """
    estimate  Estimates a BARC4-like burn severity raster from dNBR, BARC256, or other burn-severity measure
    ----------
    estimate(raster)
    Estimates a BARC4 burn severity from a raster assumed to be (raw dNBR * 1000).
    (See the following syntax if you instead have raw dNBR, BARC256, or another
    burn-severity measure). This process classifies the burn severity of each
    raster pixel using an integer from 1 to 4. The classification scheme is as follows:

        Classification - Interpretation: dNBR Range
        1 - unburned:  [-Inf, 125]
        2 - low:       ( 125, 250]
        3 - moderate:  ( 250, 500]
        4 - high:      ( 500, Inf]

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
    upper bound (inclusive) of the less-burned class, and the lower bound (exclusive)
    of the more-burned class. The thresholds must be in increasing order.
    ----------
    Inputs:
        raster: A raster holding the data used to classify burn severity
        thresholds: The 3 thresholds to use to distinguish between burn severity classes

    Outputs:
        Raster: The BARC4 burn severity estimate
    """

    # Validate
    thresholds = validate.vector(thresholds, "thresholds", dtype=real, length=3)
    validate.defined(thresholds, "thresholds")
    validate.sorted(thresholds, "thresholds")
    raster = Raster(raster, "input raster")

    # Get the burn severity classes and return as raster
    severity = classify(raster.values, thresholds, nodata=raster.nodata, nodata_to=0)
    severity = severity.astype("int8", copy=False)
    return Raster.from_array(
        severity, nodata=0, crs=raster.crs, transform=raster.transform, copy=False
    )


#####
# Utilities
#####
def _validate_descriptions(descriptions: Any) -> set[str]:
    "Checks that burn severity descriptions are recognized"

    descriptions = aslist(descriptions)
    allowed = tuple(_classification.keys())
    for d, description in enumerate(descriptions):
        name = f"descriptions[{d}] ({description})"
        descriptions[d] = validate.option(description, name, allowed)
    return set(descriptions)
