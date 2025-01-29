"""
Classes used to implement raster projections and spatial metadata
----------
Classes:
    CRS         - Coordinate reference system (alias for pyproj.CRS)
    Transform   - Affine transform
    BoundingBox - Rectangular bounding box

Modules:
    crs         - Utility functions for working with pyproj.CRS objects

Internal modules:
    _bbox       - Module to implement the BoundingBox class
    _locator    - Module implementing an abstract base class for BoundingBox and Transform
    _transform  - Module implementing the Transform class
"""

from pyproj import CRS

from pfdf.projection import crs
from pfdf.projection._bbox import BoundingBox
from pfdf.projection._transform import Transform
