"""
severity  Functions that estimate and locate burn severity
----------

"""

import numpy as np
from dfha import validate
from dfha.utils import real, save_raster
from dfha.typing import Raster, OutputRaster, DNBRThresholds, Pathlike, scalar


# Reports the BARC4 classification scheme used in the module.
classification = {
    0: "nodata",
    1: "unburned",
    2: "low",
    3: "moderate",
    4: "high",
}


def estimate(
    dNBR: Raster,
    thresholds: DNBRThresholds = [125, 250, 500],
    *,
    path: Pathlike,
    overwrite: bool,
    nodata: scalar,
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

    NoData pixels are set to 0. Returns a numpy 2D array holding the estimated
    BARC4 burn severity raster.

    estimate(dNBR, thresholds)
    Specifies the dNBR thresholds to use to distinguish between burn severity
    classes. The "thresholds" input should have 3 elements. In order, these should
    be the thresholds between (1) unburned and low severity, (2) low and moderate
    severity, and (3) moderate and high severity. Each threshold defines the
    upper bound (exclusive) of the less-burned class, and the lower bound (inclusive)
    of the more-burned class. The thresholds must be increasing order.

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
    thresholds = validate.vector(thresholds, "thresholds", dtype=real, length=3)
    _validate_thresholds(thresholds)
    dNBR, nodata = validate.raster(dNBR, "dNBR", numpy_nodata=nodata, nodata_to=np.nan, return_mask=True)
    path, save = validate.output_path(path, overwrite)

    # Build the burn severity
    severity = np.empty(dNBR.shape, dtype="int8")
    severity[nodata] = 0
    severity[dNBR < thresholds[0]] = 1
    _classify(severity, dNBR, thresholds[0:2], 2)
    _classify(severity, dNBR, thresholds[1:3], 3)
    severity[dNBR > thresholds[2]] = 4

    # Optionally save
    if save:
        save_raster(severity, path, nodata=0)
        return path
    else:
        return severity


def _validate_thresholds(thresholds):
    "Checks that dNBR thresholds are sorted and not NaN"
    if any(thresholds == np.nan):
        bad = np.nonzero(thresholds == np.nan)[0]
        raise ValueError("dNBR thresholds cannot be NaN, but threshold {bad} is NaN.")

    names = ["unburned-low", "low-moderate", "moderate-high"]
    _compare(thresholds[0:2], names[0:2])
    _compare(thresholds[1:], names[1:])


def _compare(thresholds, names):
    "Checks that the second threshold is >= the first threshold"
    if thresholds[1] < thresholds[0]:
        raise ValueError(
            f"The {names[1]} threshold ({thresholds[1]}) is less than the {names[0]} threshold ({thresholds[0]})."
        )


def _classify(severity, dNBR, thresholds, value):
    "Locates a severity class using 2 thresholds"
    severity[dNBR >= thresholds[0] & dNBR < thresholds[1]] = value
