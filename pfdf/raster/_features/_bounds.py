"""
Functions used to determine the bounds of rasters built from vector features
----------
Functions:
    unbounded       - Returns a bounds dict for an unbounded spatial domain
    add_geometry    - Updates bounds in-place given a new geometry
    _from_point     - Returns bbox edges for a point feature
    _from_polygon   - Returns bbox edges for a polygon feature
"""

from __future__ import annotations

import typing
from math import inf

import numpy as np

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.projection import CRS
    from pfdf.typing.core import EdgeDict

    coords = list[tuple[float, float]]
    edges = tuple[float, float, float, float]
    bounds = dict[str, float]


def unbounded(crs: Optional[CRS] = None) -> EdgeDict:
    "Returns a bounds dict for an unbounded spatial domain"
    bounds = {"left": inf, "bottom": inf, "right": -inf, "top": -inf}
    if crs is not None:
        bounds["crs"] = crs
    return bounds


def add_geometry(geotype: str, coords: coords, bounds: EdgeDict) -> edges:
    "Updates bounds in-place to include a geometry"

    # Parse the edges of the new geometry
    if geotype == "Point":
        edges = _from_point
    elif geotype == "Polygon":
        edges = _from_polygon
    left, bottom, right, top = edges(coords)

    # Update bounds in-place to contain new edges
    bounds["left"] = min(bounds["left"], left)
    bounds["right"] = max(bounds["right"], right)
    bounds["bottom"] = min(bounds["bottom"], bottom)
    bounds["top"] = max(bounds["top"], top)


def _from_point(coords: coords) -> edges:
    "Returns the bbox edges of a point geometry"
    left = coords[0]
    right = coords[0]
    top = coords[1]
    bottom = coords[1]
    return left, bottom, right, top


def _from_polygon(coords: coords) -> edges:
    "Returns the bbox edges of a polygon geometry"
    shell = np.array(coords[0])
    left = np.min(shell[:, 0])
    right = np.max(shell[:, 0])
    bottom = np.min(shell[:, 1])
    top = np.max(shell[:, 1])
    return left, bottom, right, top
