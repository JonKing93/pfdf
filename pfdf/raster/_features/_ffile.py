"""
Context manager class for opening vector feature files
----------
The FeatureFile class ensures that a vector feature file is closed after opening, and
also provides informative errors when a feature file cannot be read.
----------
Class:
    FeatureFile - Context manager with informative errors for opening feature files
"""

from __future__ import annotations

import typing

import fiona

from pfdf.errors import FeatureFileError

if typing.TYPE_CHECKING:
    from pfdf.raster._features.typing import driver, encoding, layer
    from pfdf.typing.core import Pathlike


class FeatureFile:
    """
    Context Manager for opening vector feature files.
    ----------
    Dunders:
        __init__        - Creates object and records file IO options
        __enter__       - Entry point for "with" block and informative errors for invalid files
        __exit__        - Closes file upon exiting a "with" block
    """

    def __init__(
        self, path: Pathlike, layer: layer, driver: driver, encoding: encoding
    ) -> None:
        """Creates a FeatureFile object for use in a "with" block. Also performs
        initial validation of fiona file parameters"""

        # File reading attributes
        self.path = path
        self.layer = layer
        self.driver = driver
        self.encoding = encoding

        # Functional attributes
        self.file = None
        self.crs = None

    def __enter__(self) -> FeatureFile:
        """Opens vector feature file upon entry into a "with" block. Also provides
        informative error if file opening fails"""

        # Attempt to open the feature file. Informative error if failed
        try:
            self.file = fiona.open(
                self.path, driver=self.driver, layer=self.layer, encoding=self.encoding
            )
        except Exception as error:
            raise FeatureFileError(
                f"Could not read data from the feature file. "
                f"The file may be corrupted or formatted incorrectly.\n"
                f"File: {self.path}"
            ) from error

        self.crs = self.file.crs
        return self

    def __exit__(self, *args, **kwargs) -> None:
        "Closes file upon exiting the 'with' block"
        self.file.close()
