"""
Class for working with bounding boxes
----------
Class:
    BoundingBox - Implements a bounding box
"""

from math import isfinite
from typing import Any, Callable, Optional, Self

import numpy as np
import rasterio.warp
from pyproj import CRS

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import MissingCRSError
from pfdf.projection import CRSInput, _crs, _Locator, transform
from pfdf.typing.core import Quadrant, Units, scalar

# Type aliases
limits = tuple[float, float]


class BoundingBox(_Locator):
    """
    Implements a bounding box
    ----------
    The BoundingBox class implements a rectangular bounding box, typically used
    to locate the edges of a raster dataset. The "left", "right", "top", and
    "bottom" properties provide the X and Y coordinates of the box's edges. A
    BoundingBox may optionally have an associated CRS. This is a pyproj.CRS
    object, and provides an absolute reference frame for the box's coordinates.
    The CRS may be accessed via the "crs" property.

    As stated, a BoundingBox is intended to represent the edges of a raster dataset.
    where the left/right edges are the first/last columns, and the top/bottom edges
    are the first/last rows. There is no guarantee on the spatial ordering of a
    raster's rows and columns, and so a BoundingBox's left coordinate is not
    necessarily less than the right coordinate. The same holds for the top and
    bottom coordinates. You can use the "orientation" property to see how these
    coordinates relate to one another. This property returns the quadrant of the
    Cartesian plane that the box would lie in, where the origin point is defined
    as the minimum X and minimum Y coordinate for the box. As follows:

    1: left <= right, bottom <= top
    2: left >  right, bottom <= top
    3: left >  right, bottom >  top
    4: left <= right, bottom >  top

    NOTE:
    Although BoundingBox does not guarantee the spatial ordering along an axis,
    the X axis (left/right) is interpreted as westing/easting, and the Y axis
    (bottom/top) is interpreted as northing/southing.

    Each BoundingBox provides methods to compute lengths along the X or Y axis.
    The xdisp and ydisp methods return the displacement from left to right and
    bottom to top, respectively. The width and height methods are similar, but
    always return a positive value. By default, axis lengths are returned in the
    axis's base unit, but setting the "meters" option to True will return a length
    in meters instead. Note that conversion to meters is only possible when a
    BoundingBox has a CRS.

    A BoundingBox also includes methods that return a transformed version of the
    box. For example, the "orient" method returns a box in a requested orientation,
    the "reproject" returns a box in a requested CRS, and the "buffer" command
    returns a box with a buffer added to the edges. Two convenience methods
    reproject the box into commonly used projections: "to_utm" reprojects the box
    into the best UTM zone for its center point, and "to_4326" reprojects into
    EPSG:4326 (often referred to as WGS 84).

    TIP:
    If you want to work in longitudes and latitudes, use the "to_4326" method
    to reproject the box to EPSG:4326 (often referred to as WGS 84). The coordinates
    of the reprojected box will be in longitude/latitude.
    ----------
    PROPERTIES:
    Edges:
        left            - The left coordinate
        right           - The right coordinate
        bottom          - The bottom coordinate
        top             - The top coordinate

    Edge Tuples:
        xs              - A (left, right) tuple
        ys              - A (bottom, top) tuple
        bounds          - A (left, bottom, right, top) tuple

    Center:
        center          - The (X, Y) coordinate of the box's center
        center_x        - The X coordinate of the box's center
        center_y        - The Y coordinate of the box's center

    Orientation:
        orientation     - The Cartesian quadrant of the box's orientation

    CRS:
        crs             - Coordinate reference system (pyproj.CRS or None)
        units           - The units of the X and Y axes
        xunit           - The unit of the CRS X axis
        yunit           - The unit of the CRS Y axis

    Units per meter:
        units_per_m     - The number of CRS units per meter along the X and Y axes
        x_units_per_m   - The number of CRS X units per meter
        y_units_per_m   - The number of CRS Y units per meter

    METHODS:
    Object Creation:
        __init__        - Creates a new BoundingBox from edge coordinates and optional CRS
        from_list       - Creates a BoundingBox from a list or tuple of edge coordinates and optional CRS
        from_dict       - Creates a BoundingBox from a dict
        copy            - Returns a copy of the current BoundingBox

    Dunders:
        __repr__        - A string representing the bounding box
        __eq__          - True if both objects are BoundingBox objects with the same edges and CRS

    Axis lengths:
        xdisp           - Right minus Left
        ydisp           - Top minus bottom
        width           - Absolute value of xdisp
        height          - Absolute value of ydisp

    Misc:
        orient          - Returns a copy of the box in the requested orientation
        buffer          - Buffers the edges of the box by the indicated distance(s)

    Reprojection:
        utm_zone        - Returns the best UTM CRS for the box's center
        reproject       - Returns a copy of the box projected into a different CRS
        to_utm          - Returns a copy of the box projected into the best UTM zone
        to_4326         - Returns a copy of the box projected into EPSG:4326

    Transform Conversion:
        dx              - Pixel dx given a number of columns
        dy              - Pixel dy given a number of rows
        transform       - Converts the box to a Transform

    As built-in types:
        tolist          - Returns the box as a list
        todict          - Returns the box as a dict

    Testing:
        isclose         - True if an input is a BoundingBox with similar values

    INTERNAL:
        _inversion      - True if an axis requires inversion
        _buffer_edges   - Computes buffered edges, accounting for orientation
        _delta          - Computes dx and dy
    """

    _names = ["left", "bottom", "right", "top"]

    #####
    # Object creation
    #####

    def __init__(
        self,
        left: scalar,
        bottom: scalar,
        right: scalar,
        top: scalar,
        crs: Optional[CRSInput] = None,
    ) -> None:
        """
        Creates a new bounding box object
        ----------
        BoundingBox(left, bottom, right, top)
        Creates a new BoundingBox from the indicated edge coordinates.

        BoundingBox(..., crs)
        Creates a new BoundingBox with an associated coordinate reference system.
        ----------
        Inputs:
            left, bottom, right, top: The edges of the new BoundingBox. Each coordinate
                must be a scalar numeric value.
            crs: The coordinate reference system for the bounding box. Must be
                convertible to a pyproj.CRS object via the standard API.

        Outputs:
            BoundingBox: The new BoundingBox object
        """
        super().__init__([left, bottom, right, top], crs)

    #####
    # Properties
    #####

    ##### Edges

    @property
    def right(self) -> float:
        return self._right

    @property
    def bottom(self) -> float:
        return self._bottom

    ##### Edge Tuples

    @property
    def xs(self) -> limits:
        "A (left, right) tuple"
        return (self.left, self.right)

    @property
    def ys(self) -> limits:
        "A (bottom, top) tuple"
        return (self.bottom, self.top)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        "A (left, bottom, right, top) tuple"
        return self.left, self.bottom, self.right, self.top

    ##### Center

    @property
    def center_x(self) -> float:
        "The X coordinate of the BoundingBox's center"
        return np.mean(self.xs)

    @property
    def center_y(self) -> float:
        "The Y coordinate of the BoundingBox's center"
        return np.mean(self.ys)

    @property
    def center(self) -> tuple[float, float]:
        "The (X, Y) coordinate of the BoundingBox's center"
        return self.center_x, self.center_y

    ##### Misc

    @property
    def orientation(self) -> Quadrant:
        "The Cartesian quadrant of the box's orientation"
        xinverted = self.left > self.right
        yinverted = self.bottom > self.top
        return self._orientation(xinverted, yinverted)

    @property
    def x_units_per_m(self) -> float | None:
        "The number of X axis units per meter"
        return _crs.x_units_per_m(self.crs, self.center_y)

    @property
    def units_per_m(self) -> tuple[float, float] | tuple[None, None]:
        "The number of CRS units per meter for the X and Y axes"
        x = self.x_units_per_m
        y = self.y_units_per_m
        return x, y

    #####
    # Box Lengths
    #####

    def xdisp(self, units: Units = "base") -> float:
        """
        Returns the change in X-coordinate (displacement) from left to right
        ----------
        self.xdisp()
        self.xdisp(units)
        Returns the X-coordinate displacement (right - left). By default, returns
        xdisp in the base unit of the X axis. Use the "units" option to specify
        the units instead. Note that this option is only available when the
        BoundingBox has a CRS. Supported units include: "meters", "kilometers",
        "feet", and "miles".
        ----------
        Inputs:
            units: The units that xdisp should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The change in X coordinate (right - left)
        """
        xdisp = self.right - self.left
        return self._length("x", xdisp, "xdisp", units, self.center_y)

    def ydisp(self, units: Units = "base") -> float:
        """
        Returns the change in Y-coordinate (displacement) from bottom to top
        ----------
        self.ydisp()
        self.ydisp(units)
        Returns the Y-coordinate displacement (top - bottom). By default, returns
        ydisp in the base units of the Y axis. Use the "units" option to specify
        the units instead. Note that this option is only supported when the
        BoundingBox has a CRS. Supported units include: "meters", "kilometers",
        "feet", and "miles".
        ----------
        Inputs:
            units: The units that ydisp should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The change in Y coordinate (right - left)
        """
        ydisp = self.top - self.bottom
        return self._length("y", ydisp, "ydisp", units)

    def width(self, units: Units = "base") -> float:
        """
        Returns the length of the BoundingBox along the X-axis
        ----------
        self.width()
        self.width(units)
        Returns the length of the BoundingBox along the X-axis. By default, returns
        the width in the CRS base unit. Use the "units" option to specify the
        units instead. Note that this option is only supported when the BoundingBox
        has a CRS. Supported units include: "meters", "kilometers", "feet", and
        "miles".
        ----------
        Inputs:
            units: The units that width should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The length of the box along the X-axis
        """
        return abs(self.xdisp(units))

    def height(self, units: Units = "base") -> float:
        """
        Returns the length of the BoundingBox along the Y-axis
        ----------
        self.height()
        self.height(units)
        Returns the length of the BoundingBox along the Y-axis. By default, returns
        the height in the CRS base unit. Use the "units" option to specify the
        units instead. Note that this option is only supported when the BoundingBox
        has a CRS. Supported units include: "meters", "kilometers", "feet", and
        "miles".
        ----------
        Inputs:
            units: The units that height should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The length of the box along the Y-axis
        """
        return abs(self.ydisp(units))

    #####
    # Orientation
    #####

    def _inversion(self, quadrant: Quadrant, inverted: list[int]) -> bool:
        "True if an axis will require inversion"
        return (quadrant in inverted) != (self.orientation in inverted)

    def orient(self, quadrant: Quadrant = 1) -> Self:
        """
        Returns a copy of the BoundingBox in the requested orientation
        ----------
        self.orient(quadrant)
        Returns a copy of the BoundingBox in the requested orientation. The input
        should be either 1, 2, 3, or 4, and represent the quadrant of the Cartesian
        plane that would contain the box when the origin point is defined as the
        box's minimum X and minimum Y coordinate. As follows:

        1: left <= right, bottom <= top
        2: left >  right, bottom <= top
        3: left >  right, bottom >  top
        4: left <= right, bottom >  top
        ----------
        Inputs:
            quadrant: The orientation of the output BoundingBox

        Outputs:
            BoundingBox: A copy of the BoundingBox in the requested orientation
        """

        # Validate the new quadrant
        quadrant = validate.scalar(quadrant, "quadrant", dtype=real)
        if quadrant not in [1, 2, 3, 4]:
            raise ValueError("Orientation quadrant must be 1, 2, 3, or 4.")

        # Determine which axes to invert
        invert_x = self._inversion(quadrant, [2, 3])
        invert_y = self._inversion(quadrant, [3, 4])

        # Build the oriented box
        left, bottom, right, top = self.bounds
        if invert_x:
            left, right = right, left
        if invert_y:
            bottom, top = top, bottom
        return BoundingBox(left, bottom, right, top, self.crs)

    #####
    # Buffering
    #####

    @staticmethod
    def _buffer_edges(
        min_edge: float,
        min_buffer: float,
        max_edge: float,
        max_buffer: float,
    ) -> tuple[float, float]:
        "Computes buffered edges, accounting for orientation"
        if min_edge > max_edge:
            min_buffer = -min_buffer
            max_buffer = -max_buffer
        return min_edge - min_buffer, max_edge + max_buffer

    def buffer(
        self,
        distance: Optional[scalar] = None,
        units: Units = "base",
        *,
        left: Optional[scalar] = None,
        bottom: Optional[scalar] = None,
        right: Optional[scalar] = None,
        top: Optional[scalar] = None,
    ) -> Self:
        """
        Buffers the edges of a BoundingBox
        ----------
        self.buffer(distance)
        self.buffer(distance, units)
        Returns a copy of the box for which the edges have been buffered by the
        indicated distance. Note that distance must be positive. By default,
        distances are interpreted as the base unit of the bounding box. Use the
        "units" option to specify the units of the input distance instead. Note
        that this option is only available when the box has a CRS. Supported units
        include: "meters", "kilometers", "feet", and "miles".

        self.buffer(..., *, left, bottom, right, top)
        Specifies buffers for specific edges of the box. Use the keyword options
        to implement different buffers along different edges. If a keyword option
        is not specified, uses the default buffer from the 'distance' input for
        the associated edge. If distance is not provided, uses a default buffering
        distance of 0.
        ----------
        Inputs:
            distance: The default buffering distance for the box edges
            units: The units of the input buffering distances. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"
            left: The buffer for the left edge
            bottom: The buffer for the bottom edge
            right: The buffer for the right edge
            top: The buffer for the top edge

        Outputs:
            BoundingBox: A BoundingBox with buffered edges
        """

        # Validate buffers. Convert distances to axis units
        units = self._validate_units(units, "buffering distances", "from")
        buffers = validate.buffers(distance, left, bottom, right, top)
        if units != "base":
            buffers = _crs.buffers_to_base(self, buffers, units)

        # Build the buffered box
        left, right = self._buffer_edges(
            self.left, buffers["left"], self.right, buffers["right"]
        )
        bottom, top = self._buffer_edges(
            self.bottom, buffers["bottom"], self.top, buffers["top"]
        )
        return BoundingBox(left, bottom, right, top, self.crs)

    #####
    # Reprojection
    #####

    def utm_zone(self) -> CRS | None:
        """
        Returns the CRS of the best UTM zone for the box's center point
        ----------
        self.utm_zone()
        Returns the pyproj.CRS of the best UTM zone for the box's center point.
        The best UTM zone is whichever zone contains the center point. If the
        point is exactly on the border of multiple UTM zones, then returns one
        of the zones arbitrarily. Returns None if the point is not within a UTM
        zone (typically high-latitude polar regions). This method is only
        available when a BoundingBox has a CRS.
        ----------
        Outputs:
            pyproj.CRS | None: The best UTM CRS for the box's center point
        """
        if self.crs is None:
            raise MissingCRSError(
                f"Cannot determine the UTM zone for the BoundingBox "
                "because it does not have a CRS."
            )
        return _crs.utm_zone(self.crs, *self.center)

    def reproject(self, crs: CRSInput) -> Self:
        """
        reproject  Returns a copy of a BoundingBox projected into the indicated CRS
        ----------
        self.reproject(crs)
        Returns a copy of the bounding box reprojected into a new CRS. Note that
        this method is only available when a BoundingBox has a CRS.
        ----------
        Inputs:
            crs: The CRS of the reprojected BoundingBox

        Outputs:
            BoundingBox: The reprojected box
        """

        crs = self._validate_reprojection(crs)
        reprojected = rasterio.warp.transform_bounds(self.crs, crs, *self.bounds)
        finite = [isfinite(edge) for edge in reprojected]
        if not all(finite):
            raise RuntimeError(
                "Cannot reproject the BoundingBox because it contains points "
                "outside the domain of its CRS."
            )
        return BoundingBox(*reprojected, crs)

    def to_utm(self) -> Self:
        """
        to_utm  Returns a copy of the BoundingBox in the best UTM zone
        ----------
        self.to_utm()
        Returns a copy of a box reprojected into the best UTM zone for the box's
        center coordinate. Only available when a BoundingBox has a CRS. Raises a
        ValueError if the box's center coordinate is not within the UTM domain.
        ----------
        Outputs:
            BoundingBox: The reprojected BoundingBox
        """
        utm = self.utm_zone()
        if utm is None:
            raise ValueError(
                "Cannot reproject the BoundingBox to UTM because its center "
                "is not in the UTM domain."
            )
        return self.reproject(utm)

    def to_4326(self) -> Self:
        """
        to_4326  Returns a copy of the BoundingBox in EPSG:4326
        ----------
        self.to_4326()
        Returns a copy of a BoundingBox reprojected into EPSG:4326 (often referred
        to as WGS 84). This method is only available when a BoundingBox has a CRS.
        ----------
        Outputs:
            BoundingBox: The reprojected BoundingBox
        """
        return self.reproject(4326)

    #####
    # Transform Conversion
    #####

    def _delta(self, N: Any, name: str, delta: Callable, units: Units) -> float:
        "Returns pixel spacing"
        N = self._validate_N(N, name)
        return delta(units) / N

    def dx(self, ncols: int, units: Units = "base") -> float:
        """
        Computes pixel spacing, given a number of raster columns
        ----------
        self.dx(ncols)
        self.dx(ncols, units)
        Computes the pixel spacing required to fit an input number of columns into
        the BoundingBox. By default, returns spacing in the base unit of the CRS.
        Use the "units" option to specify the units instead. Note that this option
        is only available when the BoundingBox has a CRS. Supported units include:
        "meters", "kilometers", "feet", and "miles".
        ----------
        Inputs:
            ncols: The number of columns in a raster
            units: The units that dx should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The computed pixel spacing
        """
        return self._delta(ncols, "ncols", self.xdisp, units)

    def dy(self, nrows: int, units: Units = "base") -> float:
        """
        Computes pixel spacing, given a number of raster rows
        ----------
        self.dy(nrows)
        self.dy(nrows, units)
        Computes the pixel spacing required to fit an input number of rows into
        the BoundingBox. By default, returns spacing in the base unit of the CRS.
        Use the "units" option to specify the units instead. Note that this option
        is only available when the BoundingBox has a CRS. Supported units include:
        "meters", "kilometers", "feet", and "miles".
        ----------
        Inputs:
            nrows: The number of rows in a raster
            units: The units that dy should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The computed pixel spacing
        """
        return -self._delta(nrows, "nrows", self.ydisp, units)

    def transform(self, nrows: int, ncols: int) -> "transform.Transform":
        """
        Returns a Transform object derived from the BoundingBox
        ----------
        self.transform(nrows, ncols)
        Converts the BoundingBox to a Transform object, given a number of raster
        rows and columns.
        ----------
        Inputs:
            nrows: The number of raster rows
            ncols: The number of raster columns

        Outputs:
            Transform: A Transform object derived from the BoundingBox
        """
        dx = self.dx(ncols)
        dy = self.dy(nrows)
        return transform.Transform(dx, dy, self.left, self.top, self.crs)
