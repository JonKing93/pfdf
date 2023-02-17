"""
paths  Defines paths to use with the DFHA Step 1
"""

# IO
repo = r"C:\Users\jking\Documents\arcpy-testing"
input = repo + r"\input"
output = repo + r"\output"

# Working folders / geodatabases
fire_input = input + r"\col2022_df_input.gdb"
saved = output + r"\output.gdb"
scratch = output + r"\scratch.gdb"

# Multi-purpose
perimeter = fire_input + r"\col2022_perim_feat"
projection = input + r"\ProjectionData.gdb"
projected   = scratch + r"\projected"

# UTM zone
utm          = projection + r"\UTMZones_Feat_GCS_WGS84"
dissolved    = scratch + r"\dissolved"
centroid     = scratch + r"\centroid"
centroid_utm = scratch + r"\centroid_utm"
zone         = scratch + r"\zone"

# Extent box
bounds         = scratch + r"\bounds"
extent_feature = saved + r"\extent_feature"
extent_raster  = saved + r"\extent_raster"

# DEM (Digital elevation model)
firedem_existing = fire_input + r"\col2022_dem"
reference_tiles  = input + r"\NationalElevationDataset.gdb/NED_Tile_Reference_1deg_10m"
demdata          = input + r"\DEM"

intersect   = scratch + r"\intersect"
firetiles   = scratch + r"\firetiles"
mosaic      = scratch + r"\mosaic"
firedem     = saved + r"\firedem"

# Debris basins
basins_existing = fire_input + r"\col2022_db_feat"
basins_dataset = input + r"\DebrisBasins.gdb/WesternUS_db_feat"
clipped = scratch + r"\clipped"
basins = saved + r"\basins"

# Burn Severity
severity = fire_input + r"\col2022_sev"
dnbr = fire_input + r"\col2022_dnbr"

# UTM projections
extent_utm   = saved + r"\extent_utm"
dem_utm      = saved + r"\dem_utm"
basins_utm   = saved + r"\basins_utm"
severity_utm = saved + r"\severity_utm"
dnbr_utm     = saved + r"\dnbr_utm"



















# # Fire-independent input geodatabases
# evt        = input + "LandFire_EVT.gdb"
# landfire   = input + "LandFire_SAF_SRM.gdb"
# mtbs       = input + "DFHA/MTBS_Data.gdb"
# soils      = input + "STATSGO_Soils.gdb"
# projection = input + "ProjectionData.gdb"

# # Fire-dependent inputs
# sev        = firein + "/col2022_sev"
# dnbr       = firein + "/col2022_dnbr"


# # Output geodatabases
# modelcalcs     = output + "dfestimates_utm"
# modelcalcs_web = output + "dfestimates_wgs84"
# symbology      = output + "Symbology"  

