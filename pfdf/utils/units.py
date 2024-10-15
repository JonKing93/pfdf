"""
Functions to convert distances between different units
----------
Functions:
    supported   - Returns a list of supported unit options
    convert     - Converts distances from one unit to another
    units_per_m - Returns the conversion factors from supported units to meters
"""

import pfdf._validate.core as validate
from pfdf._utils import real, units
from pfdf.typing.core import RealArray


def units_per_meter() -> dict[str, float]:
    """
    Returns conversion factors between supported units and meters
    ----------
    units_per_meter()
    Returns a dict whose keys are the (string) names of unit options supported
    by pfdf. Values are the multiplicative conversion factors used to convert
    from meters to the associated unit. Note that the "base" unit refers to the
    base units of a CRS. The base conversion factor is nan because these units
    are variable and depend on the selection of CRS.
    ----------
    Outputs:
        dict: Multiplicative conversion factors from meters to each unit
    """
    return units.units_per_meter()


def supported() -> list[str]:
    """
    Returns a list of unit options supported by pfdf
    ----------
    supported()
    Returns a list of supported unit options.
    ----------
    Outputs:
        list: The unit systems supported by pfdf
    """
    return units.supported()


def convert(distance: RealArray, from_units: str, to_units: str) -> RealArray:
    """
    Converts distances from one unit to another
    ----------
    convert(distance, from_units, to_units)
    Converts the input distances from one unit to another. Distances may be a
    scalar or array-like dataset. Always returns converted distances as a numpy
    array. Note that you cannot convert between "base" units, as these units are
    ambiguous and depend on the selection of CRS.
    ----------
    Inputs:
        distance: The distances that should be converted
        from_units: The current units of distances
        to_units: The units that the distances should be converted to

    Outputs:
        np.ndarray: The converted distances
    """

    # Validate distance and units
    allowed = supported()[1:]
    from_units = validate.option(from_units, "from_units", allowed)
    to_units = validate.option(to_units, "to_units", allowed)
    distance = validate.array(distance, "distance", dtype=real)

    # Standardize alternate spellings
    from_units = units.standardize(from_units)
    to_units = units.standardize(to_units)

    # Trivial case
    if from_units == to_units:
        return distance

    # Use meters as intermediate conversion step
    units_per_m = units_per_meter()
    if from_units != "meters":
        distance = distance / units_per_m[from_units]
    if to_units != "meters":
        distance = distance * units_per_m[to_units]
    return distance
