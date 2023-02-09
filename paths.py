"""
paths  Defines paths to use with the DFHA Step 1
"""

# IO
input = "/home/jking/DFHA/"
output = "home/jking/code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment/output/"
backup = "home/jking/code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment/backup/"

# Fire-independent input geodatabases
evt        = input + "LandFire_EVT.gdb"
landfire   = input + "LandFire_SAF_SRM.gdb"
mtbs       = input + "DFHA/MTBS_Data.gdb"
soils      = input + "STATSGO_Soils.gdb"
projection = input + "ProjectionData.gdb"
dem        = input + "NationalElevationDataset.gdb/NED_Tile_Reference_1deg_10m"

# Log
log = output + "log.txt"

# Working folders
arcpy_scratch  = output + "arcpy_scratch"
scratch        = output + "scratch"
kernel         = output + "kernel"

# Output geodatabases
firein         = output + "df_input"
modelcalcs     = output + "dfestimates_utm"
modelcalcs_web = output + "dfestimates_wgs84"
symbology      = output + "Symbology"  

# 
