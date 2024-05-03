"""
Utilities to help process vector features into rasters
----------
This module contains a variety of utilities to help parse vector feature files.
The key component is the FeatureFile class. This provides a context manager
and utilities for opened vector feature files. The class is only intended to be
used within a "with" block and ensures that the file is always closed. Within the
with block, the "process" method is the main entry point. This calls the various
utilities needed to parse the values used to create the final raster array.
----------
Functions:
    parse_features  - Validates feature records, collects into (geometry, value) tuples
                      and calculates bounds for the retained features
    _unbounded      - Returns a dict for an unbounded spatial domain
    _update_bounds  - Updates a bounds dict to account for new edges
    _add_coords     - Updates a bounds dict to include geometry coordinates

Class:
    FeatureFile     - Context manager and utilities for parsing vector features
    .process        - Main function
"""

from math import ceil, inf
from typing import Any, Self

import fiona
import numpy as np
import shapely.geometry

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import FeatureFileError, GeometryError, MissingCRSError
from pfdf.projection import CRS, BoundingBox, Transform, _crs
from pfdf.typing import Pathlike, shape2d

features = list[dict]
dxdy = tuple[float, float]


#####
# Feature parsing functions
#####


def _unbounded():
    "Returns a bounds dict for an unbounded spatial domain"
    return {"left": inf, "bottom": inf, "right": -inf, "top": -inf}


def _update_bounds(
    bounds: dict, left: float, bottom: float, right: float, top: float
) -> None:
    "Updates bounds to contain new edges"
    bounds["left"] = min(bounds["left"], left)
    bounds["right"] = max(bounds["right"], right)
    bounds["bottom"] = min(bounds["bottom"], bottom)
    bounds["top"] = max(bounds["top"], top)


def _add_coords(
    bounds: dict[str, float], coords: list[tuple[float, float]], ispoint: bool
) -> None:
    "Updates bounds (in-place) to include a geometry's coordinates"

    # Get bounds from points...
    if ispoint:
        left = coords[0]
        right = coords[0]
        top = coords[1]
        bottom = coords[1]

    # ...or from a polygon shell
    else:
        shell = np.array(coords[0])
        left = np.min(shell[:, 0])
        right = np.max(shell[:, 0])
        bottom = np.min(shell[:, 1])
        top = np.max(shell[:, 1])

    # Update the bounds
    _update_bounds(bounds, left, bottom, right, top)


geometry = dict[str, Any]
GeometryValue = tuple[geometry, float | int | bool]


def parse_features(
    features: list[dict],
    field: str | None,
    geometries: tuple[str, str],
    crs: CRS | None,
    window: BoundingBox | None,
) -> tuple[GeometryValue, BoundingBox]:
    """
    Checks that input features have valid geometries. Returns features as
    (geometry, value) tuples. Also returns the spatial bounds needed to fully
    contain the features.
    """

    # Initialize the final bounds and geometry-value tuples.
    bounds = _unbounded()
    geometry_values = []

    # Build a shapely box from the load window
    if window is not None:
        window = window.reproject(crs).orient()
        window = window.aslist()[:-1]
        window = shapely.geometry.box(*window)

    # Each feature must have a geometry
    for f, feature in enumerate(features):
        geometry = feature["geometry"]
        if geometry is None:
            raise GeometryError(f"Feature[{f}] does not have a geometry.")

        # Require expected geometry
        type = geometry["type"]
        if type not in geometries:
            allowed = " or ".join(geometries)
            raise GeometryError(
                f"Each feature in the input file must have a {allowed} geometry. "
                f"However, feature[{f}] has a {type} geometry instead."
            )

        # Arrange single geometries like multi geometries
        multicoordinates = geometry["coordinates"]
        if type in ["Point", "Polygon"]:
            multicoordinates = [multicoordinates]

        # Record feature bounds, and track whether to keep. By default, keep
        # everything. But if a window is provided, only keep intersecting features
        fbounds = _unbounded()
        keep = window is None

        # Validate geometry coordinates.
        for c, coordinates in enumerate(multicoordinates):
            ispoint = "Point" in type
            if ispoint:
                shape = validate.point(f, c, coordinates)
            else:
                shape = validate.polygon(f, c, coordinates)

            # Check if the feature should be kept and record the bounds
            if (not keep) and window.intersects(shape):
                keep = True
            _add_coords(fbounds, coordinates, ispoint)

        # Skip the feature if not being kept. Otherwise, update the final bounds
        # to include the feature.
        if not keep:
            continue
        _update_bounds(bounds, **fbounds)

        # Associate each geometry with a value
        if field is None:
            value = True
        else:
            value = feature["properties"][field]
        geometry_values.append((geometry, value))
    return geometry_values, BoundingBox.from_dict(bounds)


