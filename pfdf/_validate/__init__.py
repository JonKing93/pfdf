"""
Validation functions used throughout pfdf
----------
This subpackage contains functions used to validate user inputs throughout pfdf.
The recommended import syntax is:

import pfdf._validate as validate

Broadly, most of these functions ensure that inputs are representable as various
types of numpy arrays. However, a few misc functions are also included.
----------
Misc:
    type            - Checks input has the specified type
    option          - Checks input is a recognized string option
    buffers         - Checks inputs represent buffering distances for a rectangle

Paths:
    input_path      - Checks input is a path to an existing file
    output_path     - Checks output is a path, and optionally prevents overwriting

Unit Conversion:
    units           - Checks units are supported
    conversion      - Checks a units-per-meter conversion factor

Low level arrays:
    dtype_          - Checks a dtype is an allowed value
    shape_          - Checks that a shape is allowed
    nonsingletons   - Locates nonsingleton dimensions

Array Shape and Type:
    array           - Checks an input represents a numpy array
    scalar          - Checks input represents a scalar
    vector          - Checks input represents a vector
    matrix          - Checks input represents a matrix
    broadcastable   - Checks two shapes can be broadcasted

Array Elements:
    defined         - Checks elements are not NaN
    finite          - Checks elements are neither infinite nor NaN
    boolean         - Checks elements are all 1s and 0s
    integers        - Checks elements are all integers
    positive        - Checks elements are all positive
    inrange         - Checks elements are all within a valid data range
    sorted          - Checks elements are in sorted order
    flow            - Checks elements represents TauDEM-style flow directions (integers 1 to 8)

Internal Modules:
    _array      - Functions that validate array shapes and dtypes
    _buffers    - Function to validate buffers for a rectangle
    _elements   - Functions that check the values of array elements
    _misc       - Miscellaneous validation functions
"""

from pfdf._validate._array import (
    array,
    broadcastable,
    dtype_,
    matrix,
    nonsingleton,
    scalar,
    shape_,
    vector,
)
from pfdf._validate._buffers import buffers
from pfdf._validate._elements import (
    boolean,
    defined,
    finite,
    flow,
    inrange,
    integers,
    positive,
    sorted,
)
from pfdf._validate._misc import (
    conversion,
    input_path,
    option,
    output_path,
    type,
    units,
)
