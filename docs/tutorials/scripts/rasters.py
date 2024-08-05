"Code for the Raster tutorial"

import numpy as np

from pfdf.raster import Raster

#####
# Raster Creation
#####

# Constructor: File-based raster
dem = Raster("dem.tif")
print(dem)

# Constructor: Array-based raster
araster = np.arange(200).reshape(20, 10)
Raster(araster)

# Constructor: Boolean raster (naive)
mask = Raster("mask.tif")

print(mask.dtype)
print(mask.nodata)

# Constructor: Boolean raster (isbool)
mask = Raster("mask.tif", isbool=True)

print(mask.dtype)
print(mask.nodata)

# File-based raster from specific band
dem = Raster.from_file("dem.tif", band=1)
print(dem.shape)

# Window of a file-based raster
dnbr = Raster("dnbr.tif")
dem = Raster.from_file("dem.tif", bounds=dnbr)
print(dem.shape)

# Array raster without metadata
raster = Raster(araster)
print(raster)

# Array raster with metadata
raster = Raster.from_array(
    araster, nodata=0, crs="EPSG:26911", transform=(10,-10,0,0)
)
print(raster)

# Array raster with matching spatial metadata
raster = Raster.from_array(araster, nodata=0, spatial=dem)
print(raster)


#####
# Properties
#####

# Data grid
dem.values
print(dem.dtype)
print(dem.shape)
print(dem.size)
print(dem.height)
print(dem.width)

# NoData values
dem.nodata
print(dem.values)
print(dem.data_mask)
print(dem.nodata_mask)

# Spatial metadata
dem.crs
dem.transform
dem.bounds

# Pixel properties
dem.resolution()
dem.resolution(units="feet")
dem.dx()
dem.dy()
dem.pixel_area()
dem.pixel_diagonal()


#####
# Saving
#####

# Save to file
araster = np.arange(200).reshape(20,10)
raster = Raster(araster)
raster.save("example.tif")

# By default, no overwriting
raster.save("example.tif")  # This will cause an error

# Overwrite file
raster.save("example.tif", overwrite=True)
