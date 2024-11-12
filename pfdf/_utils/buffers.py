"""
Function to standardize buffer units
----------
Functions:
    buffers_to_base - Converts a dict of edge buffers from units to axis base units
"""

from __future__ import annotations

import typing

from pfdf.projection.crs import units_to_base

if typing.TYPE_CHECKING:
    from pfdf.typing.core import Units


def buffers_to_base(obj, buffers: dict[str, float], units: Units) -> dict[str, float]:
    "Converts a dict of edge buffers from units to axis base units"
    _, y = obj.center
    output = {}
    for edge in buffers:
        axis = "x" if edge in ["left", "right"] else "y"
        value = units_to_base(obj.crs, axis, buffers[edge], units, y)[0]
        output[edge] = value
    return output
