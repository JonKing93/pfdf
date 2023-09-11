"""
_utils  Low-level utilities used throughout the package
----------
Modules:
    nodata_     - Functions for working with NoData values
    validate    - Functions that validate input numpy arrays
    
Type hint:
    real        - A list of numpy dtypes considered to be real-valued numbers
    
Functions:
    aslist      - Returns an input as a list
    astuple     - Returns an input as a tuple
    classify    - Classify array values based on thresholds

Internal modules:
    _misc       - Container module for the aforementioned type hint and functions
"""

from pfdf._utils._misc import aslist, astuple, classify, real
