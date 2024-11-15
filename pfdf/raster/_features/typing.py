from pfdf.projection import Transform
from pfdf.typing.core import VectorArray, value

# Spatial
Transform_CRS = Transform
VectorArray_NoCRS = VectorArray
Resolution = VectorArray_NoCRS | Transform_CRS

# File IO options
layer = str | int | None
driver = str | None
encoding = str | None

# Data values
nodata = value
