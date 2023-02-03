"""
parameters  Parameters and configuration details for Step 1

METADATA:
    name        - The full name of the fire
    code        - The 3 letter abbreviation
    state       - The 2 letter state abbreviation
    location    - The location of the fire
    start_date  - Start date in MM DD, YYYY format
"""

# Fire metadata
name = 'Colorado'                   # Full fire name
code = 'col'                        # 3 letter abbreviation
state = 'CA'                        # 2 letter state abbreviation
location = 'Monterey County'        # Should not include state abbreviation
start_date = 'January 21, 2022'     # Start date

# Pre-fire assessment
pre_fire = False                        # Whether to compute a pre-fire assessment
evt_version = 140                       # ???
mtbs_perim_distance_km = 50             # ???
prefire_percentile_list = [0.5 0.84]    # The percentiles to compute

# Overwrite permission
overwrite = False       # Whether Step 1 is allowed to overwrite an existing analysis

# Output options
make_webtext = True          # Prepare output for the web app
make_booktest = True         # ??? Perhaps for PDF output
make_logfile = True          # Whether to create a logfile
logfile = 'DFModel_Log.txt'  # The name of the logfile

# Algorithm Options
segment_guess = 'PERIM'  # ??? Unknown. Options are 'PERIM' and 'NO_PERIM'
barc_threshold = 'CALC'  # ??? Unknown. Options are 'CALC' and 'DEFINED'
                         # Original notes say that you should only use 'DEFINED'
                         # if you have DNBR but no SBS or BARC4, and that the option
                         # has not been tested on recent versions of ArcGIS
                         # (so this option may be defunct)

# Options for designing network basins
min_basin_size_km2 = 0.025   # Minimum basin size
max_basin_size_km2 = 8.0     # Maximum basin size
cell_res = 10.0              # ??? something about resolution. Perhaps 10 meters of topography file?
burn_acc_threshold = 100     # ??? Original comment is: n_pixels

# Maximum segment length is based on an algorithm option
if segment_guess == 'PERIM':
    max_segment_length_m = 200
else:
    max_segment_length_m = 500

# Thresholds for triggering debris-flow
confine_threshold_degree = 174  # ??? Perhaps a limit of topographic slope
slope_threshold_pct = 12        # ??? Perhaps related to topographic slope
pct_burn_threshold = 0.25       # ???
perim_buffer_dist_m = 500       # ???

# ??? Sum threshold parameters. Unknown what these are
if segment_guess == 'PERIM':
    dev_sum_threshold = 250
else:
    dev_sum_threshold = 250
db_sum_threshold = 1

# ??? acc stands for accumulation in some way...
min_acc = (min_basin_size_km2 * 1000000) / (cell_res * cell_res)
max_acc = (max_basin_size_km2 * 1000000) / (cell_res * cell_res)

# dNBR thresholds for the 4-step BARC classification
dnbr_unburned = 25
dnbr_low = 125
dnbr_mod = 250
dnbr_high = 500

# Server locations
server_dir = "P:\\DF_Assessment_GeneralData"
script_dir = "P:\\Scripts"

# Fire-independent geodatabase file names
evt_gdb_name = 'LandFire_EVT.gdb'
landfire_gdb_name = 'LandFire_SAF_SRM.gdb'
mtbs_gdb_name = 'MTBS_Data.gdb'
soils_gdb_name = 'STATSGO_Soils.gdb'
projection_gdb_name = 'ProjectionData.gdb'

# Fire-dependent geodatabase tags
firein_gdb_tag = 'df_input'
temp_gdb_tag = 'scratch'
modelcalcs_gdb_tag = 'dfestimates_utm'
modelcalcs_web_gdb_tag = 'dfestimates_wgs84'

