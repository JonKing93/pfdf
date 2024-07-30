"""
Functions that compute update attributes for a filtered network
----------
In-place updates:
    family          - Updates parent-child relationships in-place following segment removal
    indices         - Updates connectivity indices in-place following segment removal

Misc:
    segments        - Computes updated segment linestrings and pixel indices
    connectivity    - Computes updated child and parents
    basins          - Resets basins if terminal outlets were removed
"""

import numpy as np
import shapely

from pfdf.typing import (
    MatrixArray,
    NetworkIndices,
    RealArray,
    SegmentIndices,
    SegmentParents,
    SegmentValues,
    VectorArray,
)

#####
# In-place
#####


def family(
    child: SegmentValues, parents: SegmentParents, remove: SegmentIndices
) -> None:
    "Updates child-parent relationships in-place after segments are removed"

    indices = np.nonzero(remove)
    removed = np.isin(child, indices)
    child[removed] = -1
    removed = np.isin(parents, indices)
    parents[removed] = -1


def indices(family: RealArray, nremoved: VectorArray) -> None:
    "Updates connectivity indices in-place after segments are removed"

    adjust = family != -1
    indices = family[adjust]
    family[adjust] = indices - nremoved[indices]


#####
# Misc
#####


def segments(
    segments, remove: SegmentIndices
) -> tuple[list[shapely.LineString], NetworkIndices]:
    "Computes updated linestrings and pixel indices after segments are removed"

    # Initialize new attributes
    linestrings = segments.segments
    indices = segments.indices

    # Delete items from lists
    (removed,) = np.nonzero(remove)
    for k in reversed(removed):
        del linestrings[k]
        del indices[k]
    return linestrings, indices


def connectivity(
    segments, remove: SegmentIndices
) -> tuple[SegmentValues, SegmentParents]:
    "Computes updated child and parents after segments are removed"

    # Initialize new attributes
    child = segments._child.copy()
    parents = segments._parents.copy()

    # Limit arrays to retained segments
    keep = ~remove
    child = child[keep]
    parents = parents[keep]

    # Update connectivity relationships and reindex as necessary
    family(child, parents, remove)
    nremoved = np.cumsum(remove)
    indices(child, nremoved)
    indices(parents, nremoved)
    return child, parents


def basins(segments, remove: SegmentIndices) -> MatrixArray | None:
    "Resets basins if any terminal basin outlets were removed"

    # If there aren't any basins, just leave them as None
    if segments._basins is None:
        return None

    # Get the ids of the removed segments. Reset if any of the removed IDs
    # are in the raster. Otherwise, retain the old raster
    ids = segments.ids[remove]
    if np.any(np.isin(ids, segments._basins)):
        return None
    else:
        return segments._basins
