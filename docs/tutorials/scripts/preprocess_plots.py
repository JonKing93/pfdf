"Code for the preprocessing tutorial, including plots"

import plot
from pfdf import severity
from pfdf.raster import Raster

# Create buffered burn perimeter
perimeter = Raster.from_polygons("perimeter.geojson")
perimeter.buffer(3, units="kilometers")
plot.mask(perimeter, "Buffered Perimeter", gridalpha=1)

# Load datasets that are already rasters
dem = Raster.from_file("dem.tif", bounds=perimeter)
dnbr = Raster.from_file("dnbr.tif", bounds=perimeter)
evt = Raster.from_file("evt.tif", bounds=perimeter)

plot.raster(dem, "terrain", "DEM", gridalpha=1)
plot.raster(dnbr, "OrRd", "dNBR", gridalpha=1)
plot.raster(evt, "tab20", "EVT", gridalpha=1)

# KF factor
kf = Raster.from_polygons("kf.geojson", field="KFFACT", bounds=perimeter)
plot.raster(kf, "turbo", "KF-factor", gridalpha=1)

# Retainment features
retainments = Raster.from_points("retainments.geojson")
plot.pr(perimeter, "Retainment Features")

# Reproject to the same CRS, resolution and alignment as the DEM
rasters = [perimeter, dnbr, evt, kf, retainments]
for raster in rasters:
    raster.reproject(template=dem)

# Clip to the bounds of the perimeter
rasters = [dem, dnbr, evt, kf, retainments]
for raster in rasters:
    raster.clip(bounds=perimeter)

# Plot the projections
plot.mask(perimeter, "Reprojected Perimeter")
plot.raster(dem, "terrain", "Reprojected DEM")
plot.raster(dnbr, "OrRd", "Reprojected dNBR")
plot.raster(evt, "tab20", "Reprojected EVT")
plot.raster(kf, "turbo", "Reprojected KF-factor")

# Constrain data ranges
dnbr.set_range(min=-1000, max=1000)
plot.raster(dnbr, "OrRd", "Constrained dNBR")

kf.set_range(min=0, fill=True, exclude_bounds=True)
plot.raster(kf, "Oranges", "Constrained KF-factor")

# Estimate severity
barc4 = severity.estimate(dnbr)
plot.raster(barc4, "OrRd", "Burn Severity")

# Build terrain masks
iswater = evt.find(7292)
plot.mask(iswater, "Water Mask")

development = [7296, 7297, 7298, 7299, 7300]
isdeveloped = evt.find(development)
plot.mask(isdeveloped, "Development Mask")
