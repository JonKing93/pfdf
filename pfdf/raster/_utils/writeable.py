"""
Context manager class for making numpy array's temporarily writeable
----------
The Writeable class provides a context manager to temporarily makes an array writeable.
This is useful for ensuring that Raster data arrays remain read-only, even after
routines that alter the base array.
----------
Class:
    WriteableArray  - Context manager for altering array write permissions
"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import numpy as np


class WriteableArray:
    """
    Context manager for setting array write permissions
    ----------
    Dunders:
        __init__    - Creates object. Records the array and its initial write permission
        __enter__   - Entry point for "with" block that sets array to writeable
        __exit__    - Restores write permissions to initial state upon exiting "with" block
    """

    def __init__(self, array: np.ndarray) -> None:
        "Creates a WriteableArray object for use in a 'with' block"

        self.array = array
        self.initial = array.flags.writeable

    def __enter__(self) -> None:
        """Sets the data array to writable upon entry to a 'with' block. Provides an
        informative error message if the raster does not own the array"""

        try:
            self.array.setflags(write=True)
        except ValueError as error:
            raise ValueError(
                "You cannot set copy=False because the raster cannot set the "
                "write permissions of its data array."
            ) from error

    def __exit__(self, *args, **kwargs) -> None:
        "Restores write permissions to initial state upon exiting 'with' block"
        self.array.setflags(write=self.initial)
