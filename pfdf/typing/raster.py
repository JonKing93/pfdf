"""
Type hints derived from the Raster class
"""

from pathlib import Path
from typing import Any

import pysheds.sview
import rasterio
from affine import Affine

from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster
from pfdf.typing.core import matrix, scalar, vector

# Raster
RasterInput = (
    Raster | str | Path | rasterio.DatasetReader | matrix | pysheds.sview.Raster
)

# Raster metadata
CRSInput = CRS | Raster | int | str | dict | Any
BoundsInput = BoundingBox | Raster | dict | list | tuple
TransformInput = Transform | Raster | dict | list | tuple | Affine
ResolutionInput = TransformInput | scalar | vector
