"""
Functions that reproject feature geometries
----------
Functions:
    geometries  - Main function to reproject feature geometries in-place
    _basins     - Reprojects basin polygons in-place
    _segments   - Reprojects segment linestrings in-place
    _point      - Reprojects a point and returns the new coordinates
    _line       - Reprojects a line in-place
"""

from pyproj import CRS, Transformer

from pfdf.typing import ExportType

# Type aliases
XY = tuple[float, float]
Line = list[XY]
GeomIDs = list[tuple[dict, float]]
Segments = list[Line]
Outlets = list[XY]
Geometries = GeomIDs | Segments | Outlets


def _point(point: XY, transform: Transformer) -> XY:
    "Reprojects a point coordinate"
    return transform.transform(*point)


def _line(line: Line, transform: Transformer) -> Line:
    "Reprojects a line geometry in-place"
    for p, point in enumerate(line):
        line[p] = _point(point, transform)


def _basins(basins: GeomIDs, transform: Transformer) -> None:
    "Reprojects basin geometries in-place"
    for geometry, _ in basins:
        for ring in geometry["coordinates"]:
            _line(ring, transform)


def _segments(lines: list[Line], transform: Transformer) -> None:
    "Reprojects segment geometries in-place"
    for line in lines:
        _line(line, transform)


def geometries(
    geometries: Geometries, type: ExportType, from_crs: CRS, to_crs: CRS
) -> None:
    "Reprojects feature geometries in-place"

    if from_crs != to_crs:
        transform = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        if type == "basins":
            _basins(geometries, transform)
        elif type == "segments":
            _segments(geometries, transform)
        else:
            _line(geometries, transform)
