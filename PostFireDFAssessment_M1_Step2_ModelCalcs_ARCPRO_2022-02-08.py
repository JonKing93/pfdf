print("Post-Fire Debris-Flow Hazard Assessment: Step 2 - Calculate Debris-Flow Estimates")
print("Importing Modules...")
import arcpy
import os
import numpy as np
#from numpy import *
import scipy
from scipy import interpolate
#import matplotlib
import glob
import string
from arcpy import env
from arcpy import gp
from arcpy.sa import *
import os.path
import csv
import datetime
import calendar
import time
import shutil
import math
import sys
import pandas as pd


arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("spatial")
workingdir = os.getcwd()
env.workspace = workingdir

arcpy.env.overwriteOutput = True

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##fire_list = ['bct','fst','gap','hps','jnk','pny','sgc','wlv']
##state_list =['CA','WA','CA','CO','CO','CA','CA','WA']
##fireyear_list = ['2016','2015','2016','2016','2016','2016','2016','2015']

fire_list = ['col'] #3 letter abbreviation
state_list =['CA'] #State abbreviation
fireyear_list = ['2022'] #fire start year

server_root = 'P:\\'

log_modelrun = 'YES'
#log_modelrun = 'NO'

prefilter_dnbr = 'YES'
#prefilter_dnbr = 'NO'

prefilter_type = 'MEDIAN'
#prefilter_type = 'MINIMUM'

server_dir = os.path.join(server_root,'DF_Assessment_GeneralData')
script_dir = os.path.join(server_root,'Scripts')

min_basin_size_km2 = 0.1  # MINIMUM MODELED DRAINAGE SIZE IN KM2
max_basin_size_km2 = 8.00  # MAXIMUM MODELED DRAINAGE SIZE IN KM2
burn_acc_threshold = 100 # N PIXELS

lv_duration_list = [15]
duration_map_list = [15]

accum_list = [3,4,5,6,7,8,9,10]
accum_map_list = [6]

#intensity_list = [10,15,20,25,30,35,40,45,50]

RainAtP_list = [.10,.25,.40,.50,.60,.75,.90]
RainAtP_map_list = [0.50]
#threshold_p = 0.5

thresh_duration_list = [15,30,60]
thresh_duration_map_list = [15]

pfe_list = [1,2,5,10,25,50,100]

model = 'M1'

mapping_scale_list = ['Segment','Basin']

join_estimates = 'YES'
#join_estimates = 'NO'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MODEL PARAMETERS

p_b_array = np.array([(-3.63,-3.61,-3.21),(-3.62,-3.61,-3.22),(-3.71,-3.79,-3.46),(-3.60,-3.64,-3.30)])
p_c1_array = np.array([(0.41,0.26,0.17),(0.64,0.42,0.27),(0.32,0.21,0.14),(0.51,0.33,0.20)])
p_c2_array = np.array([(0.67,0.39,0.20),(0.65,0.38,0.19),(0.33,0.19,0.10),(0.82,0.46,0.24)])
p_c3_array = np.array([(0.70,0.50,0.22),(0.68,0.49,0.22),(0.47,0.36,0.18),(0.27,0.26,0.13)])

p_x1_list = ['PropHM23','HMSinTheta','Rugged','B30']
p_x2_list = ['dNBRdiv1000','dNBRdiv1000','PropHM','dNBRdiv1000']
p_x3_list = ['KF','KF','Thick/100','Thick/100']
p_r_type = 'Acc'

v_x1_name = 'SqRtRelief'
v_x2_name = 'lnHMkm2'
v_x3_name = 'SqRtI15'
v_b = 4.22
v_c1 = 0.13 #Relief
v_c2 = 0.36 #HHkm2
v_c3 = 0.39 #I15
v_se = 1.04

dnbr_filter_x = 20
dnbr_filter_y = 20
dnbr_null_threshold = -2000
dnbr_min_threshold = -1000
dnbr_max_threshold = 1000

if model == 'M1':
    model_row = 0

elif model == 'M2':
    model_row = 1

elif model == 'M3':
    model_row = 2

elif model == 'M4':
    model_row = 3

else:
    model_row = 0


pour_pt_buffer_dist_eq = '(cell_res * 0.5) + cell_res'

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
        target.write('TIMESTAMP,FIRE_ID,Processing_Step_Completed')
        target.close()

print('Processing Model = '+model+'...')

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

# BACK UP EDITED POUR POINTS AND STREAM NETWORK

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

    print(" Processing Started at "+str(hour)+":"+str(minute)+" GMT")


    if log_modelrun == 'YES':
        string = 'Start Step 2'
        write_log(logfile,i,string)

# BUILD GEODATABASES, SCRATCH DIRECTORIES, DEFINE SERVER DATA LOCATION

    fire_webinfo = os.path.join(workingdir,i+"_webinfo.txt")

    if os.path.exists(fire_webinfo):
        target = open(fire_webinfo,'rt')
        lines = target.readlines()
        fire_name_full_text_raw = lines[0]
        fire_name_full_text = str.replace(fire_name_full_text_raw,'Fire Name = ','')
        fire_name_full_text = str.replace(fire_name_full_text,'\n','')
        startdate_text_raw = lines[2]
        startdate_text = str.replace(startdate_text_raw, 'Fire Start Date = ','')
        startdate_text = str.replace(startdate_text,'\n','')
        state_text_raw = lines[6]
        state_name_text = str.replace(state_text_raw, 'State = ','')
        state_name_text = str.replace(state_name_text,'\n','')

    else:
        fire_name_full_text = i
        startdate_text = 'N/A'
        state_name_text = state_abbrev

    projection_gdb_name = 'ProjectionData.gdb'
    projection_gdb = os.path.join(server_dir,projection_gdb_name)
    if os.path.exists(projection_gdb):
        print('     Connected to P: Drive, Continuing Processing...')
    else:
        print('     Not Connected to P:, Terminating Program')
        print('     ***Please Reconnect to P: and Restart Script***')
        sys.exit()

    print("     Backing Up Data from Step 1...")

    step1_backup_dir = os.path.join(workingdir,i+"_step1_backup_"+str(year4digit)+"-"+monthstr+"-"+str(day)+"_"+str(hour)+str(minute))
    if not os.path.exists (step1_backup_dir): os.mkdir(step1_backup_dir)

    symbology_dir_name = 'AssessmentResults_Symbology'
    estimates_symbology_dir_name = 'Estimates_Symbology'
    threshold_symbology_dir_name = 'Threshold_Symbology'
    streamwork_symbology_dir_name = 'StreamWork_Symbology'
    symbology_dir = os.path.join(server_dir,symbology_dir_name)
    estimates_symbology_dir = os.path.join(symbology_dir,estimates_symbology_dir_name)
    threshold_symbology_dir = os.path.join(symbology_dir,threshold_symbology_dir_name)

    streamwork_symbology_dir = os.path.join(symbology_dir,streamwork_symbology_dir_name)

    firein_gdb_name = i+"_df_input.gdb"
    firein_gdb = os.path.join(workingdir,firein_gdb_name) # Geodatabase Name and Path
    firein_gdb_backup = os.path.join(step1_backup_dir,firein_gdb_name)
    arcpy.Copy_management(firein_gdb, firein_gdb_backup)

    temp_gdb_name = i+"_scratch.gdb"
    temp_gdb = os.path.join(workingdir,temp_gdb_name) # Geodatabase Name and Path
    if not os.path.exists (temp_gdb): arcpy.CreateFileGDB_management(workingdir, temp_gdb_name, "CURRENT")    # Create File Geodatabase
    arcpy.env.scratchWorkspace = temp_gdb
    temp_gdb_backup = os.path.join(step1_backup_dir,temp_gdb_name)
    arcpy.Copy_management(temp_gdb, temp_gdb_backup)

    if os.path.exists(fire_webinfo):
        fire_webinfo_backup = os.path.join(step1_backup_dir,i+"_webinfo.txt")
        shutil.copyfile(fire_webinfo,fire_webinfo_backup)

    modelcalcs_gdb_name = i+"_dfestimates_utm.gdb"
    modelcalcs_gdb = os.path.join(workingdir,modelcalcs_gdb_name) # Geodatabase Name and Path
    if not os.path.exists (modelcalcs_gdb): arcpy.CreateFileGDB_management(workingdir, modelcalcs_gdb_name, "CURRENT")    # Create File Geodatabase
    modelcalcs_gdb_backup = os.path.join(step1_backup_dir,modelcalcs_gdb_name)
    arcpy.Copy_management(modelcalcs_gdb, modelcalcs_gdb_backup)
    modelcalcs_web_gdb_name = i+'_dfestimates_wgs84.gdb'
    modelcalcs_web_gdb = os.path.join(workingdir,modelcalcs_web_gdb_name) # Geodatabase Name and Path
    if not os.path.exists (modelcalcs_web_gdb): arcpy.CreateFileGDB_management(workingdir, modelcalcs_web_gdb_name, "CURRENT")    # Create File Geodatabase

    verification_gdb_name = i+"_verification.gdb"
    verification_gdb = os.path.join(workingdir,verification_gdb_name) # Geodatabase Name and Path
    if not os.path.exists (verification_gdb): arcpy.CreateFileGDB_management(workingdir, verification_gdb_name, "CURRENT")    # Create File Geodatabase

    threshold_utm_gdb_name = i+"_threshold_utm.gdb"
    threshold_utm_gdb = os.path.join(workingdir,threshold_utm_gdb_name) # Geodatabase Name and Path
    if not os.path.exists (threshold_utm_gdb): arcpy.CreateFileGDB_management(workingdir, threshold_utm_gdb_name, "CURRENT")    # Create File Geodatabase

    threshold_wgs_gdb_name = i+"_threshold_wgs.gdb"
    threshold_wgs_gdb = os.path.join(workingdir,threshold_wgs_gdb_name) # Geodatabase Name and Path
    if not os.path.exists (threshold_wgs_gdb): arcpy.CreateFileGDB_management(workingdir, threshold_wgs_gdb_name, "CURRENT")    # Create File Geodatabase

    soils_gdb_name = "STATSGO_Soils.gdb"
    soils_gdb = os.path.join(server_dir,soils_gdb_name)

    scratch_name = i+"_scratch"
    scratch = os.path.join(workingdir,scratch_name)
    if not os.path.exists (scratch): os.mkdir(scratch)

    scratch_backup_name = i+"_scratch"
    scratch_backup = os.path.join(step1_backup_dir,scratch_backup_name)
    shutil.copytree(scratch,scratch_backup)

    kerneldir = os.path.join(scratch,'kernel_files')
    if not os.path.exists (kerneldir): os.mkdir(kerneldir)

    nws_server_dir_name = 'NWS_Data'
    nws_server_dir = os.path.join(server_root,nws_server_dir_name)
    nws_server_gdb_name = 'NWS_ThresholdCompilation_BaseData.gdb'
    nws_server_gdb = os.path.join(nws_server_dir,nws_server_gdb_name)

    pfe_gdb_name = 'NOAA14_PFEData_Final.gdb'
    pfe_gdb = os.path.join(nws_server_dir,pfe_gdb_name)

# IMPORT MODULES

    tau_py = 'DFTools_TauDEM_PRO.py'
    arc_py = 'DFTools_ArcGIS_PRO.py'
    confine_py = 'DFTools_Confinement_PRO.py'
    module_list = [tau_py,arc_py,confine_py]


    for module_name in module_list:

        in_module = os.path.join(script_dir,module_name)
        out_module = os.path.join(workingdir,module_name)
        if not os.path.exists(out_module):
            shutil.copy(in_module,out_module)

    import DFTools_TauDEM_PRO as DFTools_TauDEM
    import DFTools_ArcGIS_PRO as DFTools_ArcGIS
    import DFTools_Confinement_PRO as DFTools_Confinement

# DEFINE INPUT DATA~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # REQUIRED INPUT DATA

    dem_name = i+"_dem"
    dem = os.path.join(firein_gdb,dem_name)

    shd_name = i+'_shd'
    shd = os.path.join(firein_gdb,shd_name)

    sev_name = i+"_sev"
    sev = os.path.join(firein_gdb,sev_name)

    dnbr_name = i+'_dnbr'
    dnbr = os.path.join(firein_gdb,dnbr_name)

    perim_feat_name = i+"_perim_feat"
    perim_feat = os.path.join(firein_gdb,perim_feat_name)

    db_feat_name = i+"_db_feat"
    db_feat = os.path.join(firein_gdb,db_feat_name)#NOT REQUIRED

    step1_strm_feat_name = i+"_step1_strm_feat"
    step1_strm_feat = os.path.join(firein_gdb,step1_strm_feat_name)
    step1_strm_feat_backup_name = step1_strm_feat+"edited_"+str(year4digit)+"_"+monthstr+"_"+str(day)+"_"+str(hour)+str(minute)+str(second)
    step1_strm_feat_backup = os.path.join(firein_gdb,step1_strm_feat_backup_name)
    arcpy.CopyFeatures_management(step1_strm_feat, step1_strm_feat_backup)

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight

    min_acc = (min_basin_size_km2 * 1000000) / (cell_res * cell_res)
    max_acc = (max_basin_size_km2 * 1000000) / (cell_res * cell_res)

    pour_pt_buffer_dist = eval(pour_pt_buffer_dist_eq)

# SET INITIAL ENVIRONMENTS



