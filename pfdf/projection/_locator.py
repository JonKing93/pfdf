"""
Base class for BoundingBox and Transform objects
----------
Class:
    _Locator    - Base class for BoundingBox and Transform objects
"""

from abc import ABC, abstractmethod
from typing import Any, Self

import numpy as np
from pyproj import CRS

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import CRSError, MissingCRSError
from pfdf.projection import CRSInput, _crs
from pfdf.typing.core import XY, Quadrant, Units, scalar


class _Locator(ABC):
    """
    Base class for BoundingBox and Transform objects
    ----------
    This class provides base functionality for the BoundingBox and Transform
    classes. These two classes are broadly similar - both use the location of
    the top-left coordinate, 2 additional numbers, and an optional CRS to partially
    locate a raster in space. When combined with the shape of a raster array, they
    provide a complete spatial reference. As such, the two classes are complementary
    ways of representing location information, and may be converted when provided
    with a raster shape.

    Both classes also have similar user-experiences within pfdf. Typically,
    these classes are used by raster preprocessing methods and are provided via
    a single arg (either "bounds" for a BoundingBox, or "transform" for a Transform).
    When provided as a user arg, pfdf supports multiple flavors of inputs including
    from a Raster, BoundingBox/Transform, dict, or None, with broadly similar
    conversion mechanics. This class provides the shared code for these mechanics.

    The distinction between the classes lies in how they encode spatial information.
    A Transform class focuses on pixels and pixel resolutions, whereas a BoundingBox
    provides the edges (and thereby center) of the raster array. As such, resolution
    and edge functionality is left to the individual classes.
    ----------
    **PROPERTIES**
    Class:
        _names          - The names of the 4 floats as they appear in the constructor
        _atts           - The names of the attributes to query for list conversion
        _args           - The names of dict keyword args
        _class          - The name of an object's class as a string

    CRS:
        crs             - The coordinate reference system
        xunit           - X axis unit
        yunit           - Y axis unit
        units           - (X unit, Y unit) tuple

    Units per meter:
        x_units_per_m   - Abstract property for X axis conversion factor
        y_units_per_m   - Y axis conversion factor
        units_per_m     - Abstract property for (X conversion, Y conversion) tuple

    Spatial:
        left            - Left edge coordinate
        top             - Top edge coordinate
        orientation     - Abstract property for cartesian quadrant of the object

    **METHODS**
    Object Creation:
        __init__        - Initializes object from 4 floats and an optional CRS
        from_dict       - Builds object from a keyword dict
        from_list       - Builds object from a list of 4 or 5 elements
        copy            - Returns a copy of the object

    Dunders:
        __repr__    - String representation using class name, float values, and CRS name
        __eq__      - True if the other object is the same class and has matching floats/CRS

    Validation:
        _validate_reprojection  - Checks there are two CRSs for reprojection
        _validate_units         - Checks that unit conversion is supported

    Class Conversion:
        _validate_N     - Checks that nrows or ncols is valid
        tolist          - Returns the object as a list
        todict          - Returns the object as a dict

    Misc:
        _orientation    - Returns cartesian quadrant given inversion status
        _length         - Convert a length along an axis to the requested units
        isclose         - True if two objects have similar floats and the same CRS
    """

    #####
    # Class attributes
    #####

    @property
    @abstractmethod
    def _names(self) -> tuple[str, str, str, str]:
        "The names of the 4 floats, in the order they appear in the constructor"

    @property
    def _atts(self) -> tuple[str, str, str, str, str]:
        "The names of the attributes that should be extracted for list conversion"
        return [f"_{name}" for name in self._names] + ["crs"]

    @classmethod
    def _args(cls) -> tuple[str, str, str, str, str]:
        "The names of dict keyword args"
        return cls._names + ["crs"]

    @property
    def _class(self) -> str:
        return type(self).__name__

    #####
    # CRS Properties
    #####

    @property
    def crs(self) -> CRS | None:
        "Coordinate reference system"
        return self._crs

    @property
    def xunit(self) -> str | None:
        return _crs.xunit(self.crs)

    @property
    def yunit(self) -> str | None:
        return _crs.yunit(self.crs)

    @property
    def units(self) -> tuple[str, str] | tuple[None, None]:
        return _crs.units(self.crs)

    ##### Units per meter

    @abstractmethod
    def x_units_per_m(self, *args) -> float | None:
        "The number of units per meter along the X axis"

    @property
    def y_units_per_m(self) -> float | None:
        "The number of Y axis units per meter"
        return _crs.y_units_per_m(self.crs)

    @abstractmethod
    def units_per_m(self, *args) -> tuple[float, float] | tuple[None, None]:
        "The number of CRS units per meter along the X and Y axes"

    #####
    # Spatial properties
    #####

    @property
    def left(self) -> float:
        "The left coordinate"
        return self._left

    @property
    def top(self) -> float:
        "The top coordinate"
        return self._top

    @property
    @abstractmethod
    def orientation(self) -> Quadrant:
        "The Cartesian quandrant associated with the projection object"

    #####
    # Object creation
    #####

    def __init__(
        self, floats: tuple[scalar, scalar, scalar, scalar], crs: CRSInput
    ) -> None:
        "Initializes object from 4 floats and an optional CRS"

        for attr, value in zip(self._atts[:-1], floats):
            value = validate.scalar(value, attr[1:], dtype=real)
            validate.finite(value, attr[1:])
            setattr(self, attr, value)
        self._crs = _crs.validate(crs)

    @classmethod
    def from_dict(cls, input: dict) -> Self:
        """
        Builds a projection class from a keyword dict
        ----------
        Class.from_dict(input)
        Builds a Transform or BoundingBox object from a keyword dict. The dict
        may have either 4 or 5 keys, and each key must be a string. The dict must
        include a key for each of the four floats used to initialize the projection
        class, and the value of each key should be a float. The dict may optionally
        include a "crs" key, which will be used to add CRS information to the object.
        ----------
        Inputs:
            input: A dict used to create a projection class

        Outputs:
            Transform | BoundingBox: The projection class being created
        """

        name = f"{cls.__name__} dict"
        args = cls._args()
        validate.type(input, name, dict, "dict")
        for key in args[:-1]:
            if key not in input:
                raise KeyError(f"{name} is missing the '{key}' key")
        for key in input.keys():
            if key not in args:
                raise KeyError(f"{name} has an unrecognized key: {key}")
        return cls(**input)

    @classmethod
    def from_list(cls, input: tuple | list) -> Self:
        """
        Creates a Transform or BoundingBox from a list or tuple
        ----------
        Class.from_list(input)
        Creates a Transform or BoundingBox from an input list or tuple. The input
        may have either 4 or 5 or five elements. The first four elements should
        be floats and correspond to the four floats used to initialize the object.
        The optional fifth element should be a value used to add CRS information
        to the object.
        ----------
        Inputs:
            input: A list or tuple with either 4 or 5 elements.

        Outputs:
            Transform | BoundingBox: The projection class being created
        """
        name = f"{cls.__name__} sequence"
        validate.type(input, name, (list, tuple), "list or tuple")
        if len(input) not in [4, 5]:
            raise ValueError(
                f"{name} must have either 4 or 5 elements, "
                f"but it has {len(input)} elements instead."
            )
        return cls(*input)

    def copy(self) -> Self:
        """
        Returns a copy of a projection class
        ----------
        self.copy()
        Returns a copy of the current object with the same values and CRS.
        ----------
        Outputs:
            Transform | BoundingBox: A copy of the current object
        """
        return self.from_dict(self.todict())

    #####
    # Dunders
    #####

    def __repr__(self) -> str:
        "String representation including class name, float values, and CRS name"
        args = self.todict()
        crs = _crs.name(self.crs)
        if crs != "None":
            crs = f'"{crs}"'
        args["crs"] = crs
        args = ", ".join([f"{name}={value}" for name, value in args.items()])
        return f"{self._class}({args})"

    def __eq__(self, other: Any) -> bool:
        "True if other is the same class, and has the same values and CRS"
        return isinstance(other, type(self)) and (self.tolist() == other.tolist())

    #####
    # Orientation
    #####

    @staticmethod
    def _orientation(xinverted: bool, yinverted: bool) -> Quadrant:
        if xinverted and yinverted:
            return 3
        elif xinverted:
            return 2
        elif yinverted:
            return 4
        else:
            return 1

    #####
    # CRS Validation
    #####

    def _validate_reprojection(self, crs: Any) -> CRS:
        "Checks there are two valid CRSs for reprojection"
        if self.crs is None:
            raise MissingCRSError(
                f"Cannot reproject the {self._class} because it does not have a CRS."
            )
        elif crs is None:
            raise CRSError("The 'crs' input cannot be None")
        return _crs.validate(crs)

    def _validate_units(self, units: Any, name: str, direction: str = "to"):
        units = validate.units(units)
        if units != "base" and self.crs is None:
            raise MissingCRSError(
                f"Cannot convert {name} {direction} {units} because the {self._class} "
                "does not have a CRS."
            )
        return units

    #####
    # Class conversion
    #####

    @staticmethod
    def _validate_N(N: Any, name: str) -> int:
        "Checks that nrows or ncols is valid"
        N = validate.scalar(N, name, real)
        validate.positive(N, name, allow_zero=True)
        validate.integers(N, name)
        return int(N)

    def tolist(self, crs: bool = True) -> list:
        """
        Returns the object as a list
        ----------
        self.tolist()
        self.tolist(crs=False)
        Returns the current object as a list. By default, the list will have 5
        elements. The first four elements are the floats used to define the object,
        and the fifth element is the CRS information. Set crs=False to exclude the
        CRS information and only return a list with 4 elements.
        ----------
        Inputs:
            crs: True (default) to return CRS information as the 5th element.
                False to exclude CRS information and return a list with 4 elements.

        Outputs:
            list: The current object as a list
        """
        output = [getattr(self, att) for att in self._atts]
        if not crs:
            output = output[:-1]
        return output

    def todict(self) -> dict:
        """
        Returns object as a dict
        ----------
        self.todict()
        Returns the object as a dict. The dict will have 5 keys. The first four
        are the floats used to define the object. The 5th key is "crs" and holds
        the associated CRS information.
        ----------
        Outputs:
            dict: The object as a dict
        """
        return {name: value for name, value in zip(self._args(), self.tolist())}

    #####
    # Testing
    #####

    def isclose(
        self,
        other: Self,
        rtol: scalar = 1e-5,
        atol: scalar = 1e-8,
    ) -> bool:
        """
        True if two projection objects are similar
        ----------
        self.isclose(other)
        Tests if another projection class object has similar values to the current
        object. Compares both the CRSs and the 4 float values. Uses numpy.allclose
        to compare the 4 float values. True if numpy.allclose return True AND the
        two objects have compatible CRSs. (Two CRSs are compatible if the two CRSs
        are equal, or at least one CRS is None).

        self.isclose(..., rtol, atol)
        Specify the relative tolerance and absolute tolerance for the
        numpy.allclose check. By default, uses a relative tolerance of 1E-5,
        and an absolute tolerance of 1E-8.
        ----------
        Inputs:
            other: Another object of the same projection class
            rtol: The relative tolerance for float comparison. Defaults to 1E-5.
            atol: The absolute tolerance for float comparison. Defaults to 1E-8

        Outputs:
            bool: True if the other object is similar to the current object
        """

        # Require same type of class
        if not isinstance(other, self.__class__):
            raise TypeError(f"Other object must also be a {self._class} object.")

        # False if different CRS
        if _crs.different(self.crs, other.crs):
            return False

        # Collect floats and compare
        selfs = self.tolist(crs=False)
        others = other.tolist(crs=False)
        return np.allclose(selfs, others, rtol=rtol, atol=atol)

    #####
    # Axis length units
    #####

    def _length(
        self, axis: XY, length: float, name: str, units: Units, y: float | None = None
    ) -> float:
        units = self._validate_units(units, name)
        if units != "base":
            length = _crs.base_to_units(self.crs, axis, length, units, y)
        return length
