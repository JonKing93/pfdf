"""
Utilities to process vector features into rasters
----------
Main function:
    parse_file          - Validates feature file and computes values for raster creation

Processing Functions:
    parse_nodata        - Determines default nodata or validates user input
    parse_features      - Validates feature values and returns (geometry, value) tuples
    parse_value         - Determines the value for a geometry
    require_features    - Informative errors if there are no features
    parse_resolution    - Returns resolution in axis units
    compute_extent      - Computes the transform and shape from the raster bounds and resolution

BoundingBox Utilities:
    unbounded           - Returns a bounds dict for an unbounded spatial domain
    point_edges         - Determines the edges of a point geometry
    polygon_edges       - Determins the edges of a polygon geometry
    add_coords          - Updates bounds (in-place) to include a geometry
    update_bounds       - Updates bounds to contain new edges

Class:
    FeatureFile         - Context manager for opened vector feature files
"""

from math import ceil, inf
from pathlib import Path
from typing import Any, Optional, Self

import fiona
import numpy as np
import shapely.geometry

import pfdf.raster._validate as validate
from pfdf.errors import FeatureFileError, NoFeaturesError
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.typing import Pathlike, Units, shape2d
from pfdf.utils.nodata import default as default_nodata

#####
# Main function
#####

geometry = dict[str, Any]
value = float | int | bool
nodata = value
GeometryValues = list[tuple[geometry, value]]


def parse_file(
    geometry: str,
    path: Any,
    field: Any,
    window: Any,
    nodata: Any,
    casting: Any,
    resolution: Any,
    units: Any,
    layer: Any,
    driver: Any,
    encoding: Any,
) -> tuple[GeometryValues, CRS, Transform, shape2d, type, nodata]:
    "Validates feature file and computes values for raster creation"

    # Validate resolution, unit option, and bounds
    units = validate.units(units)
    resolution = validate.resolution(resolution)
    if window is not None:
        window = validate.bounds(window)

    # Open file and extract property schema
    with FeatureFile(path, layer, driver, encoding) as ffile:
        properties = ffile.file.schema["properties"]

        # Validate field. Get dtype and nodata
        dtype = validate.field(properties, field)
        nodata = parse_nodata(nodata, casting, dtype)

        # Validate CRS and resolution unit conversion
        crs = _crs.validate(ffile.crs)
        validate.resolution_units(units, crs, resolution, geometry, ffile.path)

        # Load features and validate geometries. Get (geometry, value) tuples
        # and bounds. Require at least one feature
        features, bounds = parse_features(geometry, ffile, field, crs, window)

    # Convert resolution to axis unit. Then compute transform and shape
    resolution, crs = parse_resolution(resolution, units, crs, bounds)
    transform, shape = compute_extent(bounds, resolution)
    return features, crs, transform, shape, dtype, nodata


#####
# Processing functions
#####


dxdy = tuple[float, float]


def parse_nodata(nodata: Any | None, casting: str, dtype: type) -> value:
    "Default or validate NoData value"
    if dtype == bool:
        return False
    elif nodata is not None:
        return validate.nodata(nodata, casting, dtype)
    else:
        return default_nodata(dtype)


def parse_features(
    type: str,
    ffile: "FeatureFile",
    field: str | None,
    crs: CRS | None,
    window: BoundingBox | None,
) -> tuple[GeometryValues, BoundingBox]:
    """
    Checks that input features have valid geometries. Returns features as
    (geometry, value) tuples. Also returns the spatial bounds needed to fully
    contain the features.
    """

    # Get the allowed geometries and coordinate array validator
    validate_coordinates = getattr(validate, type)
    geometries = type.capitalize()
    geometries = [geometries, f"Multi{geometries}"]

    # Initialize the final bounds and geometry-value tuples.
    bounds = unbounded(crs)
    geometry_values = []

    # Build a shapely box from the load window
    if window is not None:
        window = window.reproject(crs).orient()
        window = window.tolist(crs=False)
        window = shapely.geometry.box(*window)

    # Validate each feature's geometry and get the coordinate array
    for f, feature in enumerate(list(ffile.file)):
        geometry = feature["geometry"]
        multicoordinates = validate.geometry(f, geometry, geometries)

        # Record feature bounds, and track whether to keep. By default, keep
        # everything. But if a window is provided, only keep intersecting features
        fbounds = unbounded()
        keep = window is None

        # Validate geometry coordinates. Check if the feature should be kept and
        # record the bounds
        for c, coordinates in enumerate(multicoordinates):
            shape = validate_coordinates(f, c, coordinates)
            if (not keep) and window.intersects(shape):
                keep = True
            add_coords(type, coordinates, fbounds)

        # Skip the feature if not being kept. Otherwise, update the final bounds
        # to include the feature.
        if not keep:
            continue
        update_bounds(bounds, **fbounds)

        # Associate each geometry with a value, and record the geometry-value tuple
        value = parse_value(feature, field)
        geometry_values.append((geometry, value))

    # Require at least one feature. Return geometry-value tuples and feature bounds
    require_features(type, geometry_values, window, ffile.path)
    return geometry_values, BoundingBox.from_dict(bounds)


