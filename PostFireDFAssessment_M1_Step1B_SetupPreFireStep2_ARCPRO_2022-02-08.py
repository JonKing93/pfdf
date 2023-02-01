# This step of the code seems to implement the algorithm that determines the
# stream network.

### SETUP
# Initial tasks before running anything

# Notify console of the current step
print("Post-Fire Debris-Flow Hazard Assessment: Step 1 - Estimate Modeled Stream Network")
print("Importing Modules...")

# Import modules
import time
import arcpy
import os
import numpy as np
from numpy import *
import scipy
import glob
import string
from arcpy import env
from arcpy import gp
from arcpy.sa import *
import os.path
import csv
import datetime
import calendar
import shutil
import sys

# Set up arcpy.
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('spatial')
workingdir = os.getcwd()
env.workspace = workingdir
arcpy.env.overwriteOutput = True



### PARAMETERS
# Set various input parameters for the script

# string metadata for the fire
fire_name_list = ['Colorado']                 # Full fire name
fire_list = ['col']                           # 3 letter abbreviation
state_list =['CA']                            # State abbreviation
fire_location_list = ['Monterey County, CA']  # Location, State  (See main webpage for examples of formatting)
fire_start_date_list = ['January 21, 2022']   # Full start date -- MM DD, YYYY format
fireyear_list = ['2022']                      # fire start year

# The drive that holds the input datasets
server_root = 'P:\\'

# Pre-fire assessment parameters
pre_fire = 'NO'   # Change to 'YES' to implement a pre-fire assessment
if pre_fire == 'YES':
    evt_version = 140                        # ??? Unknown
    mtbs_perim_distance_km = 50              # ??? Unknown
    prefire_percentile_list = [0.5, 0.84]    # The percentiles to compute

# Output options. Options are 'YES' and 'NO'
make_webtext = 'YES'    # Prepare output for the web app
make_booktext= 'YES'    # ??? Perhaps for PDF Output
log_modelrun = 'YES'    # Create a logfile for the run
perim_check = 'YES'     # Prevent from overwriting an existing run on the server

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

# Location of data inputs and processing scripts
# Note: We should probably make separate settings for these
server_dir = os.path.join(server_root,'DF_Assessment_GeneralData')
script_dir = os.path.join(server_root,'Scripts')

# ??? Need to research what acc is
min_acc = (min_basin_size_km2 * 1000000) / (cell_res * cell_res)
max_acc = (max_basin_size_km2 * 1000000) / (cell_res * cell_res)

# ??? Unknown
# This may be a step to initialize a set of lists
soil_warn_list = []
fire_watch_list = []
fire_name_list_all = []
fire_location_list_all = []
fire_start_date_list_all = []
fire_statename_list = []
fire_state_name_list_all = []

# Set the dNBR thresholds for the 4-step BARC classification
dnbr_unburned = 25
dnbr_low = 125
dnbr_mod = 250
dnbr_high = 500





# START THE SCRIPT
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from contextlib import contextmanager
import sys, os
@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def write_log(logfile,id,string):
    targetfile = open(logfile,'a')

    log_now = time.gmtime()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S GMT', log_now)
    zone = 'GMT'

    log_string = timestamp+','+id+','+string+'\n'
    targetfile.write(log_string)
    targetfile.close()

if log_modelrun == 'YES':
    logfile_name = 'DFModel_Log.txt'
    logfile = os.path.join(workingdir,logfile_name)

    if os.path.isfile (logfile):
        pass
    else:
        target = open(logfile,'wt')
        target.write('TIMESTAMP,FIRE_ID,Processing_Step_Completed\n')
        target.close()

