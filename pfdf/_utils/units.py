"""
Functions to facilitate unit conversions
----------
Functions:
    supported       - Returns a list of supported unit options
    units_per_meter - Returns conversion factors between supported units and meters
    standardize     - Standardizes alternate units spellings
"""

from math import nan


def units_per_meter() -> dict[str, float]:
    "Returns a dict of conversion factors between supported units and meters"

    # Get factors
    kilometers = 1 / 1000
    feet = 100 / 2.54 / 12
    miles = feet / 5280

    # Organize dict
    return {
        "base": nan,
        "meters": 1,
        "metres": 1,
        "kilometers": kilometers,
        "kilometres": kilometers,
        "feet": feet,
        "miles": miles,
    }


def supported() -> list[str]:
    "Returns a list of unit options supported by pfdf"
    return list(units_per_meter().keys())


def standardize(unit: str) -> str:
    "Standardizes alternate unit spellings"
    if unit == "metres":
        return "meters"
    elif unit == "kilometres":
        return "kilometers"
    else:
        return unit
