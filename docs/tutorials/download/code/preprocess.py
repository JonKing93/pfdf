"Code for the preprocessing tutorial. Does not include plots."

import pfdf.severity
from pfdf.raster import Raster

# Load datasets that are already rasters
dem = Raster("dem.tif")
dnbr = Raster("dnbr.tif")
evt = Raster("evt.tif")

# Convert vector features to rasters
perimeter = Raster.from_polygons("perimeter.geojson", resolution=dem)
perimeter.buffer(3000)
kf = Raster.from_polygons("kf-factor.geojson", field="KFFACT", resolution=dem)
retainments = Raster.from_points("retainments.geojson", resolution=dem)

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
kf.set_range(min=0, fill=True)

# Estimate severity
severity = pfdf.severity.estimate(dnbr)

# Build terrain masks
iswater = evt.find(7292)
development = [7296, 7297, 7298, 7299, 7300]
isdeveloped = evt.find(development)
