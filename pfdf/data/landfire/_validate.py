"""
Functions that validate LFPS query parameters
----------
Functions:
    layer           - Checks an input represents a single data layer
    job_time        - Ensures a timing parameter is a number greater than 15
    max_job_time    - Checks an input represents the maximum job time
    refresh_rate    - Checks an input represents a refresh rate
"""

from __future__ import annotations

import typing
from math import inf

import pfdf._validate.core as validate
from pfdf._utils import real

if typing.TYPE_CHECKING:
    from typing import Any


def layer(layer: Any) -> str:
    "Checks an input represents a single data layer"

    layer = validate.string(layer, "layer")
    if ";" in layer:
        raise ValueError("layer cannot contain semicolons (;)")
    return layer


def job_time(time: Any, name: str) -> float:
    "Ensures a job querying parameter is a float >= 15 (seconds)"
    time = validate.scalar(time, name, dtype=real)
    validate.inrange(time, name, min=15)
    return float(time)


def max_job_time(time: Any) -> float:
    if time is None:
        return inf
    else:
        return job_time(time, "max_job_time")


def refresh_rate(time: Any) -> float:
    time = job_time(time, "refresh_rate")
    if time > 3600:
        raise ValueError("refresh_rate cannot be greater than 3600 seconds (1 hour)")
    return time
