"""
Functions that help clip a raster's data array
----------
This module contains functions that help clip a raster's data array to new spatial
bounds. The main entry point is the "values" function. Everything else is internal.
----------
Functions:
    values      - Returns a clipped data array for a raster
    _interior   - Clips an array to an interior subset, returning a view of the base array
    _exterior   - Clips an array outside of its original bounds returning a new base array
    _indices    - Returns the indices of retained pixels in the current and clipped arrays
"""

from __future__ import annotations

import typing

import numpy as np

from pfdf._utils import merror
from pfdf.errors import MissingNoDataError

if typing.TYPE_CHECKING:
    from pfdf.raster import RasterMetadata
    from pfdf.typing.core import MatrixArray, VectorArray

    limits = tuple[int, int]


def values(
    values: MatrixArray,
    metadata: RasterMetadata,
    rows: limits,
    cols: limits,
) -> MatrixArray:
    "Returns the data array for a clipped raster"

    height, width = values.shape
    if min(rows) >= 0 and max(rows) <= height and min(cols) >= 0 and max(cols) <= width:
        return _interior(values, rows, cols)
    else:
        return _exterior(values, metadata, rows, cols)


def _interior(values: MatrixArray, rows: limits, cols: limits) -> MatrixArray:
    """Clips a raster to bounds completely within the current bounds
    Uses a view of the current base array."""

    rows = slice(*rows)
    cols = slice(*cols)
    return values[rows, cols]


def _exterior(
    values: MatrixArray,
    metadata: RasterMetadata,
    rows: limits,
    cols: limits,
) -> MatrixArray:
    """Clips a raster to an area at least partially outside its current bounds.
    Creates a new base array and requires a NoData value"""

    # Require a Nodata value
    if metadata.nodata is None:
        raise MissingNoDataError(
            f"Cannot clip {metadata.name} because it does not have a NoData value, and "
            "the clipping bounds are outside the raster's current bounds. See the "
            '"ensure_nodata" command to provide a NoData value for the raster.'
        )

    # Preallocate a new base array
    try:
        clipped = np.full(metadata.shape, metadata.nodata, dtype=metadata.dtype)
    except Exception as error:
        message = (
            f"Cannot clip {metadata.name} because the clipped raster is too large for "
            "memory. Try clipping to a smaller bounding box."
        )
        merror.supplement(error, message)

    # Get the complete set of indices for the final clipped array
    crows = np.arange(0, metadata.nrows)
    ccols = np.arange(0, metadata.ncols)

    # Get the same indices, but in the indexing scheme of the source array.
    srows = np.arange(*rows)
    scols = np.arange(*cols)

    # Limit indices to real pixels, then copy pixels between arrays
    height, width = values.shape
    srows, crows = _indices(srows, crows, height)
    scols, ccols = _indices(scols, ccols, width)
    clipped[crows, ccols] = values[srows, scols]
    return clipped


def _indices(current: VectorArray, clipped: VectorArray, nmax: int) -> limits:
    """
    Returns the indices of retained pixels in the current and clipped arrays
    ----------
    current: Indices of complete clipped raster within source array
    clipped: Indices of complete clipped raster within clipped array
    nmax: The length of the dimension in the source array
    """

    # Limit the indices to those that correspond to pixels in the current raster
    keep = (current >= 0) & (current < nmax)
    current = current[keep]
    clipped = clipped[keep]

    # Convert to slices. Use empty slice if there is no overlap
    if current.size == 0:
        current = slice(0, 0)
        clipped = current
    else:
        current = slice(current[0], current[-1] + 1)
        clipped = slice(clipped[0], clipped[-1] + 1)
    return current, clipped
