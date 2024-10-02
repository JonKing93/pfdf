"Function to build a raster windowing object"

import numpy as np
import rasterio
from rasterio.windows import Window

from pfdf._utils import limits
from pfdf.projection import BoundingBox, Transform, _crs


def build(
    file: rasterio.DatasetReader,
    bounds: BoundingBox,
) -> tuple[Window, Transform]:
    """
    Builds a rasterio Window object for loading a raster subset from file
    Also updates the CRS and transform as necessary.
    ----------
    file: The dataset reader for the dataset
    bounds: The bounds of the area to load
    """

    # Parse the CRS and affine transform
    crs = _crs.parse(file.crs, bounds.crs)
    if _crs.different(crs, bounds.crs):
        bounds = bounds.reproject(crs)
    affine = file.transform

    # Get pixel indices
    rows, cols = rasterio.transform.rowcol(affine, xs=bounds.xs, ys=bounds.ys, op=round)
    rows = np.array(rows).astype(int).tolist()
    cols = np.array(cols).astype(int).tolist()

    # Order from smallest to largest (easier to make slices)
    top, bottom = min(rows), max(rows)
    left, right = min(cols), max(cols)

    # Remove indices outside the dataset bounds. Build the window
    rows = limits(top, bottom, file.height)
    cols = limits(left, right, file.width)
    window = Window.from_slices(rows, cols)

    # Update the transform edges
    transform = Transform.from_affine(affine)
    dx, dy = transform.dx(), transform.dy()
    left = transform.left + dx * cols[0]
    top = transform.top + dy * rows[0]
    transform = Transform(dx, dy, left, top)
    return window, crs, transform
