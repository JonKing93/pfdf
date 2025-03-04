"""
nodata  Support for working with NoData values
----------
The nodata module includes various utilities for efficiently working with NoData
values in raster datasets. The "equal" and "isin" are standalone functions to
support comparison of NoData values. The remainder of the module is the NodataMask
class, which provides objects that facilitate working with nodata/data masks.
All the utilities in this module support the case wherein a NoData value is None.
----------
Comparison Functions:
    equal       - True if two NoData values are equal
    isin        - True if an array contains a NoData value
    mask        - Returns a boolean nodata mask for an array

Class:
    NodataMask  - Objects to facilitate working with nodata/data masks
"""

from __future__ import annotations

import operator
import typing

import numpy as np
from numpy import isnan

from pfdf._utils import aslist, no_nones

if typing.TYPE_CHECKING:
    from typing import Callable, Optional

    from pfdf._utils.nodata import NodataMask
    from pfdf.typing.core import BooleanArray, RealArray, VectorArray, ignore, scalar

    other = NodataMask | BooleanArray | None
    nodata = scalar | None


def mask(array: RealArray, nodata: nodata) -> BooleanArray:
    "Returns a boolean nodata mask for an array"

    if nodata is None:
        return np.zeros(array.shape, bool)
    elif isnan(nodata):
        return isnan(array)
    else:
        return array == nodata


def equal(nodata1: nodata, nodata2: nodata) -> bool:
    """
    equal  True if two NoData values are equal
    ----------
    equal(nodata1, nodata2)
    True if two NoData values are equal. Otherwise False. NoData values are
    considered equal if they are the same numeric value, both None, or both NaN.
    ----------
    Inputs:
        nodata1: The first nodata value in the comparison
        nodata2: The second nodata value in the comparison

    Outputs:
        bool: True if the two NoData values are equal. Otherwise False
    """

    if no_nones(nodata1, nodata2) and isnan(nodata1) and isnan(nodata2):
        return True
    else:
        return nodata1 == nodata2


def isin(array: RealArray, nodata: nodata) -> bool:
    """
    isin  True if any elements of an array are NoData
    ----------
    isin(array, nodata)
    True if nodata is not None and any elements of the array match the NoData
    values. Otherwise False.
    ----------
    Inputs:
        array: The array whose elements are being compared to NoData
        nodata: The NoData value

    Outputs:
        bool: Whether the array contains NoData values
    """

    if nodata is None:
        return False
    else:
        nodata = mask(array, nodata)
        return np.any(nodata)