def parse_value(feature: dict, field: str | None) -> value:
    "Determines the feature value"
    if field is None:
        return True
    else:
        return feature["properties"][field]


def require_features(
    geometry: str, features: list | None, window: BoundingBox | None, path: Path
) -> None:
    "Provides informative errors if there are no features"

    if len(features) == 0:
        if window is None:
            raise NoFeaturesError(
                f"The {geometry} feature file is empty and does not have any "
                f"{geometry} features.\nFile: {path}"
            )
        else:
            raise NoFeaturesError(
                f"None of the {geometry} features intersect the input bounds.\n"
                f"File: {path}"
            )


def parse_resolution(
    resolution: dxdy | Transform,
    units: Units,
    crs: CRS | None,
    bounds: BoundingBox,
) -> tuple[dxdy, CRS]:
    "Returns resolution in axis units"

    # Transform: Reproject as needed, then extract resolution
    if isinstance(resolution, Transform):
        crs = _crs.parse(crs, resolution.crs)
        if _crs.different(crs, resolution.crs):
            y = bounds.reproject(resolution.crs).center_y
            resolution = resolution.reproject(crs, y)
        resolution = resolution.resolution()

    # Vector: Convert to base units as needed
    elif units != "base":
        xres, yres = resolution
        xres = _crs.units_to_base(crs, "x", xres, units, bounds.center_y)
        yres = _crs.units_to_base(crs, "y", yres, units)
        resolution = (xres, yres)
    return resolution, crs


def compute_extent(bounds: BoundingBox, resolution: dxdy) -> tuple[Transform, shape2d]:
    "Computes the transform and shape from the raster bounds and resolution"

    # Build the transform
    xres, yres = resolution
    transform = Transform(xres, -yres, bounds.left, bounds.top)

    # Compute the shape
    nrows = ceil(bounds.ydisp() / yres)
    ncols = ceil(bounds.xdisp() / xres)
    return transform, (nrows, ncols)


#####
# BoundingBox Utilities
#####

coords = list[tuple[float, float]]
edges = tuple[float, float, float, float]
bounds = dict[str, float]


def unbounded(crs: Optional[CRS] = None) -> dict:
    "Returns a bounds dict for an unbounded spatial domain"
    bounds = {"left": inf, "bottom": inf, "right": -inf, "top": -inf}
    if crs is not None:
        bounds["crs"] = crs
    return bounds


def point_edges(coords: coords) -> edges:
    "Returns the edges of a point geometry"
    left = coords[0]
    right = coords[0]
    top = coords[1]
    bottom = coords[1]
    return left, bottom, right, top


def polygon_edges(coords: coords) -> edges:
    "Returns the edges of a polygon geometry"
    shell = np.array(coords[0])
    left = np.min(shell[:, 0])
    right = np.max(shell[:, 0])
    bottom = np.min(shell[:, 1])
    top = np.max(shell[:, 1])
    return left, bottom, right, top


def add_coords(geometry: str, coords: coords, bounds: bounds) -> edges:
    "Updates bounds in-place to include a geometry"
    if geometry == "point":
        edges = point_edges
    elif geometry == "polygon":
        edges = polygon_edges
    update_bounds(bounds, *edges(coords))


def update_bounds(
    bounds: dict, left: float, bottom: float, right: float, top: float
) -> None:
    "Updates bounds in-place to contain new edges"
    bounds["left"] = min(bounds["left"], left)
    bounds["right"] = max(bounds["right"], right)
    bounds["bottom"] = min(bounds["bottom"], bottom)
    bounds["top"] = max(bounds["top"], top)


#####
# Feature File
#####


class FeatureFile:
    """
    Context Manager for opened vector feature files.
    ----------
    Dunders:
        __init__        - Initial validation of file settings
        __enter__       - Entry point for "with" block and informative errors for invalid files
        __exit__        - Closes file upon exiting a "with" block
    """

    def __init__(
        self, path: Pathlike, layer: str | int, driver: str, encoding: str
    ) -> None:
        """Creates a FeatureFile object for use in a "with" block. Also performs
        initial validation of fiona file parameters"""

        # Validate
        if driver is not None:
            validate.type(driver, "driver", str, "string")
        if encoding is not None:
            validate.type(encoding, "encoding", str, "string")
        if layer is not None:
            validate.type(layer, "layer", (int, str), "int or string")
        path = validate.input_path(path, "path")

        # File reading attributes
        self.path = path
        self.layer = layer
        self.driver = driver
        self.encoding = encoding

        # Functional attributes
        self.file = None
        self.crs = None

    def __enter__(self) -> Self:
        """Opens vector feature file upon entry into a "with" block. Also provides
        informative error if file opening fails"""

        # Attempt to open the feature file. Informative error if failed
        try:
            self.file = fiona.open(
                self.path, driver=self.driver, layer=self.layer, encoding=self.encoding
            )
        except Exception as error:
            raise FeatureFileError(
                f"Could not read data from the feature file. "
                f"The file may be corrupted or formatted incorrectly.\n"
                f"File: {self.path}"
            ) from error

        self.crs = self.file.crs
        return self

    def __exit__(self, *args, **kwargs) -> None:
        "Closes file upon exiting the 'with' block"
        self.file.close()