# GET UTM ZONE......~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    in_perim_centroid_feat_name = i+'_perim_centroid_feat'
    in_perim_centroid_feat = os.path.join(temp_gdb,in_perim_centroid_feat_name)

    in_perim_dissolve_feat_name = i+'_perim_dissolve_feat'
    in_perim_dissolve_feat = os.path.join(temp_gdb,in_perim_dissolve_feat_name)

    utmzone_feat_name = 'UTMZones_Feat_GCS_WGS84'
    utmzone_feat = os.path.join(projection_gdb,utmzone_feat_name)

    perim_centroid_utmfind_feat_name = i+'_perim_centroid_utmfind_feat'
    perim_centroid_utmfind_feat = os.path.join(temp_gdb,perim_centroid_utmfind_feat_name)

    perim_centroid_utmzone_feat_name = i+'_perim_centroid_utmzone_feat'
    perim_centroid_utmzone_feat = os.path.join(temp_gdb,perim_centroid_utmzone_feat_name)



    if arcpy.Exists(perim_centroid_utmzone_feat):

        zone_array = arcpy.da.TableToNumPyArray(perim_centroid_utmzone_feat,'ZONE')

        zone_array2 = zone_array[0]
        zone = int(zone_array2[0])
        zone_str = str(zone)

        ref_utmzone_perim_feat_name = 'UTMZone_'+zone_str+'_Perim_Feat'
        ref_utmzone_perim_feat = os.path.join(projection_gdb,ref_utmzone_perim_feat_name)

    else:

        arcpy.AddField_management(perim_feat, "Perim_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        perim_id_field_list = ['Perim_ID']
        with arcpy.da.UpdateCursor(perim_feat, perim_id_field_list) as cursor:
            for row in cursor:
                row[0] = 1
                cursor.updateRow(row)

        arcpy.Dissolve_management(perim_feat,in_perim_dissolve_feat,'Perim_ID')

        arcpy.FeatureToPoint_management(in_perim_dissolve_feat,in_perim_centroid_feat,"CENTROID")

        arcpy.Project_management(in_perim_centroid_feat,perim_centroid_utmfind_feat,utmzone_feat)

        arcpy.Identity_analysis(perim_centroid_utmfind_feat,utmzone_feat,perim_centroid_utmzone_feat,"ALL")

        zone_array = arcpy.da.TableToNumPyArray(perim_centroid_utmzone_feat,'ZONE')

        zone_array2 = zone_array[0]
        zone = int(zone_array2[0])
        zone_str = str(zone)

        ref_utmzone_perim_feat_name = 'UTMZone_'+zone_str+'_Perim_Feat'
        ref_utmzone_perim_feat = os.path.join(projection_gdb,ref_utmzone_perim_feat_name)

    print('     Burn Area Located in UTM Zone '+zone_str+'...')

    wgs84_ref_feat_name = 'UTMZones_Feat_WGS84_WebMercator'
    wgs84_ref_feat = os.path.join(projection_gdb,wgs84_ref_feat_name)

    ref_wgs= arcpy.Describe(wgs84_ref_feat)

    wgs_spatial_ref = ref_wgs.SpatialReference


# GET UTM ZONE OF PERIMETER

    print('     Calculating Relevant Extent Data....')

    in_perim_centroid_feat_name = i+'_perim_centroid_feat'
    in_perim_centroid_feat = os.path.join(temp_gdb,in_perim_centroid_feat_name)

    in_perim_dissolve_feat_name = i+'_perim_dissolve_feat'
    in_perim_dissolve_feat = os.path.join(temp_gdb,in_perim_dissolve_feat_name)

    utmzone_feat_name = 'UTMZones_Feat_GCS_WGS84'
    utmzone_feat = os.path.join(projection_gdb,utmzone_feat_name)

    perim_centroid_utmfind_feat_name = i+'_perim_centroid_utmfind_feat'
    perim_centroid_utmfind_feat = os.path.join(temp_gdb,perim_centroid_utmfind_feat_name)

    perim_centroid_utmzone_feat_name = i+'_perim_centroid_utmzone_feat'
    perim_centroid_utmzone_feat = os.path.join(temp_gdb,perim_centroid_utmzone_feat_name)


    arcpy.AddField_management(perim_feat, "Perim_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    perim_id_field_list = ['Perim_ID']
    with arcpy.da.UpdateCursor(perim_feat, perim_id_field_list) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)


    arcpy.Dissolve_management(perim_feat,in_perim_dissolve_feat,'Perim_ID')

    arcpy.FeatureToPoint_management(in_perim_dissolve_feat,in_perim_centroid_feat)

    arcpy.Project_management(in_perim_centroid_feat,perim_centroid_utmfind_feat,utmzone_feat)

    arcpy.Identity_analysis(perim_centroid_utmfind_feat,utmzone_feat,perim_centroid_utmzone_feat,"ALL")

    zone_array = arcpy.da.TableToNumPyArray(perim_centroid_utmzone_feat,'ZONE')

    zone_array2 = zone_array[0]
    zone = int(zone_array2[0])
    zone_str = str(zone)

    ref_utmzone_perim_feat_name = 'UTMZone_'+zone_str+'_Perim_Feat'
    ref_utmzone_perim_feat = os.path.join(projection_gdb,ref_utmzone_perim_feat_name)

    ref_utmzone_desc = arcpy.Describe(ref_utmzone_perim_feat)
    utm_spatial_ref = ref_utmzone_desc.SpatialReference

    print('         Burn Area Located in UTM Zone '+zone_str+'...')

# CALCULATING BOX OF EXTENT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('         Creating Extent Rectangle...')
    ref_utmzone_desc = arcpy.Describe(ref_utmzone_perim_feat)
    utm_spatial_ref = ref_utmzone_desc.SpatialReference

    perim_desc = arcpy.Describe(perim_feat)
    perim_spatial_ref = perim_desc.SpatialReference

    perim_dd_feat_name = perim_feat_name+'_dd'
    perim_dd_feat = os.path.join(temp_gdb,perim_dd_feat_name)

    perim_box_dd_feat_name = perim_dd_feat_name+'_box'
    perim_box_dd_feat = os.path.join(temp_gdb,perim_box_dd_feat_name)

    extentbox_dd_feat_name = i+'_extent_dd_feat'
    extentbox_dd_feat = os.path.join(temp_gdb,extentbox_dd_feat_name)

    extentbox_feat_name = i+'_extent_feat'
    extentbox_feat = os.path.join(temp_gdb,extentbox_feat_name)

    extentbox_name = i+'_extent'
    extentbox = os.path.join(temp_gdb,extentbox_name)

    if perim_spatial_ref.name == 'GCS_North_American_1983':
        arcpy.CopyFeatures_management(perim_feat,perim_dd_feat)
    else:
        arcpy.Project_management(perim_feat,perim_dd_feat,"GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]")

    desc = arcpy.Describe(perim_dd_feat)
    extent = desc.extent
    left = extent.XMin
    bottom = extent.YMin
    top = extent.YMax
    right = extent.XMax

    lowerleft = extent.lowerLeft
    lowerright = extent.lowerRight
    upperright = extent.upperRight
    upperleft = extent.upperLeft

    arcpy.MinimumBoundingGeometry_management(perim_dd_feat,perim_box_dd_feat,'RECTANGLE_BY_AREA','ALL')

    arcpy.Buffer_analysis(perim_box_dd_feat,extentbox_dd_feat,0.02)

    arcpy.AddField_management(extentbox_dd_feat,"Extent_Code", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    extent_code_field_list = ['Extent_Code']
    with arcpy.da.UpdateCursor(extentbox_dd_feat, extent_code_field_list) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)

    arcpy.Project_management(extentbox_dd_feat,extentbox_feat,utm_spatial_ref)
    arcpy.PolygonToRaster_conversion(extentbox_feat,'Extent_Code',extentbox,'CELL_CENTER','',cell_res)

# CHECK PROJECTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print("     Checking Projections...")


    ref_utmzone_desc = arcpy.Describe(ref_utmzone_perim_feat)
    utm_spatial_ref = ref_utmzone_desc.SpatialReference

    project_check = "Fail"

    dem_desc = arcpy.Describe(dem)
    dem_spatial_ref = dem_desc.SpatialReference
    print("         DEM Projection = "+dem_spatial_ref.name)

    if dem_spatial_ref.name == utm_spatial_ref.name:
        dem_project_check = "Pass"
    else:
        dem_project_check = "Fail"

    if arcpy.Exists(sev):
        sev_desc = arcpy.Describe(sev)
        sev_spatial_ref = sev_desc.SpatialReference
        print("         Classified Burn Severity Projection = "+sev_spatial_ref.name)
        if sev_spatial_ref.name == utm_spatial_ref.name:
            sev_project_check = "Pass"
        else:
            sev_project_check = "Fail"
    else:
        sev_project_check = "Pass"

    if arcpy.Exists(dnbr):
        dnbr_desc = arcpy.Describe(dnbr)
        dnbr_spatial_ref = dnbr_desc.SpatialReference
        print("         dNBR Projection = "+dnbr_spatial_ref.name)
        if dnbr_spatial_ref.name == utm_spatial_ref.name:
            dnbr_project_check = "Pass"
        else:
            dnbr_project_check = "Fail"
    else:
        dnbr_project_check = "Pass"

    perim_desc = arcpy.Describe(perim_feat)
    perim_spatial_ref = perim_desc.SpatialReference
    print("         Burn Perimeter Projection = "+perim_spatial_ref.name)

    if perim_spatial_ref.name == utm_spatial_ref.name:
        perim_project_check = "Pass"
    else:
        perim_project_check = "Fail"

    if arcpy.Exists(db_feat):
        db_desc = arcpy.Describe(db_feat)
        db_spatial_ref = db_desc.SpatialReference
        print("         Debris Basin Projection = "+db_spatial_ref.name)

        if db_spatial_ref.name == utm_spatial_ref.name:
            db_project_check = "Pass"
        else:
            db_project_check = "Fail"

    else:
        db_project_check = "Pass"

    if (dem_project_check == "Fail") or (sev_project_check == "Fail") or (dnbr_project_check == "Fail") or (perim_project_check == "Fail") or (db_project_check == "Fail"):
        project_check = "Fail"
    else:
        project_check = "Pass"

    if project_check == "Fail":
        print("     WARNING: Input Data Projections are not all "+utm_spatial_ref.name+", Reprojecting Datasets...")
        print("         DEM Projection Check = "+dem_project_check)

        if dem_project_check == "Fail":
            print("             Projecting DEM to UTM...")
            z_dem = os.path.join(temp_gdb,"z"+i+"_dem")
            arcpy.Copy_management(dem, z_dem)
            arcpy.Delete_management(dem)
            arcpy.ProjectRaster_management(z_dem, dem, utm_spatial_ref, "BILINEAR", cell_res)
        else:
            pass

        arcpy.env.overwriteOutput = True
        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem

        if arcpy.Exists(sev):
            print("         Classified Burn Severity Projection Check = "+sev_project_check)
            if sev_project_check == "Fail":
                print("             Projecting Burn Severity Raster to UTM...")
                arcpy.env.cellSize = dem
                arcpy.env.extent = dem
                arcpy.env.snapRaster = dem
                z_sev = os.path.join(temp_gdb,"z"+i+"_sev")
                arcpy.Copy_management(sev, z_sev)
                arcpy.Delete_management(sev)
                arcpy.ProjectRaster_management(z_sev, sev, dem, "NEAREST", cell_res)
            else:
                pass
        else:
            pass

        if arcpy.Exists(dnbr):
            print("         dNBR Projection Check = "+dnbr_project_check)
            if dnbr_project_check == "Fail":
                print("             Projecting dNBR Raster to UTM...")
                arcpy.env.cellSize = dem
                arcpy.env.extent = dem
                arcpy.env.snapRaster = dem
                z_dnbr = os.path.join(temp_gdb,"z"+i+"_dnbr")
                arcpy.Copy_management(dnbr, z_dnbr)
                arcpy.Delete_management(dnbr)
                arcpy.ProjectRaster_management(z_dnbr, dnbr, dem, "NEAREST", cell_res)
            else:
                pass
        else:
            pass

        print("         Burn Perimeter Projection Check = "+perim_project_check)
        if perim_project_check == "Fail":
            print("             Projecting Burn Perimeter Feature Class to UTM...")
            z_perim_feat = os.path.join(temp_gdb,"z"+i+"_perim_feat")
            arcpy.Copy_management(perim_feat,z_perim_feat)
            arcpy.Delete_management(perim_feat)
            arcpy.Project_management(z_perim_feat, perim_feat, dem)
        else:
            pass


        if arcpy.Exists(db_feat):
            print("         Debris Basin Projection Check = "+db_project_check)
            if db_project_check == "Fail":
                print("             Projecting Debris Basin Feature Class to UTM...")
                z_db_feat = os.path.join(temp_gdb,"z"+i+"_db_feat")
                arcpy.Copy_management(db_feat, z_db_feat)
                arcpy.Delete_management(db_feat)
                arcpy.Project_management(z_db_feat, db_feat, dem)
            else:
                pass
        else:
            pass

    else:
        print("     Input Data Properly Projected as "+utm_spatial_ref.name+", Continuing Processing...")

# CALCULATING COMMON EXTENT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print("     Checking DEM, Severity and DNBR Extents...")

    dem_cols = arcpy.GetRasterProperties_management(dem,'COLUMNCOUNT')
    dem_rows = arcpy.GetRasterProperties_management(dem,'ROWCOUNT')

    sev_cols = arcpy.GetRasterProperties_management(sev,'COLUMNCOUNT')
    sev_rows = arcpy.GetRasterProperties_management(sev,'ROWCOUNT')

    dnbr_cols = arcpy.GetRasterProperties_management(dnbr,'COLUMNCOUNT')
    dnbr_rows = arcpy.GetRasterProperties_management(dnbr,'ROWCOUNT')

    print('         Input DEM is '+str(dem_rows)+' Rows X '+str(dem_cols)+' Columns')
    print('         Input Burn Severity Raster is '+str(sev_rows)+' Rows X '+str(sev_cols)+' Columns')
    print('         Input DNBR Raster is '+str(dnbr_rows)+' Rows X '+str(dnbr_cols)+' Columns')

    if (str(dem_rows) == str(sev_rows) == str(dnbr_rows)) and (str(dem_cols) == str(sev_cols) == str(dnbr_cols)):
        print('     DEM, Severity, and dNBR Share Common Extent, Continuing Processing...')

    else:

        print('     Finding Common Extent...')

        dem_orig_name = i+'_dem_orig'
        dem_orig = os.path.join(temp_gdb,dem_orig_name)

        sev_orig_name = i+'_sev_orig'
        sev_orig = os.path.join(temp_gdb,sev_orig_name)

        dnbr_orig_name = i+'_dnbr_orig'
        dnbr_orig = os.path.join(temp_gdb,dnbr_orig_name)

        arcpy.Copy_management(dem,dem_orig)
        arcpy.Copy_management(sev,sev_orig)
        arcpy.Copy_management(dnbr,dnbr_orig)

        arcpy.Delete_management(dem)
        arcpy.Delete_management(sev)
        arcpy.Delete_management(dnbr)


        arcpy.env.overwriteOutput = True
        arcpy.env.cellSize = extentbox
        arcpy.env.extent = extentbox
        arcpy.env.snapRaster = extentbox

        out_dem = Raster(extentbox) * Raster(dem_orig)
        out_dem.save(dem)

        out_sev = Raster(extentbox) * Raster(sev_orig)
        out_sev.save(sev)

        out_dnbr = Raster(extentbox) * Raster(dnbr_orig)
        out_dnbr.save(dnbr)

        dem_cols = arcpy.GetRasterProperties_management(dem,'COLUMNCOUNT')
        dem_rows = arcpy.GetRasterProperties_management(dem,'ROWCOUNT')

        sev_cols = arcpy.GetRasterProperties_management(sev,'COLUMNCOUNT')
        sev_rows = arcpy.GetRasterProperties_management(sev,'ROWCOUNT')

        dnbr_cols = arcpy.GetRasterProperties_management(dnbr,'COLUMNCOUNT')
        dnbr_rows = arcpy.GetRasterProperties_management(dnbr,'ROWCOUNT')

        print('         Processed DEM is '+str(dem_rows)+' Rows X '+str(dem_cols)+' Columns')
        print('         Processed Burn Severity Raster is '+str(sev_rows)+' Rows X '+str(sev_cols)+' Columns')
        print('         Processed DNBR Raster is '+str(dnbr_rows)+' Rows X '+str(dnbr_cols)+' Columns')

    arcpy.env.overwriteOutput = True
    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem



# TAUDEM VARIABLES FROM STEP 1~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # REMOVED PITS
    dem_taudem_name = i+"_dem.tif"
    dem_taudem = os.path.join(scratch,dem_taudem_name)

    fel_taudem_name = i+"_fel.tif"
    fel_taudem = os.path.join(scratch,fel_taudem_name)

    #D8 FLOW DIRECTION
    fdird8_taudem_name = i+"_d8.tif"
    fdird8_taudem = os.path.join(scratch,fdird8_taudem_name)

    sd8_taudem_name = i+"_sd8.tif"
    sd8_taudem = os.path.join(scratch,sd8_taudem_name)

    #D8 UPSLOPE AREA
    aread8_taudem_name = i+"_aread8.tif"
    aread8_taudem = os.path.join(scratch,aread8_taudem_name)

    #D-INFINITY FLOW DIRECTION
    dinfang_taudem_name = i+"_ang.tif"
    dinfang_taudme = os.path.join(scratch,dinfang_taudem_name)

    dinfslp_taudem_name = i+"_dinfslp.tif"
    dinfslp_taudme = os.path.join(scratch,dinfslp_taudem_name)

    #D-INFINITY UPSLOPE AREA
    areadinf_taudem_name = i+"_sca.tif"
    areadinf_taudem = os.path.join(scratch,areadinf_taudem_name)

    #D-INFINITY BASED RELIEF BUT TRANSLATING TO D8 USING THRESHOLD = 0.49 (TARBOTON PERSONAL COMM.)
    reliefd8_taudem_name = i+"_reliefd8.tif"
    relief_taudem = os.path.join(scratch,reliefd8_taudem_name)

    #D-INFINITY BASED FLOW LENGTH BUT TRANSLATING TO D8 USING THRESHOLD = 0.49 (TARBOTON PERSONAL COMM.)
    lengthd8_taudem_name = i+"_lend8.tif"
    lengthd8_taudem = os.path.join(scratch,lengthd8_taudem_name)

    #TAUDEM D8 FLOW GRIDS IN ARCGIS

    fdir_taudem_arc_name = i+"_taud8"
    fdir_taudem_arc = os.path.join(temp_gdb,fdir_taudem_arc_name)

    fdir_name = i+"_fdir"
    fdir = os.path.join(firein_gdb,fdir_name)
    facc_name = i+"_facc"
    facc = os.path.join(firein_gdb,facc_name)
    relief_name = i+"_relief"
    relief = os.path.join(firein_gdb,relief_name)
    flen_name = i+"_flen"
    flen = os.path.join(firein_gdb,flen_name)

    # DERIVED DATA

    basin_pt_feat_name = i+'_basinpt_feat'
    basin_pt_feat = os.path.join(firein_gdb,basin_pt_feat_name)

# SET ENVIRONMENTS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight
    pixel_area = cell_res * cell_res

# FILTER DNBR DATA VOIDS

    print('     Filtering dNBR image...')

    raw_dnbr_name = i+'_rawdnbr'
    raw_dnbr = os.path.join(temp_gdb,raw_dnbr_name)

    dnbr_NullCondition = 'Value <= '+str(dnbr_null_threshold)
    dnbr_MaxCondition = 'Value >= '+str(dnbr_max_threshold)
    dnbr_MinCondition = 'Value >= '+str(dnbr_min_threshold)

    if prefilter_dnbr == 'YES':

        print('         Applying '+prefilter_type+' Filter...')

        z_filtered_dnbr_name = i+'_dnbr_zfilter'
        z_filtered_dnbr = os.path.join(temp_gdb,z_filtered_dnbr_name)

        z_filter_neighborhood = NbrRectangle(5,5, 'CELL')

        out_FocalStats = FocalStatistics(dnbr,z_filter_neighborhood,prefilter_type)
        out_FocalStats.save(z_filtered_dnbr)


        print('         Identifying Data Voids...')
        outSetNull = SetNull(z_filtered_dnbr,z_filtered_dnbr,dnbr_NullCondition)
        outSetNull.save(raw_dnbr)

    else:
        print('         Identifying Data Voids...')
        outSetNull = SetNull(dnbr,dnbr,dnbr_NullCondition)
        outSetNull.save(raw_dnbr)

    print('         Removing Data Voids...')
    null_filtered_dnbr_name = i+'_dnbr_filtered_null'
    null_filtered_dnbr = os.path.join(temp_gdb,null_filtered_dnbr_name)

    filtered_dnbr_name = i+'_dnbr_filtered'
    filtered_dnbr = os.path.join(firein_gdb,filtered_dnbr_name)

    min_filtered_dnbr_name = i+'_dnbr_filtered_min'
    min_filtered_dnbr = os.path.join(temp_gdb,min_filtered_dnbr_name)


    dnbr_maxfilter_name = i+'_dnbr_max_'+str(dnbr_filter_x)+'x'+str(dnbr_filter_y)
    dnbr_maxfilter = os.path.join(temp_gdb,dnbr_maxfilter_name) # CHANGE TO TEMP GDB!!!!!!!!!!!

    dnbr_neighborhood = NbrRectangle(dnbr_filter_x,dnbr_filter_y, 'CELL')

    out_FocalStats = FocalStatistics(raw_dnbr,dnbr_neighborhood,'MAXIMUM')
    out_FocalStats.save(dnbr_maxfilter)

    DFTools_ArcGIS.ReplaceNull(raw_dnbr,null_filtered_dnbr,dnbr_maxfilter,raw_dnbr)

    print('         Applying High-Pass and Low-Pass Filters...')

    out_min_filter = Con(Raster(null_filtered_dnbr) <= dnbr_min_threshold, dnbr_min_threshold,null_filtered_dnbr)
    out_min_filter.save(min_filtered_dnbr)
    out_max_filter = Con(Raster(min_filtered_dnbr) >= dnbr_max_threshold, dnbr_max_threshold,min_filtered_dnbr)
    out_max_filter.save(filtered_dnbr)


# CREATING POUR POINTS
    print("     Deriving Basin Outlets...")

    z_step1_strmcl1_lyr = os.path.join(temp_gdb,"z"+i+"_step1_strm_lyr")
    z_step1_strmcl0_lyr = os.path.join(temp_gdb,"z"+i+"_step1_strm_lyr")

    step1_strm_lyr = os.path.join(temp_gdb,i+"_step1_strm_lyr")
    z_step1_strm_feat = os.path.join(temp_gdb,"z"+i+"_step1_strm_feat")
    step1_strmcl1_feat = os.path.join(temp_gdb,i+"_step1_strmcl1_feat")
    step1_strmcl0_feat = os.path.join(temp_gdb,i+"_step1_strmcl0_feat")
    z_step1_strmcl1_feat = os.path.join(temp_gdb,"z"+i+"_step1_strmcl1_feat")
    z_step1_strmcl0_feat = os.path.join(temp_gdb,"z"+i+"_step1_strmcl0_feat")

    z_step1_strmcl1 = os.path.join(temp_gdb,"z"+i+"_strmcl1")
    z_step1_strmcl0 = os.path.join(temp_gdb,"z"+i+"strmcl0")

    step1_strmcl0_buffer_feat = os.path.join(temp_gdb,i+"_step1_strmcl0_buffer_feat")
    z_step1_strmcl0_buffer = os.path.join(temp_gdb,"z"+i+"_scl0buf")
    step1_strmcl0_buffer = os.path.join(temp_gdb,i+"_scl0buf")
    step1_strmcl0_buffer_bin_feat = os.path.join(temp_gdb,i+"_step1_strmcl0_buffer_bin_feat")
    step1_strm_buffer_int_feat = os.path.join(temp_gdb,i+"_step1_strm_buffer_int_feat")

    arcpy.CopyFeatures_management(step1_strm_feat,z_step1_strmcl1_feat)
    arcpy.MakeFeatureLayer_management(z_step1_strmcl1_feat,z_step1_strmcl1_lyr)
    arcpy.SelectLayerByAttribute_management(z_step1_strmcl1_lyr, "NEW_SELECTION", "\"ModelClass\" = 0")
    arcpy.DeleteFeatures_management(z_step1_strmcl1_lyr)

    arcpy.CopyFeatures_management(step1_strm_feat,z_step1_strmcl0_feat)
    arcpy.MakeFeatureLayer_management(z_step1_strmcl0_feat,z_step1_strmcl0_lyr)
    arcpy.SelectLayerByAttribute_management(z_step1_strmcl0_lyr, "NEW_SELECTION", "\"ModelClass\" = 1")
    arcpy.DeleteFeatures_management(z_step1_strmcl0_lyr)

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

    arcpy.FeatureToRaster_conversion(z_step1_strmcl0_feat, "ModelClass", z_step1_strmcl0, dem)

    arcpy.FeatureToRaster_conversion(z_step1_strmcl1_feat, "ModelClass", z_step1_strmcl1, dem)

    step1_strmcl0_dist = os.path.join(temp_gdb,i+"_scl0dst")
    step1_strmcl0_buff = os.path.join(temp_gdb,i+"_scl0buf")

    out_step1_strmcl0_dist = EucDistance(z_step1_strmcl0)
    out_step1_strmcl0_dist.save(step1_strmcl0_dist)

    out_step1_strmcl0_buff = Con(Raster(step1_strmcl0_dist) > pour_pt_buffer_dist, 1, 0)
    out_step1_strmcl0_buff.save(step1_strmcl0_buff)

    arcpy.RasterToPolygon_conversion(step1_strmcl0_buff, step1_strmcl0_buffer_bin_feat, "NO_SIMPLIFY")
    arcpy.AddField_management(step1_strmcl0_buffer_bin_feat, "BUFFER_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    buffer_id_field_list = ['gridcode','BUFFER_ID']
    with arcpy.da.UpdateCursor(step1_strmcl0_buffer_bin_feat, buffer_id_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    intersect_features = '"'+step1_strm_feat+'", "'+step1_strmcl0_buffer_bin_feat+'"'
    arcpy.Intersect_analysis([step1_strm_feat, step1_strmcl0_buffer_bin_feat], step1_strm_buffer_int_feat)

    arcpy.MakeFeatureLayer_management(step1_strm_buffer_int_feat, step1_strm_lyr)
    arcpy.SelectLayerByAttribute_management(step1_strm_lyr, "NEW_SELECTION", "\"BUFFER_ID\" = 1")
    arcpy.CopyFeatures_management(step1_strm_lyr, step1_strmcl1_feat)

    arcpy.SelectLayerByAttribute_management(step1_strm_lyr, "NEW_SELECTION", "\"BUFFER_ID\" = 0")
    arcpy.CopyFeatures_management(step1_strm_lyr, step1_strmcl0_feat)

    step1_strmvert_feat = os.path.join(temp_gdb,i+"_step1_strmvert_feat")
    step1_strmvert_lyr = os.path.join(temp_gdb,i+"_step1_strmvert_lyr")
    step1_strmvertcl1_feat = os.path.join(temp_gdb,i+"_step1_strmvertcl1_feat")
    step1_strmvertcl0_feat = os.path.join(temp_gdb,i+"_step1_strmvertcl0_feat")
    step1_strmvertcl1_lyr = os.path.join(temp_gdb,i+"_step1_strmvertcl1_lyr")

    zpourpt_feat_name = "z"+i+"_pourpt_feat"
    zpourpt_feat = os.path.join(temp_gdb,zpourpt_feat_name)

    zpourpt_lyr_name = "z"+i+"_pourpt_lyr"
    zpourpt_lyr = os.path.join(temp_gdb,zpourpt_lyr_name)

    pourpt_feat_name = i+"_pourpt_feat"
    pourpt_feat = os.path.join(temp_gdb,pourpt_feat_name)

    arcpy.FeatureVerticesToPoints_management(step1_strm_buffer_int_feat, step1_strmvert_feat, "BOTH_ENDS")

    arcpy.MakeFeatureLayer_management(step1_strmvert_feat,step1_strmvert_lyr)
    arcpy.SelectLayerByLocation_management(step1_strmvert_lyr, "INTERSECT", step1_strmcl0_feat, "", "NEW_SELECTION")
    arcpy.CopyFeatures_management(step1_strmvert_lyr, step1_strmvertcl0_feat)

    arcpy.MakeFeatureLayer_management(step1_strmvert_feat,step1_strmvert_lyr)
    arcpy.SelectLayerByLocation_management(step1_strmvert_lyr, "INTERSECT", step1_strmcl1_feat, "", "NEW_SELECTION")
    arcpy.CopyFeatures_management(step1_strmvert_lyr, step1_strmvertcl1_feat)

    arcpy.MakeFeatureLayer_management(step1_strmvertcl1_feat,step1_strmvertcl1_lyr)
    arcpy.SelectLayerByLocation_management(step1_strmvertcl1_lyr, "ARE_IDENTICAL_TO", step1_strmvertcl0_feat)
    arcpy.CopyFeatures_management(step1_strmvertcl1_lyr, zpourpt_feat)

    arcpy.MakeFeatureLayer_management(zpourpt_feat,zpourpt_lyr)
    arcpy.SelectLayerByAttribute_management(zpourpt_lyr, "NEW_SELECTION", "\"BUFFER_ID\" = 1")
    arcpy.CopyFeatures_management(zpourpt_lyr, pourpt_feat)


    pourpt_drop_fields = ["FID_"+i+"_step1_strm_feat", "from_node", "to_node", "facc", "bacc", "burn_bin", "slp","conf","DevCl","Perim","MIN","DBCl","AreaCl","BurnCl","PerimCl","PctBurn","PctBurnCl","ConfineCl","SlopeCl","MorphCl","NonDevCl","zModCl","ModelClass","FID_"+i+"_step1_strmcl0_buffer_bin_feat","Id","grid_code","ORIG_FID"]
    arcpy.DeleteField_management(pourpt_feat, pourpt_drop_fields)
    arcpy.AddField_management(pourpt_feat, "BASIN_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    basin_id_field_list = ['Segment_ID','BASIN_ID']
    with arcpy.da.UpdateCursor(pourpt_feat, basin_id_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    basinpt_feat_name = i+"_basinpt_feat"
    basinpt_feat = os.path.join(firein_gdb,basinpt_feat_name)

    arcpy.CopyFeatures_management(pourpt_feat, basinpt_feat)

    arcpy.DeleteField_management(basinpt_feat,['Acc_Cl','Perim_BuffCl','InsidePerim_Cl','OutsidePerim_Cl'])

    arcpy.AddField_management(basinpt_feat,'Fire_Name','TEXT','','',50,'Fire_Name')
    arcpy.AddField_management(basinpt_feat,'Start_Date','TEXT','','',20,'Start_Date')
    arcpy.AddField_management(basinpt_feat,'State_Name','TEXT','','',20,'State_Name')

    fire_info_field_list = ['Fire_Name','Start_Date','State_Name']
    with arcpy.da.UpdateCursor(basinpt_feat, fire_info_field_list) as cursor:
        for row in cursor:
            row[0] = fire_name_full_text
            row[1] = startdate_text
            row[2] = state_name_text
            cursor.updateRow(row)


# BUILD STREAM NETWORK~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print("     Refining The Stream Network...")
    step1_strm_buffer_int_feat = os.path.join(temp_gdb,i+"_step1_strm_buffer_int_feat")
    step1_strm_buffer_int_lyr = os.path.join(temp_gdb,i+"_step1_strm_buffer_int_lyr")
    step1_strm_feat = os.path.join(firein_gdb,i+"_step1_strm_feat")
    step1_strm_lyr = os.path.join(firein_gdb,i+"_step1_strm_lyr")
    z_model_strm_feat = os.path.join(temp_gdb,"z"+i+"_modelstrm_feat")
    model_strm_feat = os.path.join(temp_gdb,i+"_modelstrm_feat")
    model_strm_lyr = os.path.join(temp_gdb,i+"_modelstrm_lyr")
    nonmodel_strm_feat = os.path.join(temp_gdb,i+"_nonmodelstrm_feat")
    bin_allstrm_link = os.path.join(temp_gdb,i+"_alllink")
    model_strmoutlet_feat = os.path.join(temp_gdb,i+"_modeloutlet_feat")
    model_strmoutlet = os.path.join(firein_gdb,i+"_basinpt")
    db_acc_bin = os.path.join(temp_gdb,i+"_dbaccb")
    db_acc_bin2 = os.path.join(temp_gdb,i+"_dbaccb2")

    outdbaccbin2 = Con(Raster(db_acc_bin) == 1, 0, 1)
    outdbaccbin2.save(db_acc_bin2)

    z_modlink_bin = os.path.join(temp_gdb,"z"+i+"_mlnkbin")

    strm_link_predict_float_name = i+"_modlink_float"
    strm_link_predict_float = os.path.join(temp_gdb,strm_link_predict_float_name)

    strm_link_predict_name = i+"_modlink"
    strm_link_predict = os.path.join(temp_gdb,strm_link_predict_name)
    strm_link_predict_acc_name = os.path.join(i+"_mlnkacc")
    strm_link_predict_acc = os.path.join(temp_gdb,strm_link_predict_acc_name)

    arcpy.MakeFeatureLayer_management(step1_strm_buffer_int_feat,step1_strm_buffer_int_lyr)
    arcpy.SelectLayerByAttribute_management(step1_strm_buffer_int_lyr, "NEW_SELECTION", '\"BUFFER_ID\" =  1')
    arcpy.CopyFeatures_management(step1_strm_buffer_int_lyr, z_model_strm_feat)

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight
    arcpy.FeatureToRaster_conversion(z_model_strm_feat, "BUFFER_ID", z_modlink_bin, dem)
    arcpy.FeatureToRaster_conversion(z_model_strm_feat, "BUFFER_ID", z_modlink_bin, dem)

    if arcpy.Exists(db_feat):
        out_strm_link_predict = Raster(z_modlink_bin) * Raster(bin_allstrm_link) * Raster(step1_strmcl0_buffer) * Raster(db_acc_bin2)
        out_strm_link_predict.save(strm_link_predict_float)
    else:
        out_strm_link_predict = Raster(z_modlink_bin) * Raster(bin_allstrm_link) * Raster(step1_strmcl0_buffer)
        out_strm_link_predict.save(strm_link_predict_float)

    out_strm_link_predict_acc = Raster(facc) * Raster(z_modlink_bin)
    out_strm_link_predict_acc.save(strm_link_predict_acc)

    out_stream_link_predict = Int(strm_link_predict_float)
    out_stream_link_predict.save(strm_link_predict)

    StreamToFeature(strm_link_predict, fdir, model_strm_feat, "NO_SIMPLIFY")
    arcpy.AddField_management(model_strm_feat, "Segment_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    segment_id_field_list = ['grid_code','Segment_ID']
    with arcpy.da.UpdateCursor(model_strm_feat, segment_id_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)
    arcpy.DeleteField_management(model_strm_feat, "arcid;grid_code;from_node,to_node")

    arcpy.SelectLayerByAttribute_management(step1_strm_buffer_int_lyr, "NEW_SELECTION", '\"BUFFER_ID\" =  0')
    arcpy.CopyFeatures_management(step1_strm_buffer_int_lyr, nonmodel_strm_feat)

    arcpy.MakeFeatureLayer_management(model_strm_feat, model_strm_lyr)
    arcpy.SelectLayerByLocation_management(model_strm_lyr, "INTERSECT", pourpt_feat, "", "NEW_SELECTION")
    arcpy.CopyFeatures_management(model_strm_lyr, model_strmoutlet_feat)

    pourpt_id_feat_name = i+'_pourpt_id_feat'
    pourpt_id_feat = os.path.join(temp_gdb,pourpt_id_feat_name)

    arcpy.Intersect_analysis([pourpt_feat, z_model_strm_feat],pourpt_id_feat,'ALL','','POINT')

    model_strmoutlet_id_feat_name =i+"_modeloutlet_id_feat"
    model_strmoutlet_id_feat = os.path.join(temp_gdb,model_strmoutlet_id_feat_name)

    arcpy.SpatialJoin_analysis(model_strmoutlet_feat,pourpt_id_feat,model_strmoutlet_id_feat,'JOIN_ONE_TO_ONE','KEEP_COMMON')

    pourpt_id_name = i+'_pourpt_id'
    pourpt_id = os.path.join(temp_gdb,pourpt_id_name)

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight
    arcpy.FeatureToRaster_conversion(model_strmoutlet_feat, "Segment_ID", pourpt_id, dem)


# CALC DRAINAGE BASINS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print("     Defining Drainage Basins...")
    pourpt_feat_name = i+"_pourpt_feat"
    pourpt_feat = temp_gdb+"\\"+pourpt_feat_name

    pourpt_name = i+"_pourpt"
    pourpt = temp_gdb+"\\"+pourpt_name

    basin = firein_gdb+"\\"+i+"_basin"
    basin_feat = firein_gdb+"\\"+i+"_basin_feat"
    z_basin_feat = temp_gdb+"\\z"+i+"_basin_feat"
    z_basin_lyr = temp_gdb+"\\z"+i+"_basin_lyr"
    basin_pt_link_table = temp_gdb+"\\"+i+"_basinpt_link"

    out_basin = Watershed(fdir,pourpt_id,'VALUE')
    out_basin.save(basin)

    arcpy.RasterToPolygon_conversion(basin, z_basin_feat, "NO_SIMPLIFY", "VALUE")
    arcpy.AddField_management(z_basin_feat, "BASIN_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    basin_id_field_list = ['gridcode','BASIN_ID']
    with arcpy.da.UpdateCursor(z_basin_feat, basin_id_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)


    arcpy.Dissolve_management(z_basin_feat, basin_feat, "BASIN_ID", "", "MULTI_PART")

    arcpy.DeleteField_management(basin_feat,['Acc_Cl','Perim_BuffCl','InsidePerim_Cl','OutsidePerim_Cl','Shape_Length_1'])

    arcpy.AddField_management(basin_feat,'Fire_Name','TEXT','','',50,'Fire_Name')
    arcpy.AddField_management(basin_feat,'Start_Date','TEXT','','',20,'Start_Date')
    arcpy.AddField_management(basin_feat,'State_Name','TEXT','','',20,'State_Name')

    fire_info_field_list = ['Fire_Name','Start_Date','State_Name']
    with arcpy.da.UpdateCursor(basin_feat, fire_info_field_list) as cursor:
        for row in cursor:
            row[0] = fire_name_full_text
            row[1] = startdate_text
            row[2] = state_name_text
            cursor.updateRow(row)

    basin_strm_int_name = i+'_basinstrm_feat'
    basin_strm_int = os.path.join(temp_gdb,basin_strm_int_name)

    prelim_model_strm_feat_name = i+'_prelim_model_strm_feat'
    prelim_model_strm_feat = os.path.join(temp_gdb,prelim_model_strm_feat_name)
    arcpy.Copy_management(model_strm_feat,prelim_model_strm_feat)

    arcpy.Delete_management(model_strm_feat)
    arcpy.Copy_management(z_step1_strmcl1_feat, model_strm_feat)
    delete_fields = ["Join_Count","TARGET_FID","from_node","to_node","from_node_1","to_node_1","Shape_Length_1","StrmOrd","facc","bacc","burn_bin","slppct","conf","DevCl","Perim","MIN","DBCl","AreaCl","BurnCl","PerimCl","PctBurn","PctBurnCl","ConfineCl","SlopeCl","MorphCl","NonDevCl","zModCl","ModelClass",'Acc_Cl','Perim_BuffCl','InsidePerim_Cl','OutsidePerim_Cl']
    arcpy.DeleteField_management(model_strm_feat,delete_fields)


    arcpy.AddField_management(model_strm_feat,'Fire_Name','TEXT','','',50,'Fire_Name')
    arcpy.AddField_management(model_strm_feat,'Start_Date','TEXT','','',20,'Start_Date')
    arcpy.AddField_management(model_strm_feat,'State_Name','TEXT','','',20,'State_Name')

    with arcpy.da.UpdateCursor(model_strm_feat, fire_info_field_list) as cursor:
        for row in cursor:
            row[0] = fire_name_full_text
            row[1] = startdate_text
            row[2] = state_name_text
            cursor.updateRow(row)

# DEFINE PRELIMINARY WATCH STREAMS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    step1cl0_strm_lyr = os.path.join(temp_gdb,i+"_step1cl0_strm_lyr")

    watchstream_feat_name = i+'_watchstream_feat'
    watchstream_feat = os.path.join(firein_gdb,watchstream_feat_name)

    arcpy.MakeFeatureLayer_management(z_step1_strmcl0_feat,step1cl0_strm_lyr)
    arcpy.SelectLayerByAttribute_management(step1cl0_strm_lyr, "NEW_SELECTION", '\"StrmOrder\" >  1')
    arcpy.SelectLayerByAttribute_management(step1cl0_strm_lyr, "SUBSET_SELECTION", '\"bacc\" >  500')
    arcpy.SelectLayerByAttribute_management(step1cl0_strm_lyr, "SUBSET_SELECTION", '\"DBCl\" >  0')
    arcpy.CopyFeatures_management(step1cl0_strm_lyr, watchstream_feat)

    delete_fields = ["Join_Count","TARGET_FID","from_node","to_node","from_node_1","to_node_1","Shape_Length_1","StrmOrd","facc","bacc","burn_bin","slppct","conf","DevCl","Perim","MIN","DBCl","AreaCl","BurnCl","PerimCl","PctBurn","PctBurnCl","ConfineCl","SlopeCl","MorphCl","NonDevCl","zModCl","ModelClass",'Acc_Cl','StrmOrder','Perim_BuffCl','InsidePerim_Cl','OutsidePerim_Cl']
    arcpy.DeleteField_management(watchstream_feat,delete_fields)

    arcpy.AddField_management(watchstream_feat,'Fire_ID','TEXT','','',12,'Fire_ID')
    arcpy.AddField_management(watchstream_feat,'Fire_Name','TEXT','','',50,'Fire_Name')
    arcpy.AddField_management(watchstream_feat,'Start_Date','TEXT','','',20,'Start_Date')
    arcpy.AddField_management(watchstream_feat,'State_Name','TEXT','','',20,'State_Name')

    watchstream_info_field_list = ['Fire_ID','Fire_Name','Start_Date','State_Name']
    with arcpy.da.UpdateCursor(watchstream_feat, watchstream_info_field_list) as cursor:
        for row in cursor:
            row[0] = i
            row[1] = fire_name_full_text
            row[2] = startdate_text
            row[3] = state_name_text
            cursor.updateRow(row)

# ANALYZE AND CONVERT PERIMETERS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    centroid = os.path.join(firein_gdb,i+"_centroid_feat")

    out_perim_feat = os.path.join(modelcalcs_gdb,i+"_perim_feat")
    perim = os.path.join(temp_gdb,i+"_perim")

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight

    if arcpy.Exists(perim):
        arcpy.Delete_management(perim)
    else:
        pass
    arcpy.FeatureToRaster_conversion(perim_feat, "Perim_ID", perim, dem)


# CLASSIFY DNBR IF SEVERITY DATA DO NOT EXIST

    if arcpy.Exists(sev):
        pass
    else:
        if arcpy.Exists(filtered_dnbr):
            dnbr_reclass_string = '-99999 '+str(dnbr_unburned)+' 1;'+str(dnbr_unburned)+' '+str(dnbr_low)+' 2;'+str(dnbr_low)+' '+str(dnbr_mod)+' 3;'+str(dnbr_mod)+' 9999 4'
            arcpy.gp.Reclassify_sa(filtered_dnbr, "Value", dnbr_reclass_string, sev, "DATA")
        else:
            pass




# CALCULATE MODEL VARIABLES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('     Calculating Model Variables...')

    arcpy.AddField_management(model_strm_feat,'Fire_ID','TEXT','','',20,'','','')
    fire_id_field_list = ['Fire_ID']
    with arcpy.da.UpdateCursor(model_strm_feat, fire_id_field_list) as cursor:
        for row in cursor:
            row[0] = i
            cursor.updateRow(row)


    fire_column = "Fire_ID"
    segmentID_column = 'Segment_ID'
    fire_segmentID_column = 'Fire_SegmentID'
    arcpy.AddField_management(model_strm_feat,fire_segmentID_column,"TEXT","","",25)

    with arcpy.da.UpdateCursor(model_strm_feat, [fire_column,segmentID_column,fire_segmentID_column]) as cursor:
        for row in cursor:
            id_string = str(row[0])+'_'+str(row[1])
            row[2] = id_string
            cursor.updateRow(row)


# LIKELIHOOD VARIABLES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# X1 - PropHM23 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #print('     Calculating Slope (Degree and Pct)...')

    p_x1_name = p_x1_list[model_row]
    p_x2_name = p_x2_list[model_row]
    p_x3_name = p_x3_list[model_row]

    print('         Calculating Likelihood X1 = '+str(p_x1_name)+'...')

    l_x1_col_header = 'L_X1'

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight


    slpdeg_name = i+'_slpdeg'
    slpdeg = os.path.join(temp_gdb,slpdeg_name)
    out_slpdeg = Slope(dem,"DEGREE")
    out_slpdeg.save(slpdeg)

    slppct_name = i+'_slppct'
    slppct = os.path.join(temp_gdb,slppct_name)
    out_slppct = Slope(dem,"PERCENT_RISE")
    out_slppct.save(slppct)


    slppct30_name = i+'_slppct30'
    slppct30 = os.path.join(temp_gdb,slppct30_name)
    out_slppct30 = Con(Raster(slppct) >= 30, 1, 0)
    out_slppct30.save(slppct30)

    slpdeg23_name = i+'_slpdeg23'
    slpdeg23 = os.path.join(temp_gdb,slpdeg23_name)
    out_slpdeg23 = Con(Raster(slpdeg) >= 23, 1, 0)
    out_slpdeg23.save(slpdeg23)

    slpdeg30_name = i+'_slpdeg30'
    slpdeg30 = os.path.join(temp_gdb,slpdeg30_name)
    out_slpdeg30 = Con(Raster(slpdeg) >= 30, 1, 0)
    out_slpdeg30.save(slpdeg30)

    slppct30_binary_name = i+'_slppct30_binary'
    slppct30_binary = os.path.join(temp_gdb,slppct30_name)

    slpdeg23_binary_name = i+'_slpdeg23_binary'
    slpdeg23_binary = os.path.join(temp_gdb,slpdeg23_binary_name)

    slpdeg30_binary_name = i+'_slpdeg30_binary'
    slpdeg30_binary = os.path.join(temp_gdb,slpdeg30_binary_name)

    DFTools_ArcGIS.ReplaceNull(slpdeg23,slpdeg23_binary,0,slpdeg23)
    DFTools_ArcGIS.ReplaceNull(slppct30,slppct30_binary,0,slppct30)
    DFTools_ArcGIS.ReplaceNull(slpdeg30,slpdeg30_binary,0,slpdeg30)

    #print('     Extracting Burn Severity Characteristics...')

    DFTools_ArcGIS.Extract_Severity(i,perim_feat,sev,dem,temp_gdb)

    hm_name = i+"_hm"
    hm = os.path.join(temp_gdb,hm_name)

    hm_binary_name = i+"_hm_binary"
    hm_binary = os.path.join(temp_gdb,hm_binary_name)

    DFTools_ArcGIS.ReplaceNull(hm,hm_binary,0,hm)

    #HM23

    if model == 'M1':

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight

        hmslpdeg23_name = i+"_hmslpdeg23"
        hmslpdeg23 = os.path.join(temp_gdb,hmslpdeg23_name)

        out_hmslpdeg23 = Raster(hm_binary) * Raster(slpdeg23_binary)
        out_hmslpdeg23.save(hmslpdeg23)

        hmslpdeg23_binary_name = i+"_hmslpdeg23_binary"
        hmslpdeg23_binary = os.path.join(temp_gdb,hmslpdeg23_binary_name)

        DFTools_ArcGIS.ReplaceNull(hmslpdeg23,hmslpdeg23_binary,0,hmslpdeg23)

        hmslpdeg23_binary_upsum_name = i+"_hmslpdeg23_binary_upsum"
        hmslpdeg23_binary_upsum = os.path.join(temp_gdb,hmslpdeg23_binary_upsum_name)

        hmslpdeg23_binary_upsum2_name = i+"_hmslpdeg23_binary_upsum2"
        hmslpdeg23_binary_upsum2 = os.path.join(temp_gdb,hmslpdeg23_binary_upsum2_name)

        hmslpdeg23_binary_upprop_name = i+"_hmslpdeg23_binary_upprop"
        hmslpdeg23_binary_upprop = os.path.join(temp_gdb,hmslpdeg23_binary_upprop_name)

        with suppress_stdout():

            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, hmslpdeg23_binary, hmslpdeg23_binary_upsum, scratch, cell_res)

        DFTools_ArcGIS.ReplaceNull(hmslpdeg23_binary_upsum,hmslpdeg23_binary_upsum2,0,hmslpdeg23_binary_upsum)

        DFTools_ArcGIS.Upslope_Prop(hmslpdeg23_binary_upsum2,hmslpdeg23_binary_upprop,facc)

        hmslpdeg_upprop_segmentstats_name = i+'_hmslpdeg_upprop_segmentstats'
        hmslpdeg_upprop_segmentstats = os.path.join(temp_gdb,hmslpdeg_upprop_segmentstats_name)

        DFTools_ArcGIS.AddNumericStatToTable(hmslpdeg23_binary_upprop,strm_link_predict,model_strm_feat,hmslpdeg_upprop_segmentstats,l_x1_col_header,'MEAN','FLOAT')

    else:
        pass

    #SIN(SLP)

    if model == 'M2':

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight

        slpsin_name = i+'_slpsin'
        slpsin = os.path.join(temp_gdb,slpsin_name)

        hmslpsin_name = i+'_hmslpsin'
        hmslpsin = os.path.join(temp_gdb,hmslpsin_name)

        hmslpsin_upsum_name = i+'_hmslpsin_upsum'
        hmslpsin_upsum = os.path.join(temp_gdb,hmslpsin_upsum_name)

        hmslpsin_avg_name = i+'_hmslpsin_upavg'
        hmslpsin_avg = os.path.join(temp_gdb,hmslpsin_avg_name)


        hm_binary_upsum_name = i+'_hm_binary_upsum'
        hm_binary_upsum = os.path.join(temp_gdb,hm_binary_upsum_name)

        out_slpsin = Sin((Raster(slpdeg) / (180/3.14159)))
        out_slpsin.save(slpsin)

        out_hmslpsin = Raster(hm_binary) * Raster(slpsin)
        out_hmslpsin.save(hmslpsin)

        with suppress_stdout():

            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, hmslpsin, hmslpsin_upsum, scratch, cell_res)
            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, hm_binary, hm_binary_upsum, scratch, cell_res)

        DFTools_ArcGIS.Upslope_Mean(hmslpsin_upsum,hmslpsin_avg,hm_binary_upsum)

        hmslpsin_upavg_segmentstats_name = i+'_hmslpsin_upavg_segmentstats'
        hmslpsin_upavg_segmentstats = os.path.join(temp_gdb,hmslpsin_upavg_segmentstats_name)

        DFTools_ArcGIS.AddNumericStatToTable(hmslpsin_avg,strm_link_predict,model_strm_feat,hmslpsin_upavg_segmentstats,l_x1_col_header,'MEAN','FLOAT')

    else:
        pass

    #RUGGEDNESS

    if model == 'M3':

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight

        relief = os.path.join(firein_gdb,i+"_relief")

        up_area_m2_name = i+'_uparea_m2'
        up_area_m2 = os.path.join(temp_gdb,up_area_m2_name)

        out_up_area_m2 = Raster(facc) * cell_res * cell_res
        out_up_area_m2.save(up_area_m2)

        sqrt_up_area_m2_name = i+'sqrt__uparea_m2'
        sqrt_up_area_m2 = os.path.join(temp_gdb,sqrt_up_area_m2_name)

        out_sqrt_up_area_m2 = SquareRoot(up_area_m2)
        out_sqrt_up_area_m2.save(sqrt_up_area_m2)

        rugged_name = i+'_rugged'
        rugged = os.path.join(temp_gdb,rugged_name)

        out_rugged = Raster(relief) / Raster(sqrt_up_area_m2)
        out_rugged.save(rugged)

        rugged_segmentstats_name = i+'_rugged_segmentstats'
        rugged_segmentstats = os.path.join(temp_gdb,rugged_segmentstats_name)

        DFTools_ArcGIS.AddNumericStatToTable(rugged,strm_link_predict,model_strm_feat,rugged_segmentstats,l_x1_col_header,'MEAN','FLOAT')

    else:
        pass


    #B30

    if model == 'M4':

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight


        burn_binary_name = i+'_burn_binary'
        burn_binary = os.path.join(temp_gdb,burn_binary_name)

        zburn =  os.path.join(temp_gdb,i+"_zburn")
        burn =  os.path.join(temp_gdb,i+"_burn")
        z1burn_bin =  os.path.join(temp_gdb,i+"_z1bbin")
        z2burn_bin =  os.path.join(temp_gdb,i+"_z2bbin")

        out_zburn = Con(Raster(sev) >= 2, 1)
        out_zburn.save(zburn)
        out_burn = Raster(zburn) * Raster(perim)
        out_burn.save(burn)

        out_z2burn_bin = IsNull(burn)
        out_z2burn_bin.save(z2burn_bin)
        out_burn_bin = Con(Raster(z2burn_bin) > 0, 0, 1)
        out_burn_bin.save(burn_binary)


        z_b30_name = 'z'+i+'_b30'
        z_b30 = os.path.join(temp_gdb,z_b30_name)

        b30_name = i+'_b30'
        b30 = os.path.join(temp_gdb,b30_name)

        out_z_b30 = Raster(burn_binary) * Raster(slpdeg30)
        out_z_b30.save(z_b30)

        DFTools_ArcGIS.ReplaceNull(z_b30,b30,0,z_b30)

        b30_upsum_name = i+'_b30_upsum'
        b30_upsum = os.path.join(temp_gdb,b30_upsum_name)

        b30_upprop_name = i+'_b30_upprop'
        b30_upprop = os.path.join(temp_gdb,b30_upprop_name)

        with suppress_stdout():

            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, b30, b30_upsum, scratch, cell_res)

        b30_segmentstats_name = i+'_b30_segmentstats'
        b30_segmentstats = os.path.join(temp_gdb,b30_segmentstats_name)

        DFTools_ArcGIS.Upslope_Prop(b30_upsum,b30_upprop,facc)

        DFTools_ArcGIS.AddNumericStatToTable(b30_upprop,strm_link_predict,model_strm_feat,b30_segmentstats,l_x1_col_header,'MEAN','FLOAT')

    else:
        pass

# X2 - dNBRdiv1000 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #print('     Extracting Average dNBR...')
    print('         Calculating Likelihood X2 = '+str(p_x2_name)+'...')

    l_x2_col_header = 'L_X2'
    perim_bin =  os.path.join(temp_gdb,i+"_perbin")

    if model == 'M3':

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight

        hm_binary_name = i+"_hm_binary"
        hm_binary = os.path.join(temp_gdb,hm_binary_name)

        hm_upsum_name = i+'_hm_upsum'
        hm_upsum = os.path.join(temp_gdb,hm_upsum_name)

        hm_upprop_name = i+'_hm_upprop'
        hm_upprop = os.path.join(temp_gdb,hm_upprop_name)

        with suppress_stdout():

            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, hm_binary, hm_upsum, scratch, cell_res)

        DFTools_ArcGIS.Upslope_Prop(hm_upsum,hm_upprop,facc)

        hm_segmentstats_name = i+'_hm_segmentstats'
        hm_segmentstats = os.path.join(temp_gdb,hm_segmentstats_name)

        DFTools_ArcGIS.AddNumericStatToTable(hm_upprop,strm_link_predict,model_strm_feat,hm_segmentstats,l_x2_col_header,'MEAN','FLOAT')

    else:

        dnbr_perim_name = i+'_dnbr_perim'
        dnbr_perim = os.path.join(temp_gdb,dnbr_perim_name)

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight

        out_dnbr_perim = Raster(perim_bin) * Raster(filtered_dnbr)
        out_dnbr_perim.save(dnbr_perim)

        dnbr_perim_float_name = i+'_dnbr_perim_float'
        dnbr_perim_float = os.path.join(temp_gdb,dnbr_perim_float_name)
        out_dnbr_perim_float = Float(dnbr_perim)
        out_dnbr_perim_float.save(dnbr_perim_float)


        z_dnbrdiv1000_name = 'z'+i+'_dNBRdiv1000'
        z_dnbrdiv1000 = os.path.join(temp_gdb,z_dnbrdiv1000_name)
        out_z_dnbrdiv1000 = Raster(dnbr_perim_float) / 1000
        out_z_dnbrdiv1000.save(z_dnbrdiv1000)

        dnbrdiv1000_name = i+'_dNBRdiv1000'
        dnbrdiv1000 = os.path.join(firein_gdb,dnbrdiv1000_name)

        out_dnbrdiv1000 = Con(Raster(z_dnbrdiv1000) < 0, 0, z_dnbrdiv1000)
        out_dnbrdiv1000.save(dnbrdiv1000)

        dnbr_perim_upsum_name = dnbr_perim_name+'_upsum'
        dnbr_perim_upsum = os.path.join(temp_gdb,dnbr_perim_upsum_name)

        dnbr_avg_name = dnbr_name+'_avg'
        dnbr_avg = os.path.join(temp_gdb,dnbr_avg_name)

        with suppress_stdout():

            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, dnbrdiv1000, dnbr_perim_upsum,scratch, cell_res)

        DFTools_ArcGIS.Upslope_Mean(dnbr_perim_upsum,dnbr_avg,facc)

        dnbr_stats_name = dnbr_perim_name+'_stats'
        dnbr_stats = os.path.join(temp_gdb,dnbr_stats_name)
        DFTools_ArcGIS.AddNumericStatToTable(dnbr_avg,strm_link_predict,model_strm_feat,dnbr_stats,l_x2_col_header,"MEAN","FLOAT")

 # X3 - KF ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #print('         Calculating Soil Properties...')
    print('         Calculating Likelihood X3 = '+str(p_x3_name)+'...')

    fire_soils_feat_name = i+'_soils_feat'
    fire_soils_feat = os.path.join(firein_gdb,fire_soils_feat_name)

    soils_list = ['KFFACT','THICK']

    l_x3_col_header = 'L_X3'

    for soil_prop in soils_list:

        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.env.snapRaster = dem
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight

        zsoil_name = i+'_z'+soil_prop
        zsoil = os.path.join(temp_gdb,zsoil_name)

        soil_name = i+'_'+soil_prop
        soil = os.path.join(temp_gdb,soil_name)

        soil_area_name = i+'_'+soil_prop+'_area'
        soil_area = os.path.join(temp_gdb,soil_area_name)

        arcpy.FeatureToRaster_conversion(fire_soils_feat, soil_prop, zsoil, dem)

        z2soil_name = i+'_z2'+soil_prop
        z2soil = os.path.join(temp_gdb,z2soil_name)

        if soil_prop == 'THICK':

            out_z2soil = Raster(zsoil) / 100
            out_z2soil.save(z2soil)

        else:
            arcpy.Copy_management(zsoil,z2soil)

        outsetnull = SetNull(z2soil,z2soil,"VALUE < -1")
        outsetnull.save(soil)

        out_soilarea = Con(Raster(soil) >= 0, 1)
        out_soilarea.save(soil_area)


        fire_soil_prop_name = i+'_'+soil_prop
        fire_soil_prop = os.path.join(temp_gdb,fire_soil_prop_name)

        fire_soil_prop_area_name = i+'_'+soil_prop+'_area'
        fire_soil_prop_area = os.path.join(temp_gdb,fire_soil_prop_area_name)

        soil_upsum_name = i+'_'+soil_prop+'upsum'
        soil_upsum = os.path.join(temp_gdb,soil_upsum_name)

        soil_area_upsum_name = i+'_'+soil_prop+'areaupsum'
        soil_area_upsum = os.path.join(temp_gdb,soil_area_upsum_name)

        soil_mean_name = i+'_'+soil_prop+'avg'
        soil_mean = os.path.join(temp_gdb,soil_mean_name)

        with suppress_stdout():

            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, fire_soil_prop, soil_upsum, scratch, cell_res)
            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, fire_soil_prop_area, soil_area_upsum, scratch, cell_res)

        DFTools_ArcGIS.Upslope_Mean(soil_upsum,soil_mean,soil_area_upsum)

    if model == 'M1' or model == 'M2':
        model_soil_prop = 'KFFACT'
    else:
        model_soil_prop = 'THICK'

    model_soil_mean_name = i+'_'+model_soil_prop+'avg'
    model_soil_mean = os.path.join(temp_gdb,model_soil_mean_name)

    up_soil_stats_name = i+'_'+model_soil_prop+'_stats'
    up_soil_stats = os.path.join(temp_gdb,up_soil_stats_name)
    DFTools_ArcGIS.AddNumericStatToTable(model_soil_mean,strm_link_predict,model_strm_feat,up_soil_stats,l_x3_col_header,"MEAN","FLOAT")