#####
# Feature File Context Manager
#####


class FeatureFile:
    """
    Context Manager and utility methods for opened vector feature files.
    Note that methods are only available within a "with" block
    ----------
    Dunders:
        __init__        - Initial validation of file settings
        __enter__       - Entry point for "with" block and informative errors for invalid files
        __exit__        - Closes file upon exiting a "with" block

    Validation:
        parse_field     - Checks that field and fill can be used to build a raster
        validate_meters - Checks that meters conversion is valid
        parse_resolution    - Parses resolution from Transform or 2-tuple

    Misc:
        load            - Returns feature records as a list
        extent          - Computes Transform and shape of output raster

    Main:
        process         - Parses a vector feature file for raster conversion
    """

    #####
    # Dunders
    #####

    def __init__(
        self, type: str, path: Pathlike, layer: str | int, driver: str, encoding: str
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

        # Record attributes
        self.type = type
        self.path = path
        self.layer = layer
        self.driver = driver
        self.encoding = encoding

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
                f"Could not read data from the {self.type} feature file. "
                f"The file may be corrupted or formatted incorrectly.\n"
                f"File: {self.path}"
            ) from error

        self.crs = self.file.crs
        return self

    def __exit__(self, *args, **kwargs) -> None:
        "Closes file upon exiting the 'with' block"
        self.file.close()

    #####
    # Validation / Parsing
    #####

    nodata = float | bool
    fill = float | bool

    def parse_field(self, field: Any, fill: Any) -> tuple[type, nodata, fill]:
        "Checks that a feature data field and fill can be used to build a raster"

        properties = self.file.schema["properties"]
        return validate.field(properties, field, fill)

    def validate_meters(
        self, crs: CRS | None, resolution: tuple | Transform, meters: bool
    ) -> None:
        "When relevant, checks that meters conversion is possible"
        if (crs is None) and (not isinstance(resolution, Transform)) and meters:
            raise MissingCRSError(
                f"Cannot convert resolution from meters because the {self.type} "
                "feature file does not have a CRS.\n"
                f"File: {self.path}"
            )

    @staticmethod
    def parse_resolution(
        resolution: tuple[float, float] | Transform,
        meters: bool,
        crs: CRS | None,
        bounds: BoundingBox,
    ) -> tuple[float, float]:
        "Returns resolution in axis units"

        # Transform: Reproject as needed, then extract resolution
        if isinstance(resolution, Transform):
            crs = _crs.parse(crs, resolution.crs)
            transform = resolution._format(crs, bounds)
            resolution = transform.resolution()

        # Vector: Convert from meters as needed
        elif meters:
            _, y = bounds.center
            xres, yres = resolution
            xres = _crs.dx_from_meters(crs, xres, y)
            yres = _crs.dy_from_meters(crs, yres)
            resolution = (xres, yres)
        return resolution, crs

    #####
    # Feature Records
    #####

    def load(self) -> list:
        "Returns vector features as a list"
        return list(self.file)

    @staticmethod
    def extent(bounds: BoundingBox, resolution: dxdy) -> tuple[Transform, shape2d]:
        "Computes the transform and shape from the raster bounds and resolution"

        # Build the transform
        xres, yres = resolution
        transform = Transform(xres, -yres, bounds.left, bounds.top)

        # Compute the shape
        nrows = ceil(bounds.ydisp() / yres)
        ncols = ceil(bounds.xdisp() / xres)
        return transform, (nrows, ncols)

    #####
    # Main
    #####

    def process(
        self,
        field: str | None,
        fill: float | None,
        resolution: tuple | Transform,
        meters: bool,
        bounds: BoundingBox,
    ) -> tuple[list, CRS, Transform, shape2d, type, float, float]:

        # Get geometries
        if self.type == "polygon":
            geometries = ["Polygon", "MultiPolygon"]
        else:
            geometries = ["Point", "MultiPoint"]

        # Validate settings
        dtype, nodata, fill = self.parse_field(field, fill)
        crs = _crs.validate(self.crs)
        self.validate_meters(crs, resolution, meters)

        # Load and validate features. Convert to (geometry, value) tuples and get bounds
        features = self.load()
        features, bounds = parse_features(features, field, geometries, crs, bounds)

        # Convert resolution to axis unit. Then compute transform and shape
        resolution, crs = self.parse_resolution(resolution, meters, crs, bounds)
        transform, shape = self.extent(bounds, resolution)
        return features, crs, transform, shape, dtype, nodata, fill
