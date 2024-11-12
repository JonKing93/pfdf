"""
Functions that parse spatial metadata
----------
Functions:
    template    - Parses CRS and transform from template and keyword options
"""

from __future__ import annotations

import typing

import pfdf._validate.core as validate
from pfdf import raster

if typing.TYPE_CHECKING:
    from typing import Any

    from pfdf.raster import RasterMetadata


def template(kwargs: RasterMetadata, template: Any, name: str) -> RasterMetadata:
    "Parses CRS and transform from kwarg metadata and a template"

    # Validate the template
    if template is not None:
        validate.type(
            template,
            name,
            (raster.Raster, raster.RasterMetadata),
            "Raster or RasterMetadata object",
        )

        # Parse and update CRS and Transform
        crs = kwargs.crs or template.crs
        transform = kwargs.transform or template.transform
        kwargs = kwargs.update(crs=crs, transform=transform)
    return kwargs
