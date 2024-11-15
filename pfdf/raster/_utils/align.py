"""
Functions to determine alignment of a reprojected raster
----------
Functions:
    reprojection    - Computes Transform and shape of an aligned reprojection
    _edge           - Locates an aligned edge
    _npixels        - Computes the number of pixels along an aligned axis
"""

from __future__ import annotations

import typing
from math import ceil, floor

from pfdf.projection import BoundingBox, Transform

if typing.TYPE_CHECKING:
    from pfdf.raster import RasterMetadata
    from pfdf.typing.core import shape2d


def reprojection(
    bounds: BoundingBox, template: RasterMetadata
) -> tuple[Transform, shape2d]:
    "Computes the transform and shape for an aligned reprojection"

    # Get the current bounds in the template CRS and orientation. The reprojected
    # raster must fully contain these bounds
    bounds = bounds.match_crs(template.crs)
    bounds = bounds.orient(template.orientation)

    # Build the new transform. The new transform must align with the template --
    # i.e. the left and top edges must be an integer number of pixels away from the
    # template's left and top edges
    transform = template.transform
    dx, dy = transform.dx(), transform.dy()
    left = _edge(dx, transform.left, bounds.left)
    top = _edge(dy, transform.top, bounds.top)
    transform = Transform(dx, dy, left, top, template.crs)

    # Compute the new shape. Return updated metadata
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
