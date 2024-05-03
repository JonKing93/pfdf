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

import numpy as np
import rasterio.transform
from affine import Affine

from pfdf.errors import MissingNoDataError
from pfdf.projection import BoundingBox
from pfdf.typing import MatrixArray, ScalarArray, VectorArray

limits = tuple[int, int]


def values(
    values: MatrixArray, bounds: BoundingBox, affine: Affine, nodata: ScalarArray
) -> MatrixArray:
    "Returns the data array for a clipped raster"

    # Get the indices of the clipped array
    rows, cols = rasterio.transform.rowcol(affine, bounds.xs, bounds.ys, op=round)

    # Clip to a view (interior) or filled array (exterior) as needed
    height, width = values.shape
    if rows[1] >= 0 and rows[0] <= height and cols[0] >= 0 and cols[1] <= width:
        return _interior(values, rows, cols)
    else:
        return _exterior(values, rows, cols, nodata)


def _interior(values: MatrixArray, rows: limits, cols: limits) -> MatrixArray:
    """Clips a raster to bounds completely within the current bounds
    Uses a view of the current base array."""

    rows = slice(rows[1], rows[0])
    cols = slice(cols[0], cols[1])
    return values[rows, cols]


def _exterior(
    values: MatrixArray, rows: limits, cols: limits, nodata: ScalarArray | None
) -> MatrixArray:
    """Clips a raster to an area at least partially outside its current bounds.
    Creates a new base array and requires a NoData value"""

    # Require a Nodata value
    if nodata is None:
        raise MissingNoDataError("You must provide a NoData value to clip")

    # Preallocate a new base array
    nrows = rows[0] - rows[1]
    ncols = cols[1] - cols[0]
    clipped = np.full((nrows, ncols), nodata, dtype=nodata.dtype)

    # Get the complete set of indices for the final clipped array
    crows = np.arange(0, nrows)
    ccols = np.arange(0, ncols)

    # Get the same indices, but in the indexing scheme of the source array.
    srows = np.arange(rows[1], rows[0])
    scols = np.arange(cols[0], cols[1])

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
