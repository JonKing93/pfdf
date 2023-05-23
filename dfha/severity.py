"""
severity  Functions that estimate and locate burn severity
----------
The severity module is used to generate and work with rasters that report
BARC4-like burn severity. The BARC4 classification is as follows:

    1 - Unburned
    2 - Low burn severity
    3 - Moderate burn severity
    4 - High burn severity

These burn severity rasters are typically used to derive data masks used to
implement various parts of a hazard assessment. For example, the burned pixel
mask used to delineate a stream network, or the high-moderate burn mask used to
implement the M1, M2, and M3 models from Staley et al., 2017. Users can use the
"locate" function to generate these masks from a burn severity raster.

We recommend using official BARC4 data when possible, but these maps are not
always available. If this is the case, users can use the "estimate" function
to estimate a burn severity raster from dNBR.
----------
User Functions:
    locate                  - Builds a burn severity mask
    estimate                - Estimates burn severity from dNBR
    classification          - Returns a dict with the BARC4 classification scheme

Private:
    _validate_thresholds    - Checks that dNBR thresholds are valid
    _validate_descriptions  - Checks that burn severity descriptions are recognized
    _compare                - Compares two dNBR thresholds
    _classify               - Locates a burn severity class using two thresholds 
"""

import numpy as np
from dfha import validate
from dfha.utils import real, save_raster, nodata_mask, astuple
from typing import Dict, Optional, Set, Any
from dfha.typing import (
    Raster,
    RasterArray,
    OutputRaster,
    Pathlike,
    scalar,
    strs,
    Thresholds,
    ThresholdArray,
    VectorArray,
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


def locate(
    severity: Raster,
    descriptions: strs,
    *,
    path: Optional[Pathlike] = None,
    overwrite: bool = False,
) -> OutputRaster:
    """
    locate  Generates a burn severity mask
    ----------
    locate(severity, descriptions)
    Given a burn severity raster, locates pixels that match any of the specified
    burn severity levels. Returns a numpy 2D array holding the mask of matching
    pixels. Pixels that match one of the specified burn severities will have a
    value of 1. All other pixels will be 0.

    locate(..., *, path)
    locate(..., *, path, overwrite)
    Saves the burn severity mask to the indicated file. Returns the Path to the
    saved raster. Set overwrite=True to allow the output to overwrite an existing
    file. Otherwise, raises a FileExistsError if the file already exists.
    ----------
    Inputs:
        severity: A BARC4 style burn severity raster.
        descriptions: A list of strings indicating the burn severity levels that
            should be set as True in the returned mask
        path: A path for a saved burned severity mask
        overwrite: True to allow saved output to replace existing files. Set to
            False (default) to prevent replacement.

    Outputs:
        numpy 2D bool array | pathlib.Path: The burn severity mask or Path to
            a saved mask.
    """

    # Validate inputs
    descriptions = _validate_descriptions(descriptions)
    if path is not None:
        path = validate.output_path(path, overwrite)
    severity, _ = validate.raster(severity, "burn severity raster")

    # Get the queried classes and build the severity mask
    classes = [
        number
        for number, description in _classification.items()
        if description in descriptions
    ]
    mask = np.isin(severity, classes)

    # Optionally save. Return the mask
    if path is not None:
        mask = save_raster(mask, path)
    return mask


def estimate(
    dNBR: Raster,
    thresholds: Thresholds = [125, 250, 500],
    *,
    path: Optional[Pathlike] = None,
    overwrite: bool = False,
    nodata: Optional[scalar] = None,
) -> OutputRaster:
    """
    estimate  Estimates BARC4 burn severity raster from a dNBR raster
    ----------
    estimate(dNBR)
    Estimates a BARC4 burn severity from a dNBR raster. This process classifies
    the burn severity of each raster pixel using an integer from 1 to 4.
    The classification scheme is as follows:

        Classification - Interpretation: dNBR Range
        1 - unburned:  [-Inf, 125)
        2 - low:       [ 125, 250)
        3 - moderate:  [ 250, 500)
        4 - high:      [ 500, Inf]

    NoData values are set to 0. Returns a numpy 2D array holding the estimated
    BARC4 burn severity raster.

    estimate(dNBR, thresholds)
    Specifies the dNBR thresholds to use to distinguish between burn severity
    classes. The "thresholds" input should have 3 elements. In order, these should
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

    estimate(..., *, nodata)
    Specifies a dNBR nodata value when dNBR is provided as a numpy array.
    If dNBR is a file-based raster, then this option is ignored and NoData values
    are instead determined from the file metadata.
    ----------
    Inputs:
        dNBR: A raster holding dNBR data
        thresholds: The 3 thresholds to use to distinguish between burn severity classes
        path: A file in which to save the estimated BARC4 burn severity.
        overwrite: True to allow saved burn severities to replace existing files.
            False to prevent replacement.
        nodata: Indicates the dNBR NoData value for when dNBR is a numpy array.

    Outputs:
        numpy 2D array | pathlib.Path: The BARC4 burn severity estimate or the
            Path to a saved estimate.
    """

    # Validate inputs
    thresholds = _validate_thresholds(thresholds)
    if path is not None:
        path = validate.output_path(path, overwrite)
    dNBR, nodata = validate.raster(dNBR, "dNBR", numpy_nodata=nodata)

    # Preallocate. Fill NoData values
    severity = np.empty(dNBR.shape, dtype="int8")
    nodata = nodata_mask(dNBR, nodata)
    severity[nodata] = 0

    # Get the burn severity classes
    severity[dNBR < thresholds[0]] = 1
    _classify(severity, dNBR, thresholds[0:2], 2)
    _classify(severity, dNBR, thresholds[1:3], 3)
    severity[dNBR > thresholds[2]] = 4

    # Return raster. Optionally save
    if path is None:
        return severity
    else:
        return save_raster(severity, path, nodata=0)


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
    "Checks that dNBR thresholds are sorted and not NaN"
    thresholds = validate.vector(thresholds, "thresholds", dtype=real, length=3)
    if any(thresholds == np.nan):
        bad = np.nonzero(thresholds == np.nan)[0]
        raise ValueError(f"dNBR thresholds cannot be NaN, but threshold {bad} is NaN.")
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
    severity: RasterArray, dNBR: RasterArray, thresholds: ThresholdArray, value: int
) -> None:
    "Locates a severity class using 2 thresholds"
    severity[dNBR >= thresholds[0] & dNBR < thresholds[1]] = value
