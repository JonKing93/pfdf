"Code for the Transform tutorial"

from pfdf.projection import Transform
from affine import Affine

# Constructor. With/without CRS
Transform(dx=10, dy=-10, left=5000, top=19)
Transform(10, -10, 5000, 19, crs=26911)

# From a dict. CRS key is optional
input = {'dx': 10, 'dy': -10, 'left': 5000, 'top': 19, 'crs': 26911}
Transform.from_dict(input)

# From a list or tuple. With/without CRS
Transform.from_list([10, -10, 5000, 19])
Transform.from_list([10, -10, 5000, 19, 26911])

# From an affine.Affine object
input = Affine(10, 0, 5000, 0, -10, 19)
Transform.from_affine(input)

# To list or dict
transform = Transform(10, -10, 5000, 19)
transform.todict()
transform.tolist()

# Properties
transform.left
transform.top
transform.crs
transform.units
transform.affine

# Orientation
Transform(1,-1,0,0).orientation
Transform(-1,-1,0,0).orientation
Transform(-1,1,0,0).orientation
Transform(1,1,0,0).orientation

# Resolution
transform = Transform(10, -10, 0, 0, 26911)
transform.dx()
transform.dy()
transform.resolution()

# Resolution: CRS base units (degrees in this case)
transform = Transform(9e-5, 9e-5, -121, 0, 4326)
transform.dx()
transform.dy()

# Resolution: Explicit units
transform.dx(units="meters")
transform.dy("feet")

# Geodetic CRS: default at equator
transform = Transform(9e-5, -9e-5, -121, 30, crs=4326)
transform.dx("meters")
transform.resolution("meters")

# Geodetic CRS: other latitude
transform.dx("meters", y=35)
transform.resolution("meters", y=35)

# Pixel geometries: equator and higher latitude
transform.pixel_area("meters")
transform.pixel_area("meters", y=35)
transform.pixel_diagonal("meters")
transform.pixel_diagonal("meters", y=35)

# Convert to BoundingBox
transform = Transform(10, -10, 0, 0, 26911)
nrows, ncols = (1000, 2000)
bounds = transform.bounds(nrows, ncols)

# Reprojection: Discouraged
transform = Transform(10, -10, 0, 0, 26911)
transform.reproject(crs=4326)

# Reprojection: Preferred
bounds = transform.bounds(nrows, ncols)
bounds.reproject(crs=4326)
transform = bounds.transform(nrows, ncols)