# EXTRACT VOLUME VARIABLES ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # VOLUME X1 - SqRtRelief ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('         Calculating Volume X1: '+v_x1_name)

    relief_col_header = v_x1_name
    v_x1_col_header = 'V_X1'
    relief_mean_name = i+'_relief_avg'
    relief_mean = os.path.join(temp_gdb,relief_mean_name)

    up_relief_stats_name = i+'_relief_stats'
    up_relief_stats = os.path.join(temp_gdb,up_relief_stats_name)


    DFTools_ArcGIS.Upslope_Mean(relief,relief_mean,facc)

    sqrt_relief_name = i+'_SqRtRelief'
    sqrt_relief = os.path.join(temp_gdb,sqrt_relief_name)

    out_sqrt_relief = SquareRoot(relief)
    out_sqrt_relief.save(sqrt_relief)

    sqrt_relief_stats_name = i+'_SqRtRelief_Stats'
    sqrt_relief_stats = os.path.join(temp_gdb,sqrt_relief_stats_name)

    DFTools_ArcGIS.AddNumericStatToTable(sqrt_relief,strm_link_predict,model_strm_feat,sqrt_relief_stats,v_x1_col_header,"MEAN","FLOAT")

# VOLUME X2 - lnHMkm2 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('         Calculating Volume X2: '+v_x2_name)

    v_x2_col_header = 'V_X2'

    lnhmkm2_col_header = v_x2_name

    hm_binary_upsum_name = i+'_hm_binary_upsum'
    hm_binary_upsum = os.path.join(temp_gdb,hm_binary_upsum_name)

    hmkm2_name = i+'_hmkm2'
    hmkm2 = os.path.join(temp_gdb,hmkm2_name)

    z_hmkm2_name = 'z'+i+'_hmkm2'
    z_hmkm2 = os.path.join(temp_gdb,z_hmkm2_name)

    if arcpy.Exists(hm_binary_upsum):
        pass
    else:
        with suppress_stdout():
            DFTools_TauDEM.TauDem_UpSum(fdird8_taudem, hm_binary, hm_binary_upsum, scratch, cell_res)

    DFTools_ArcGIS.Upslope_Area_km2(hm_binary_upsum,z_hmkm2,cell_res)

    out_hmkm2 = Con(Raster(z_hmkm2) == 0, 0.000001, z_hmkm2)
    out_hmkm2.save(hmkm2)

    lnhmkm2_name = i+'_lnhmkm2'
    lnhmkm2 = os.path.join(firein_gdb,lnhmkm2_name)

    out_lnhmkm2 = Ln(hmkm2)
    out_lnhmkm2.save(lnhmkm2)

    lnhmkm2_stats_name = i+'_lnhmkm2_stats'
    lnhmkm2_stats = os.path.join(temp_gdb,lnhmkm2_stats_name)

    DFTools_ArcGIS.AddNumericStatToTable(lnhmkm2,strm_link_predict,model_strm_feat,lnhmkm2_stats,v_x2_col_header,"MEAN","FLOAT")