for fire_name in fire_list:

    i_index = fire_list.index(fire_name)
    state_abbrev = state_list[i_index]
    fire_year = fireyear_list[i_index]

    i = fire_name+fire_year

    print('Processing Fire = '+i+'...')

    arcpy.env.overwriteOutput = True
    arcpy.ClearEnvironment("cellSize")
    arcpy.ClearEnvironment("extent")
    arcpy.ClearEnvironment("snapRaster")
    arcpy.ClearEnvironment("mask")

    now = time.gmtime()
    datetimenow = datetime.datetime.now()
    year4digit = datetimenow.year
    monthstr = time.strftime('%m', now)
    monthint = int(monthstr)
    month = calendar.month_abbr[monthint]

    day = time.strftime('%d', now)
    year = time.strftime('%y', now)
    hour = time.strftime('%H', now)
    minute = time.strftime('%M', now)
    second = time.strftime('%S', now)
    zone = 'GMT'

    print(' Processing Started at '+str(hour)+':'+str(minute)+' GMT')

    if log_modelrun == 'YES':
        string = 'Start Step 1B'
        write_log(logfile,i,string)


    firein_gdb_name = i+'_df_input.gdb'
    firein_gdb = os.path.join(workingdir,firein_gdb_name) # Geodatabase Name and Path

    temp_gdb_name = i+'_scratch.gdb'
    temp_gdb = os.path.join(workingdir,temp_gdb_name) # Geodatabase Name and Path
    arcpy.env.scratchWorkspace = temp_gdb

    modelcalcs_gdb_name = i+'_dfestimates_utm.gdb'
    modelcalcs_gdb = os.path.join(workingdir,modelcalcs_gdb_name) # Geodatabase Name and Path

    modelcalcs_web_gdb_name = i+'_dfestimates_wgs84.gdb'
    modelcalcs_web_gdb = os.path.join(workingdir,modelcalcs_web_gdb_name) # Geodatabase Name and Path

    scratch_name = i+"_scratch"
    scratch = os.path.join(workingdir,scratch_name)

    pyscript_glob_string = os.path.join(workingdir,'*.py')
    py_file_list = glob.glob(pyscript_glob_string)

    webtext_name = i+'_webinfo.txt'
    webtext = os.path.join(workingdir,webtext_name)


    sim_sev_warn_list = []

    for sim_sev in sim_sev_list:



        print(' Copying Severity = '+str(sim_sev))
        out_dir_name = 'PreFire_Sev'+str(sim_sev)
        out_dir = os.path.join(workingdir,out_dir_name)

        if os.path.exists(out_dir):
            pass
        else:
            os.mkdir(out_dir)

        out_input_gdb = os.path.join(out_dir,firein_gdb_name)
        if os.path.exists(out_input_gdb):
            shutil.rmtree(out_input_gdb)
        out_temp_gdb = os.path.join(out_dir,temp_gdb_name)
        if os.path.exists(out_temp_gdb):
            shutil.rmtree(out_temp_gdb)
        out_modelcalcs_gdb = os.path.join(out_dir,modelcalcs_gdb_name)
        if os.path.exists(out_modelcalcs_gdb):
            shutil.rmtree(out_modelcalcs_gdb)
        out_modelcalcs_web_gdb = os.path.join(out_dir,modelcalcs_web_gdb_name)
        if os.path.exists(out_modelcalcs_web_gdb):
            shutil.rmtree(out_modelcalcs_web_gdb)
        out_scratch = os.path.join(out_dir,scratch_name)
        if os.path.exists(out_scratch):
            shutil.rmtree(out_scratch)

        print('     Copying Python Scripts...')

        for py_file in py_file_list:
            py_file_name = os.path.split(py_file)
            in_file = os.path.join(workingdir,py_file_name[1])
            out_file = os.path.join(out_dir,py_file_name[1])
            if os.path.exists(out_file):
                os.remove(out_file)
            shutil.copyfile(in_file,out_file)

        print('     Copying Info for Web...')
        in_file = webtext
        out_file = os.path.join(out_dir,webtext_name)
        shutil.copyfile(in_file,out_file)

        print('     Copying Model Geodatabases...')

        arcpy.Copy_management(firein_gdb,out_input_gdb)
        arcpy.Copy_management(temp_gdb,out_temp_gdb)
        arcpy.Copy_management(modelcalcs_gdb,out_modelcalcs_gdb)
        arcpy.Copy_management(modelcalcs_web_gdb,out_modelcalcs_web_gdb)

        print('     Copying Scratch Directory...')

        if os.path.exists(out_scratch):
            shutil.rmtree(out_scratch)

        shutil.copytree(scratch,out_scratch)

        print('     Converting Simulated Severity and dNBR data...')

        simdnbr_name = i+'_SimDNBR_P'+str(sim_sev)
        simdnbr = os.path.join(out_input_gdb,simdnbr_name)

        simsev_name = i+'_SimSeverity_P'+str(sim_sev)
        simsev = os.path.join(out_input_gdb,simsev_name)

        out_simdnbr_name = i+'_dnbr'
        out_simdnbr = os.path.join(out_input_gdb,out_simdnbr_name)

        out_simsev_name = i+'_sev'
        out_simsev = os.path.join(out_input_gdb,out_simsev_name)


        arcpy.CopyRaster_management(simdnbr,out_simdnbr)

        sim_sev_index = sim_sev_list.index(sim_sev)


        if sev_input == 'SIM':
            arcpy.CopyRaster_management(simsev,out_simsev)
            sim_sev_warn_list.extend([' No Severity Warnings for Severity = '+str(sim_sev)])
        else:
            if arcpy.Exists(out_simsev):
                pass
            else:
                sim_sev_warn_list_string = '  WARNING: Missing User-Specified Severity Raster, Please Copy Into '+out_input_gdb+' Prior to Running Step 2'
                print(sim_sev_warn_list_string)

                sim_sev_warn_list_add = [sim_sev_warn_list_string]
                sim_sev_warn_list.extend(sim_sev_warn_list_add)




# FINISHING PROCESSING~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



    now = time.gmtime()
    datetimenow = datetime.datetime.now()
    year4digit = datetimenow.year
    monthstr = time.strftime('%m', now)
    monthint = int(monthstr)
    month = calendar.month_abbr[monthint]

    day = time.strftime('%d', now)
    year = time.strftime('%y', now)
    hour = time.strftime('%H', now)
    minute = time.strftime('%M', now)
    second = time.strftime('%S', now)
    zone = 'GMT'


    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    for sev_string in sim_sev_warn_list:
        print(sev_string)
    print('')

    print(" Processing Finished at "+str(hour)+":"+str(minute)+" GMT")

    if log_modelrun == 'YES':
        string = 'Finished Step 1B'
        write_log(logfile,i,string)

    arcpy.env.overwriteOutput = True
    arcpy.ClearEnvironment("cellSize")
    arcpy.ClearEnvironment("extent")
    arcpy.ClearEnvironment("snapRaster")
    arcpy.ClearEnvironment("mask")
    arcpy.ResetEnvironments()
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')



