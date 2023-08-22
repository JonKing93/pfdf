"""
errors  Classes that define custom exceptions
----------
Numpy Arrays:
    DimensionError      - When a numpy array has invalid nonsingleton dimensions
    ShapeError          - When a numpy axis has an invalid shape
    EmptyArrayError     - When a numpy array has no elements

Stream Segments:
    RasterShapeError    - When a raster shape does not match that of the stream raster
"""

from pfdf.typing import shape


class EmptyArrayError(Exception):
    "When a numpy array has no elements"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DimensionError(Exception):
    "When a numpy array has invalid non-singleton dimensions"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ShapeError(Exception):
    """
    When a numpy axis has the wrong length
    ----------
    Properties:
        required: The required shape of the numpy array
        actual: The actual shape of the numpy array
        index: The index of the bad axis
    """

    def __init__(
        self, name: str, axis: str, index: int, required: shape, actual: shape
    ) -> None:
        message = f"{name} must have {required[index]} {axis}, but it has {actual[index]} {axis} instead."
        self.index = index
        self.required = required
        self.actual = actual
        super().__init__(message)


class RasterShapeError(Exception):
    "When the shape of a values raster does not match the shape of the stream segment raster"

    def __init__(self, name: str, cause: ShapeError) -> None:
        message = (
            f"The shape of the {name} raster {cause.actual} does not match the "
            f"shape of the stream segment raster used to derive the segments {cause.required}."
        )
        super().__init__(message)
