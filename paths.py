"""
paths  Defines paths to use with the DFHA Step 1
"""

# IO
repo = r"C:\Users\jking\Documents\arcpy-testing""\\"
input = repo + "input""\\"
output = repo + "\output""\\"

# Working folders / geodatabases
fire_input = input + "col2022_df_input.gdb""\\"
saved = output + "\output.gdb""\\"
scratch = output + "\scratch.gdb""\\"
taudem = output + "\taudem""\\"

# Multi-purpose
perimeter = fire_input + "col2022_perim_feat"
projection = input + "ProjectionData.gdb""\\"
projected   = scratch + "projected"

# UTM zone
utm          = projection + "UTMZones_Feat_GCS_WGS84"
dissolved    = scratch + "dissolved"
centroid     = scratch + "centroid"
centroid_utm = scratch + "centroid_utm"
zone         = scratch + "zone"

# Extent box
bounds         = scratch + "bounds"
extent_feature = saved + "extent_feature"
extent_raster  = saved + "extent_raster"

# DEM (Digital elevation model)
firedem_existing = fire_input + "col2022_dem"
reference_tiles  = input + "NationalElevationDataset.gdb/NED_Tile_Reference_1deg_10m"
demdata          = input + "DEM"

intersect      = scratch + "intersect"
firetiles      = scratch + "firetiles"
mosaic         = scratch + "mosaic"
firedem        = saved + "firedem"
firedem_masked = saved + "firedem_masked"

# Debris basins
basins_existing = fire_input + "col2022_db_feat"
basins_dataset = input + "DebrisBasins.gdb/WesternUS_db_feat"
clipped = scratch + "clipped"
basins = saved + "basins"

# Burn Severity
severity = fire_input + "col2022_sev"
dnbr = fire_input + "col2022_dnbr"
isburned = saved + "isburned"
hasburndata = saved + "has_burn_data"

# UTM projections
extent_utm   = saved + "extent_utm"
dem_utm      = saved + "dem_utm"
basins_utm   = saved + "basins_utm"
severity_utm = saved + "severity_utm"
dnbr_utm     = saved + "dnbr_utm"

# Regridded rasters
dem_regrid      = saved + "dem_regrid"
severity_regrid = saved + "severity_regrid"
dnbr_regrid     = saved + "dnbr_regrid"

# Soils
soil_database = input + "STATSGO_Soils.gdb\STATSGO_US_NAD27_Albers"
soil = fire_input + "col2022_soils_feat"

# Burned area
buffered = scratch + "buffered"
buffered_raster = output + "buffered_raster"
buffered_mask = output + "buffered_mask"
perimeter_raster = output + "perimeter_raster"
mask = output + "mask"

# Topography
slope = output + "slope"
hillshade = output + "hillshade"

# TauDEM
firedem_tiff   = taudem + "firedem.tif"
pitfilled = taudem + "pitfilled.tif"

d8flow = taudem + "d8_flow.tif"
d8slope = taudem + "d8_slope.tif"

diflow = taudem + "di_flow.tif"
dislope = taudem + "di_slope.tif"

d8area = taudem + "area.tif"
d8relief = taudem + "relief.tif"
d8length = taudem + "length.tif"

# TauDEM export
flow = saved + "flow"
area = saved + "area"
relief = saved + "relief"
length = saved + "length"

# ...working
normal_area = saved + "normal_area"

# Uplope burned area
hasburn_tiff = taudem + "has_burn.tif"
d8burned_area = taudem + "burned_area.tif"
burned_area = output + "burned_area"

# Stream network
streams_raster = output + "streams_raster"
streams = output + "streams"
stream_points = output + "stream_points"
segments = output + "segments"
segment_raster = output + "segment_raster"
strahler_raster = output + "strahler_raster"
strahler = output + "strahler"

























# # Fire-independent input geodatabases
# evt        = input + "LandFire_EVT.gdb"
# landfire   = input + "LandFire_SAF_SRM.gdb"
# mtbs       = input + "DFHA/MTBS_Data.gdb"
# projection = input + "ProjectionData.gdb"



# # Output geodatabases
# modelcalcs     = output + "dfestimates_utm"
# modelcalcs_web = output + "dfestimates_wgs84"
# symbology      = output + "Symbology"
