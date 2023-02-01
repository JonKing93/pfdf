#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#fire_list = ['T32117E1','T33115A1','T33115E1','T33116A1','T33116E1','T33117A1','T33117E1','T33118E1','T34115A1','T34116A1','T34117A1','T34118E1','T34119A1','T34119E1','T34120A1','T34120E1','T32115E1','T32116E1']
#fire_list = ['T33116E1','T33115E1','T33116A1','T33115A1','T32116E1','T32115E1','T34119A1']
fire_list = ['aug'] #3 letter abbreviation
state_list =['CA'] #State abbreviation
fireyear_list = ['2020'] #fire start year

sim_sev_list = [50,84]

sev_input = 'SIM'
#sev_input = 'USER' #USER NEEDS TO MANUALLY COPY IF THE SEV_INPUT VARIABLE IS SET TO USER!

log_modelrun = 'YES'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
print("Post-Fire Debris-Flow Hazard Assessment: Step 1B - PRE-FIRE ONLY: Setup Step 2 Working Directories")
print("Importing Modules...")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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


arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('spatial')
workingdir = os.getcwd()
env.workspace = workingdir

arcpy.env.overwriteOutput = True

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


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



