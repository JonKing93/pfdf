"""
paths  Defines paths to use with the DFHA Step 1
"""

# IO
repo = "/home/jking/code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment/"
input = repo + "input/"
output = repo + "output/"
backup = repo + "backup/"
log = output + "log.txt"

# Working folders / geodatabases
fire_input = input + "col2022_df_input.gdb/"
scratch = output + "scratch.gdb/"

# Perimeter
perimeter = fire_input + "col2022_perim_feat"

# UTM zone
utm          = input + "ProjectionData.gdb/UTMZones_Feat_GCS_WGS84"
dissolved    = scratch + "dissolved"
centroid     = scratch + "centroid"
centroid_utm = scratch + "centroid_utm"
zone         = scratch + "zone"

# Extent box
bounds         = scratch + "bounds"
extent_feature = output + "extent_feature"
extent_raster  = output + "extent_raster"

# DEM (Digital elevation model)
firedem_existing = fire_input + "col2022_dem"
reference_tiles  = input + "NationalElevationDataset.gdb/NED_Tile_Reference_1deg_10m"
demdata          = input + "DEM_data"

projected   = scratch + "projected"
intersect   = scratch + "intersect"
firetiles   = scratch + "firetiles"
mosaic      = scratch + "mosaic"
firedem     = output + "firedem"

# Debris basins
basins_existing = fire_input + "col2022_db_feat"













# Fire-independent input geodatabases
evt        = input + "LandFire_EVT.gdb"
landfire   = input + "LandFire_SAF_SRM.gdb"
mtbs       = input + "DFHA/MTBS_Data.gdb"
soils      = input + "STATSGO_Soils.gdb"
projection = input + "ProjectionData.gdb"

# Fire-dependent inputs
sev        = firein + "/col2022_sev"
dnbr       = firein + "/col2022_dnbr"


# Output geodatabases
modelcalcs     = output + "dfestimates_utm"
modelcalcs_web = output + "dfestimates_wgs84"
symbology      = output + "Symbology"  