class NodataMask:
    """
    NodataMask  Objects for working with nodata/data masks that may be boolean arrays or None
    ----------
    The NodataMask class provides objects that work efficiently with NoData and
    data masks. In a basic setup, a nodata/data mask consists of a boolean array.
    However, these arrays are not strictly necessary when NoData values are None, and
    so the class doesn't build a mask when this is the case. The class methods
    then facilitate common logical indexing / element-wise comparison tasks, while
    allowing for the possibility that there is no boolean mask in memory.

    When there is no mask in memory, the __or__ method interprets every element
    as False. By contrast, the "indices" and "values" methods interpret every
    element as True. This behavior supports the Nodata mask/valid data mask
    workflows intended for these methods.
    ----------
    Attributes:
        size        - The size of the array used to derive the mask
        mask        - Boolean array or None

    Object Creation:
        __int__     - Create an object to track the locations of data or nodata elements
        _mask       - Returns a boolean array mask

    NoData workflows:
        __or__      - Element-wise logical "or" of two masks
        fill        - Returns an array in which mask elements are replaced by a fill value
        isnan       - True if a NoData value is NaN

    Data workflows:
        indices     - Returns the linear indices of the True elements of the mask
        values      - Returns array values at the mask indices
    """

    # Type hint

    #####
    # Object Creation
    #####

    def __init__(self, array: RealArray, nodata: ignore, invert: bool = False) -> None:
        """
        __int__  Create a new NodataMask object
        ----------
        NodataMask(array, nodata)
        Given an array of data values, records the locations of NoData elements
        within the array. Only builds a boolean mask array if nodata is not None.

        NodataMask(array, nodata, invert=True)
        Records the locations of data elements within the array. Only builds a
        boolean mask array if nodata is not None.
        ----------
        Inputs:
            array: An array of data values
            nodata: A value, or list of values that are considered NoData.
            invert: True to track the locations of data elements. False to track
                locations of NoData elements

        Outputs:
            NodataMask: The new NodataMask object
        """

        # Initialize attributes
        self.mask: Optional[BooleanArray] = None
        self.size: int = array.size

        # Remove None NoDatas
        nodata = aslist(nodata)
        nodata = [value for value in nodata if value is not None]
        nodata = np.unique(nodata)

        # Build the mask
        if nodata.size == 0:
            self.mask = None
        else:
            self.mask = mask(array, nodata[0])
            for k in range(1, nodata.size):
                self.mask = self.mask | mask(array, nodata[k])

            # Optionally invert
            if invert:
                self.mask = ~self.mask

    #####
    # Element-wise logical operators
    #####

    def _logical(self, operator: Callable, other: other) -> NodataMask:
        "Implements an element-wise logical operator like 'and' or 'or'."

        # Extract the mask array if the second object is also a NodataMask object
        if isinstance(other, NodataMask):
            other = other.mask

        # Get the final mask
        if other is None:
            final = self.mask
        elif self.mask is None:
            final = other
        else:
            final = operator(self.mask, other)

        # Return the new object
        mask = super().__new__(NodataMask)
        mask.mask = final
        mask.size = self.size
        return mask

    def __or__(self, other: other) -> NodataMask:
        """
        __or__  Element-wise logical "or" for nodata masks
        ----------
        self | mask
        Computes an element-wise logical "or" over the elements of two NodataMasks.
        Returns a new NodataMask representing the True elements of the logical "or".
        ----------
        Inputs:
            other: Another representation of a nodata mask

        Outputs:
            NodataMask: A new mask tracking the True elements of the logical "or"
        """

        return self._logical(operator.or_, other)

    def __and__(self, other: other) -> NodataMask:
        """
        __and__  Element-wise logical "and" for nodata masks
        ----------
        self & mask
        Computes an element-wise logical "and" over the elements of two masks.
        Returns a new NodataMask representing the True elements of the logical "and".
        ----------
        Inputs:
            other: Another representation of a mask

        Outputs:
            NodataMask: A new mask tracking the True elements of the logical "and"
        """

        return self._logical(operator.and_, other)

    #####
    # Workflow methods
    #####

    def fill(self, array: RealArray, fill: nodata, invert: bool = False) -> RealArray:
        """
        fill  Returns an array in which mask elements are replaced with a fill value
        ----------
        self.fill(array, fill)
        Returns an array for which the True mask elements have been replaced with a
        fill value. Alters the original array in-place whenever possible.

        self.fill(array, fill, invert=True)
        Returns an array for which the False mask elements have been replaced with
        a fill value.
        ----------
        Inputs:
            array: An array of data values matching the size of the mask
            fill: A fill value for the array

        Outputs:
            ndarray: An array in which the mask elements have been replaced with
                a fill value.
        """

        # Handle case when there isn't a mask
        if self.mask is None:
            if invert:
                shape = [0] * array.ndim
                return np.empty(shape, dtype=array.dtype)
            else:
                return array

        # If filling with NaN, need to ensure the array has a float dtype
        if isnan(fill) and not np.issubdtype(array.dtype, np.floating):
            array = array.astype(float, copy=False)

        # Fill values
        mask = self.mask
        if invert:
            mask = ~mask
        array[mask] = fill
        return array

    def indices(self) -> VectorArray:
        """
        indices  Returns the indices of the True elements of the mask
        ----------
        self.indices()
        Returns the linear indices of the mask elements that are considered True.
        ----------
        Outputs:
            1D integer numpy array: The linear indices of the mask elements that
                are considered True
        """

        indices = np.arange(self.size)
        if self.mask is not None:
            mask = self.mask.reshape(-1)
            indices = indices[mask]
        return indices

    @staticmethod
    def isnan(nodata: nodata) -> bool:
        """
        isnan  True if a NoData value is NaN, allowing for nodata=None
        ----------
        NodataMask.isnan(nodata)
        Returns True if the input NoData value is NaN. Otherwise, returns False.
        Note that this method returns False when the input nodata value is None.
        ----------
        Inputs:
            nodata: The nodata value being tested

        Outputs:
            bool: True if the ndoata value was NaN. Otherwise False.
        """

        if nodata is None:
            return False
        else:
            return isnan(nodata)

    def values(self, array: RealArray) -> RealArray:
        """
        values  Returns the values of an array at the True elements of the mask
        ----------
        self.values(array)
        Returns the values of the input array that are at the True elements of
        the mask.
        ----------
        Inputs:
            array: An array for which to return the values at the True mask elements
        """
        if self.mask is None:
            return array
        else:
            return array[self.mask]
