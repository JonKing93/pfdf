"Code for the BoundingBox tutorial"

from pfdf.projection import BoundingBox

# Constructor: With/without CRS
BoundingBox(left=50, bottom=0, right=2000, top=4000)
BoundingBox(left=50, bottom=0, right=2000, top=4000, crs=26911)

# From a dict. CRS key is optional
input = {"left": 50, "bottom": 0, "right": 2000, "top": 4000, "crs": 26911}
BoundingBox.from_dict(input)

# From a list or tuple. With/without CRS
BoundingBox.from_list([50, 0, 2000, 4000])
BoundingBox.from_list([50, 0, 2000, 4000, 26911])

# To list or dict
bounds = BoundingBox(50, 0, 2000, 4000)
bounds.todict()
bounds.tolist()

# Spatial coordinates of box edges
bounds.left
bounds.bottom
bounds.right
bounds.top

# X/Y coordinates. Center coordinate
bounds.xs
bounds.ys
bounds.center

# CRS and CRS units
bounds = BoundingBox(-121, 30, -119, 40, crs=4326)
bounds.crs
bounds.units
bounds.units_per_m

# Orientation
BoundingBox(0, 2, 10, 5).orientation
BoundingBox(10, 2, 0, 5).orientation
BoundingBox(10, 5, 0, 2).orientation
BoundingBox(0, 5, 10, 2).orientation

# Height and width: CRS base units (degrees in this case)
bounds = BoundingBox(-121, 30, -119, 35, crs=4326)
bounds.height()
bounds.width()

# Height and width: Explicit units (kilometers)
bounds.height("kilometers")
bounds.width("kilometers")

# Reprojection
bounds = BoundingBox(-121, 30, -119, 35, crs=4326)
bounds.utm_zone()
bounds.reproject(crs=26911)
bounds.to_utm()
bounds.to_4326()

# Reorient
bounds = BoundingBox(100, 8, 50, 1)
bounds.orient()
bounds.orient(2)
bounds.orient(3)
bounds.orient(4)

# Buffer
bounds = BoundingBox(50, 0, 2000, 4000, crs=26911)
bounds.buffer(2, units='kilometers')
bounds.buffer(left=0, right=12, bottom=100, top=50)

# Convert to Transform
bounds = BoundingBox(50, 0, 2000, 4000, crs=26911)
nrows, ncols = (1000, 200)
transform = bounds.transform(nrows, ncols)
