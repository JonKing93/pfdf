"""
Class for working with Raster affine transforms
----------
Class:
    Transform   - Class to represent a Raster affine transform
"""

from math import sqrt
from typing import Any, Optional, Self

from affine import Affine

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import TransformError
from pfdf.projection import CRSInput, _crs, _Locator, bbox
from pfdf.typing import scalar


class Transform(_Locator):
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

    Reprojection:
        reproject       - Returns a copy of a Transform in a new CRS

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
        crs: Optional[CRSInput] = None,
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
    def from_affine(input: Affine, crs: Optional[CRSInput] = None) -> Self:
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
    def from_list(input: list | tuple) -> Self:
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
    def orientation(self):
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
            return y

    def dx(self, meters: bool = False, y: Optional[float] = None) -> float:
        """
        Return the change in X coordinate when moving one pixel right
        ----------
        self.dx()
        Returns the change in X coordinate when moving one pixel right.

        self.dx(meters=True)
        self.dx(meters=True, y)
        Returns dx in meters. This option is only available when the Transform
        has a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts dx to meters as if dx were measured along the equator. Use the
        "y" input to specify a different latitude for meters conversion. Note that
        y should be in the base units of the CRS.
        ----------
        Inputs:
            meters: True to return dx in meters. False (default) to return dx in
                the default unit of the Transform
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which dx is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float: The dx for the transform
        """

        # Validate y and meters conversion
        self._validate_conversion(meters, "dx")
        y = self._validate_y(y)

        # Compute dx, converting to meters as appropriate
        dx = self._dx
        if meters:
            dx = _crs.dx_to_meters(self.crs, dx, y)
        return dx

    def dy(self, meters: bool = False) -> float:
        """
        Return the change in Y coordinate when moving one pixel down
        ----------
        self.dy()
        self.dy(meters=True)
        Returns the change in Y coordinate when moving one pixel down. By default,
        return the distance in the default unit of the transform. Set meters=True
        to return the distance in meters instead. Note that the meters option is
        only available when the Transform has a CRS.
        ----------
        Inputs:
            meters: True to return dy in meters. False (default) to return dy in
                the default unit of the Transform

        Outputs:
            float: The dy for the transform
        """

        self._validate_conversion(meters, "dy")
        dy = self._dy
        if meters:
            dy = _crs.dy_to_meters(self.crs, dy)
        return dy

    def xres(self, meters: bool = False, y: Optional[float] = None) -> float:
        """
        Return pixel resolution along the X axis
        ----------
        self.xres()
        Returns the pixel resolution along the X axis (the absolute value of dx)
        in the units of the CRS.

        self.xres(meters=True)
        self.xres(meters=True, y)
        Returns xres in meters. This option is only available when the Transform
        has a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts xres to meters as if xres were measured along the equator. Use the
        "y" input to specify a different latitude for meters conversion. Note that
        y should be in the base units of the CRS.
        ----------
        Inputs:
            meters: True to return xres in meters. False (default) to return
                xres in the default unit of the Transform
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Deafults to the equator

        Outputs:
            float: The X resolution for the Transform
        """
        return abs(self.dx(meters, y))

    def yres(self, meters: bool = False) -> float:
        """
        Return pixel resolution along the Y axis
        ----------
        self.yres()
        self.yres(meters=True)
        Returns the pixel resolution along the Y axis. This is the absolute value
        of dy. By default, returns resolution in the default unit of the Transform.
        Set meters=True to return the distance in meters instead. Note that the
        meters option is only available when the Transform has a CRS.
        ----------
        Inputs:
            meters: True to return resolution in meters. False (default) to
                return resolution the default unit of the Transform

        Outputs:
            float: The Y resolution for the Transform
        """
        return abs(self.dy(meters))

    def resolution(
        self, meters: bool = False, y: Optional[float] = None
    ) -> tuple[float, float]:
        """
        Return pixel resolution
        ----------
        self.resolution()
        Returns the pixel resolution for the Transform. This is an (X res, Y res)
        tuple in the units of the Transform CRS.

        self.resolution(meters=True)
        self.resolution(meters=True, y)
        Returns resolution in meters. This option is only available when the Transform
        has a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts resolution to meters as if xres were measured along the equator.
        Use the "y" input to specify a different latitude for meters conversion.
        Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            meters: True to return resolution in meters. False (default) to
                return resolution the default unit of the Transform
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float, float: The (X, Y) resolution for the Transform
        """
        return self.xres(meters, y), self.yres(meters)

    #####
    # Pixel geometries
    #####

    def pixel_area(self, meters: bool = False, y: Optional[float] = None) -> float:
        """
        Returns the area of a pixel for the Transform
        ----------
        self.pixel_area()
        Returns the area of a pixel for the Transform in the units of the CRS squared.

        self.pixel_area(meters=True)
        self.pixel_area(meters=True, y)
        Returns area in meters squared. This option is only available when the Transform
        has a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts area to meters as if x-resolution were measured along the equator.
        Use the "y" input to specify a different latitude for meters conversion.
        Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            meters: True to return area in meters^2. False (default) to
                return resolution the default unit of the Transform squared
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float: The area of a pixel in the Transform
        """
        xres, yres = self.resolution(meters, y)
        return xres * yres

    def pixel_diagonal(self, meters: bool = False, y: Optional[float] = None) -> float:
        """
        Returns the area of a pixel for the Transform
        ----------
        self.pixel_diagonal()
        Returns the length of a pixel diagonal for the Transform in the CRS units.

        self.pixel_diagonal(meters=True)
        self.pixel_diagonal(meters=True, y)
        Returns length in meters. This option is only available when the Transform
        has a CRS. If the Transform uses a geographic (angular) coordinate system,
        converts length to meters as if x-resolution were measured along the equator.
        Use the "y" input to specify a different latitude for meters conversion.
        Note that y should be in the base units of the CRS.
        ----------
        Inputs:
            meters: True to return length in meters. False (default) to
                return resolution the default unit of the Transform
            y: An optional y coordinate (in the units of the CRS) indicating the
                latitude at which xres is being assessed. Ignored if the CRS is not
                geographic (angular). Defaults to the equator

        Outputs:
            float: The length of a pixel diagonal in the Transform
        """
        xres, yres = self.resolution(meters, y)
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
        not have a CRS. If the Transofrm uses an angular (geographic) CRS, converts
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
        return _crs.x_units_per_m(self.crs, y)

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

        # Converting from property to function for consistency with x_per_m
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
        N = self._validate_N(N, name)
        return min + N * delta

    def right(self, ncols: int) -> float:
        """
        Compute the right edge of a bounding box
        ----------
        self.right(ncols)
        Computes the locates of the right edge of a raster with the given number
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
        Computes the locates of the bottom edge of a raster with the given number
        of rows for the Transform.
        ----------
        Inputs:
            nrows: The number of raster rows

        Outputs:
            float: The spatial coordinate of the raster's bottom edge
        """
        return self._edge(nrows, "nrows", self.top, self.dy())

    def bounds(self, nrows: int, ncols: int) -> "bbox.BoundingBox":
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
        return bbox.BoundingBox(self.left, bottom, right, self.top, self.crs)

    #####
    # Reprojection
    #####

    def reproject(self, crs: CRSInput, y: Optional[float] = None) -> Self:
        """
        Reprojects the Transform into a different CRS
        ----------
        self.reproject(crs)
        self.reproject(crs, y)
        Reprojects the Transform into a different CRS. By default, reprojects the
        Transform as for a dataset located at the equator. Use the "y" input to
        specify a different latitude for reprojection. Note that y should be in
        the base unit of the current CRS.
        ----------
        Inputs:
            crs: The CRS in which to reproject the Transform
            y: The Y coordinate at which to perform the reprojection. Defaults to
                the equator.

        Outputs:
            Transform: The reprojected Transform
        """

        # Validate. Reproject left and top coordinates
        crs = self._validate_reprojection(crs)
        left, top = _crs.reproject(self.crs, crs, self.left, self.top)

        # Reproject coordinates of next pixel. Use to compute dx and dy
        right = self.left + self.dx(y=y)
        bottom = self.top + self.dy()
        right, bottom = _crs.reproject(self.crs, crs, right, bottom)
        dx = right - left
        dy = bottom - top
        return Transform(dx, dy, left, top, crs)
