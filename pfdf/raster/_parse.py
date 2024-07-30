"""
Functions that parse spatial metadata
----------
Functions:
    projection  - Parses CRS and transform from raster properties and projection input
    template    - Parses CRS and transform from template and keyword options
    src_dst     - Parses source and destination values
"""

import pfdf._validate as validate
from pfdf._utils import all_nones, no_nones
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.raster import _raster


def projection(
    crs: CRS | None, projection: Transform | BoundingBox | None, shape
) -> tuple[CRS | None, Transform | None]:
    "Parses CRS and transform from raster properties and a projection input"

    # Just exit if the projection is None
    if projection is None:
        return crs, None

    # Otherwise, detect projection type
    elif isinstance(projection, BoundingBox):
        bounds = projection
        transform = bounds.transform(*shape)
    else:
        bounds = None
        transform = projection

    # Inherit CRS if None was provided
    if crs is None:
        crs = transform.crs

    # Reproject the transform as needed
    elif _crs.different(crs, transform.crs):
        if bounds is None:
            bounds = transform.bounds(*shape)
        y = bounds.center_y
        transform = transform.reproject(crs, y)
    return crs, transform


def template(template, name, crs, transform):
    """Parses CRS and transfrom from a template raster and keyword options.
    Prioritizes keywords, but uses template metadata as backup if available"""

    if template is not None:
        validate.type(template, name, _raster.Raster, "Raster object")
        if crs is None:
            crs = template.crs
        if transform is None:
            transform = template.transform
    return crs, transform


def src_dst(source, dest, default):
    "Parses source and destination values"
    if no_nones(source, dest):
        return source, dest
    elif all_nones(source, dest):
        return default, default
    elif source is None and dest is not None:
        return dest, dest
    else:
        return source, source
