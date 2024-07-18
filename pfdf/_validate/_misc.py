"""
Misc low-level validation functions
----------
Misc:
    type        - Checks input has the specified type
    option      - Checks input is a recognized string option

Paths:
    input_path  - Checks input is a path to an existing file
    output_path - Checks output is a path, and optionally prevents overwriting

Unit Conversions:
    units       - Checks units are supported
    conversion  - Validates a units-per-meter conversion factor
"""

from pathlib import Path
from typing import Any, Optional, Sequence

from pfdf._utils import real
from pfdf._utils.units import supported as supported_units
from pfdf._validate._array import scalar
from pfdf._validate._elements import positive

#####
# Misc
#####


def type(input: Any, name: str, type: type, type_name: str) -> None:
    """
    type  Checks that the input is the indicated type
    ----------
    type(input, types)
    Checks that the input is the indicated type. Raises a TypeError if not.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages
        type: The required type for the input
        type_name: A name for the type for use in error messages
    """

    if not isinstance(input, type):
        raise TypeError(f"{name} must be a {type_name}")


def option(input: Any, name: str, allowed: Sequence[str]) -> str:
    """
    option  Checks that an input string selects a recognized option
    ----------
    option(input, allowed)
    First checks that an input is a string (TypeError if not). Then, checks that
    the (case-insensitive) input belongs to a list of allowed options (ValueError
    if not). If valid, returns a lowercased version of the input.
    ----------
    Inputs:
        input: The input option being checked
        name: A name to identify the option in error messages
        allowed: A list of allowed strings

    Outputs:
        lowercased string: The lowercased version of the input

    Raises:
        TypeError: If the input is not a string
        ValueError: If the the lowercased string is not in the list of recognized options
    """

    type(input, name, str, "string")
    input_lowered = input.lower()
    if input_lowered not in allowed:
        allowed = ", ".join(allowed)
        raise ValueError(
            f"{name} ({input}) is not a recognized option. Supported options are: {allowed}"
        )
    return input_lowered


#####
# Paths
#####


def input_path(path: Any, name: str) -> Path:
    """
    input_path  Checks that an input path exists
    ----------
    input_path(path, name)
    Checks that an input path is a resolvable Path. Returns the resolved pathlib.Path.
    Raises a TypeError if not a Path, and a FileNotFoundError if not resolvable.
    ----------
    Inputs:
        path: A user provided path to an input file
        name: A name for the input path for use in error messages.

    Outputs:
        pathlib.Path: The resolved path to the file

    Raises:
        TypeError: If the input is not a string or Path
        FileNotFoundError: If the file does not exist.
    """

    if isinstance(path, str):
        path = Path(path)
    type(path, name, Path, "file path")
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"{name} is not a file")
    return path


def output_path(path: Any, overwrite: bool) -> Path:
    """
    output_path  Checks that a path is suitable for an output file
    ----------
    output_path(path, overwrite)
    Checks that an input path is resolvable. Raises a FileExistsError if overwrite=False
    and the file already exists. Otherwise, returns the resolved pathlib.Path to the file.
    ----------
    Inputs:
        path: A user provided path for an output file
        overwrite: True if the file can already exist. False to raise an error
            for exists (i.e. prevent overwriting)

    Outputs:
        pathlib.Path: The resolved path to the output file

    Raises:
        FileExistsError: If the path exists and overwrite=False
    """

    path = Path(path).resolve()
    if (not overwrite) and path.exists():
        raise FileExistsError(
            f"Output file already exists:\n\t{path}\n"
            'If you want to replace existing files, set "overwrite=True"'
        )
    return path


#####
# Unit Conversions
#####


def units(units: Any, include: Optional[str] = None) -> str:
    "Checks that a unit is supported"
    supported = supported_units()
    if include is not None:
        supported.append(include)
    return option(units, "units", allowed=supported)


def conversion(input: Any, name: str) -> float:
    "Validates a units-per-meter conversion factor"
    if input is not None:
        input = scalar(input, name, real)
        positive(input, name)
    return input
