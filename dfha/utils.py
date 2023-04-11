"""
utils  Utility functions
"""

from typing import List, Any


def aslist(input: Any) -> List[Any]:
    "aslist  Place input in list if not already a list."
    if not isinstance(input, list):
        input = [input]
    return input


def any_defined(*args: Any) -> bool:
    "any_defined  True if any input is not None"
    for arg in args:
        if arg is not None:
            return True
    return False
