"Code for the Raster tutorial"

import numpy as np

from pfdf.raster import Raster

#####
# Raster Creation
#####

# Constructor: File-based raster
dem = Raster("dem.tif")

print(dem.shape)
print(dem.dtype)
print(dem.crs)
print(dem.transform)

# Constructor: Array-based raster
araster = np.arange(200).reshape(20, 10)
raster = Raster(araster)

print(dem.shape)
print(dem.dtype)
print(dem.crs)
print(dem.transform)

# Constructor: Boolean raster (naive)
mask = Raster("mask.tif")

print(mask.dtype)
print(mask.nodata)

# Constructor: Boolean raster (isbool)
mask = Raster("mask.tif", isbool=True)

print(mask.dtype)
print(mask.nodata)

# Window of a file-based raster
window = Raster("dnbr.tif")
dem = Raster.from_file("dem.tif", window=window)
print(dem.shape)

# File-based raster from specific band
dem = Raster.from_file("dem.tif", band=1)
print(dem.shape)

# Array raster without metadata
raster = Raster(araster)

print(raster.nodata)
print(raster.crs)
print(raster.transform)

# Array raster with metadata
raster = Raster.from_array(
    araster, nodata=0, crs="EPSG:4326", transform=(1, 0, 0, 0, 1, 0)
)

print(raster.nodata)
print(raster.crs)
print(raster.transform)

# Array raster with matching spatial metadata
raster = Raster.from_array(araster, nodata=0, spatial=dem)

print(raster.nodata)
print(raster.crs)
print(raster.transform)


#####
# Properties
#####

# Data grid
dem.values
print(dem.dtype)
print(dem.shape)
print(dem.size)

# NoData values
dem.nodata
print(dem.values)
print(dem.data_mask)
print(dem.nodata_mask)

# Spatial metadata
dem.crs
dem.transform
dem.dx
dem.dy

# Bounds
dem.bounds
dem.left
dem.right
dem.top
dem.bottom

# NaN metadata if transform is missing
raster = Raster(araster)

print(raster.transform)
print(raster.dx)
print(raster.dy)
print(raster.bounds)

# Pixel properties
dem.resolution
dem.pixel_width
dem.pixel_height
dem.pixel_area
dem.pixel_diagonal

# NaN pixel metadata if transform is missing
raster = Raster(araster)

print(raster.transform)
print(raster.resolution)
print(raster.pixel_area)
print(raster.pixel_diagonal)


#####
# Saving
#####

# Save to file
raster.save("example.tif")

# By default, no overwriting
raster.save("example.tif")  # This will cause an error

# Overwrite file
raster.save("example.tif", overwrite=True)
