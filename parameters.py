"""
parameters  Parameters and configuration details for Step 1


"""

# Pre-fire assessment
pre_fire = False                        # Whether to compute a pre-fire assessment
evt_version = 140                       # ???
mtbs_perim_distance_km = 50             # ???
prefire_percentile_list = [0.5, 0.84]    # The percentiles to compute

# Options for designing network basins
min_basin_size_km2 = 0.025   # Minimum basin size
max_basin_size_km2 = 8.0     # Maximum basin size
cellsize = 10.0              # The cell size (in meters) when converting features to rasters
burn_acc_threshold = 100     # ??? Original comment is: n_pixels

# Algorithm Options
segment_guess = 'PERIM'  # ??? Unknown. Options are 'PERIM' and 'NO_PERIM'
barc_threshold = 'CALC'  # ??? Unknown. Options are 'CALC' and 'DEFINED'
                         # Original notes say that you should only use 'DEFINED'
                         # if you have DNBR but no SBS or BARC4, and that the option
                         # has not been tested on recent versions of ArcGIS
                         # (so this option may be defunct)

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