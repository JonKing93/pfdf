"""
Holds classes used to implement raster projections and spatial metadata
----------
Classes:
    CRS         - Coordinate reference system (currently pyproj.CRS)
    Transform   - Affine transform
    BoundingBox - Bounding box of a raster's edges

Type Hint:
    CRSInput    - User inputs that may be converted to a CRS

Internal:
    _Locator    - Abstract base class for Transform and BoundingBox objects
"""

from pyproj import CRS

from pfdf.projection._crs import CRSInput
from pfdf.projection._locator import _Locator
from pfdf.projection.bbox import BoundingBox
from pfdf.projection.transform import Transform
