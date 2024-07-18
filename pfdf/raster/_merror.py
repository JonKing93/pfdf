"""
Functions that handle and supplement memory errors
----------
Certain raster operations can produce memory-related errors. This typically occurs
when a very large raster is requested as an array output. These types of errors
are typically issued by numpy, and are usually rather unclear about what is
actually happening. As such, it can be difficult for users to parse these errors
and determine a suitable fix. This module provides functions that supplement
these errors to provide more user-oriented information.
----------
Functions:
    supplement  - Adds supplementary info to memory-related errors
    features    - Supplements memory errors caused by converting features to rasters
"""

from typing import NoReturn


def features(error: Exception, geometry: str) -> NoReturn:
    "Handles memory errors caused by converting features to rasters"
    message = (
        f"Cannot create the {geometry} raster because the requested array is "
        f"too large for your computer's memory. Try increasing the "
        f'"resolution" input to a coarser resolution, or use the "bounds" '
        f"option to load a smaller subset of {geometry} data."
    )
    supplement(error, message)


def supplement(error: Exception, message: str) -> NoReturn:
    "Detect and supplement memory-related errors"

    # Detect whether this is a memory issue
    ismemory = False
    if isinstance(error, MemoryError):
        ismemory = True
    elif isinstance(error, ValueError):
        for pattern in ["Maximum allowed dimension exceeded", "array is too big"]:
            if pattern in error.args[0]:
                ismemory = True

    # Supplement memory issues, reraise anything else
    if ismemory:
        raise MemoryError(message) from error
    else:
        raise error from None
