"""
Functions used to determine the bounds of rasters built from vector features
----------
Functions:
    unbounded       - Returns a bounds dict for an unbounded spatial domain
    update          - Updates bounds in-place to add new edges
    add_geometry    - Updates bounds in-place given a new geometry
    _from_point     - Returns bbox edges for a point feature
    _from_polygon   - Returns bbox edges for a polygon feature
"""

from math import inf
from typing import Optional

import numpy as np

from pfdf.projection import CRS

# Type hints
coords = list[tuple[float, float]]
edges = tuple[float, float, float, float]
bounds = dict[str, float]


def unbounded(crs: Optional[CRS] = None) -> dict:
    "Returns a bounds dict for an unbounded spatial domain"
    bounds = {"left": inf, "bottom": inf, "right": -inf, "top": -inf}
    if crs is not None:
        bounds["crs"] = crs
    return bounds


def update(bounds: dict, left: float, bottom: float, right: float, top: float) -> None:
    "Updates bounds in-place to contain new edges"
    bounds["left"] = min(bounds["left"], left)
    bounds["right"] = max(bounds["right"], right)
    bounds["bottom"] = min(bounds["bottom"], bottom)
    bounds["top"] = max(bounds["top"], top)


def add_geometry(geometry: str, coords: coords, bounds: bounds) -> edges:
    "Updates bounds in-place to include a geometry"
    if geometry == "point":
        edges = _from_point
    elif geometry == "polygon":
        edges = _from_polygon
    update(bounds, *edges(coords))


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
