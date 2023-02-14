"""
paths  Defines paths to use with the DFHA Step 1
"""

# IO
input = "/home/jking/DFHA/"
output = "home/jking/code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment/output/"
backup = "home/jking/code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment/backup/"
log = output + "log.txt"

# Working folders
fire_input    = output + "df_input/"
arcpy_scratch  = output + "arcpy_scratch/"
scratch        = output + "scratch/"
kernel         = output + "kernel/"

# Fire-independent inputs
utm = input + "ProjectionData.gdb/UTMZones_Feat_GCS_WGS84"
dem = input + "NationalElevationDataset.gdb/NED_Tile_Reference_1deg_10m"

# Fire-dependent inputs
perimeter = fire_input + "col2022_perim_feat"
firedem = fire_input + "col2022_dem"

# UTM Zone outputs
dissolved = arcpy_scratch + "col2022_perim_dissolve"
centroid = arcpy_scratch + "col2022_perim_centroid"
zone = arcpy_scatch + "col2022_perim_centroid_utmzone"

# Extent box outputs
perimeter_nad83 = arcpy_scratch + "col2022_perim_feat_nad83"
box_feature = output + "col2022_extent_feature"
box_raster = output + "col2022_extent_raster"

# DEM extraction outputs
box_dem = arcpy_scratch + "col2022_extent_dem_ref_feat"
dem_layer = arcpy_scratch + "NED_Tile_Reference_1deg_10m_extent_dem_ref_feat"










# Fire-independent input geodatabases
evt        = input + "LandFire_EVT.gdb"
landfire   = input + "LandFire_SAF_SRM.gdb"
mtbs       = input + "DFHA/MTBS_Data.gdb"
soils      = input + "STATSGO_Soils.gdb"
projection = input + "ProjectionData.gdb"
dem        = input + "NationalElevationDataset.gdb/NED_Tile_Reference_1deg_10m"

# Fire-dependent inputs
firedem        = firein + "/col2022_dem"
sev        = firein + "/col2022_sev"
dnbr       = firein + "/col2022_dnbr"
db_feat    = firein + "/col2022_db_feat"

# Log



# Output geodatabases
firein         = output + "df_input"
modelcalcs     = output + "dfestimates_utm"
modelcalcs_web = output + "dfestimates_wgs84"
symbology      = output + "Symbology"  

# Zone outputs

# DEM Extraction
dem_extent = arcpy_scatch + "/col2022_extent_dem_ref_feat"
dem_layer = arcpy_scratch + "/"