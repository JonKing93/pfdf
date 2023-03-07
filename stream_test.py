
"""
stream_test  Test the stream network module
"""

import stream
import arcpy

input = r"C:\Users\jking\Documents\Colorado_perim\Colorado_perim\col2022_df_input.gdb""\\"
scratch = r"C:\Users\jking\Documents\Colorado_perim\Colorado_perim\col2022_scratch.gdb""\\"
output = r"C:\Users\jking\Documents\DFHA-arcpy\DFHA-arcpy.gdb""\\"

total_area = input + "col2022_facc"
min_basin_area = 250
burned_area = scratch + "col2022_bacc"
min_burned_area = 100
flow_direction = input + "col2022_fdir"
stream_features = output + "stream_features_unsplit"
stream_raster = output + "stream_raster"
max_segment_length = 500
split_points = output + "split_points"
split_segments = output + "split_segments"

arcpy.env.overwriteOutput = True

final = stream.network(total_area, min_basin_area, burned_area, min_burned_area,
               flow_direction, stream_features, stream_raster,
               max_segment_length, split_points, split_segments)