# START LOOP FOR DURATIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pfe_field_list_all = []

    for dur in thresh_duration_list:
        dur_string = str(dur)+'min'
        dur_index = thresh_duration_list.index(dur)

        dur_h = dur / 60.0
        print('     Calculations for Duration = '+dur_string)
        p_b_value = p_b_array[model_row,dur_index]
        p_c1_value = p_c1_array[model_row,dur_index]
        p_c2_value = p_c2_array[model_row,dur_index]
        p_c3_value = p_c3_array[model_row,dur_index]

        print('         Extracting NOAA Atlas 14 Precipitation Frequency Estimates...')

        print('             Checking PFE Data...')

        pfe_extent_feat_name = 'NOAA14_PFEExtent_feat'
        pfe_extent_feat = os.path.join(pfe_gdb,pfe_extent_feat_name)

        fire_pfe_extent_feat_name = i+'_'+pfe_extent_feat_name
        fire_pfe_extent_feat = os.path.join(temp_gdb,fire_pfe_extent_feat_name)

        arcpy.Clip_analysis(pfe_extent_feat,perim_feat,fire_pfe_extent_feat)

        n_pfe_extent = arcpy.GetCount_management(fire_pfe_extent_feat)

        if int(n_pfe_extent[0]) > 0:
            pfe_exists = 'YES'
            print('                 NOAA Atlas 14 Data Exist...')
        else:
            pfe_exists = 'NO'
            print('                 NOAA Atlas 14 Data Do Not Exist, Skipping...')


        if pfe_exists == 'NO':
            pass
        else:

            strm_ri_feat_name = i+'_ri_stream_feat'
            strm_ri_feat = os.path.join(temp_gdb,strm_ri_feat_name)
            pfe_field_list = []


            arcpy.CopyFeatures_management(model_strm_feat,strm_ri_feat)

            for pfe_yr in pfe_list:
                pfe_yr_str = str(pfe_yr)
                print('             Processing PFE = '+pfe_yr_str+' year...')
                in_pfe_name = 'sw'+pfe_yr_str+'y'+str(dur)+'m_i'
                in_pfe = os.path.join(pfe_gdb,in_pfe_name)
                fire_pfe_name = i+'_'+pfe_yr_str+'yr_'+str(dur)+'min_mmh'
                fire_pfe = os.path.join(temp_gdb,fire_pfe_name)

                ri_stats_name = i+'_'+pfe_yr_str+'yr_'+str(dur)+'min_mmh_zstats'
                ri_stats = os.path.join(temp_gdb,ri_stats_name)

                ri_col_header = 'PFE_'+pfe_yr_str+'yr_'+str(dur)+'min_mmh'
                ri_col_headerlist = [ri_col_header]
                pfe_field_list = pfe_field_list + ri_col_headerlist
                pfe_field_list_all = pfe_field_list_all + ri_col_headerlist

                out_pfe = ExtractByMask(in_pfe,extentbox_feat)
                out_pfe.save(fire_pfe)

                DFTools_ArcGIS.AddNumericStatToTable(fire_pfe,strm_link_predict,model_strm_feat,ri_stats,ri_col_header,"MEAN","FLOAT")


        print('         Estimating Rainfall Thresholds...')

        for thresh_p in RainAtP_list:
            p_string = str('%.2f' % thresh_p)
            p_100 = thresh_p * 100.0
            p_100_string = str(int(p_100))
            rainacc_at_p_string = 'RainAccAtP'+p_100_string+'_mm'
            rainint_at_p_string = 'RainIntAtP'+p_100_string+'_mmh'
            ri_at_p_string = 'RIAtP_yrs'
            v_x3_at_p_string = 'V_X3AtP'+p_100_string+'_mmh'
            lnv_at_p_string = 'LnVAtP'+p_100_string+'_mmh'
            vol_at_p_string = 'VolumeAtP'+p_100_string+'_mmh'
            vcl_at_p_string = 'VolClAtP'+p_100_string+'_mmh'
            vol_min_at_p_string = 'VolMinAtP'+p_100_string+'_mmh'
            vol_max_at_p_string = 'VolMaxAtP'+p_100_string+'_mmh'

            logit_p = math.log(thresh_p / (1 - thresh_p))

            print('             Calculating Rainfall Estimates for P = '+ p_string+'...')

            strm_thresh_feat_name = i+'_Segment_RainfallEstimates_'+dur_string+'_RainAtP_'+p_100_string
            strm_thresh_feat = os.path.join(threshold_utm_gdb,strm_thresh_feat_name)

            basin_thresh_feat_name = i+'_Basin_RainfallEstimates_'+dur_string+'_RainAtP_'+p_100_string
            basin_thresh_feat = os.path.join(threshold_utm_gdb,basin_thresh_feat_name)

            arcpy.CopyFeatures_management(model_strm_feat,strm_thresh_feat)

            rainacc_at_p_field = rainacc_at_p_string
            rainacc_at_p_legend_field = rainacc_at_p_string+'_Legend'
            rainint_at_p_field = rainint_at_p_string
            rainint_at_p_legend_field = rainint_at_p_string+'_Legend'
            ri_at_p_field = ri_at_p_string
            v_x3_at_p_field = v_x3_at_p_string
            lnv_at_p_field = lnv_at_p_string
            vol_at_p_field = vol_at_p_string
            vmin_at_p_field = vol_min_at_p_string
            vmax_at_p_field = vol_max_at_p_string
            vcl_at_p_field = vcl_at_p_string
            vol_at_p_legend_field = vol_at_p_string+'_Legend'

            arcpy.AddField_management(strm_thresh_feat, rainacc_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_feat, rainint_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_feat, rainacc_at_p_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_feat, rainint_at_p_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_feat, ri_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

            rain_at_p_field_list = [l_x1_col_header,l_x2_col_header,l_x3_col_header,rainacc_at_p_field,rainint_at_p_field]
            with arcpy.da.UpdateCursor(strm_thresh_feat,rain_at_p_field_list) as cursor:
                for row in cursor:
                    if None in row[0:3]:
                        pass
                    else:
                        row_acc = (logit_p - p_b_value) / ((p_c1_value * row[0]) + (p_c2_value * row[1]) + (p_c3_value * row[2]))
                        row[3] = row_acc
                        row[4] = row_acc / dur_h
                    cursor.updateRow(row)

            if pfe_exists == 'NO':
                ri_field_list = [ri_at_p_field]
                with arcpy.da.UpdateCursor(strm_thresh_feat,ri_field_list) as cursor:
                    for row in cursor:
                        row[0] = -9999
                        cursor.updateRow(row)
            else:
                ri_field_list = [ri_at_p_field] + pfe_field_list + [rainint_at_p_field]

                def calc_ri(i,ri_years,ri_rates):  #i = rainfall intensity for calc (in_rain_rate_list[dur_min]), x = list of ri years (ri_years_list),y = rainfall rates for the different RI (ri_rates[dur_min])
                    x = np.log(ri_years)
                    y = ri_rates
                    f = interpolate.interp1d(y,x,kind='linear',fill_value='extrapolate')  #linear fit of x = log(years), y = rainfall rates for each RI, values less than 1 or greater than 100 are exptrapolated.
                    out_ri_interp = np.exp(f(i))

                    return out_ri_interp

                with arcpy.da.UpdateCursor(strm_thresh_feat,ri_field_list) as cursor:
                    for row in cursor:
                        if None in row[1:8]:
                            pass
                        else:
                            ri_rates_dur = row[1:8]
                            in_intensity = row[8]

                            out_ri = calc_ri(in_intensity,pfe_list,ri_rates_dur)
                            out_ri_rounded = np.round(out_ri,1)

                            row[0] = out_ri_rounded
                        cursor.updateRow(row)

                rain_field_list = [rainacc_at_p_field,rainint_at_p_field,rainacc_at_p_legend_field,rainint_at_p_legend_field]
                DFTools_ArcGIS.addThresholdLegendFields(strm_thresh_feat,dur,rain_field_list)

                arcpy.DeleteField_management(strm_thresh_feat,pfe_field_list)

            if dur == 15:

                arcpy.AddField_management(strm_thresh_feat, v_x3_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(strm_thresh_feat, lnv_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(strm_thresh_feat, vol_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(strm_thresh_feat, vmin_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(strm_thresh_feat, vmax_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(strm_thresh_feat, vcl_at_p_field, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.AddField_management(strm_thresh_feat, vol_at_p_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")



                v_x3_field_list = [rainint_at_p_field,v_x3_at_p_field]

                with arcpy.da.UpdateCursor(strm_thresh_feat,v_x3_field_list) as cursor:
                    for row in cursor:
                        if row[0] == None:
                            pass
                        elif row[0] > 0:
                            row[1] = np.sqrt(row[0])
                        else:
                            pass
                        cursor.updateRow(row)

                ln_v_field_list = [v_x1_col_header,v_x2_col_header,v_x3_at_p_field,lnv_at_p_field]

                with arcpy.da.UpdateCursor(strm_thresh_feat,ln_v_field_list) as cursor:
                    for row in cursor:
                        if None in row[0:3]:
                            pass
                        elif row[0] > 0:
                            row[3] = v_b + (v_c1 * row[0]) + (v_c2 * row[1]) + (v_c3 * row[2])
                        else:
                            pass
                        cursor.updateRow(row)

                v_at_p_field_list = [lnv_at_p_field,vol_at_p_field]
                with arcpy.da.UpdateCursor(strm_thresh_feat, v_at_p_field_list) as cursor:
                    for row in cursor:
                        if row[0] == None:
                            pass
                        else:
                            row[1] = np.e**(row[0])
                        cursor.updateRow(row)

                v_min_max_field_list = [lnv_at_p_field,vmin_at_p_field,vmax_at_p_field]
                with arcpy.da.UpdateCursor(strm_thresh_feat, v_min_max_field_list) as cursor:
                    for row in cursor:
                        if row[0] == None:
                            pass
                        else:
                            row[1] = np.e**(row[0] - (2 * v_se))
                            row[2] = np.e**(row[0] + (2 * v_se))
                        cursor.updateRow(row)


                v_fields = [vol_at_p_field,vcl_at_p_field,vol_at_p_legend_field]

                DFTools_ArcGIS.addVolumeLegendFields(strm_thresh_feat,v_fields)

            strm_thresh_feat_wgs = os.path.join(threshold_wgs_gdb,strm_thresh_feat_name)
            basin_thresh_feat_wgs = os.path.join(threshold_wgs_gdb,basin_thresh_feat_name)

            if pfe_exists == 'YES':
                arcpy.DeleteField_management(strm_thresh_feat,pfe_field_list_all)
            #arcpy.DeleteField_management(model_strm_feat,pfe_field_list_all)
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

            arcpy.Project_management(strm_thresh_feat,strm_thresh_feat_wgs,wgs_spatial_ref)

            arcpy.CopyFeatures_management(basin_feat, basin_thresh_feat)

            basin_thresh_feat_wgs84 = os.path.join(threshold_wgs_gdb,basin_thresh_feat_name)

            arcpy.JoinField_management(basin_thresh_feat, "BASIN_ID", basinpt_feat, "BASIN_ID")
            arcpy.JoinField_management(basin_thresh_feat, "SEGMENT_ID", strm_thresh_feat, "SEGMENT_ID")
            delete_fields = ['Join_Count','TARGET_FID','from_node','to_node','StrmOrder_1','slppct','gridcode','BUFFER_ID','FID_'+i+'_modelstrm_feat','from_node_1','to_node_1','BASIN_ID_12','BASIN_ID_1','Segment_ID_1','V_X1','V_X2','Fire_Name_1','Start_Date_1','State_Name_1','UpArea_km2_1','UpBurnArea_km2_1','Fire_Name_12','Start_Date_12','State_Name_12']
            arcpy.DeleteField_management(basin_thresh_feat,delete_fields)
            if pfe_exists == 'YES':
                arcpy.DeleteField_management(basin_thresh_feat,pfe_field_list_all) #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            arcpy.Project_management(basin_thresh_feat,basin_thresh_feat_wgs84,wgs_spatial_ref)

        print('             Calculating Rainfall Estimates for All Likelihood Values...')

        strm_thresh_all_feat_name = i+'_Segment_RainfallEstimates_'+dur_string+'_RainAtAllP'
        strm_thresh_all_feat = os.path.join(threshold_utm_gdb,strm_thresh_all_feat_name)

        basin_thresh_all_feat_name = i+'_Basin_RainfallEstimates_'+dur_string+'_RainAtAllP'
        basin_thresh_all_feat = os.path.join(threshold_utm_gdb,basin_thresh_all_feat_name)

        arcpy.CopyFeatures_management(model_strm_feat,strm_thresh_all_feat)

        delete_fields = ['V_X1','V_X2']

        arcpy.DeleteField_management(strm_thresh_all_feat,delete_fields)

        for thresh_p in RainAtP_list:

            p_string = str('%.2f' % thresh_p)
            p_100 = thresh_p * 100.0
            p_100_string = str(int(p_100))
            rainacc_at_p_string = 'RainAccAtP'+p_100_string+'_mm'
            rainint_at_p_string = 'RainIntAtP'+p_100_string+'_mmh'

            rainacc_at_p_field = rainacc_at_p_string
            rainacc_at_p_legend_field = rainacc_at_p_string+'_Legend'
            rainint_at_p_field = rainint_at_p_string
            rainint_at_p_legend_field = rainint_at_p_string+'_Legend'

            logit_p = math.log(thresh_p / (1 - thresh_p))

            arcpy.AddField_management(strm_thresh_all_feat, rainacc_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_all_feat, rainint_at_p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_all_feat, rainacc_at_p_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_thresh_all_feat, rainint_at_p_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")

            rain_at_p_field_list = [l_x1_col_header,l_x2_col_header,l_x3_col_header,rainacc_at_p_field,rainint_at_p_field]
            with arcpy.da.UpdateCursor(strm_thresh_all_feat,rain_at_p_field_list) as cursor:
                for row in cursor:
                    if None in row[0:3]:
                        pass
                    else:
                        row_acc = (logit_p - p_b_value) / ((p_c1_value * row[0]) + (p_c2_value * row[1]) + (p_c3_value * row[2]))
                        row[3] = row_acc
                        row[4] = row_acc / dur_h
                    cursor.updateRow(row)

            rain_fields = [rainacc_at_p_field,rainint_at_p_field,rainacc_at_p_legend_field,rainint_at_p_legend_field]

            DFTools_ArcGIS.addThresholdLegendFields(strm_thresh_all_feat,dur,rain_fields)

            strm_thresh_all_feat_wgs = os.path.join(threshold_wgs_gdb,strm_thresh_all_feat_name)
            basin_thresh_all_feat_wgs = os.path.join(threshold_wgs_gdb,basin_thresh_all_feat_name)

            wgs84_ref_feat_name = 'UTMZone_'+zone_str+'_Perim_Feat_WGS84'
            wgs84_ref_feat = os.path.join(projection_gdb,wgs84_ref_feat_name)

            ref_wgs= arcpy.Describe(wgs84_ref_feat)
            wgs_spatial_ref = ref_wgs.SpatialReference
            arcpy.Project_management(strm_thresh_all_feat,strm_thresh_all_feat_wgs,wgs_spatial_ref)

            arcpy.CopyFeatures_management(basin_feat, basin_thresh_all_feat)

            basin_thresh_all_feat_wgs84 = os.path.join(threshold_wgs_gdb,basin_thresh_all_feat_name)

            arcpy.JoinField_management(basin_thresh_all_feat, "BASIN_ID", basinpt_feat, "BASIN_ID")
            arcpy.JoinField_management(basin_thresh_all_feat, "SEGMENT_ID", strm_thresh_all_feat, "SEGMENT_ID")

            delete_fields = ['Join_Count','TARGET_FID','from_node','to_node','StrmOrd','slppct','gridcode','BUFFER_ID','FID_'+i+'_modelstrm_feat','from_node_1','to_node_1','BASIN_ID_12','BASIN_ID_1','Segment_ID_1','Fire_Name_1','Start_Date_1','State_Name_1','UpArea_km2_1','UpBurnArea_km2_1','Fire_Name_12','Start_Date_12','State_Name_12']
            arcpy.DeleteField_management(basin_thresh_all_feat,delete_fields)
            arcpy.Project_management(basin_thresh_all_feat,basin_thresh_all_feat_wgs84,wgs_spatial_ref)


    print('     Writing Threshold Guidance File...')
    basin_threshold_text_name = i+'_ThresholdGuidance_Basin.txt'
    basin_threshold_text = os.path.join(workingdir,basin_threshold_text_name)

    segment_threshold_text_name = i+'_ThresholdGuidance_Segment.txt'
    segment_threshold_text = os.path.join(workingdir,segment_threshold_text_name)

    target = open(basin_threshold_text,'wt')
    target.write('FireID,FireName,FireState,Duration_min,Threshold_P,Acc_mm,Int_mmh-1,Acc_In,Int_Inh-1,RI_yr'+'\n')
    target.close()

    target = open(segment_threshold_text,'wt')
    target.write('FireID,FireName,FireState,Duration_min,Threshold_P,Acc_mm,Int_mmh-1,Acc_In,Int_Inh-1,RI_yr'+'\n')
    target.close()

    basin_threshold_y1_email_list_SI = []
    basin_threshold_y1_email_list_ENG = []
    basin_threshold_y1_email_list_RI = []
    segment_threshold_y1_email_list_SI = []
    segment_threshold_y1_email_list_ENG = []
    segment_threshold_y1_email_list_RI = []

    basin_threshold_y2_email_list_SI = []
    basin_threshold_y2_email_list_ENG = []
    basin_threshold_y2_email_list_RI = []
    segment_threshold_y2_email_list_SI = []
    segment_threshold_y2_email_list_ENG = []
    segment_threshold_y2_email_list_RI = []


    def round_nearest(x, a):
        return round(round(x / a) * a, -int(math.floor(math.log10(a))))

    for dur in thresh_duration_list:
        dur_string = str(dur)

        for p_value in RainAtP_list:
            p_string = str(int(p_value * 100))

            basin_threshold_feat_name = i+'_Basin_RainfallEstimates_'+str(dur)+'min_RainAtP_'+p_string
            basin_threshold_feat = os.path.join(threshold_utm_gdb,basin_threshold_feat_name)

            segment_threshold_feat_name = i+'_Segment_RainfallEstimates_'+str(dur)+'min_RainAtP_'+p_string
            segment_threshold_feat = os.path.join(threshold_utm_gdb,segment_threshold_feat_name)

            acc_field_name = 'RainAccAtP'+p_string+'_mm'
            int_field_name = 'RainIntAtP'+p_string+'_mmh'
            ri_field_name = 'RIAtP_yrs'

            # BASINS

            basin_arr = arcpy.da.TableToNumPyArray(basin_threshold_feat,[acc_field_name,int_field_name,ri_field_name])

            basin_accum_array_mm = basin_arr[acc_field_name]
            basin_intensity_array_mm = basin_arr[int_field_name]
            basin_ri_array_yr = basin_arr[ri_field_name]
            basin_accum_median_mm = np.nanmedian(basin_accum_array_mm)
            basin_accum_mm = np.round(basin_accum_median_mm)
            basin_accum_median_mm_string = str("%i" % basin_accum_mm)
            basin_intensity_median_mm = np.nanmedian(basin_intensity_array_mm)
            basin_intensity_median_mm_string = str("%.i" % basin_intensity_median_mm)
            basin_ri_median_yr = np.nanmedian(basin_ri_array_yr)

            basin_accum_median_in = basin_accum_median_mm / 25.4
            basin_accum_in = round_nearest(basin_accum_median_in,0.05)
            basin_accum_median_in_string = str("%.2f" % basin_accum_in)
            basin_intensity_median_in = basin_intensity_median_mm / 25.4
            basin_intensity_median_in_string = str("%.1f" % basin_intensity_median_in)
            basin_ri_median_yr_str = str("%.1f" % basin_ri_median_yr)
            basin_data_string = i+','+fire_name_full_text+','+state_abbrev+','+dur_string+','+p_string+','+basin_accum_median_mm_string+','+basin_intensity_median_mm_string+','+basin_accum_median_in_string+','+basin_intensity_median_in_string+','+basin_ri_median_yr_str

            target = open(basin_threshold_text,'a')
            target.write(basin_data_string+'\n')
            target.close()

            # SEGMENTS

            segment_arr = arcpy.da.TableToNumPyArray(segment_threshold_feat,[acc_field_name,int_field_name,ri_field_name])

            segment_accum_array_mm = segment_arr[acc_field_name]
            segment_intensity_array_mm = segment_arr[int_field_name]
            segment_ri_array_yr = segment_arr[ri_field_name]
            segment_accum_median_mm = np.nanmedian(segment_accum_array_mm)
            segment_accum_mm = round_nearest(segment_accum_median_mm,0.05)
            segment_accum_median_mm_string = str("%i" % segment_accum_mm)
            segment_intensity_median_mm = np.nanmedian(segment_intensity_array_mm)
            segment_intensity_median_mm_string = str("%i" % segment_intensity_median_mm)
            segment_ri_median_yr = np.nanmedian(segment_ri_array_yr)

            segment_accum_median_in = segment_accum_median_mm / 25.4
            segment_accum_in = round_nearest(segment_accum_median_in,0.05)
            segment_accum_median_in_string = str("%.2f" % segment_accum_in)
            segment_intensity_median_in = segment_intensity_median_mm / 25.4
            segment_intensity_median_in_string = str("%.1f" % segment_intensity_median_in)
            segment_ri_median_yr_str = str("%.1f" % segment_ri_median_yr)
            segment_data_string = i+','+fire_name_full_text+','+state_abbrev+','+dur_string+','+p_string+','+segment_accum_median_mm_string+','+segment_intensity_median_mm_string+','+segment_accum_median_in_string+','+segment_intensity_median_in_string+','+segment_ri_median_yr_str


            target = open(segment_threshold_text,'a')
            target.write(segment_data_string+'\n')
            target.close()



            if p_value == 0.5:

                basin_threshold_y1_email_list_SI.append(basin_intensity_median_mm_string)
                basin_threshold_y1_email_list_ENG.append(basin_accum_median_in_string)
                basin_threshold_y1_email_list_RI.append(basin_ri_median_yr_str)
                segment_threshold_y1_email_list_SI.append(segment_intensity_median_mm_string)
                segment_threshold_y1_email_list_ENG.append(segment_accum_median_in_string)
                segment_threshold_y1_email_list_RI.append(segment_ri_median_yr_str)

            if p_value == 0.75:

                basin_threshold_y2_email_list_SI.append(basin_intensity_median_mm_string)
                basin_threshold_y2_email_list_ENG.append(basin_accum_median_in_string)
                basin_threshold_y2_email_list_RI.append(basin_ri_median_yr_str)
                segment_threshold_y2_email_list_SI.append(segment_intensity_median_mm_string)
                segment_threshold_y2_email_list_ENG.append(segment_accum_median_in_string)
                segment_threshold_y2_email_list_RI.append(segment_ri_median_yr_str)

# START LOOP FOR ACCUMULATIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    for dur in lv_duration_list:
        dur_string = str(dur)+'min'
        dur_index = lv_duration_list.index(dur)

        for acc in accum_list:
            acc_string = str(acc)+'mm'
            acc_index = accum_list.index(acc)

            dur_h = dur / 60.0
            intensity = acc / dur_h
            intensity_string = str(int(intensity))+'mmh'

            print('         Calculating Estimates for Intensity = '+intensity_string)

            strm_pred_feat_name = i+'_Segment_DFPredictions_'+dur_string+'_'+intensity_string
            strm_pred_feat = os.path.join(modelcalcs_gdb,strm_pred_feat_name)

            basin_pred_feat_name = i+'_Basin_DFPredictions_'+dur_string+'_'+intensity_string
            basin_pred_feat = os.path.join(modelcalcs_gdb,basin_pred_feat_name)

            arcpy.CopyFeatures_management(model_strm_feat,strm_pred_feat)

# LIKELIHOOD CALCS

            print('             Calculating Likelihood Estimates...')

            p_rain = acc

            p_r_col_header = 'R'
            arcpy.AddField_management(strm_pred_feat, p_r_col_header, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            v_rain = math.sqrt(intensity)
            v_x3_col_header = 'V_X3'
            arcpy.AddField_management(strm_pred_feat, v_x3_col_header, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

            model_rain_field_list = [p_r_col_header,v_x3_col_header]
            with arcpy.da.UpdateCursor(strm_pred_feat, model_rain_field_list) as cursor:
                for row in cursor:
                    row[0] = p_rain
                    row[1] = v_rain
                    cursor.updateRow(row)


            p_b_value = p_b_array[model_row,dur_index]
            p_c1_value = p_c1_array[model_row,dur_index]
            p_c2_value = p_c2_array[model_row,dur_index]
            p_c3_value = p_c3_array[model_row,dur_index]

            x_field = "X"
            expx_field = "ExpX"
            p_field = "P"
            pcl_field = "PCl"
            pcl_legend_field = "PCl_Legend"

            arcpy.AddField_management(strm_pred_feat, x_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, expx_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, p_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, pcl_field, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, pcl_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")


            p_calc_field_list = [l_x1_col_header,l_x2_col_header,l_x3_col_header,p_r_col_header,x_field,expx_field,p_field]
            with arcpy.da.UpdateCursor(strm_pred_feat,p_calc_field_list) as cursor:
                for row in cursor:
                    if None in row[0:3]:
                        pass
                    else:
                        row_x = p_b_value + (p_c1_value * row[0] * row[3]) + (p_c2_value * row[1] * row[3]) + (p_c3_value * row[2] * row[3])
                        row[4] = row_x
                        row[5] = np.e**row_x
                        row[6] = np.e**row_x / (1 + np.e**row_x)
                    cursor.updateRow(row)

            p_fields = [p_field,pcl_field,pcl_legend_field]
            DFTools_ArcGIS.addPLegendFields(strm_pred_feat,p_fields)
            print('             Calculating Volume Estimates...')

            lnv_field = "LnV"
            v_field = "Volume"
            vmin_field = "VolMin"
            vmax_field = "VolMax"
            vcl_field = "VolCl"
            vcl_legend_field = "VolCl_Legend"

            arcpy.AddField_management(strm_pred_feat, lnv_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, v_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, vmin_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, vmax_field, "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, vcl_field, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, vcl_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")

            v_calc_field_list = [v_x1_col_header,v_x2_col_header,v_x3_col_header,lnv_field,v_field,vmin_field,vmax_field]
            with arcpy.da.UpdateCursor(strm_pred_feat,v_calc_field_list) as cursor:
                for row in cursor:
                    if None in row[0:3]:
                        pass
                    else:
                        row_lnv = v_b + (v_c1 * row[0]) + (v_c2 * row[1]) + (v_c3 * row[2])
                        row[3] = row_lnv
                        row[4] = np.e**row_lnv
                        row[5] = np.e**(row_lnv - (2 * v_se))
                        row[6] = np.e**(row_lnv + (2 * v_se))
                    cursor.updateRow(row)

            v_fields = [v_field,vcl_field,vcl_legend_field]

            DFTools_ArcGIS.addVolumeLegendFields(strm_pred_feat,v_fields)

            print('             Calculating Combined Hazard Estimates...')

            combhaz_field = "CombHaz"
            combhazcl_field = "CombHazCl"
            combhazcl_legend_field = "CombHazCl_Legend"

            arcpy.AddField_management(strm_pred_feat, combhaz_field, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, combhazcl_field, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(strm_pred_feat, combhazcl_legend_field, "TEXT", "", "", "25", "", "NULLABLE", "NON_REQUIRED", "")

            combcl_calc_field_list = [pcl_field,vcl_field,combhaz_field]
            with arcpy.da.UpdateCursor(strm_pred_feat,combcl_calc_field_list) as cursor:
                for row in cursor:
                    if row[0] == None:
                        pass
                    else:
                        row[2] = row[0] + row[1]
                    cursor.updateRow(row)


            c_fields = [combhaz_field,combhazcl_field,combhazcl_legend_field]

            DFTools_ArcGIS.addCombinedLegendFields(strm_pred_feat,c_fields)

##            print('             Calculating Threshold Classifications...')
##
##            for thresh_p in RainAtP_list:
##                p_string = str('%.2f' % thresh_p)
##                p_100 = thresh_p * 100.0
##                p_100_string = str(int(p_100))
##                thresh_p_cl_field = 'ThreshCl_P'+p_100_string
##
##                arcpy.AddField_management(strm_pred_feat, thresh_p_cl_field, "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
##
##                with arcpy.da.UpdateCursor(strm_pred_feat, [p_field,thresh_p_cl_field]) as cursor:
##                    for row in cursor:
##                        if row[0] is None:
##                            pass
##                        elif row[0] > thresh_p:
##                            #print('1')
##                            row[1] = 1
##                        else:
##                            #print('0')
##                            row[1] = 0
##                        cursor.updateRow(row)

            strm_pred_feat_wgs84 = os.path.join(modelcalcs_web_gdb,strm_pred_feat_name)
            wgs84_ref_feat_name = 'UTMZone_'+zone_str+'_Perim_Feat_WGS84'
            wgs84_ref_feat = os.path.join(projection_gdb,wgs84_ref_feat_name)

            ref_wgs= arcpy.Describe(wgs84_ref_feat)
            wgs_spatial_ref = ref_wgs.SpatialReference
            arcpy.Project_management(strm_pred_feat,strm_pred_feat_wgs84,wgs_spatial_ref)

            print("             Calculating Basin-Scale Estimates of Likelihood, Volume and Combined Hazard...")

            arcpy.CopyFeatures_management(basin_feat, basin_pred_feat)

            basin_pred_feat_wgs84 = os.path.join(modelcalcs_web_gdb,basin_pred_feat_name)

            arcpy.JoinField_management(basin_pred_feat, "BASIN_ID", basinpt_feat, "BASIN_ID")
            arcpy.JoinField_management(basin_pred_feat, "SEGMENT_ID", strm_pred_feat, "SEGMENT_ID")
            delete_fields = ['Join_Count','TARGET_FID','from_node','to_node','StrmOrd','StrmOrder_1','slppct','gridcode','BUFFER_ID','FID_'+i+'_modelstrm_feat','from_node_1','to_node_1','BASIN_ID_12','BASIN_ID_1','Segment_ID_1','Fire_Name_1','Start_Date_1','State_Name_1','UpArea_km2_1','UpBurnArea_km2_1','Fire_Name_12','Start_Date_12','State_Name_12']
            arcpy.DeleteField_management(basin_pred_feat,delete_fields)

            arcpy.Project_management(basin_pred_feat,basin_pred_feat_wgs84,wgs_spatial_ref)

    if join_estimates == 'YES':
        print('     Joining Estimates into a Single Feature Class...')
        for duration in lv_duration_list:
            duration_h = duration / 60.0
            dur_string = str(duration)+'min'

            print('         Processing Duration = '+str(duration)+' Minutes...')

            field_replace_list = ['R','V_X3','X','ExpX','P','PCl','PCl_Legend','LnV','Volume','VolMin','VolMax','VolCl','VolCl_Legend','CombHaz','CombHazCl','CombHazCl_Legend']
            for thresh_p in RainAtP_list:
                p_string = str('%.2f' % thresh_p)
                p_100 = thresh_p * 100.0
                p_100_string = str(int(p_100))
                thresh_p100_string = 'ThreshCl_P'+p_100_string
                field_replace_list.append(thresh_p100_string)

            for accum in accum_list:

                accum_index = accum_list.index(accum)

                intensity = accum / duration_h
                intensity_string = str(int(intensity))+'mmh'

                print('             Processing Intensity = '+str(int(intensity))+' mm/h...')

                if duration == 15:
                    for scale in mapping_scale_list:

                        join_field_list = [scale+'_ID']
                        for old_field in field_replace_list:
                            new_field = old_field+'_'+dur_string+'_'+intensity_string
                            join_field_list.append(new_field)

                        in_feat_name = i+'_'+scale+'_DFPredictions_'+dur_string+'_'+intensity_string
                        in_feat = os.path.join(modelcalcs_gdb,in_feat_name)
                        temp_table_name = scale+'_'+dur_string+'_'+intensity_string+'_TempTable'
                        temp_table = os.path.join(temp_gdb,temp_table_name)
                        all_feat_name = i+'_'+scale+'_DFPredictions_'+dur_string+'_AllIntensities'
                        all_feat = os.path.join(modelcalcs_gdb,all_feat_name)
                        if scale == 'Segment':
                            key_field = scale+'_ID'
                        else:
                            keyfield = str.upper(scale)+'_ID'
                        if accum_index == 0:
                            arcpy.CopyFeatures_management(in_feat,all_feat)
                            field_list = arcpy.ListFields(all_feat)
                            for field in field_list:
                                field_name = str(field.name)
                                if field_name in field_replace_list:
                                    field_name_new = field_name+'_'+dur_string+'_'+intensity_string
                                    arcpy.AlterField_management(all_feat,field_name,field_name_new,field_name_new)
                        else:
                            arcpy.TableToTable_conversion(in_feat,temp_gdb,temp_table_name)
                            temp_field_list = arcpy.ListFields(temp_table)
                            for field in temp_field_list:
                                field_name = str(field.name)
                                if field_name in field_replace_list:
                                    field_name_new = field_name+'_'+dur_string+'_'+intensity_string
                                    arcpy.AlterField_management(temp_table,field_name,field_name_new,field_name_new)
                                else:
                                    #if (field_name == 'OBJECTID') or (field_name == 'Shape_Length') or (field_name == 'Shape_Area') or (field_name == 'Segment_ID') or (field_name == 'BASIN_ID'):
                                    if (field_name == 'OBJECTID') or (field_name == key_field):
                                        pass
                                    else:
                                        arcpy.DeleteField_management(temp_table,field_name)
                            arcpy.JoinField_management(all_feat,key_field,temp_table,key_field)

                        all_feat_fields = arcpy.ListFields(all_feat)
                        for field in all_feat_fields:
                            field_name = field.name
                            if key_field+'_' in field_name:
                                arcpy.DeleteField_management(all_feat,field_name)


    # BUILD RESULTS MXD~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('     Building APRX for Watch Stream Editing...')

    blank_aprx_name = 'StreamWork_Template.aprx'
    blank_aprx = os.path.join(streamwork_symbology_dir,blank_aprx_name)

    watch_aprx_name = i+'_watchstream.aprx'
    watch_aprx = os.path.join(workingdir,watch_aprx_name)

    shutil.copyfile(blank_aprx,watch_aprx)

    watchAPRX = arcpy.mp.ArcGISProject(watch_aprx)

    watchmap = watchAPRX.listMaps()[0]

    streamwork_perim_symbology_name = 'StreamWork_Perim.lyr'
    streamwork_perim_symbology = os.path.join(streamwork_symbology_dir,streamwork_perim_symbology_name)

    streamwork_basin_symbology_name = 'StreamWork_Basins.lyr'
    streamwork_basin_symbology = os.path.join(streamwork_symbology_dir,streamwork_basin_symbology_name)

    streamwork_basinpt_symbology_name = 'StreamWork_PourPt.lyr'
    streamwork_basinpt_symbology = os.path.join(streamwork_symbology_dir,streamwork_basinpt_symbology_name)

    streamwork_watchstream_symbology_name = 'StreamWork_WatchStream.lyr'
    streamwork_watchstream_symbology = os.path.join(streamwork_symbology_dir,streamwork_watchstream_symbology_name)

    streamwork_db_symbology_name = 'StreamWork_DebrisBasin.lyr'
    streamwork_db_symbology = os.path.join(streamwork_symbology_dir,streamwork_db_symbology_name)

    streamwork_shd_symbology_name = 'StreamWork_HillShade.lyr'
    streamwork_shd_symbology = os.path.join(streamwork_symbology_dir,streamwork_shd_symbology_name)

    # Step 1 Stream Feature Class

    DFTools_ArcGIS.AddSymbolizedRasterToMap(shd,streamwork_shd_symbology,watchmap,watchAPRX,scratch,0)
    DFTools_ArcGIS.AddSymbolizedFeatureToMap(basin_feat,streamwork_basin_symbology,watchmap,watchAPRX,scratch,50)

    if arcpy.Exists(db_feat):
        DFTools_ArcGIS.AddSymbolizedFeatureToMap(db_feat,streamwork_db_symbology,watchmap,watchAPRX,scratch,0)
    else:
        pass

    DFTools_ArcGIS.AddSymbolizedFeatureToMap(basinpt_feat,streamwork_basinpt_symbology,watchmap,watchAPRX,scratch,0)
    DFTools_ArcGIS.AddSymbolizedFeatureToMap(perim_feat,streamwork_perim_symbology,watchmap,watchAPRX,scratch,0)
    DFTools_ArcGIS.AddSymbolizedFeatureToMap(watchstream_feat,streamwork_watchstream_symbology,watchmap,watchAPRX,scratch,0)

    watchAPRX.save()

    print('     Building APRX for Results Verification...')

    results_aprx_name = i+'_results.aprx'
    results_aprx = os.path.join(workingdir,results_aprx_name)

    symbology_dir_name = 'AssessmentResults_Symbology'
    results_symbology_dir_name = 'Results_Symbology'
    symbology_dir = os.path.join(server_dir,symbology_dir_name)
    results_symbology_dir = os.path.join(symbology_dir,results_symbology_dir_name)

    results_perim_symbology_name = 'Perimeter.lyr'
    results_perim_symbology = os.path.join(results_symbology_dir,results_perim_symbology_name)

    results_db_symbology_name = 'DebrisBasins.lyr'
    results_db_symbology = os.path.join(results_symbology_dir,results_db_symbology_name)

    results_shd_symbology_name = 'HillShade.lyr'
    results_shd_symbology = os.path.join(results_symbology_dir,results_shd_symbology_name)

    blank_aprx_name = 'StreamWork_Template.aprx'
    blank_aprx = os.path.join(streamwork_symbology_dir,blank_aprx_name)

    shutil.copyfile(blank_aprx,results_aprx)

    resultsAPRX = arcpy.mp.ArcGISProject(results_aprx)

    resultsmap = resultsAPRX.listMaps()[0]

    DFTools_ArcGIS.AddSymbolizedRasterToMap(shd,results_shd_symbology,resultsmap,resultsAPRX,scratch,0)

    if arcpy.Exists(db_feat):
        DFTools_ArcGIS.AddSymbolizedFeatureToMap(db_feat,results_db_symbology,resultsmap,resultsAPRX,scratch,0)
    else:
        pass

    DFTools_ArcGIS.AddSymbolizedFeatureToMap(basinpt_feat,streamwork_basinpt_symbology,resultsmap,resultsAPRX,scratch,0)
    DFTools_ArcGIS.AddSymbolizedFeatureToMap(perim_feat,results_perim_symbology,resultsmap,resultsAPRX,scratch,0)

    resultsAPRX.save()

    for mapping_scale in mapping_scale_list:

        for dur in duration_map_list:
            dur_string = str(dur)+'min'
            dur_index = duration_map_list.index(dur)

            for acc in accum_map_list:
                acc_string = str(acc)+'mm'
                acc_index = accum_map_list.index(acc)

                dur_h = dur / 60.0
                intensity = acc / dur_h
                intensity_string = str(int(intensity))+'mmh'

                p_feat_name = i+'_'+mapping_scale+'_DFPredictions_'+dur_string+'_'+intensity_string
                p_feat = os.path.join(modelcalcs_gdb,p_feat_name)

                v_feat_name = i+'_'+mapping_scale+'_DFPredictions_'+dur_string+'_'+intensity_string
                v_feat = os.path.join(modelcalcs_gdb,p_feat_name)

                v_symbology_name = mapping_scale+'_VolCl.lyr'
                v_symbology = os.path.join(results_symbology_dir,v_symbology_name)

                DFTools_ArcGIS.AddSymbolizedFeatureToMap(v_feat,v_symbology,resultsmap,resultsAPRX,scratch,0)

                p_symbology_name = mapping_scale+'_ProbCl.lyr'
                p_symbology = os.path.join(results_symbology_dir,p_symbology_name)
                DFTools_ArcGIS.AddSymbolizedFeatureToMap(p_feat,p_symbology,resultsmap,resultsAPRX,scratch,0)
                resultsAPRX.save()

                    # Threshold
        for dur in thresh_duration_map_list:
            dur_string = str(dur)+'min'
            dur_index = thresh_duration_map_list.index(dur)

            dur_h = dur / 60.0

            for thresh_p in RainAtP_map_list:
                p_string = str('%.2f' % thresh_p)
                p_100 = thresh_p * 100.0
                p_100_string = str(int(p_100))

                source_field = 'RainIntAtP50_mmh_Legend'
                target_field = 'RainIntAtP'+p_100_string+'_mmh_Legend'
                symbologyFields = [['VALUE_FIELD','RainIntAtP50_mmh_Legend','RainIntAtP'+p_100_string+'_mmh_Legend']]


                thresh_feat_name = i+'_'+mapping_scale+'_RainfallEstimates_'+dur_string+'_RainAtP_'+p_100_string
                thresh_feat = os.path.join(threshold_utm_gdb,thresh_feat_name)

                thresh_symbology_name = mapping_scale+'_ThresholdCl_'+dur_string+'.lyr'
                thresh_symbology = os.path.join(results_symbology_dir,thresh_symbology_name)

                DFTools_ArcGIS.AddSymbolizedFeatureToMap(thresh_feat,thresh_symbology,resultsmap,resultsAPRX,scratch,0)
                resultsAPRX.save()
            resultsAPRX.save()
        resultsAPRX.save()



    # CAlCULATING HSA, WFO and CONTACT INFO~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    nws_server_cwa_feat_name = 'NWS_CWA_feat'
    nws_server_cwa_feat = os.path.join(nws_server_gdb,nws_server_cwa_feat_name)
    nws_server_hsa_feat_name = 'NWS_HSA_feat'
    nws_server_hsa_feat = os.path.join(nws_server_gdb,nws_server_hsa_feat_name)

    nws_cwa_feat = os.path.join(temp_gdb,nws_server_cwa_feat_name)
    nws_hsa_feat = os.path.join(temp_gdb,nws_server_hsa_feat_name)

    nws_contact_file_name = 'NWS_DebrisFlow_Contacts.xlsx'
    nws_contact_file = os.path.join(nws_server_dir,nws_contact_file_name)

    arcpy.CopyFeatures_management(nws_server_cwa_feat,nws_cwa_feat)
    arcpy.CopyFeatures_management(nws_server_hsa_feat,nws_hsa_feat)

    print('      Identifying CWA...')
    perim_feat_name = i+'_perim_feat'
    perim_feat = os.path.join(firein_gdb,perim_feat_name)

    perim_dissolve_feat_name = i+'_perim_dissolve_feat'
    perim_dissolve_feat = os.path.join(temp_gdb,perim_dissolve_feat_name)
    arcpy.Dissolve_management(perim_feat,perim_dissolve_feat,'Perim_ID')

    perim_cwa_feat_name = i+'_perim_cwa_feat'
    perim_cwa_feat = os.path.join(temp_gdb,perim_cwa_feat_name)

    arcpy.Identity_analysis(perim_dissolve_feat,nws_cwa_feat,perim_cwa_feat,'ALL')
    perim_cwa_array = arcpy.da.TableToNumPyArray(perim_cwa_feat,'CWA')
    cwa_array_raw = perim_cwa_array['CWA']
    cwa_array = np.array([var for var in cwa_array_raw if var])
    n_cwa = len(cwa_array)
    cwa_string = np.array2string(cwa_array)
    cwa_string = cwa_string.replace('[','')
    cwa_string = cwa_string.replace(']','')
    cwa_string = cwa_string.replace("'","")
    cwa_string = cwa_string.replace(' ','/')
    print('        CWA = '+cwa_string)

    #FIGURE OUT HSA(s)
    print('      Identifying HSA(s)...')

    perim_hsa_feat_name = i+'_perim_hsa_feat'
    perim_hsa_feat = os.path.join(temp_gdb,perim_hsa_feat_name)

    arcpy.Identity_analysis(perim_dissolve_feat,nws_hsa_feat,perim_hsa_feat,'ALL')
    perim_hsa_array = arcpy.da.TableToNumPyArray(perim_hsa_feat,'HSA')
    hsa_array_raw = perim_hsa_array['HSA']
    hsa_array = np.array([var for var in hsa_array_raw if var])
    n_hsa = len(hsa_array)

    hsa_string = np.array2string(hsa_array)
    hsa_string = hsa_string.replace('[','')
    hsa_string = hsa_string.replace(']','')
    hsa_string = hsa_string.replace("'","")
    hsa_string = hsa_string.replace(' ','/')
    print('        HSA = '+hsa_string)

    #EXTRACT CONTACTS
    contact_df = pd.read_excel(nws_contact_file)
    hsa_citystate_col = 'CityState'
    c1_name_col = 'Contact1'
    c1_email_col = 'Email1'
    c2_name_col = 'Contact2'
    c2_email_col = 'Email2'

    #hsa_list = []
    contact_list = []

    nws_contact_file_name = i+'_NWSContacts.txt'
    nws_contact_file = os.path.join(workingdir,nws_contact_file_name)
    nws_contact_target = open(nws_contact_file,'wt')


    for hsa in hsa_array:
        row_df = contact_df.loc[(contact_df['WFO'] == hsa)]
        hsa_citystate = row_df[hsa_citystate_col].values[0]
        c1_name = row_df[c1_name_col].values[0]
        c1_email = row_df[c1_email_col].values[0]
        c1_contact_list = ['  Contact 1: '+c1_name+', '+c1_email]
        #hsa_list.append(['HSA = '+hsa+' ('+hsa_citystate+')'])
        contact_list.append(['HSA = '+hsa+' ('+hsa_citystate+')'])
        contact_list.append(c1_contact_list)

        c2_name = row_df[c2_name_col].values[0]
        c2_email = row_df[c2_email_col].values[0]
        if pd.isnull(c2_name):
            pass
        else:
            c2_contact_list = ['  Contact 2: '+c2_name+', '+c2_email]
            #contact_list = contact_list+c2_contact_list
            contact_list.append(c2_contact_list)

    for contact_row in contact_list:
        nws_contact_target.write('    '+contact_row[0]+'\n')
    if state_abbrev == 'CA':
        nws_contact_target.write('    CA Spreadsheet Contact: Cindy Matthews, cindy.matthews@nws.gov\n')
        nws_contact_target.write('    In SoCal? Also Contact: Jayme Laber, jayme.laber@nws.gov\n')
    nws_contact_target.close()



    #WRITE OUTPUT TEXT FILE
    scale_list = ['Segment','Basin']

    summary_header = 'FireID,FireName,FireYear,State,HSA,Year1_T15_mmh,Year1_T30_mmh,Year1_T60_mmh,Year2_T15_mmh,Year2_T30_mmh,Year2_T60_mmh,Year1_T15_in,Year1_T30_in,Year1_T60_in,Year2_T15_in,Year2_T30_in,Year2_T60_in'

    for scale_name in scale_list:
        summary_file_name = i+'_DFThresholdGuidance_ForNWS_'+scale_name+'.txt'
        summary_file = os.path.join(workingdir,summary_file_name)
        target = open(summary_file,'wt')
        target.write(summary_header+'\n')
        if scale_name == 'Basin':
            tvalue_array = basin_threshold_y1_email_list_SI + basin_threshold_y2_email_list_SI + basin_threshold_y1_email_list_ENG + basin_threshold_y2_email_list_ENG

        if scale_name == 'Segment':
            tvalue_array = segment_threshold_y1_email_list_SI + segment_threshold_y2_email_list_SI + segment_threshold_y1_email_list_ENG + segment_threshold_y2_email_list_ENG


        tvalue_string = ','.join(tvalue_array)


        for hsa_name in hsa_array:
            data_string = i+','+fire_name+','+fire_year+','+state_abbrev+','+hsa_name+','+tvalue_string
            target.write(data_string+'\n')

        target.close()

    # FINISH PROCESSING~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('')
    print('  Basin-Scale Thresholds for Email Guidance:')
    print('')
    print('   YEAR 1:')
    for dur in thresh_duration_list:
        dur_index = thresh_duration_list.index(dur)
        print('     '+str(dur)+'-minute: '+str(basin_threshold_y1_email_list_SI[dur_index])+' mm/h, or '+str(basin_threshold_y1_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(basin_threshold_y1_email_list_RI[dur_index])+' years')
    print('')
    print('   YEAR 2:')
    for dur in thresh_duration_list:
        dur_index = thresh_duration_list.index(dur)
        print('     '+str(dur)+'-minute: '+str(basin_threshold_y2_email_list_SI[dur_index])+' mm/h, or '+str(basin_threshold_y2_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(basin_threshold_y2_email_list_RI[dur_index])+' years')
    print('')


    print('  Segment-Scale Thresholds for Email Guidance:')
    print('')
    print('   YEAR 1:')
    for dur in thresh_duration_list:
        dur_index = thresh_duration_list.index(dur)
        print('     '+str(dur)+'-minute: '+str(segment_threshold_y1_email_list_SI[dur_index])+' mm/h, or '+str(segment_threshold_y1_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(segment_threshold_y1_email_list_RI[dur_index])+' years')
    print('')

    print('   YEAR 2:')
    for dur in thresh_duration_list:
        dur_index = thresh_duration_list.index(dur)
        print('     '+str(dur)+'-minute: '+str(segment_threshold_y2_email_list_SI[dur_index])+' mm/h, or '+str(segment_threshold_y2_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(segment_threshold_y2_email_list_RI[dur_index])+' years')
    print('')

    print('  NWS Contact Information')
    print('')

    for contact_row in contact_list:
        print('    '+contact_row[0])
    if state_abbrev == 'CA':
        print('    CA Main Contact: Cindy Matthews, cindy.matthews@nws.gov')
        print('    In SoCal? Also Contact: Jayme Laber, jayme.laber@nws.gov')

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


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

    print(" Processing Finished at "+str(hour)+":"+str(minute)+" GMT")
    if log_modelrun == 'YES':
        string = 'Finished Step 2'
        write_log(logfile,i,string)
print('')
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Step 2 Analysis Results:')
print('    Processing Successful')
print('    Verify Step 2 Modeling Results, Edit '+i+'_df_input.gdb/'+i+'_watchstream_feat (if necessary), and Proceed to Step 3')
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('')




