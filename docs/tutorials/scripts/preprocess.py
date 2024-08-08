"Code for the preprocessing tutorial."

from pfdf import severity
from pfdf.raster import Raster

# Create buffered burn perimeter
perimeter = Raster.from_polygons("perimeter.geojson")
perimeter.buffer(3, units="kilometers")

# Load datasets that are already rasters
dem = Raster.from_file("dem.tif", bounds=perimeter)
dnbr = Raster.from_file("dnbr.tif", bounds=perimeter)
evt = Raster.from_file("evt.tif", bounds=perimeter)

# Convert vector datasets to rasters
kf = Raster.from_polygons("kf.geojson", field="KFFACT", bounds=perimeter)
retainments = Raster.from_points("retainments.geojson")

# Reproject to the same CRS, resolution and alignment as the DEM
rasters = [perimeter, dnbr, evt, kf, retainments]
for raster in rasters:
    raster.reproject(template=dem)

# Clip to the bounds of the perimeter
rasters = [dem, dnbr, evt, kf, retainments]
for raster in rasters:
    raster.clip(bounds=perimeter)

# Set dNBR and KF-factor data ranges
dnbr.set_range(min=-1000, max=1000)
kf.set_range(min=0, fill=True, exclude_bounds=True)

# Estimate severity
barc4 = severity.estimate(dnbr)

# Build terrain masks
iswater = evt.find(7292)
development = [7296, 7297, 7298, 7299, 7300]
isdeveloped = evt.find(development)
