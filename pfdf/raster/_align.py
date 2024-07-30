"""
Functions to determine alignment of a reprojected raster
----------
Functions:
    reprojection    - Computes Transform and shape of an aligned reprojection
    _edge           - Locates an aligned edge
    _npixels        - Computes the number of pixels along an aligned axis
"""

from math import ceil, floor

import rasterio.warp

from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.typing import shape2d


def reprojection(
    src_crs: CRS, dst_crs: CRS, bounds: BoundingBox, transform: Transform
) -> tuple[Transform, shape2d]:
    """
    Computes transform and shape for aligned reprojection
    ----------
    src_crs: The current CRS
    dst_crs: The CRS of the reprojected dataset
    bounds: The raster's bounds in the source CRS
    transform: The template transform for the reprojection
    """

    # Reproject the bounding box, then orient to match the template transform
    bounds = rasterio.warp.transform_bounds(src_crs, dst_crs, *bounds.bounds)
    bounds = BoundingBox.from_list(bounds)
    bounds = bounds.orient(transform.orientation)

    # Build an affine transform with aligned top-left corner
    dx, dy = transform.dx(), transform.dy()
    left = _edge(dx, transform.left, bounds.left)
    top = _edge(dy, transform.top, bounds.top)
    transform = Transform(dx, dy, left, top)

    # Compute the shape of the realigned raster
    nrows = _npixels(top, bounds.bottom, transform.yres())
    ncols = _npixels(left, bounds.right, transform.xres())
    shape = (nrows, ncols)
    return transform, shape


def _edge(delta: float, transform_edge: float, data_edge: float) -> float:
    """
    Locates an aligned edge. This is an edge an integer number of pixels from
    the transform's edge that completely contains the raster's data values
    """

    distance = data_edge - transform_edge
    npixels = floor(distance / delta)
    return transform_edge + npixels * delta


def _npixels(edge1: float, edge2: float, resolution: float) -> int:
    "Computes the number of pixels along an aligned axis"

    distance = abs(edge1 - edge2)
    return ceil(distance / resolution)
