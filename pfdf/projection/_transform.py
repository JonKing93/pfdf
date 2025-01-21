"""
Class for working with Raster affine transforms
----------
Class:
    Transform   - Class to represent a Raster affine transform
"""

from __future__ import annotations

import typing
from math import sqrt

from affine import Affine

import pfdf._validate.core as validate
from pfdf import projection
from pfdf._utils import real
from pfdf.errors import TransformError
from pfdf.projection import crs as _crs
from pfdf.projection._locator import Locator

# Type hints
if typing.TYPE_CHECKING:
    from typing import Any, Optional

    from pfdf.projection import BoundingBox
    from pfdf.typing.core import CRSlike, Quadrant, Units, scalar


class Transform(Locator):
    """
    Implements a raster affine transform
    ----------
    The Transform class implements affine transforms for raster datasets. The
    transform records the coordinates of the left and top edges, as well as the
    pixel spacing along the X and Y axes. Transform objects can be used to compute
    pixel properties for a datasets, including resolution, area, and the length of
    a pixel diagonal.

    You can also use the "affine" property to return the object as an affine.Affine
    object. The "orientation" property indicates how coordinates change when
    incrementing pixel rows or columns. This property returns the quadrant of the
    Cartesian plane that would contain the transform's raster, where the origin
    point is defined as the minimum X and minimum Y coordinate for the raster. As
    follows:

    1: dx >= 0, dy <= 0
    2: dx <  0, dy <= 0
    3: dx <  0, dy >  0
    4: dx >= 0, dy >  0

    A Transform can be converted to a BoundingBox when given a raster shape as input.
    See the "bounds" method to implement this functionality.
    ----------
    PROPERTIES:
    CRS:
        crs             - The coordinate reference system (pyproj.crs or None)
        units           - The units along the X and Y axes
        xunit           - The X axis unit
        yunit           - The Y axis unit

    Misc:
        affine          - The affine.Affine object for the Transform
        left            - The spatial coordinate of the left edge
        top             - The spatial coordinate of the top edge
        orientation     - The cartesian quadrant associated with the Transform

    METHODS:
    Object Creation:
        __init__        - Create Transform from dx, dy, left, top, and optional CRS
        from_dict       - Create Transform from a keyword dict
        from_list       - Create Transform from a list or tuple
        from_affine     - Create Transform from an affine.Affine object
        copy            - Returns a copy of the current Transform

    Resolution:
        dx              - The change in X coordinate when moving one pixel right
        dy              - The change in Y coordinate when moving one pixel down
        xres            - The X-axis resolution. Equal to the absolute value of dx
        yres            - The Y-axis resolution. Equal to the absolute value of dy
        resolution      - An (X resolution, Y resolution) tuple

    Pixel Geometries:
        pixel_area      - The area of a pixel
        pixel_diagonal  - The length of a pixel diagonal

    Units Per Meter:
        units_per_m     - The number of CRS units per meter along the X and Y axes
        x_units_per_m   - The number of X axis units per meter
        y_units_per_m   - The number of Y axis units per meter

    BoundingBox conversion:
        right           - Computes the right edge, given a number of columns
        bottom          - Computes the bottom edge, given a number of rows
        bounds          - Converts Transform to BoundingBox, given the number of raster columns and rows

    Reprojection and CRS:
        reproject       - Returns a copy of a Transform in a new CRS
        match_crs       - Returns a copy of a Transform compatible with an input CRS
        remove_crs      - Returns a copy of the Transform without a CRS

    As built-in:
        tolist          - Returns a transform as a list
        todict          - Returns a transform as a dict

    Testing:
        isclose         - True if an input is a Transform with similar values

    INTERNAL:
        _edge           - Computes the location of a bounding edge
    """

    _names = ["dx", "dy", "left", "top"]

    #####
    # Object Creation
    #####

    def __init__(
        self,
        dx: scalar,
        dy: scalar,
        left: scalar,
        top: scalar,
        crs: Optional[CRSlike] = None,
    ) -> None:
        """
        Creates a new Transform object
        ----------
        Transform(dx, dy, left, top)
        Creates a new Transform from the indicated parameters

        Transform(..., crs)
        Creates a new Transform with an associated CRS
        ----------
        Inputs:
            dx: The change in X-coordinate when moving one pixel right
            dy: The change in Y-coordinate when moving one pixel down
            left: The spatial coordinate of the left edge
            top: The spatial coordinate of the top edge
            crs: The coordinate reference system for the Transform. Must be
                convertible to a pyproj.CRS object

        Outputs:
            Transform: The new Transform object
        """
        super().__init__([dx, dy, left, top], crs)

    @staticmethod
    def from_affine(input: Affine, crs: Optional[CRSlike] = None) -> Transform:
        """
        Creates a Transform from an affine.Affine object
        ----------
        Transform.from_affine(input)
        Transform.from_affine(input, crs)
        Creates a Transform from an affine.Affine object. The affine object must
        have scalar real-valued coefficients, and cannot implement a shear
        transformation. Equivalently, the "b" and "d" coefficients must be 0.
        Affine objects do not include CRS information, so use the "crs" option
        to also probide a CRS.
        ----------
        Inputs:
            input: The affine.Affine object used to create the Transform
            crs: A CRS input for the transform

        Outputs:
            Transform: The new Transform object
        """

        # Require Affine object with float coefficients
        validate.type(input, "Transform input", Affine, "affine.Affine object")
        for coeff in ["a", "b", "c", "d", "e", "f"]:
            value = getattr(input, coeff)
            validate.scalar(value, f"Affine coefficient '{coeff}'", real)

            # Shear matrices are not allowed
            if coeff in ["b", "d"] and value != 0:
                raise TransformError(
                    "The affine transform must only support scaling and translation. "
                    "Equivalently, the affine transformation matrix must have form:\n"
                    "    |a b c|     |a 0 c|\n"
                    "    |d e f|  =  |0 e f|\n"
                    "    |0 0 1|     |0 0 0|\n"
                    "such that coefficients b and d are 0. "
                    f"However, coefficient '{coeff}' is not 0 (value = {value})."
                )

        # Build object
        return Transform(dx=input.a, dy=input.e, left=input.c, top=input.f, crs=crs)

    @staticmethod
    def from_list(input: list | tuple) -> Transform:
        """
        Creates a Transform from a list or tuple
        ----------
        Transform.from_list(input)
        Creates a Transform from a list or tuple. The input may have 4, 5, 6, or
        9 elements. If 6 or 9, the list is used to initialize an affine.Affine
        object, and the Affine object used to derive the transform. If 4 or 5
        elements, then the elements are interpreted as the arguments to the
        constructor (dx, dy, left, top, crs).
        ----------
        Inputs:
            input: The list or tuple used to create the Transform

        Outputs:
            Transform: The new Transform object
        """

        validate.type(input, "Transform sequence", (list, tuple), "list or tuple")
        if len(input) in [6, 9]:
            affine = Affine(*input)
            return Transform.from_affine(affine)
        else:
            return super(Transform, Transform).from_list(input)

    #####
    # Properties
    #####

    @property
    def affine(self) -> Affine:
        "An affine.Affine object derived from the Transform"
        return Affine(self.dx(), 0, self.left, 0, self.dy(), self.top)

    @property
    def orientation(self) -> Quadrant:
        "The Cartesian quadrant associated with the Transform"
        xinverted = self.dx() < 0
        yinverted = self.dy() > 0
        return self._orientation(xinverted, yinverted)

    #####
    # Resolution
    #####

    @staticmethod
    def _validate_y(y: Any | None) -> float | None:
        "Checks that y is valid for unit conversion"
        if y is None:
            return None
        else:
            y = validate.scalar(y, "y", dtype=real)
            validate.finite(y, "y")
            return float(y)

    def dx(self, units: Units = "base", y: Optional[float] = None) -> float:
        """
        Return the change in X coordinate when moving one pixel right
        ----------
        self.dx()
        self.dx(units)
        self.dx(units, y)
        Returns the change in X coordinate when moving one pixel right. By default,
        returns dx in the base unit of the CRS. Use the "units" option to return
        dx in other units instead. Supported units include "meters", "kilometers",
        "feet", and "miles". Note that these options are only supported when the
        Transform has a CRS. If the Transform uses a geographic (angular) coordinate
        system, converts dx to the specified units as if dx were measured along
        the equator. Use the "y" input to specify a different latitude for unit
        conversion. Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            units: The units that dx should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which dx is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float: The dx for the transform
        """
        y = self._validate_y(y)
        return self._length("x", self._dx, "dx", units, y)

    def dy(self, units: Units = "base") -> float:
        """
        Return the change in Y coordinate when moving one pixel down
        ----------
        self.dy()
        self.dy(units)
        Returns the change in Y coordinate when moving one pixel down. By default,
        returns the distance in the base unit of the transform. Use the "units"
        option to return the distance in specific units instead. This option is
        only available when the Transform has a CRS. Supported units include
        "meters", "kilometers", "feet", and "miles".
        ----------
        Inputs:
            units: The units that dy should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The dy for the transform
        """
        return self._length("y", self._dy, "dy", units)

    def xres(self, units: Units = "base", y: Optional[float] = None) -> float:
        """
        Return pixel resolution along the X axis
        ----------
        self.xres()
        self.xres(units)
        self.xres(units, y)
        Returns the pixel resolution along the X axis (the absolute value of dx).
        By default, returns xres in the base units of the CRS. Use the "units" option
        to return xres in other units instead. Supported units include "meters", "kilometers",
        "feet", and "miles". Note that these options are only supported when the
        Transform has a CRS. If the Transform uses a geographic (angular) coordinate
        system, converts xres to the specified units as if xres were measured along
        the equator. Use the "y" input to specify a different latitude for unit
        conversion. Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            units: The units that xres should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Deafults to the equator

        Outputs:
            float: The X resolution for the Transform
        """
        return abs(self.dx(units, y))

    def yres(self, units: Units = "base") -> float:
        """
        Return pixel resolution along the Y axis
        ----------
        self.yres()
        self.yres(units)
        Returns the pixel resolution along the Y axis. This is the absolute value
        of dy. By default, returns resolution in the base unit of the Transform.
        Use the "units" option to return yres in the specified units instead.
        This option is only available when the Transform has a CRS. Supported
        units include: "meters", "kilometers", "feet", and "miles".
        ----------
        Inputs:
            units: The units that yres should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"

        Outputs:
            float: The Y resolution for the Transform
        """
        return abs(self.dy(units))

    def resolution(
        self, units: Units = "base", y: Optional[float] = None
    ) -> tuple[float, float]:
        """
        Return pixel resolution
        ----------
        self.resolution()
        self.resolution(units)
        self.resolution(units, y)
        Returns the pixel resolution for the Transform as an (X res, Y res) tuple.
        By default, returns resolution in the base units of the Transform CRS.
        Use the "units" option to return resolution in the specified units instead.
        Supported units include "meters", "kilometers", "feet", and "miles". Note
        that these options are only supported when the Transform has a CRS. If the
        Transform uses a geographic (angular) coordinate system, converts resolution
        to the specified units as if resolution were measured along the equator.
        Use the "y" input to specify a different latitude for unit conversion.
        Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            units: The units that resolution should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float, float: The (X, Y) resolution for the Transform
        """
        return self.xres(units, y), self.yres(units)

    #####
    # Pixel geometries
    #####

    def pixel_area(self, units: Units = "base", y: Optional[float] = None) -> float:
        """
        Returns the area of a pixel for the Transform
        ----------
        self.pixel_area()
        self.pixel_area(units)
        self.pixel_area(units, y)
        Returns the area of a pixel for the Transform. By default, returns area
        in the units of the CRS squared. Use the "units" option to return area
        in the specified units instead. Supported units include: "meters", "kilometers",
        "feet", and "miles". This option is only available when the Transform has
        a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts area to the indicated units as if x-resolution were measured along
        the equator. Use the "y" input to specify a different latitude for unit
        conversion. Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            units: The (squared) units that pixel_area should be returned in. Options
                include: "base" (default; CRS base units), "meters", "kilometers",
                "feet", and "miles"
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float: The area of a pixel in the Transform
        """
        xres, yres = self.resolution(units, y)
        return xres * yres

    def pixel_diagonal(self, units: Units = "base", y: Optional[float] = None) -> float:
        """
        Returns the area of a pixel for the Transform
        ----------
        self.pixel_diagonal()
        self.pixel_diagonal(units)
        self.pixel_diagonal(units, y)
        Returns the length of a pixel diagonal for the Transform. By default, returns length
        in the units of the CRS squared. Use the "units" option to return length
        in the specified units instead. Supported units include: "meters", "kilometers",
        "feet", and "miles". This option is only available when the Transform has
        a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts length to the indicated units as if x-resolution were measured along
        the equator. Use the "y" input to specify a different latitude for unit
        conversion. Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            units: The units that the length should be returned in. Options include:
                "base" (default; CRS base units), "meters", "kilometers", "feet",
                and "miles"
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float: The length of a pixel diagonal in the Transform
        """
        xres, yres = self.resolution(units, y)
        return sqrt(xres**2 + yres**2)

    #####
    # Units per meter
    #####

    def x_units_per_m(self, y: Optional[float] = None) -> float | None:
        """
        Returns the number of X axis units per meter
        ----------
        self.x_units_per_m()
        self.x_units_per_m(y)
        Returns the number of X axis units per meter. None if the Transform does
        not have a CRS. If the Transform uses an angular (geographic) CRS, converts
        units to meters as if along the equator. Use the "y" input to specify a
        different latitude for meters conversion. Note that y should be in the
        base units of the CRS.
        ----------
        Inputs:
            y: An optional Y coordinate (in the units of the CRS) indicating the
                latitude at which meters converson is assessed. Ignored if the
                CRS is not angular (geographic). Defaults to the equator.

        Outputs:
            float | None: The number of X axis units per meter
        """
        y = self._validate_y(y)
        value = _crs.x_units_per_m(self.crs, y)
        return self._parse_unit(value)

    def y_units_per_m(self) -> float | None:
        """
        Returns the number of Y units per meter
        ----------
        self.y_units_per_m()
        Returns the number of Y axis units per meter, or None if the Transform
        does not have a CRS.
        ----------
        Outputs:
            float | None: The number of Y axis units per meter.
        """

        # Converting from property to function for consistency with x_units_per_m
        return super(Transform, self).y_units_per_m

    def units_per_m(
        self, y: Optional[float] = None
    ) -> tuple[float, float] | tuple[None, None]:
        """
        Returns the number of units per meter along the X and Y axes
        ----------
        self.units_per_m()
        self.units_per_m(y)
        Returns the number of CRS axis units per meter. None if the Transform does
        not have a CRS. Otherwise, returns a tuple with the values for the X and
        Y axes, respectively. If the Transform uses an angular (geographic) CRS,
        converts units to meters as if along the equator. Use the "y" input to
        specify a different latitude for meters conversion. Note that y should be
        in the units of the CRS.
        ----------
        Inputs:
            y: An optional Y coordinate (in the units of the CRS) indicating the
                latitude at which meters conversion is assessed. Ignored if the
                CRS is not angular (geographic). Defaults to the equator.

        Outputs:
            (float, float) | (None, None): The conversion factors for the X and Y axes,
                or None if the Transform does not have a CRS
        """
        x = self.x_units_per_m(y)
        y = self.y_units_per_m()
        return x, y

    #####
    # Bounds Conversion
    #####

    def _edge(self, N: int, name: str, min: float, delta: float) -> float:
        "Locates a bounding box edge given the number of rows or columns"
        N = self._validate_N(N, name, allow_zero=True)
        return min + N * delta

    def right(self, ncols: int) -> float:
        """
        Compute the right edge of a bounding box
        ----------
        self.right(ncols)
        Computes the location of the right edge of a raster with the given number
        of columns for the Transform.
        ----------
        Inputs:
            ncols: The number of raster columns

        Outputs:
            float: The spatial coordinate of the raster's right edge
        """
        return self._edge(ncols, "ncols", self.left, self.dx())

    def bottom(self, nrows: int) -> float:
        """
        Compute the bottom edge of a bounding box
        ----------
        self.bottom(nrows)
        Computes the location of the bottom edge of a raster with the given number
        of rows for the Transform.
        ----------
        Inputs:
            nrows: The number of raster rows

        Outputs:
            float: The spatial coordinate of the raster's bottom edge
        """
        return self._edge(nrows, "nrows", self.top, self.dy())

    def bounds(self, nrows: int, ncols: int) -> BoundingBox:
        """
        bounds  Returns a BoundingBox object derived from the Transform
        ----------
        self.bounds(nrows, ncols)
        Converts the Transform to a BoundingBox object, given a number of raster
        rows and columns.
        ----------
        Inputs:
            nrows: The number of raster rows
            ncols: The number of raster columns

        Outputs:
            BoundingBox: A BoundingBox object derived from the Transform
        """
        right = self.right(ncols)
        bottom = self.bottom(nrows)
        return projection.BoundingBox(self.left, bottom, right, self.top, self.crs)

    #####
    # Reprojection
    #####

    def reproject(self, crs: CRSlike) -> Transform:
        """
        Reprojects the Transform into a different CRS
        ----------
        self.reproject(crs)
        Reprojects the Transform into a different CRS. Note that Transform reprojections
        are often less accurate than BoundingBox reprojections. As such, this method is
        not recommended when a raster shape is also available. In this case, you can
        achieve a more accurate reprojection by: (1) converting the Transform to a
        BoundingBox, (2) reprojecting the BoundingBox, and (3) converting the
        reprojected box back to a Transform.
        ----------
        Inputs:
            crs: The CRS in which to reproject the Transform

        Outputs:
            Transform: The reprojected Transform
        """

        # Validate. Just exit if it's the same CRS
        crs = self._validate_reprojection(crs)
        if crs == self.crs:
            return self.copy()

        # Reproject coordinates of next pixel. Use to compute dx and dy
        left, top = _crs.reproject(self.crs, crs, self.left, self.top)
        right = self.left + self.dx()
        bottom = self.top + self.dy()
        right, bottom = _crs.reproject(self.crs, crs, right, bottom)
        dx = right - left
        dy = bottom - top
        return Transform(dx, dy, left, top, crs)
