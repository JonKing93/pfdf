"""
Misc validation functions
----------
Functions:
    raster      - Checks an input raster has metadata matching the flow raster
    nprocess    - Validates the number of parallel processes for locating basins
"""

from multiprocessing import cpu_count
from typing import Any

import pfdf._validate as validate
from pfdf._utils import real
from pfdf.raster import Raster


def raster(segments, raster: Any, name: str) -> Raster:
    "Checks that an input raster has metadata matching the flow raster"
    return segments.flow.validate(raster, name)


def nprocess(nprocess: Any) -> int:
    "Validates the number of parallel processes"

    if nprocess is None:
        return max(1, cpu_count() - 1)
    else:
        nprocess = validate.scalar(nprocess, "nprocess", dtype=real)
        validate.positive(nprocess, "nprocess")
        validate.integers(nprocess, "nprocess")
        return int(nprocess)
