"""
Validation functions used throughout pfdf
----------
Low level:
    type            - Checks input has the specified type
    string          - Checks an input is a string
    option          - Checks input is a recognized string option
    callable        - Checks input is a callable object

Paths:
    input_file      - Checks input is an existing path
    output_file     - Checks output is a file path, and optionally prevents overwriting
    output_folder   - Checks output is the path to an empty or non-existent folder

Unit Conversion:
    units           - Checks units are supported
    conversion      - Checks a units-per-meter conversion factor

Low level arrays:
    real_dtype      - Checks an input represents a real-valued numpy dtype
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

URLs:
    url             - Checks input is a string with a URL scheme
    http            - Checks an http(s) connection using requests.head
    timeout         - Checks a connection timeout option is valid

Buffers:
    buffers         - Checks inputs represent buffering distances for a rectangle

Internal Modules:
    _array      - Functions that validate array shapes and dtypes
    _buffers    - Function to validate buffers for a rectangle
    _elements   - Functions that check the values of array elements
    _low        - Low level validators that only rely on the standard library
    _path       - Functions to validate file paths
    _units      - Functions to validate unit conversion options
    _url        - Functions to validate URLs
"""

from pfdf._validate.core._array import (
    array,
    broadcastable,
    dtype_,
    matrix,
    nonsingleton,
    real_dtype,
    scalar,
    shape_,
    vector,
)
from pfdf._validate.core._buffers import buffers
from pfdf._validate.core._elements import (
    boolean,
    defined,
    finite,
    flow,
    inrange,
    integers,
    positive,
    sorted,
)
from pfdf._validate.core._low import callable_ as callable
from pfdf._validate.core._low import option, string, type
from pfdf._validate.core._path import input_file, output_file, output_folder
from pfdf._validate.core._units import conversion, units
from pfdf._validate.core._url import http, timeout, url
