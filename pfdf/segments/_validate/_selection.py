"""
Functions to validate inputs that select segments in a network
----------
Functions:
    _check_in_network   - Checks the input IDs are in the network
    id                  - Checks a scalar ID is valid and returns the linear index
    ids                 - Checks a set of IDs are a valid and returns the linear indices
    selection           - Checks a filtering selection is valid and returns boolean indices
"""

from __future__ import annotations

import typing

import numpy as np

import pfdf._validate.core as validate
from pfdf._utils import real

if typing.TYPE_CHECKING:
    from typing import Any

    from pfdf.typing.core import VectorArray
    from pfdf.typing.segments import BooleanIndices


def _check_in_network(segments, ids: VectorArray, name: str) -> None:
    "Checks that segment IDs are in the network"

    validate.integers(ids, name)
    for i, id in enumerate(ids):
        if id not in segments._ids:
            if name == "ids":
                name = f"{name}[{i}]"
            raise ValueError(
                f"{name} (value={id}) is not the ID of a segment in the network. "
                "See the '.ids' property for a list of current segment IDs."
            )


def id(segments, id: Any) -> int:
    "Checks that a segment ID is valid and returns index"
    id = validate.scalar(id, "id", dtype=real)
    id = id.reshape(1)
    _check_in_network(segments, id, "id")
    index = np.argwhere(segments._ids == id)
    return int(index[0, 0])


def ids(segments, ids: Any) -> VectorArray:
    """Checks that a set of segment IDs are valid and converts to linear
    indices. If no IDs are provided, returns all indices in the network"""

    # Select all indices if unspecified. Otherwise validate
    if ids is None:
        return np.arange(segments.size)

    # Validate
    ids = validate.vector(ids, "ids", dtype=real)
    _check_in_network(segments, ids, "ids")

    # Convert IDs to indices
    indices = np.empty(ids.shape, int)
    for k, id in enumerate(ids):
        indices[k] = np.argwhere(id == segments.ids)[0, 0]
    return indices


def selection(segments, selection: Any, type: Any) -> BooleanIndices:
    "Validates boolean indices or IDs and returns them as boolean indices"

    type = validate.option(type, "type", allowed=["indices", "ids"])
    name = f"selected segment {type}"
    if type == "indices":
        indices = validate.vector(selection, name, dtype=real, length=segments.size)
        return validate.boolean(indices, name)
    elif type == "ids":
        ids = validate.vector(selection, name, dtype=real)
        _check_in_network(segments, ids, name)
        return np.isin(segments._ids, ids)
