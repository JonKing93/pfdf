"""
Low-level validation functions that only rely on the standard library
----------
Functions:
    type        - Checks input has the specified type
    string      - Checks input is a string
    option      - Checks input is a recognized string option
    callable_   - Checks input is a callable object
"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Any, Sequence


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


def string(input: Any, name: str) -> str:
    "Checks an input is a string"
    type(input, name, str, "string")
    return input


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

    string(input, name)
    input_lowered = input.lower()
    if input_lowered not in allowed:
        allowed = ", ".join(allowed)
        raise ValueError(
            f"{name} ({input}) is not a recognized option. Supported options are: {allowed}"
        )
    return input_lowered


def callable_(input: Any, name: str) -> None:
    "Checks an input is a callable object"
    if not callable(input):
        raise TypeError(
            f'The "{name}" input must be a callable object, such as a function or a '
            f"static method."
        )
