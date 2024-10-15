"""
Functions to validate export options
----------
Functions:
    _properties - Checks a property dict is valid
    export      - Checks export type and properties
"""

from typing import Any

import numpy as np

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import ShapeError
from pfdf.typing.segments import ExportType, PropertyDict, PropertySchema


def _properties(
    segments,
    properties: Any,
    terminal: bool,
) -> tuple[PropertyDict, PropertySchema]:
    "Validates a GeoJSON property dict for export"

    # Initialize the final property dict and schema. Properties are optional,
    # so just use an empty dict if there are none
    final = {}
    schema = {}
    if properties is None:
        properties = {}

    # Get the allowed lengths and the required final length
    length = segments._nbasins(terminal)
    allowed = [segments.size]
    if terminal:
        allowed.append(segments.nlocal)

    # Require a dict with string keys
    dtypes = real + [str]
    validate.type(properties, "properties", dict, "dict")
    for k, key in enumerate(properties.keys()):
        validate.type(key, f"properties key {k}", str, "string")

        # Values must be numpy 1D arrays with either one element per segment,
        # or one element per exported feature
        name = f"properties['{key}']"
        vector = validate.vector(properties[key], name, dtype=dtypes)
        if vector.size not in allowed:
            allowed = " or ".join([str(length) for length in allowed])
            raise ShapeError(
                f"{name} must have {allowed} elements, but it has "
                f"{vector.size} elements instead."
            )

        # Extract terminal properties as needed
        if vector.size != length:
            vector = vector[segments.isterminal()]

        # Convert boolean to int
        if vector.dtype == bool:
            vector = vector.astype("int")
            schema[key] = "int"

        # If a string, parse the width from the vector dtype
        elif vector.dtype.char == "U":
            dtype = str(vector.dtype)
            k = dtype.find("U")
            width = int(dtype[k + 1 :])
            schema[key] = f"str:{width}"

        # Convert int and float precisions to built-in
        elif np.issubdtype(vector.dtype, np.integer):
            vector = vector.astype(int, copy=False)
            schema[key] = "int"
        elif np.issubdtype(vector.dtype, np.floating):
            vector = vector.astype(float, copy=False)
            schema[key] = "float"

        # Record the final vector and return with the schema
        final[key] = vector
    return final, schema


def export(
    segments, properties: Any, type: Any
) -> tuple[ExportType, PropertyDict, PropertySchema]:
    "Validates export type and properties"

    type = validate.option(
        type, "type", allowed=["segments", "segment outlets", "outlets", "basins"]
    )
    terminal = "segment" not in type
    properties, schema = _properties(segments, properties, terminal)
    return type, properties, schema
