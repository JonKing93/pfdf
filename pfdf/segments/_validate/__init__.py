"""
Functions that validate inputs for Segments routines
----------
Misc:
    raster      - Checks a value raster has metadata matching the flow raster
    nprocess    - Checks the number of parallel processes are valid
    export      - Checks export type and properties are valid

Selection:
    id          - Checks a scalar ID is valid and returns index
    ids         - Checks a set of IDs are valid and returns indices
    selection   - Checks filtering selection is valid and returns indices
"""

from pfdf.segments._validate._export import export
from pfdf.segments._validate._misc import nprocess, raster
from pfdf.segments._validate._selection import id, ids, selection
