"""
Functions that validate inputs used for preprocessing
----------
Functions:
    resampling  - Validates a resampling option
    data_bound  - Checks that a data bound is castable, or provides a default if missing
"""

from typing import Any, Literal

import numpy as np
from rasterio.enums import Resampling

import pfdf._validate as validate
from pfdf._utils import real
from pfdf.raster._validate._metadata import casting
from pfdf.typing import ScalarArray


def resampling(resampling) -> str:
    "Validates a requested resampling option"

    allowed = [method.name for method in Resampling]
    allowed.remove("gauss")
    method = validate.option(resampling, "resampling", allowed)
    return getattr(Resampling, method)


def data_bound(value: Any, bound: Literal["min", "max"], dtype: type) -> ScalarArray:
    """Checks that a user provided data bound is castable to the raster dtype.
    If no bound is provided, provides a default value."""

    # Get default bounds. Bool default is True or False
    if value is None:
        if dtype == bool:
            return bound == "max"

        # Integer default is the min/max value representable in the dtype
        elif np.issubdtype(dtype, np.integer):
            info = np.iinfo(dtype)
            return getattr(info, bound)

        # Floating default is -inf/inf
        elif bound == "min":
            return -np.inf
        else:
            return np.inf

    # Otherwise, validate user values
    else:
        value = validate.scalar(value, bound, dtype=real)
        value = casting(value, bound, dtype, "safe")
        return value
