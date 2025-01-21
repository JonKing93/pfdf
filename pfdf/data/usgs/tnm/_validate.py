"""
Functions to validate TNM query parameters
----------
Paging:
    count           - Checks an input is a countable integer
    upper_bound     - Checks an input is an upper bound for a countable value
    max             - Checks input represents a maximum number of products
    max_per_query   - Checks input represents the maximum number of products per query

Hydrologic data:
    huc             - Checks input represents a HUC code
    huc48           - Checks input represents a HUC4 or HUC8 code
    nhd_format      - Checks input is a valid NHD file format
"""

from __future__ import annotations

import typing
from math import inf
from string import digits

import pfdf._validate.core as validate
from pfdf._utils import real

if typing.TYPE_CHECKING:
    from typing import Any


#####
# Paging parameters
#####


def count(N: Any, name: str, *, max: float = inf, allow_zero: bool = False) -> int:
    "Checks an input is countable integer"

    # Scalar positive integer
    N = validate.scalar(N, name, dtype=real)
    validate.integers(N, name)
    validate.positive(N, name, allow_zero=allow_zero)
    N = int(N)

    # Optionally enforce upper bound
    if N > max:
        raise ValueError(
            f"{name} cannot be greater than {max}, but the current value ({N}) is not"
        )
    return N


def upper_bound(N: Any, name: str) -> float | int:
    "Checks an input represent an upper bound on a countable value"
    if N is None:
        return inf
    else:
        return count(N, name)


def max(max: Any, name: str) -> int:
    return count(max, name, max=1000)


def max_per_query(max_per_query) -> int:
    max_per_query = max(max_per_query, "max_per_query")
    if max_per_query % 5 != 0:
        raise ValueError(
            f"max_per_query must be a multiple of 5, "
            f"but the input value ({max_per_query}) is not"
        )
    return max_per_query


#####
# Hydrologic data
#####


def huc(huc: Any) -> tuple[str, str]:
    "Validates a HUC code and returns the type of HUC"

    # Must be an ASCII numeric string with 2, 4, or 8 digits
    validate.string(huc, "huc")
    ndigits = len(huc)
    if ndigits not in [2, 4, 8]:
        raise ValueError(
            f"huc must have either 2, 4, or 8 digits, "
            f"but the input huc has {ndigits} characters instead"
        )
    elif any(char not in digits for char in huc):
        raise ValueError(
            "huc may only contain digits from 0 to 9, "
            "but the input huc includes other characters"
        )

    # Parse the HUC's polygon type
    huc_type = f"huc{ndigits}"
    return huc, huc_type


def huc48(huc_: Any) -> tuple[str, str]:
    "Checks an input is either an HU-4 or HU-8 code"

    huc_, huc_type = huc(huc_)
    if huc_type == "huc2":
        raise ValueError(
            "huc must be an HU-4 or HU-8 code. This command does not support HU-2."
        )
    return huc_, huc_type


def nhd_format(format: Any) -> str:
    "Checks an input is a valid NHD file format"

    # Case-insensitive validation
    allowed = ["shapefile", "geopackage", "filegdb"]
    format = validate.option(format, "format", allowed)

    # Get case-sensitive URL parameter
    if format == "shapefile":
        return "Shapefile"
    elif format == "geopackage":
        return "GeoPackage"
    elif format == "filegdb":
        return "FileGDB"
