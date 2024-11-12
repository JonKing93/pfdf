"""
Type hints derived from the Raster class
"""

from pathlib import Path
from typing import Any

import pysheds.sview
import rasterio
from affine import Affine

from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import Raster, RasterMetadata
from pfdf.typing.core import matrix, scalar, vector

# Raster
RasterInput = (
    Raster | str | Path | rasterio.DatasetReader | matrix | pysheds.sview.Raster
)

# Raster metadata
Template = Raster | RasterMetadata
CRSInput = CRS | Template | int | str | dict | Any
BoundsInput = BoundingBox | Template | dict | list | tuple
TransformInput = Transform | Template | dict | list | tuple | Affine
ResolutionInput = TransformInput | scalar | vector
