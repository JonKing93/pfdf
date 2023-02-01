print("Post-Fire Debris-Flow Hazard Assessment: Step 3 - Package Data for Delivery and Backup")
print("Importing Modules...")
import arcpy
import os
import numpy as np
from numpy import *
import scipy
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
import zipfile
import re
import pandas as pd

arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("spatial")
workingdir = os.getcwd()
env.workspace = workingdir

arcpy.env.overwriteOutput = True

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#fire_list = ['cas','chk','lob','mct']
#state_list =['CA','CA','CA','CA']
#fireyear_list = ['2017','2017','2017','2017']

fire_list = ['ali'] #3 letter abbreviation
state_list =['CA'] #State abbreviation
fireyear_list = ['2021'] #fire start year


status_list = ['FINAL'] #EXAMPLE FOR LOOPING
#status_list = ['PRELIMINARY']

server_root = 'P:\\'


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Processing Variables
yr1_p = 0.5
yr2_p = 0.75

duration_min_colheader = 'Duration_min'
thresh_p_colheader = 'Threshold_P'
ri_col_header = 'RI_yr'
thresh_int_SI_colheader = 'Int_mmh-1'
thresh_acc_ENG_colheader = 'Acc_In'

model = 'M1'

guidance_scale = 'Basin'
#guidance_scale = 'Segment'

# COPY RESULTS TO SERVER?
server_copy = 'YES' #DEFAULT
#server_copy = 'NO'

# CHECK PERIMETER ID?
perim_check = 'YES' # DEFAULT
#perim_check = 'NO'

# GENERATE METADATA?
generate_meta = 'YES' #DEFAULT
#generate_meta = 'NO'

# GENERATE THRESHOLD GUIDANCE FILE?
generate_threshguide = 'YES'  #DEFAULT
#generate_threshguide = 'NO'

# MAKE SHAPEFILES?
make_shapefile = 'YES' #DEFAULT
#make_shapefile = 'NO'

# PROJECT ESTIMATES FOR WEB MAPPING?
project_web = 'YES'  #DEFAULT
#project_web = 'NO'

# ZIP GEODATABASES AND SHAPEFILES?
zip_gdbs = 'YES' #DEFAULT
#zip_gdbs = 'NO'

# WRITE WEBPAGE TEXT FILE?
make_webtext = 'YES'  #DEFAULT
#make_webtext = 'NO'

# WRITE TO BOOOKKEEPING TEXT FILE?
make_booktext = 'YES'  #DEFAULT
#make_booktext = 'NO'

# APPEND CURRENT PERIMETER TO ALL ASSESSMENT PERIMETER GEODATABASE FEATURE CLASS AND ADD PERIMETER TO GEODATABASE?
append_perim = 'YES' #DEFAULT
#append_perim = 'NO'

# ZIP THE SYMBOLOGY FOR MAPPING?
zip_symbology = 'YES' #DEFAULT
#zip_symbology = 'NO'

# SPLIT THE THRESHOLD DATA INTO SEPARATE GDBS FOR EACH DURATION?
#split_thresholds = 'YES'
split_thresholds = 'NO' #DEFAULT

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


server_dir_name = 'DF_Assessment_GeneralData'
script_dir_name = 'Scripts'
symbology_dir_name = 'AssessmentResults_Symbology'
estimates_symbology_dir_name = 'Estimates_Symbology'
threshold_symbology_dir_name = 'Threshold_Symbology'

server_dir = os.path.join(server_root,server_dir_name)
script_dir = os.path.join(server_root,script_dir_name)
symbology_dir = os.path.join(server_dir,symbology_dir_name)
estimates_symbology_dir = os.path.join(symbology_dir,estimates_symbology_dir_name)
threshold_symbology_dir = os.path.join(symbology_dir,threshold_symbology_dir_name)

nws_server_dir_name = 'NWS_Data'
nws_server_dir = os.path.join(server_root,nws_server_dir_name)
nws_server_gdb_name = 'NWS_ThresholdCompilation_BaseData.gdb'
nws_server_gdb = os.path.join(nws_server_dir,nws_server_gdb_name)
nws_server_backup_dir_name = 'ThresholdGuidance_BackupFiles'
nws_server_backup_dir = os.path.join(nws_server_dir,nws_server_backup_dir_name)

if os.path.exists(server_dir):
    print('     Connected to '+server_root+', Continuing Processing...')
else:
    print('     Not Connected to '+server_root+', Terminating Program')
    print('     ***Please Reconnect to '+server_root+' and Restart Script***')
    sys.exit()

# IMPORT MODULES

tau_py = 'DFTools_TauDEM_PRO.py'
arc_py = 'DFTools_ArcGIS_PRO.py'
confine_py = 'DFTools_Confinement_PRO.py'
module_list = [tau_py,arc_py,confine_py]


for module_name in module_list:

    in_module = os.path.join(script_dir,module_name)
    out_module = os.path.join(workingdir,module_name)

    shutil.copy(in_module,out_module)

import DFTools_TauDEM_PRO as DFTools_TauDEM
import DFTools_ArcGIS_PRO as DFTools_ArcGIS
import DFTools_Confinement_PRO as DFTools_TauDEM

fire_name_list = []
fire_location_list = []
fire_date_list = []
fire_watch_list = []

#threshold_dur_list = [15, 30, 60]
threshold_duration_list = [15, 30, 60]
lv_duration_list = [15]

accum_list = [3,4,5,6,7,8,9,10]

RainAtP_list = [.10,.25,.40,.50,.60,.75,.90]


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

p_x1_name = p_x1_list[model_row]
p_x2_name = p_x2_list[model_row]
p_x3_name = p_x3_list[model_row]

duration_list = [15,30,60]
p_value_list = [0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9]

for fire_name in fire_list:

    i_index = fire_list.index(fire_name)
    state_abbrev = state_list[i_index]
    fire_year = fireyear_list[i_index]
    i = fire_name+fire_year

    status = status_list[i_index]

    if status == 'FINAL':
        disclaimer = "''"
    else:
        disclaimer = 'Note: These data are based upon preliminary imagery and assessments of soil burn severity.  These estimates will be updated as new imagery becomes available and/or the Emergency Response Teams finalize their soil burn severity map.  The estimates of debris-flow likelihood, volume, combined hazard, and rainfall thresholds presented here are preliminary and are subject to revision.'

##    text_entry = 1
##
##    while text_entry == 1:
##
##        fire_name_q = raw_input('Please Enter the Full Name of '+i+' [e.g. Silverado or Carlton Complex]')
##        fire_location_q = raw_input('Please Enter the Location of '+i+' [County Name or National Forest, State (e.g. Angeles National Forest, CA)]')
##        fire_start_date_q = raw_input('Please Enter '+i+' Start Date [e.g. August 26, 2009]')
##
##        fire_info_name = 'Fire Name = '+str(fire_name_q)
##        fire_info_location = 'Location = '+str(fire_location_q)
##        fire_info_start_date = 'Start Date = '+str(fire_start_date_q)
##
##        print('Checking Text Entry Information...')
##        print('     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
##        print('     '+fire_info_name)
##        print('     '+fire_info_location)
##        print('     '+fire_info_start_date)
##        print('     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
##
##        text_check = raw_input("\n\nIs the information in the interpeter window correct?  Enter y or n:")
##
##        if text_check == 'n' or text_check == 'N' or text_check == 'no' or text_check == 'NO' or text_check == 'No':
##            text_entry = 1
##        elif text_check == 'y' or text_check == 'y' or text_check == 'yes' or text_check == 'Yes' or text_check == 'YES':
##            text_entry = 0
##
##    fire_name_list.append(fire_name_q)
##    fire_location_list.append(fire_location_q)
##    fire_date_list.append(fire_start_date_q)
##
##
##    fire_name_full = str(fire_name_list[i_index])
##    fire_location = str(fire_location_list[i_index])
##    fire_start_date = str(fire_date_list[i_index])

    arcpy.env.overwriteOutput = True
    arcpy.ClearEnvironment("cellSize")
    arcpy.ClearEnvironment("extent")
    arcpy.ClearEnvironment("snapRaster")

    i_index = fire_list.index(fire_name)
    state_abbrev = state_list[i_index]
    fire_year = fireyear_list[i_index]

    i = fire_name+fire_year


    now = time.gmtime()
    datetimenow = datetime.datetime.now()
    year4digit = datetimenow.year
    yearstr = str(year4digit)
    monthstr = time.strftime('%m', now)
    daystr = time.strftime('%d',now)
    monthint = int(monthstr)
    month = calendar.month_abbr[monthint]

    day = time.strftime('%d', now)
    year = time.strftime('%Y', now)
    month = time.strftime('%m', now)
    hour = time.strftime('%H', now)
    minute = time.strftime('%M', now)
    second = time.strftime('%S', now)
    zone = 'GMT'

    print('Processing Fire = '+i+'...')

    print(" Processing Started at "+str(hour)+":"+str(minute)+" GMT")

    #fire_name_location = 'DEBUGGING - REMOVE COMMENT FOR USER INPUT'
    #fire_start_date = 'DEBUGGING - REMOVE COMMENT FOR USER INPUT'
    #watch_stream_check = 'DEBUGGING - REMOVE COMMENT FOR USER INPUT'


    firein_gdb_name = i+'_df_input.gdb'
    firein_gdb = os.path.join(workingdir,firein_gdb_name) # Geodatabase Name and Path

    temp_gdb_name = i+'_scratch.gdb'
    temp_gdb = os.path.join(workingdir,temp_gdb_name) # Geodatabase Name and Path

    modelcalcs_gdb_name = i+'_dfestimates_utm.gdb'
    modelcalcs_gdb = os.path.join(workingdir,modelcalcs_gdb_name) # Geodatabase Name and Path

    modelcalcs_web_gdb_name = i+'_dfestimates_wgs84.gdb'
    modelcalcs_web_gdb = os.path.join(workingdir,modelcalcs_web_gdb_name) # Geodatabase Name and Path

    verification_gdb_name = i+"_verification.gdb"
    verification_gdb = os.path.join(workingdir,verification_gdb_name) # Geodatabase Name and Path

    threshold_utm_gdb_name = i+"_threshold_utm.gdb"
    threshold_utm_gdb = os.path.join(workingdir,threshold_utm_gdb_name) # Geodatabase Name and Path

    threshold_wgs_gdb_name = i+"_threshold_wgs.gdb"
    threshold_wgs_gdb = os.path.join(workingdir,threshold_wgs_gdb_name) # Geodatabase Name and Path

    backup_main_dir_name = i+'_AssessmentData'
    backup_main_dir = os.path.join(server_root,state_abbrev,'Assessment_Data',backup_main_dir_name)
    if not os.path.exists (backup_main_dir): os.mkdir(backup_main_dir)

    backup_dir_name = 'Run_'+str(year)+str(month)+str(day)+'_'+str(hour)+str(minute)
    backup_dir = os.path.join(backup_main_dir,backup_dir_name)

    if server_copy == 'YES':
        if not os.path.exists (backup_dir): os.mkdir(backup_dir)

    backup_webdir_name = i+'_WebData'
    backup_webdir = os.path.join(backup_dir,backup_webdir_name)
    backup_main_webdir = os.path.join(backup_main_dir,backup_webdir_name)
    if server_copy == 'YES':
        if not os.path.exists (backup_webdir): os.mkdir(backup_webdir)

    if server_copy == 'YES':
        if os.path.exists(backup_main_webdir):
            shutil.rmtree(backup_main_webdir)
        os.mkdir(backup_main_webdir)

    perim_feat_name = i+'_perim_feat'
    perim_feat = os.path.join(firein_gdb,perim_feat_name)

    db_feat_name = i+'_db_feat'
    db_feat = os.path.join(firein_gdb,db_feat_name)

    perim_dir_name = 'AnalyzedPerimeters'
    perim_dir = os.path.join(server_dir,perim_dir_name)

    perim_gdb_name = 'DFAssessment_AnalyzedPerimeters.gdb'
    perim_gdb = os.path.join(perim_dir,perim_gdb_name)

    perim_check_feat_name = i+'_perim_feat'
    perim_check_feat = os.path.join(perim_gdb,perim_check_feat_name)

    if server_copy == 'NO':
        print('     Results Will Not Be Copied to Server...')
    else:
        print('     Results Will Be Copied to Server...')

    if perim_check == 'YES':

        if arcpy.Exists(perim_check_feat):
            print('     Fire Name = '+i+' Has Already Been Assigned, Please Rename Input GDB and Feature Classes to a Unique Abbreviation...')
            print('     Terminating Program...')
            quit()

        else:
            print('     Duplicate Perimeter ID Check = Pass...')

    else:
        print('     Not Checking for Duplicate Perimeter ID...')

    xml_template_dir = os.path.join(server_dir,'XML_Templates')

    estimates_xml_dir_name = i+'_'+model+'_XMLFiles'
    estimates_xml_dir = os.path.join(workingdir,estimates_xml_dir_name)
    if not os.path.exists (estimates_xml_dir): os.mkdir(estimates_xml_dir)

    threshold_xml_dir_name = i+'_Threshold_XMLFiles'
    threshold_xml_dir = os.path.join(workingdir,threshold_xml_dir_name)
    if not os.path.exists (threshold_xml_dir): os.mkdir(threshold_xml_dir)

    strm_pred_template_xml_name = 'xml_template_strm_pred_feat.xml'
    strm_pred_template_xml = os.path.join(xml_template_dir,strm_pred_template_xml_name)

    basin_pred_template_xml_name = 'xml_template_basin_pred_feat.xml'
    basin_pred_template_xml = os.path.join(xml_template_dir,basin_pred_template_xml_name)

    perim_template_xml_name = 'xml_template_perim_feat.xml'
    perim_template_xml = os.path.join(xml_template_dir,perim_template_xml_name)

    extent_template_xml_name = 'xml_template_extent_feat.xml'
    extent_template_xml = os.path.join(xml_template_dir,extent_template_xml_name)

    basinpt_template_xml_name = 'xml_template_basinpt_feat.xml'
    basinpt_template_xml = os.path.join(xml_template_dir,basinpt_template_xml_name)

    centroid_template_xml_name = 'xml_template_centroid_feat.xml'
    centroid_template_xml = os.path.join(xml_template_dir,centroid_template_xml_name)

    db_template_xml_name = 'xml_template_db_feat.xml'
    db_template_xml = os.path.join(xml_template_dir,db_template_xml_name)

    watchstream_template_xml_name = 'xml_template_watchstream_feat.xml'
    watchstream_template_xml = os.path.join(xml_template_dir,watchstream_template_xml_name)

    fire_webinfo = os.path.join(workingdir,i+"_webinfo.txt")
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

    #GENERATE METADATA

    if generate_meta == 'YES':

        perim_feat_name = i+'_perim_feat'
        perim_feat = os.path.join(firein_gdb,perim_feat_name)
        delete_fields = ['UNIT_ID','FIRE_NUM','DATE_','TIME_','COMMENTS','AGENCY','ACTIVE','FIRE','LOAD_DATE','INCIWEB_ID','INC_NUM','ACRES']
        arcpy.DeleteField_management(perim_feat,delete_fields)

        centroid_feat_name = i+'_centroid_feat'
        centroid_feat = os.path.join(firein_gdb,centroid_feat_name)
        delete_fields = ['UNIT_ID','FIRE_NUM','DATE_','TIME_','COMMENTS','AGENCY','ACTIVE','FIRE','LOAD_DATE','INCIWEB_ID','INC_NUM','ACRES','PERIM_ID','ORIG_FID']
        arcpy.DeleteField_management(centroid_feat,delete_fields)

        basinpt_feat_name = i+'_basinpt_feat'
        basinpt_feat = os.path.join(firein_gdb,basinpt_feat_name)
        delete_fields = ['Join_Count','TARGET_FID','from_node','to_node','Shape_Length_1','StrmOrd','StrmOrder','slppct','gridcode','BUFFER_ID','from_node_1','to_node_1','Segment_ID']
        arcpy.DeleteField_management(basinpt_feat,delete_fields)

        watchstream_feat_name = i+'_watchstream_feat'
        watchstream_feat = os.path.join(firein_gdb,watchstream_feat_name)

        if arcpy.Exists(watchstream_feat):
            delete_fields = ['FID_'+i+'_step1_strm_feat','Join_count','TARGET_FID','from_node','to_node','Shape_Length1','StrmOrd','facc','bacc','burnbin','StrmOrder','slppct','conf', 'DevCl','Perim','MIN','DBCl','AreaCL','BurnCl','PerimCl','PctBurn','PctBurnCl','ConfineCl','SlopeCl','MorphCl','NonDevCl','zModCl','ModelClasss','ID','gridcode','BUFFER_ID','FID_'+i+'_step1_strmcl0_buffer_bin_feat','from_node_1','to_node_1','Shape_Length_1','burn_bin','ModelClass']
            arcpy.DeleteField_management(watchstream_feat,delete_fields)

        analysis_date = str(year)+str(month)+str(day)
        likelihood_ref = '(Staley et al., 2016, USGS Open-File Report 2016-1106, https://pubs.er.usgs.gov/publication/ofr20161106)'
        volume_ref = '(Gartner et al., 2014, Engineering Geology 176:45-56 https://dx.doi.org/10.1016/j.enggeo.2014.04.008)'
        threshold_ref = '(Staley et al. 2017, Geomorphology 278(1):149-162, https://doi.org/10.1016/j.geomorph.2016.10.019)'

        m1_x1_desc = 'Likelihood Model M1 X1: Proportion of the contributing area burned at high or moderate severity with gradients in excess of 23 degrees'+likelihood_ref
        m2_x1_desc = 'Likelihood Model M2 X1: '+likelihood_ref
        m3_x1_desc = 'Likelihood Model M3 X1: '+likelihood_ref
        m4_x1_desc = 'Likelihood Model M4 X1: '+likelihood_ref

        l_x1_desc_array = [m1_x1_desc,m2_x1_desc,m3_x1_desc,m4_x1_desc]

        m1_x2_desc = 'Likelihood Model M1 X2: Average dNBR of the contributing area divided by 1000 '+likelihood_ref
        m2_x2_desc = 'Likelihood Model M2 X2: '+likelihood_ref
        m3_x2_desc = 'Likelihood Model M3 X2: '+likelihood_ref
        m4_x2_desc = 'Likelihood Model M4 X2: '+likelihood_ref

        l_x2_desc_array = [m1_x2_desc,m2_x2_desc,m3_x2_desc,m4_x2_desc]

        m1_x3_desc = 'Likelihood Model M1 X3: Average USSoils KF-Factor of the contributing area '+likelihood_ref
        m2_x3_desc = 'Likelihood Model M2 X3: '+likelihood_ref
        m3_x3_desc = 'Likelihood Model M3 X3: '+likelihood_ref
        m4_x3_desc = 'Likelihood Model M4 X3: '+likelihood_ref

        l_x3_desc_array = [m1_x3_desc,m2_x3_desc,m3_x3_desc,m4_x3_desc]

        v_x1_desc = 'Volume Model X1: square root of the relief (in meters) of the contributing area '+volume_ref
        v_x2_desc = 'Volume Model X1: natural log of the total area (km^2) burned at high or moderate severity in the contributing area '+volume_ref
        m1_r_raw_desc = 'Likelihood Model R: Modeled XX-minute rainfall accumulation (mm) '+likelihood_ref
        v_x3_desc = 'Volume Model X3: square root of the modeled peak 15-minute intensity (mm/h) '+volume_ref


        vol_eq = 'LnV = '+str(v_b)+' + ('+str(v_c1)+' * V_X1) + ('+str(v_c2)+' * V_X2) + ('+str(v_c3)+' * V_X3) ' + volume_ref

        print('     Generating Metadata for Segment and Basin Estimates of Rainfall Thresholds...')

        for thresh_dur in threshold_duration_list:
            print('         Duration = '+str(thresh_dur)+' Minutes...')
            thresh_dur_string = str(thresh_dur)+'min'
            thresh_dur_index = threshold_duration_list.index(thresh_dur)
            thresh_dur_str = str(thresh_dur)
            p_b_value = p_b_array[model_row,thresh_dur_index]
            p_c1_value = p_c1_array[model_row,thresh_dur_index]
            p_c2_value = p_c2_array[model_row,thresh_dur_index]
            p_c3_value = p_c3_array[model_row,thresh_dur_index]

            l_x1_desc = l_x1_desc_array[model_row]
            l_x2_desc = l_x2_desc_array[model_row]
            l_x3_desc = l_x3_desc_array[model_row]

            strm_thresh_template_xml_name = 'xml_template_rainatp_'+thresh_dur_str+'min_segment_feat.xml'
            strm_thresh_template_xml = os.path.join(xml_template_dir,strm_thresh_template_xml_name)

            basin_thresh_template_xml_name = 'xml_template_rainatp_'+thresh_dur_str+'min_basin_feat.xml'
            basin_thresh_template_xml = os.path.join(xml_template_dir,basin_thresh_template_xml_name)


            # RAIN AT ALL P VALUES
            print('             All P Values...')
            strm_thresh_all_template_xml_name = 'xml_template_rainatallp_'+thresh_dur_str+'min_segment_feat.xml'
            strm_thresh_all_template_xml = os.path.join(xml_template_dir,strm_thresh_all_template_xml_name)

            basin_thresh_all_template_xml_name = 'xml_template_rainatallp_'+thresh_dur_str+'min_basin_feat.xml'
            basin_thresh_all_template_xml = os.path.join(xml_template_dir,basin_thresh_all_template_xml_name)

            strm_thresh_all_feat_name = i+'_Segment_RainfallEstimates_'+thresh_dur_str+'min_RainAtAllP'
            strm_thresh_all_feat = os.path.join(threshold_utm_gdb,strm_thresh_all_feat_name)

            strm_thresh_all_feat_wgs = os.path.join(threshold_wgs_gdb,strm_thresh_all_feat_name)

            basin_thresh_all_feat_name = i+'_Basin_RainfallEstimates_'+thresh_dur_str+'min_RainAtAllP'
            basin_thresh_all_feat = os.path.join(threshold_utm_gdb,basin_thresh_all_feat_name)

            p10_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.1, in mm'
            p10_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.1, in mm/h'
            p10_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.1, in mm '+threshold_ref
            p10_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.1, in mm/h '+threshold_ref

            p25_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.25, in mm'
            p25_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.25, in mm/h'
            p25_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.25, in mm '+threshold_ref
            p25_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.25, in mm/h '+threshold_ref

            p40_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.4, in mm'
            p40_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.4, in mm/h'
            p40_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.4, in mm '+threshold_ref
            p40_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.4, in mm/h '+threshold_ref

            p50_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.5, in mm'
            p50_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.5, in mm/h'
            p50_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.5, in mm '+threshold_ref
            p50_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.5, in mm/h '+threshold_ref

            p60_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.6, in mm'
            p60_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.6, in mm/h'
            p60_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.6, in mm '+threshold_ref
            p60_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.6, in mm/h '+threshold_ref

            p75_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.75, in mm'
            p75_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.75, in mm/h'
            p75_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.75, in mm '+threshold_ref
            p75_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.75, in mm/h '+threshold_ref

            p90_acc_desc = 'Peak '+thresh_dur_str+' minute rainfall accumulation that results in P = 0.9, in mm'
            p90_int_desc = 'Peak '+thresh_dur_str+' minute rainfall intensity that results in P = 0.9, in mm/h'
            p90_acc_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall accumulations that results in P = 0.9, in mm '+threshold_ref
            p90_int_legend_desc = 'Legend field representing range of peak '+thresh_dur_str+' minute rainfall intensities that results in P = 0.9, in mm/h '+threshold_ref


            fid_strm_thresh_all_feat_desc = 'FID_'+strm_thresh_all_feat_name
            fid_basin_thresh_all_feat_desc = 'FID_'+basin_thresh_all_feat_name

            strm_thresh_all_raw_xml_name = strm_thresh_all_feat_name+'_raw.xml'
            strm_thresh_all_raw_xml = os.path.join(threshold_xml_dir,strm_thresh_all_raw_xml_name)

            strm_thresh_all_xml_name = strm_thresh_all_feat_name+'.xml'
            strm_thresh_all_xml = os.path.join(threshold_xml_dir,strm_thresh_all_xml_name)

            strm_desc_wgs = arcpy.Describe(strm_thresh_all_feat_wgs)
            strm_lat_top_dd_value = strm_desc_wgs.Extent.YMax
            strm_lat_bottom_dd_value = strm_desc_wgs.Extent.YMin
            strm_lon_left_dd_value = strm_desc_wgs.Extent.XMin
            strm_lon_right_dd_value = strm_desc_wgs.Extent.XMax

            lat_top_dd = str('%.4f' % strm_lat_top_dd_value)
            lat_bottom_dd = str('%.4f' % strm_lat_bottom_dd_value)
            lon_left_dd = str('%.4f' % strm_lon_left_dd_value)
            lon_right_dd = str('%.4f' % strm_lon_right_dd_value)

            strm_desc_utm = arcpy.Describe(strm_thresh_all_feat)
            strm_desc_utm_sr = strm_desc_utm.spatialReference
            utm_name_full = str(strm_desc_utm_sr.name)
            utm_zone_string = str.replace(utm_name_full,'NAD_1983_UTM_Zone_','')
            utm_zone_string = str.replace(utm_zone_string,'N','')

            basin_thresh_all_raw_xml_name = basin_thresh_all_feat_name+'_raw.xml'
            basin_thresh_all_raw_xml = os.path.join(threshold_xml_dir,basin_thresh_all_raw_xml_name)

            basin_thresh_all_xml_name = basin_thresh_all_feat_name+'.xml'
            basin_thresh_all_xml = os.path.join(threshold_xml_dir,basin_thresh_all_xml_name)

            fid_strm_feat = 'FID_'+strm_thresh_all_feat_name
            fid_basin_feat = 'FID_'+basin_thresh_all_feat_name

            shutil.copy(strm_thresh_all_template_xml,strm_thresh_all_raw_xml)

            input_file = open(strm_thresh_all_raw_xml)
            xmlcontents = input_file.read()
            input_file.close()

            xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
            xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
            xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
            xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
            xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
            xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
            xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
            xmlcontents = xmlcontents.replace('%%THRESHOLD_FEATURENAME%%',strm_thresh_all_feat_name)
            xmlcontents = xmlcontents.replace('%FID_STREAMFEAT%',fid_strm_thresh_all_feat_desc)
            xmlcontents = xmlcontents.replace('%FID_BASINFEAT%',fid_basin_thresh_all_feat_desc)
            xmlcontents = xmlcontents.replace('%M1_X1_DESCRIPTION%',l_x1_desc)
            xmlcontents = xmlcontents.replace('%M1_X2_DESCRIPTION%',l_x2_desc)
            xmlcontents = xmlcontents.replace('%M1_X3_DESCRIPTION%',l_x3_desc)
            xmlcontents = xmlcontents.replace('%FID_THRESHOLD_BASINFEATURENAME%',fid_strm_thresh_all_feat_desc)
            xmlcontents = xmlcontents.replace('%FID_THRESHOLD_SEGMENTFEATURENAME%',fid_basin_thresh_all_feat_desc)

            xmlcontents = xmlcontents.replace('%P10_ACC%',p10_acc_desc)
            xmlcontents = xmlcontents.replace('%P10_INT%',p10_int_desc)
            xmlcontents = xmlcontents.replace('%P10_ACC_LEGEND%',p10_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P10_INT_LEGEND%',p10_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P25_ACC%',p25_acc_desc)
            xmlcontents = xmlcontents.replace('%P25INT%',p25_int_desc)
            xmlcontents = xmlcontents.replace('%P25_ACC_LEGEND%',p25_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P25_INT_LEGEND%',p25_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P40_ACC%',p40_acc_desc)
            xmlcontents = xmlcontents.replace('%P40_INT%',p40_int_desc)
            xmlcontents = xmlcontents.replace('%P40_ACC_LEGEND%',p40_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P40_INT_LEGEND%',p40_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P50_ACC%',p50_acc_desc)
            xmlcontents = xmlcontents.replace('%P50_INT%',p50_int_desc)
            xmlcontents = xmlcontents.replace('%P50_ACC_LEGEND%',p50_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P50_INT_LEGEND%',p50_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P60_ACC%',p60_acc_desc)
            xmlcontents = xmlcontents.replace('%P60_INT%',p60_int_desc)
            xmlcontents = xmlcontents.replace('%P60_ACC_LEGEND%',p60_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P60_INT_LEGEND%',p60_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P75_ACC%',p75_acc_desc)
            xmlcontents = xmlcontents.replace('%P75_INT%',p75_int_desc)
            xmlcontents = xmlcontents.replace('%P75_ACC_LEGEND%',p75_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P75_INT_LEGEND%',p75_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P90_ACC%',p90_acc_desc)
            xmlcontents = xmlcontents.replace('%P90_INT%',p90_int_desc)
            xmlcontents = xmlcontents.replace('%P90_ACC_LEGEND%',p90_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P90_INT_LEGEND%',p90_int_legend_desc)

            output_file = open(strm_thresh_all_xml,'w')
            output_file.write(xmlcontents)
            output_file.close()

            os.remove(strm_thresh_all_raw_xml)

            #arcpy.ImportMetadata_conversion(strm_thresh_all_xml,'',strm_thresh_all_feat)

            # BASINS
            shutil.copy(basin_thresh_all_template_xml,basin_thresh_all_raw_xml)

            input_file = open(basin_thresh_all_raw_xml)
            xmlcontents = input_file.read()
            input_file.close()

            xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
            xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
            xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
            xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
            xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
            xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
            xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
            xmlcontents = xmlcontents.replace('%THRESHOLD_FEATURENAME%',strm_thresh_all_feat_name)
            xmlcontents = xmlcontents.replace('%FID_STREAMFEAT%',fid_strm_thresh_all_feat_desc)
            xmlcontents = xmlcontents.replace('%FID_BASINFEAT%',fid_basin_thresh_all_feat_desc)
            xmlcontents = xmlcontents.replace('%M1_X1_DESCRIPTION%',m1_x1_desc)
            xmlcontents = xmlcontents.replace('%M1_X2_DESCRIPTION%',m1_x2_desc)
            xmlcontents = xmlcontents.replace('%M1_X3_DESCRIPTION%',m1_x3_desc)
            xmlcontents = xmlcontents.replace('%FID_THRESHOLD_BASINFEATURENAME%',fid_strm_thresh_all_feat_desc)
            xmlcontents = xmlcontents.replace('%FID_THRESHOLD_SEGMENTFEATURENAME%',fid_basin_thresh_all_feat_desc)

            xmlcontents = xmlcontents.replace('%P10_ACC%',p10_acc_desc)
            xmlcontents = xmlcontents.replace('%P10_INT%',p10_int_desc)
            xmlcontents = xmlcontents.replace('%P10_ACC_LEGEND%',p10_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P10_INT_LEGEND%',p10_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P25_ACC%',p25_acc_desc)
            xmlcontents = xmlcontents.replace('%P25INT%',p25_int_desc)
            xmlcontents = xmlcontents.replace('%P25_ACC_LEGEND%',p25_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P25_INT_LEGEND%',p25_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P40_ACC%',p40_acc_desc)
            xmlcontents = xmlcontents.replace('%P40_INT%',p40_int_desc)
            xmlcontents = xmlcontents.replace('%P40_ACC_LEGEND%',p40_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P40_INT_LEGEND%',p40_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P50_ACC%',p50_acc_desc)
            xmlcontents = xmlcontents.replace('%P50_INT%',p50_int_desc)
            xmlcontents = xmlcontents.replace('%P50_ACC_LEGEND%',p50_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P50_INT_LEGEND%',p50_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P60_ACC%',p60_acc_desc)
            xmlcontents = xmlcontents.replace('%P60_INT%',p60_int_desc)
            xmlcontents = xmlcontents.replace('%P60_ACC_LEGEND%',p60_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P60_INT_LEGEND%',p60_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P75_ACC%',p75_acc_desc)
            xmlcontents = xmlcontents.replace('%P75_INT%',p75_int_desc)
            xmlcontents = xmlcontents.replace('%P75_ACC_LEGEND%',p75_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P75_INT_LEGEND%',p75_int_legend_desc)

            xmlcontents = xmlcontents.replace('%P90_ACC%',p90_acc_desc)
            xmlcontents = xmlcontents.replace('%P90_INT%',p90_int_desc)
            xmlcontents = xmlcontents.replace('%P90_ACC_LEGEND%',p90_acc_legend_desc)
            xmlcontents = xmlcontents.replace('%P90_INT_LEGEND%',p90_int_legend_desc)

            output_file = open(basin_thresh_all_xml,'w')
            output_file.write(xmlcontents)
            output_file.close()

            os.remove(basin_thresh_all_raw_xml)

            #arcpy.ImportMetadata_conversion(basin_thresh_all_xml,'',basin_thresh_all_feat)

            print('             Individual P Values...')
            for p_calc in RainAtP_list:
                p_str = str('%.2f' % p_calc)
                p_100 = p_calc * 100.0
                p_100_string = str(int(p_100))
                threshold_eq = '(ln('+p_str+'/ 1 - '+p_str+') + '+str(p_b_value)+') / ('+str(p_c1_value)+' * M1_X1 + '+str(p_c1_value)+' * M1_X2 + '+str(p_c3_value)+' * M1_X3) '+likelihood_ref

                strm_thresh_feat_name = i+'_Segment_RainfallEstimates_'+thresh_dur_string+'_RainAtP_'+p_100_string
                strm_thresh_feat = os.path.join(threshold_utm_gdb,strm_thresh_feat_name)

                strm_thresh_feat_wgs_name = i+'_Segment_RainfallEstimates_'+thresh_dur_string+'_RainAtP_'+p_100_string
                strm_thresh_feat_wgs = os.path.join(threshold_wgs_gdb,strm_thresh_feat_name)

                basin_thresh_feat_name = i+'_Basin_RainfallEstimates_'+thresh_dur_string+'_RainAtP_'+p_100_string
                basin_thresh_feat = os.path.join(threshold_utm_gdb,basin_thresh_feat_name)

                fid_strm_threshold_feat = 'FID_'+strm_thresh_feat_name
                fid_basin_threshold_feat = 'FID_'+basin_thresh_feat_name

                rainaccatp_varname = 'RainAccAtP'+p_100_string+'_mm'
                rainintatp_varname = 'RainIntAtP'+p_100_string+'_mm'

                rainaccatp_legend_varname = 'RainAccAtP'+p_100_string+'_mm_Legend'
                rainintatp_legend_varname = 'RainIntAtP'+p_100_string+'_mm_Legend'

                rainaccatp_desc = thresh_dur_str+' rainfall accumulation (in millimeters) resulting in a statistical likelihood (P) = '+p_str+' '+threshold_ref
                rainintatp_desc = thresh_dur_str+' rainfall intensity (in millimeters per hour) resulting in a statistical likelihood (P) = '+p_str+' '+threshold_ref

                rainaccatp_legend_desc = 'Legend field for mapping '+thresh_dur_str+' rainfall accumulation (in millimeters) resulting in a statistical likelihood (P) = '+p_str+' '+threshold_ref
                rainintatp_legend_desc = 'Legend field for mapping '+thresh_dur_str+' rainfall intensity (in millimeters per hour) resulting in a statistical likelihood (P) = '+p_str+' '+threshold_ref

                fid_strm_thresh_feat_desc = 'FID_'+strm_thresh_feat_name
                fid_basin_thresh_feat_desc = 'FID_'+basin_thresh_feat_name

                strm_thresh_raw_xml_name = strm_thresh_feat_name+'_raw.xml'
                strm_thresh_raw_xml = os.path.join(threshold_xml_dir,strm_thresh_raw_xml_name)

                strm_thresh_xml_name = strm_thresh_feat_name+'.xml'
                strm_thresh_xml = os.path.join(threshold_xml_dir,strm_thresh_xml_name)

                strm_desc_wgs = arcpy.Describe(strm_thresh_feat_wgs)
                strm_lat_top_dd_value = strm_desc_wgs.Extent.YMax
                strm_lat_bottom_dd_value = strm_desc_wgs.Extent.YMin
                strm_lon_left_dd_value = strm_desc_wgs.Extent.XMin
                strm_lon_right_dd_value = strm_desc_wgs.Extent.XMax

                lat_top_dd = str('%.4f' % strm_lat_top_dd_value)
                lat_bottom_dd = str('%.4f' % strm_lat_bottom_dd_value)
                lon_left_dd = str('%.4f' % strm_lon_left_dd_value)
                lon_right_dd = str('%.4f' % strm_lon_right_dd_value)

                strm_desc_utm = arcpy.Describe(strm_thresh_feat)
                strm_desc_utm_sr = strm_desc_utm.spatialReference
                utm_name_full = str(strm_desc_utm_sr.name)
                utm_zone_string = str.replace(utm_name_full,'NAD_1983_UTM_Zone_','')
                utm_zone_string = str.replace(utm_zone_string,'N','')

                basin_thresh_raw_xml_name = basin_thresh_feat_name+'_raw.xml'
                basin_thresh_raw_xml = os.path.join(threshold_xml_dir,basin_thresh_raw_xml_name)

                basin_thresh_xml_name = basin_thresh_feat_name+'.xml'
                basin_thresh_xml = os.path.join(threshold_xml_dir,basin_thresh_xml_name)

                fid_strm_feat = 'FID_'+strm_thresh_feat_name
                fid_basin_feat = 'FID_'+basin_thresh_feat_name

                shutil.copy(strm_thresh_template_xml,strm_thresh_raw_xml)

                input_file = open(strm_thresh_raw_xml)
                xmlcontents = input_file.read()
                input_file.close()

                xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
                xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
                xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
                xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
                xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
                xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
                xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
                xmlcontents = xmlcontents.replace('%%THRESHOLD_FEATURENAME%%',strm_thresh_feat_name)
                xmlcontents = xmlcontents.replace('%FID_STREAMFEAT%',fid_strm_thresh_feat_desc)
                xmlcontents = xmlcontents.replace('%FID_BASINFEAT%',fid_basin_thresh_feat_desc)
                xmlcontents = xmlcontents.replace('%M1_X1_DESCRIPTION%',m1_x1_desc)
                xmlcontents = xmlcontents.replace('%M1_X2_DESCRIPTION%',m1_x2_desc)
                xmlcontents = xmlcontents.replace('%M1_X3_DESCRIPTION%',m1_x3_desc)
                xmlcontents = xmlcontents.replace('%FID_THRESHOLD_BASINFEATURENAME%',fid_strm_thresh_feat_desc)
                xmlcontents = xmlcontents.replace('%FID_THRESHOLD_SEGMENTFEATURENAME%',fid_basin_thresh_feat_desc)

                xmlcontents = xmlcontents.replace('%RAINACCATP_VARNAME%',rainaccatp_varname)
                xmlcontents = xmlcontents.replace('%RAININTATP_VARNAME%',rainintatp_varname)
                xmlcontents = xmlcontents.replace('%RAINACCATP_DESC%',rainaccatp_desc)
                xmlcontents = xmlcontents.replace('%RAININTATP_DESC%',rainintatp_desc)

                xmlcontents = xmlcontents.replace('%RAINACCATP_VARNAME_LEGEND%',rainaccatp_legend_varname)
                xmlcontents = xmlcontents.replace('%RAININTATP_VARNAME_LEGEND%',rainintatp_legend_varname)
                xmlcontents = xmlcontents.replace('%RAINACCATP_LEGEND_DESC%',rainaccatp_legend_desc)
                xmlcontents = xmlcontents.replace('%RAININTATP_LEGEND_DESC%',rainintatp_legend_desc)

                output_file = open(strm_thresh_xml,'w')
                output_file.write(xmlcontents)
                output_file.close()

                os.remove(strm_thresh_raw_xml)

                #arcpy.ImportMetadata_conversion(strm_thresh_xml,'',strm_thresh_feat)

                shutil.copy(basin_thresh_template_xml,basin_thresh_raw_xml)

                input_file = open(basin_thresh_raw_xml)
                xmlcontents = input_file.read()
                input_file.close()

                xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
                xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
                xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
                xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
                xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
                xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
                xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
                xmlcontents = xmlcontents.replace('%%THRESHOLD_FEATURENAME%%',strm_thresh_feat_name)
                xmlcontents = xmlcontents.replace('%FID_STREAMFEAT%',fid_strm_thresh_feat_desc)
                xmlcontents = xmlcontents.replace('%FID_BASINFEAT%',fid_basin_thresh_feat_desc)
                xmlcontents = xmlcontents.replace('%M1_X1_DESCRIPTION%',m1_x1_desc)
                xmlcontents = xmlcontents.replace('%M1_X2_DESCRIPTION%',m1_x2_desc)
                xmlcontents = xmlcontents.replace('%M1_X3_DESCRIPTION%',m1_x3_desc)
                xmlcontents = xmlcontents.replace('%FID_THRESHOLD_BASINFEATURENAME%',fid_strm_thresh_feat_desc)
                xmlcontents = xmlcontents.replace('%FID_THRESHOLD_SEGMENTFEATURENAME%',fid_basin_thresh_feat_desc)

                xmlcontents = xmlcontents.replace('%RAINACCATP_VARNAME%',rainaccatp_varname)
                xmlcontents = xmlcontents.replace('%RAININTATP_VARNAME%',rainintatp_varname)
                xmlcontents = xmlcontents.replace('%RAINACCATP_DESC%',rainaccatp_desc)
                xmlcontents = xmlcontents.replace('%RAININTATP_DESC%',rainintatp_desc)

                xmlcontents = xmlcontents.replace('%RAINACCATP_VARNAME_LEGEND%',rainaccatp_legend_varname)
                xmlcontents = xmlcontents.replace('%RAININTATP_VARNAME_LEGEND%',rainintatp_legend_varname)
                xmlcontents = xmlcontents.replace('%RAINACCATP_LEGEND_DESC%',rainaccatp_legend_desc)
                xmlcontents = xmlcontents.replace('%RAININTATP_LEGEND_DESC%',rainintatp_legend_desc)

                output_file = open(basin_thresh_xml,'w')
                output_file.write(xmlcontents)
                output_file.close()

                os.remove(basin_thresh_raw_xml)

                #arcpy.ImportMetadata_conversion(basin_thresh_xml,'',basin_thresh_feat)


        print('     Generating Metadata for Segment and Basin Predictions of Likelihood and Volume...')
        for dur in lv_duration_list:
            dur_string = str(dur)+'min'
            dur_index = lv_duration_list.index(dur)

            m1_r_desc = str.replace(m1_r_raw_desc,'XX-minute',str(dur)+'-minute')

            dur_h = dur / 60.0

            p_b_value = p_b_array[dur_index]
            p_c1_value = p_c1_array[dur_index]
            p_c2_value = p_c2_array[dur_index]
            p_c3_value = p_c3_array[dur_index]

            likelihood_eq = 'X = '+str(p_b_value)+'('+str(p_c1_value)+' * M1_X1 * M1_R) + ('+str(p_c2_value)+' * M1_X2 * M1_R) + ('+str(p_c3_value)+' * M1_X2 * M1_R) '+likelihood_ref

            for acc in accum_list:
                acc_string = str(acc)+'mm'
                acc_index = accum_list.index(acc)

                dur_h = dur / 60.0
                intensity = acc / dur_h
                intensity_string = str(int(intensity))+'mmh'

                strm_pred_feat_name = i+'_Segment_DFPredictions_'+dur_string+'_'+intensity_string
                strm_pred_feat = os.path.join(modelcalcs_gdb,strm_pred_feat_name)

                strm_pred_feat_wgs = os.path.join(modelcalcs_web_gdb,strm_pred_feat_name )

                basin_pred_feat_name = i+'_Basin_DFPredictions_'+dur_string+'_'+intensity_string
                basin_pred_feat = os.path.join(modelcalcs_gdb,basin_pred_feat_name)

                strm_pred_raw_xml_name = strm_pred_feat_name+'_raw.xml'
                strm_pred_raw_xml = os.path.join(estimates_xml_dir,strm_pred_raw_xml_name)

                strm_pred_xml_name = strm_pred_feat_name+'.xml'
                strm_pred_xml = os.path.join(estimates_xml_dir,strm_pred_xml_name)

                strm_desc_wgs = arcpy.Describe(strm_thresh_feat_wgs)
                strm_lat_top_dd_value = strm_desc_wgs.Extent.YMax
                strm_lat_bottom_dd_value = strm_desc_wgs.Extent.YMin
                strm_lon_left_dd_value = strm_desc_wgs.Extent.XMin
                strm_lon_right_dd_value = strm_desc_wgs.Extent.XMax

                lat_top_dd = str('%.4f' % strm_lat_top_dd_value)
                lat_bottom_dd = str('%.4f' % strm_lat_bottom_dd_value)
                lon_left_dd = str('%.4f' % strm_lon_left_dd_value)
                lon_right_dd = str('%.4f' % strm_lon_right_dd_value)


                strm_desc_utm = arcpy.Describe(strm_pred_feat)
                strm_desc_utm_sr = strm_desc_utm.spatialReference
                utm_name_full = str(strm_desc_utm_sr.name)
                utm_zone_string = str.replace(utm_name_full,'NAD_1983_UTM_Zone_','')
                utm_zone_string = str.replace(utm_zone_string,'N','')

                basin_pred_raw_xml_name = basin_pred_feat_name+'_raw.xml'
                basin_pred_raw_xml = os.path.join(estimates_xml_dir,basin_pred_raw_xml_name)

                basin_pred_xml_name = basin_pred_feat_name+'.xml'
                basin_pred_xml = os.path.join(estimates_xml_dir,basin_pred_xml_name)

                fid_strm_feat = 'FID_'+strm_pred_feat_name
                fid_basin_feat = 'FID_'+basin_pred_feat_name

                shutil.copy(strm_pred_template_xml,strm_pred_raw_xml)

                input_file = open(strm_pred_raw_xml)
                xmlcontents = input_file.read()
                input_file.close()

                xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
                xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
                xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
                xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
                xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
                xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
                xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
                xmlcontents = xmlcontents.replace('%DFPREDICTION_FEATURENAME%',strm_pred_feat_name)
                xmlcontents = xmlcontents.replace('%FID_STREAMFEAT%',fid_strm_feat)
                xmlcontents = xmlcontents.replace('%FID_BASINFEAT%',fid_basin_feat)
                xmlcontents = xmlcontents.replace('%M1_X1_DESCRIPTION%',m1_x1_desc)
                xmlcontents = xmlcontents.replace('%M1_X2_DESCRIPTION%',m1_x2_desc)
                xmlcontents = xmlcontents.replace('%M1_X3_DESCRIPTION%',m1_x3_desc)
                xmlcontents = xmlcontents.replace('%V_X1_DESCRIPTION%',v_x1_desc)
                xmlcontents = xmlcontents.replace('%V_X2_DESCRIPTION%',v_x2_desc)
                xmlcontents = xmlcontents.replace('%M1_R_DESCRIPTION%',m1_r_desc)
                xmlcontents = xmlcontents.replace('%V_X3_DESCRIPTIO%N',v_x3_desc)
                xmlcontents = xmlcontents.replace('%LIKELIHOOD_LINKFUNCTION%',likelihood_eq)
                xmlcontents = xmlcontents.replace('%VOLUME_EQUATION%',vol_eq)

                output_file = open(strm_pred_xml,'w')
                output_file.write(xmlcontents)
                output_file.close()

                os.remove(strm_pred_raw_xml)

                #arcpy.ImportMetadata_conversion(strm_pred_xml,'',strm_pred_feat)


                # BASIN PREDICTIONS

                shutil.copy(basin_pred_template_xml,basin_pred_raw_xml)

                input_file = open(basin_pred_raw_xml)
                xmlcontents = input_file.read()
                input_file.close()

                xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
                xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
                xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
                xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
                xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
                xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
                xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
                xmlcontents = xmlcontents.replace('%DFPREDICTION_FEATURENAME%',basin_pred_feat_name)
                xmlcontents = xmlcontents.replace('%FID_STREAMFEAT%',fid_strm_feat)
                xmlcontents = xmlcontents.replace('%FID_BASINFEAT%',fid_basin_feat)
                xmlcontents = xmlcontents.replace('%M1_X1_DESCRIPTION%',m1_x1_desc)
                xmlcontents = xmlcontents.replace('%M1_X2_DESCRIPTION%',m1_x2_desc)
                xmlcontents = xmlcontents.replace('%M1_X3_DESCRIPTION%',m1_x3_desc)
                xmlcontents = xmlcontents.replace('%V_X1_DESCRIPTION%',v_x1_desc)
                xmlcontents = xmlcontents.replace('%V_X2_DESCRIPTION%',v_x2_desc)
                xmlcontents = xmlcontents.replace('%M1_R_DESCRIPTION%',m1_r_desc)
                xmlcontents = xmlcontents.replace('%V_X3_DESCRIPTIO%N',v_x3_desc)
                xmlcontents = xmlcontents.replace('%LIKELIHOOD_LINKFUNCTION%',likelihood_eq)
                xmlcontents = xmlcontents.replace('%VOLUME_EQUATION%',vol_eq)

                output_file = open(basin_pred_xml,'w')
                output_file.write(xmlcontents)
                output_file.close()

                os.remove(basin_pred_raw_xml)

                #arcpy.ImportMetadata_conversion(basin_pred_xml,'',basin_pred_feat)

    else:
        print('     Not Generating Metadata...')

        # PERIMETER

        perim_xml_name = perim_feat_name+'.xml'
        perim_xml = os.path.join(estimates_xml_dir,perim_xml_name)

        perim_raw_xml_name = perim_feat_name+'_raw.xml'
        perim_raw_xml = os.path.join(workingdir,perim_raw_xml_name)

        shutil.copy(perim_template_xml,perim_raw_xml)

        input_file = open(perim_raw_xml)
        xmlcontents = input_file.read()
        input_file.close()

        xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
        xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
        xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
        xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
        xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
        xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
        xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
        xmlcontents = xmlcontents.replace('%PERIMFEATNAME%',perim_feat_name)

        output_file = open(perim_xml,'w')
        output_file.write(xmlcontents)
        output_file.close()

        os.remove(perim_raw_xml)

        #arcpy.ImportMetadata_conversion(perim_xml,'',perim_feat)

        perim_xml_thresh = os.path.join(threshold_xml_dir,perim_xml_name)
        shutil.copy(perim_xml,perim_xml_thresh)


        # extent
        extentbox_feat_name = i+'_analysis_extent_feat'
        extentbox_feat = os.path.join(firein_gdb,extentbox_feat_name)

        extent_xml_name = extentbox_feat_name+'.xml'
        extent_xml = os.path.join(estimates_xml_dir,extent_xml_name)

        extent_raw_xml_name = perim_feat_name+'_raw.xml'
        extent_raw_xml = os.path.join(workingdir,extent_raw_xml_name)

        shutil.copy(extent_template_xml,extent_raw_xml)

        input_file = open(extent_raw_xml)
        xmlcontents = input_file.read()
        input_file.close()

        xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
        xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
        xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
        xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
        xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
        xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
        xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
        xmlcontents = xmlcontents.replace('%PERIMFEATNAME%',perim_feat_name)

        output_file = open(extent_xml,'w')
        output_file.write(xmlcontents)
        output_file.close()

        os.remove(extent_raw_xml)

        #arcpy.ImportMetadata_conversion(extent_xml,'',extentbox_feat)

        extent_xml_thresh = os.path.join(threshold_xml_dir,extent_xml_name)
        shutil.copy(extent_xml,extent_xml_thresh)

        # BASIN OUTLET

        basinpt_xml_name = basinpt_feat_name+'.xml'
        basinpt_xml = os.path.join(estimates_xml_dir,basinpt_xml_name)

        basinpt_raw_xml_name = basinpt_feat_name+'_raw.xml'
        basinpt_raw_xml = os.path.join(workingdir,basinpt_raw_xml_name)

        shutil.copy(basinpt_template_xml,basinpt_raw_xml)

        input_file = open(basinpt_raw_xml)
        xmlcontents = input_file.read()
        input_file.close()

        xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
        xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
        xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
        xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
        xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
        xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
        xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
        xmlcontents = xmlcontents.replace('%BASINPTFEATNAME%',basinpt_feat_name)

        output_file = open(basinpt_xml,'w')
        output_file.write(xmlcontents)
        output_file.close()

        os.remove(basinpt_raw_xml)

        #arcpy.ImportMetadata_conversion(basinpt_xml,'',basinpt_feat)

        basinpt_xml_thresh = os.path.join(threshold_xml_dir,basinpt_xml_name)
        shutil.copy(basinpt_xml,basinpt_xml_thresh)

        # CENTROID

        centroid_xml_name = centroid_feat_name+'.xml'
        centroid_xml = os.path.join(estimates_xml_dir,centroid_xml_name)

        centroid_raw_xml_name = centroid_feat_name+'_raw.xml'
        centroid_raw_xml = os.path.join(workingdir,centroid_raw_xml_name)

        shutil.copy(centroid_template_xml,centroid_raw_xml)

        input_file = open(centroid_raw_xml)
        xmlcontents = input_file.read()
        input_file.close()

        xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
        xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
        xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
        xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
        xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
        xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
        xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
        xmlcontents = xmlcontents.replace('%CENTROIDFEATNAME%',centroid_feat_name)

        output_file = open(centroid_xml,'w')
        output_file.write(xmlcontents)
        output_file.close()

        os.remove(centroid_raw_xml)

        #arcpy.ImportMetadata_conversion(centroid_xml,'',centroid_feat)

        centroid_xml_thresh = os.path.join(threshold_xml_dir,centroid_xml_name)
        shutil.copy(centroid_xml,centroid_xml_thresh)

        # DEBRIS BASINS

        if arcpy.Exists(db_feat):

            db_xml_name = db_feat_name+'.xml'
            db_xml = os.path.join(estimates_xml_dir,db_xml_name)

            db_raw_xml_name = db_feat_name+'_raw.xml'
            db_raw_xml = os.path.join(workingdir,db_raw_xml_name)

            shutil.copy(db_template_xml,db_raw_xml)

            input_file = open(db_raw_xml)
            xmlcontents = input_file.read()
            input_file.close()

            xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
            xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
            xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
            xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
            xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
            xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
            xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
            xmlcontents = xmlcontents.replace('%DBFEATNAME%',db_feat_name)

            output_file = open(db_xml,'w')
            output_file.write(xmlcontents)
            output_file.close()

            os.remove(db_raw_xml)

            #arcpy.ImportMetadata_conversion(db_xml,'',db_feat)

            db_xml_thresh = os.path.join(threshold_xml_dir,db_xml_name)
            shutil.copy(db_xml,db_xml_thresh)

        # WATCHSTREAMS

        if arcpy.Exists(watchstream_feat):

            watchstream_xml_name = watchstream_feat_name+'.xml'
            watchstream_xml = os.path.join(estimates_xml_dir,watchstream_xml_name)

            watchstream_raw_xml_name = watchstream_feat_name+'_raw.xml'
            watchstream_raw_xml = os.path.join(workingdir,watchstream_raw_xml_name)

            shutil.copy(watchstream_template_xml,watchstream_raw_xml)

            input_file = open(watchstream_raw_xml)
            xmlcontents = input_file.read()
            input_file.close()

            xmlcontents = xmlcontents.replace('%ANALYSISDATE_YYYYMMDD%',analysis_date)
            xmlcontents = xmlcontents.replace('%FIRENAMEABBREV%',i)
            xmlcontents = xmlcontents.replace('%LON_LEFT_DD%',lon_left_dd)
            xmlcontents = xmlcontents.replace('%LON_RIGHT_DD%',lon_right_dd)
            xmlcontents = xmlcontents.replace('%LAT_TOP_DD%',lat_top_dd)
            xmlcontents = xmlcontents.replace('%LAT_BOTTOM_DD%',lat_bottom_dd)
            xmlcontents = xmlcontents.replace('%UTMZONE%',utm_zone_string)
            xmlcontents = xmlcontents.replace('%WATCHSTREAMFEATNAME%',watchstream_feat_name)

            output_file = open(watchstream_xml,'w')
            output_file.write(xmlcontents)
            output_file.close()

            os.remove(watchstream_raw_xml)

            #arcpy.ImportMetadata_conversion(watchstream_xml,'',watchstream_feat)

            watchstream_xml_thresh = os.path.join(threshold_xml_dir,watchstream_xml_name)
            shutil.copy(watchstream_xml,watchstream_xml_thresh)

    error_log_list = glob.glob('*.log')

    for error_log in error_log_list:
        os.remove(error_log)


    else: pass

    # WRITE THRESHOLD GUIDANCE

    if generate_threshguide == 'YES':
        print('     Determining Threshold Guidance...')
        basin_threshold_text_name = i+'_ThresholdGuidance_Basin.txt'
        basin_threshold_text = os.path.join(workingdir,basin_threshold_text_name)
        basin_threshold_text_backup = os.path.join(backup_dir,basin_threshold_text_name)
        basin_threshold_text_backup_main = os.path.join(backup_main_dir,basin_threshold_text_name)

        segment_threshold_text_name = i+'_ThresholdGuidance_Segment.txt'
        segment_threshold_text = os.path.join(workingdir,segment_threshold_text_name)
        segment_threshold_text_backup = os.path.join(backup_dir,segment_threshold_text_name)
        segment_threshold_text_backup_main = os.path.join(backup_main_dir,segment_threshold_text_name)

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


        basin_t_df = pd.read_csv(basin_threshold_text)
        segment_t_df = pd.read_csv(segment_threshold_text)

        basin_t_array = np.array(basin_t_df)
        segment_t_array = np.array(segment_t_df)

        duration_min_col_idx = basin_t_df.columns.get_loc(duration_min_colheader)
        thresh_p_col_idx = basin_t_df.columns.get_loc(thresh_p_colheader)
        thresh_int_SI_col_idx = basin_t_df.columns.get_loc(thresh_int_SI_colheader)
        thresh_acc_ENG_col_idx  = basin_t_df.columns.get_loc(thresh_acc_ENG_colheader)
        ri_col_idx = basin_t_df.columns.get_loc(ri_col_header)

        yr1_p100 = int(yr1_p * 100)
        yr2_p100 = int(yr2_p * 100)

        yr1_p_idx = p_value_list.index(yr1_p)
        yr2_p_idx = p_value_list.index(yr2_p)

        for dur in threshold_duration_list:
            dur_idx = threshold_duration_list.index(dur)

            basin_dur_rows = basin_t_array[basin_t_array[:,duration_min_col_idx]==dur]

            basin_t_y1_SI = basin_dur_rows[yr1_p_idx,thresh_int_SI_col_idx]
            basin_t_y1_ENG = basin_dur_rows[yr1_p_idx,thresh_acc_ENG_col_idx]
            basin_t_y1_RI = basin_dur_rows[yr1_p_idx,ri_col_idx]

            basin_t_y2_SI = basin_dur_rows[yr2_p_idx,thresh_int_SI_col_idx]
            basin_t_y2_ENG = basin_dur_rows[yr2_p_idx,thresh_acc_ENG_col_idx]
            basin_t_y2_RI = basin_dur_rows[yr2_p_idx,ri_col_idx]

            basin_threshold_y1_email_list_SI.append(str(basin_t_y1_SI))
            basin_threshold_y1_email_list_ENG.append(str(basin_t_y1_ENG))
            basin_threshold_y1_email_list_RI.append(str(basin_t_y1_RI))

            basin_threshold_y2_email_list_SI.append(str(basin_t_y2_SI))
            basin_threshold_y2_email_list_ENG.append(str(basin_t_y2_ENG))
            basin_threshold_y2_email_list_RI.append(str(basin_t_y2_RI))


            segment_dur_rows = segment_t_array[segment_t_array[:,duration_min_col_idx]==dur]

            segment_t_y1_SI = segment_dur_rows[yr1_p_idx,thresh_int_SI_col_idx]
            segment_t_y1_ENG = segment_dur_rows[yr1_p_idx,thresh_acc_ENG_col_idx]
            segment_t_y1_RI = segment_dur_rows[yr1_p_idx,ri_col_idx]

            segment_t_y2_SI = segment_dur_rows[yr2_p_idx,thresh_int_SI_col_idx]
            segment_t_y2_ENG = segment_dur_rows[yr2_p_idx,thresh_acc_ENG_col_idx]
            segment_t_y2_RI = segment_dur_rows[yr2_p_idx,ri_col_idx]

            segment_threshold_y1_email_list_SI.append(str(segment_t_y1_SI))
            segment_threshold_y1_email_list_ENG.append(str(segment_t_y1_ENG))
            segment_threshold_y1_email_list_RI.append(str(segment_t_y1_RI))

            segment_threshold_y2_email_list_SI.append(str(segment_t_y2_SI))
            segment_threshold_y2_email_list_ENG.append(str(segment_t_y2_ENG))
            segment_threshold_y2_email_list_RI.append(str(segment_t_y2_RI))


        if server_copy == 'YES':

            nws_guidance_file_name = 'USGS_DFThresholdGuidance_All.xlsx'
            nws_guidance_file = os.path.join(nws_server_dir,nws_guidance_file_name)
            nws_guidance_new_file_name = 'USGS_DFThresholdGuidance_All_'+str(yearstr)+str(monthstr)+str(daystr)+'_'+str(hour)+str(minute)+'.xlsx'
            nws_guidance_new_file = os.path.join(nws_server_dir,nws_guidance_new_file_name)
            nws_guidance_backup_file_name = 'USGS_DFThresholdGuidance_All_PriorTo'+str(yearstr)+str(monthstr)+str(daystr)+'_'+str(hour)+str(minute)+'Edits.xlsx'
            nws_guidance_backup_file = os.path.join(nws_server_backup_dir,nws_guidance_backup_file_name)

            shutil.copyfile(nws_guidance_file,nws_guidance_backup_file)

            fire_guidance_file_name = i+'_DFThresholdGuidance_ForNWS_'+guidance_scale+'.txt'
            fire_guidance_file = os.path.join(workingdir,fire_guidance_file_name)
            fire_guidance_backup_file = os.path.join(backup_dir,fire_guidance_file_name)
            fire_guidance_xlsx_file_name = i+'_DFThresholdGuidance_ForNWS_'+str(yearstr)+str(monthstr)+str(daystr)+'_'+str(hour)+str(minute)+'.xlsx'
            fire_guidance_xlsx_file = os.path.join(workingdir,fire_guidance_xlsx_file_name)
            fire_guidance_xlsx_backup_file = os.path.join(backup_dir,fire_guidance_xlsx_file_name)

            nws_contact_file_name = i+'_NWSContacts.txt'
            nws_contact_file = os.path.join(workingdir,nws_contact_file_name)
            nws_contact_backup_file = os.path.join(backup_dir,nws_contact_file_name)

            df = pd.read_excel(nws_guidance_file)
            firedf = pd.read_csv(fire_guidance_file)
            df2 = pd.concat([df,firedf],sort=False)

            df2.to_excel(nws_guidance_new_file)

            firedf.to_excel(fire_guidance_xlsx_file)

            os.remove(nws_guidance_file)
            shutil.copyfile(nws_guidance_new_file,nws_guidance_file)
            shutil.copyfile(nws_guidance_file,os.path.join(nws_server_backup_dir,nws_guidance_file_name))

    # GENERATE METADATA
    # COPY AND PROJECT BASE DATA

    if project_web == 'YES':

        print('     Copying and Projecting Base Data for Distribution...')

        wgs_web_ref_feat = os.path.join(server_dir,'ProjectionData.gdb','UTMZones_Feat_WGS84_WebMercator')
        ref_wgs= arcpy.Describe(wgs_web_ref_feat)
        wgs_spatial_ref = ref_wgs.SpatialReference

        def project_basedata(in_feat,out_feat_name,out_feat_gdb,spatial_ref):
            out_feat = os.path.join(out_feat_gdb,out_feat_name)
            arcpy.Project_management(in_feat,out_feat,spatial_ref)

        extentbox_feat_name = i+'_analysis_extent_feat'
        extentbox_feat = os.path.join(firein_gdb,extentbox_feat_name)
        extentbox_feat_utm = os.path.join(modelcalcs_gdb,extentbox_feat_name)
        extentbox_feat_threshold_utm = os.path.join(threshold_utm_gdb,extentbox_feat_name)
        arcpy.CopyFeatures_management(extentbox_feat,extentbox_feat_utm)
        arcpy.CopyFeatures_management(extentbox_feat,extentbox_feat_threshold_utm)
        project_basedata(extentbox_feat,extentbox_feat_name,modelcalcs_web_gdb,wgs_spatial_ref)
        project_basedata(extentbox_feat,extentbox_feat_name,threshold_wgs_gdb,wgs_spatial_ref)


        perim_feat_name = i+'_perim_feat'
        perim_feat = os.path.join(firein_gdb,perim_feat_name)
        perim_feat_utm = os.path.join(modelcalcs_gdb,perim_feat_name)
        perim_feat_threshold_utm = os.path.join(threshold_utm_gdb,perim_feat_name)
        arcpy.CopyFeatures_management(perim_feat,perim_feat_utm)
        arcpy.CopyFeatures_management(perim_feat,perim_feat_threshold_utm)
        project_basedata(perim_feat,perim_feat_name,modelcalcs_web_gdb,wgs_spatial_ref)
        project_basedata(perim_feat,perim_feat_name,threshold_wgs_gdb,wgs_spatial_ref)


        centroid_feat_name = i+'_centroid_feat'
        centroid_feat = os.path.join(firein_gdb,centroid_feat_name)
        centroid_feat_utm = os.path.join(modelcalcs_gdb,centroid_feat_name)
        centroid_feat_threshold_utm = os.path.join(threshold_utm_gdb,centroid_feat_name)
        arcpy.CopyFeatures_management(centroid_feat,centroid_feat_utm)
        arcpy.CopyFeatures_management(centroid_feat,centroid_feat_threshold_utm)
        project_basedata(centroid_feat,centroid_feat_name,modelcalcs_web_gdb,wgs_spatial_ref)
        project_basedata(centroid_feat,centroid_feat_name,threshold_wgs_gdb,wgs_spatial_ref)

        basinpt_feat_name = i+"_basinpt_feat"
        basinpt_feat = os.path.join(firein_gdb,basinpt_feat_name)
        basinpt_feat_utm = os.path.join(modelcalcs_gdb,basinpt_feat_name)
        basinpt_feat_threshold_utm = os.path.join(threshold_utm_gdb,basinpt_feat_name)
        arcpy.CopyFeatures_management(basinpt_feat,basinpt_feat_utm)
        arcpy.CopyFeatures_management(basinpt_feat,basinpt_feat_threshold_utm)
        project_basedata(basinpt_feat,basinpt_feat_name,modelcalcs_web_gdb,wgs_spatial_ref)
        project_basedata(basinpt_feat,basinpt_feat_name,threshold_wgs_gdb,wgs_spatial_ref)


        db_feat_name = i+'_db_feat'
        db_feat = os.path.join(firein_gdb,db_feat_name)
        if arcpy.Exists(db_feat):
            db_check = 'Yes'
            db_feat_utm = os.path.join(modelcalcs_gdb,db_feat_name)
            db_feat_threshold_utm = os.path.join(threshold_utm_gdb,db_feat_name)
            arcpy.CopyFeatures_management(db_feat,db_feat_utm)
            arcpy.CopyFeatures_management(db_feat,db_feat_threshold_utm)
            project_basedata(db_feat,db_feat_name,modelcalcs_web_gdb,wgs_spatial_ref)
            project_basedata(db_feat,db_feat_name,threshold_wgs_gdb,wgs_spatial_ref)

        else:
            db_check = 'No'

        watchstream_feat_name = i+'_watchstream_feat'
        watchstream_feat = os.path.join(firein_gdb,watchstream_feat_name)
        if arcpy.Exists(watchstream_feat):
            watch_stream_check = 'Yes'
            arcpy.AddField_management(watchstream_feat,'WS_ID','SHORT')
            arcpy.CalculateField_management(watchstream_feat,'WS_ID',1,'PYTHON')
            watchstream_feat_utm = os.path.join(modelcalcs_gdb,watchstream_feat_name)
            watchstream_feat_threshold_utm = os.path.join(threshold_utm_gdb,watchstream_feat_name)
            arcpy.CopyFeatures_management(watchstream_feat,watchstream_feat_utm)
            arcpy.CopyFeatures_management(watchstream_feat,watchstream_feat_threshold_utm)
            project_basedata(watchstream_feat,watchstream_feat_name,modelcalcs_web_gdb,wgs_spatial_ref)
            project_basedata(watchstream_feat,watchstream_feat_name,threshold_wgs_gdb,wgs_spatial_ref)
        else:
            watch_stream_check = 'No'

    else: pass

    # SPLIT THRESHOLDS..........................................................

    if split_thresholds == 'YES':

        print('     Splitting Threshold Data into Individual Geodatabases By Duration...')
        for threshold_split_duration in threshold_duration_list:
            threshold_split_duration_string = str(threshold_split_duration)+'min'
            print('         Duration = '+threshold_split_duration_string+'...')

            split_threshold_utm_gdb_name = i+'_threshold_'+str(threshold_split_duration)+'min_utm.gdb'
            split_threshold_utm_gdb = os.path.join(workingdir,split_threshold_utm_gdb_name)
            if not os.path.exists (split_threshold_utm_gdb): arcpy.CreateFileGDB_management(workingdir, split_threshold_utm_gdb_name, "CURRENT")    # Create File Geodatabase

            perim_feat_split_threshold_utm = os.path.join(split_threshold_utm_gdb,perim_feat_name)
            centroid_feat_split_threshold_utm = os.path.join(split_threshold_utm_gdb,centroid_feat_name)
            basinpt_feat_split_threshold_utm = os.path.join(split_threshold_utm_gdb,basinpt_feat_name)
            if arcpy.Exists(db_feat):
                db_feat_split_threshold_utm = os.path.join(split_threshold_utm_gdb,db_feat_name)
            watchstream_feat_split_threshold_utm = os.path.join(split_threshold_utm_gdb,watchstream_feat_name)

            arcpy.CopyFeatures_management(perim_feat_threshold_utm,perim_feat_split_threshold_utm)
            arcpy.CopyFeatures_management(centroid_feat_threshold_utm,centroid_feat_split_threshold_utm)
            arcpy.CopyFeatures_management(basinpt_feat_threshold_utm,basinpt_feat_split_threshold_utm)
            if arcpy.Exists(db_feat):
                arcpy.CopyFeatures_management(db_feat_threshold_utm,db_feat_split_threshold_utm)
            arcpy.CopyFeatures_management(watchstream_feat_threshold_utm,watchstream_feat_split_threshold_utm)
##            for acc in accum_list:
##                acc_string = str(acc)+'mm'
##                acc_index = accum_list.index(acc)

            arcpy.env.workspace = threshold_utm_gdb
            fcs = arcpy.ListFeatureClasses()
            for fc in fcs:
                fc_name = fc
                if threshold_split_duration_string in fc_name:
                    out_fc = os.path.join(split_threshold_utm_gdb,fc_name)
                    arcpy.CopyFeatures_management(fc,out_fc)
            arcpy.env.workspace = workingdir


    # ZIP GDBS..................................................................

    if zip_gdbs == 'YES':

        print('     Zipping Geodatabases...')

        firein_zip_name = str.replace(firein_gdb_name,'gdb','zip')
        firein_zip = os.path.join(workingdir,firein_zip_name)
        firein_zip_backup = os.path.join(backup_dir,firein_zip_name)
        firein_zip_backup_main = os.path.join(backup_main_dir,firein_zip_name)
        if os.path.exists(firein_zip_backup_main):
            os.remove(firein_zip_backup_main)

        modelcalcs_zip_name = str.replace(modelcalcs_gdb_name,'gdb','zip')
        modelcalcs_zip = os.path.join(workingdir,modelcalcs_zip_name)
        modelcalcs_zip_backup = os.path.join(backup_dir,modelcalcs_zip_name)
        modelcalcs_zip_backup_main = os.path.join(backup_main_dir,modelcalcs_zip_name)
        if os.path.exists(modelcalcs_zip_backup_main):
            os.remove(modelcalcs_zip_backup_main)


        modelcalcs_web_zip_name = str.replace(modelcalcs_web_gdb_name,'gdb','zip')
        modelcalcs_web_zip = os.path.join(workingdir,modelcalcs_web_zip_name)
        modelcalcs_web_zip_backup = os.path.join(backup_webdir,modelcalcs_web_zip_name)
        modelcalcs_web_zip_backup_main = os.path.join(backup_main_dir,modelcalcs_web_zip_name)
        if os.path.exists(modelcalcs_web_zip_backup_main):
            os.remove(modelcalcs_web_zip_backup_main)

        webdownload_zip_name = 'PostFireDebrisFlowEstimates.zip'
        webdownload_zip = os.path.join(workingdir,webdownload_zip_name)
        webdownload_zip_backup = os.path.join(backup_webdir,webdownload_zip_name)
        webdownload_zip_backup_main = os.path.join(backup_main_webdir,webdownload_zip_name)
        if os.path.exists(webdownload_zip_backup_main):
            os.remove(webdownload_zip_backup_main)


        verification_zip_name = str.replace(verification_gdb_name,'gdb','zip')
        verification_zip = os.path.join(workingdir,verification_zip_name)
        verification_zip_backup = os.path.join(backup_dir,verification_zip_name)
        verification_zip_backup_main = os.path.join(backup_main_dir,verification_zip_name)
        if os.path.exists(verification_zip_backup_main):
            os.remove(verification_zip_backup_main)


        threshold_utm_zip_name = str.replace(threshold_utm_gdb_name,'gdb','zip')
        threshold_utm_zip = os.path.join(workingdir,threshold_utm_zip_name)
        threshold_utm_zip_backup = os.path.join(backup_dir,threshold_utm_zip_name)
        threshold_utm_zip_backup_main = os.path.join(backup_main_dir,threshold_utm_zip_name)
        if os.path.exists(threshold_utm_zip_backup_main):
            os.remove(threshold_utm_zip_backup_main)


        threshold_wgs_zip_name = str.replace(threshold_wgs_gdb_name,'gdb','zip')
        threshold_wgs_zip = os.path.join(workingdir,threshold_wgs_zip_name)
        threshold_wgs_zip_backup = os.path.join(backup_webdir,threshold_wgs_zip_name)
        threshold_wgs_zip_backup_main = os.path.join(backup_main_webdir,threshold_wgs_zip_name)
        if os.path.exists(threshold_wgs_zip_backup_main):
            os.remove(threshold_wgs_zip_backup_main)

        DFTools_ArcGIS.ZipGDB(firein_gdb,firein_zip)
        DFTools_ArcGIS.ZipGDB(modelcalcs_gdb,modelcalcs_zip)
        DFTools_ArcGIS.ZipGDB(modelcalcs_web_gdb,modelcalcs_web_zip)
        DFTools_ArcGIS.ZipGDB(verification_gdb,verification_zip)
        DFTools_ArcGIS.ZipGDB(threshold_utm_gdb,threshold_utm_zip)
        DFTools_ArcGIS.ZipGDB(threshold_wgs_gdb,threshold_wgs_zip)

        if split_thresholds == 'YES':
            for threshold_split_duration in threshold_duration_list:
                threshold_split_duration_string = str(threshold_split_duration)+'min'

                split_threshold_utm_gdb_name = i+'_threshold_'+str(threshold_split_duration)+'min_utm.gdb'
                split_threshold_utm_gdb = os.path.join(workingdir,split_threshold_utm_gdb_name)
                split_threshold_utm_zip_name = str.replace(split_threshold_utm_gdb_name,'.gdb','.zip')
                split_threshold_utm_zip = os.path.join(workingdir,split_threshold_utm_zip_name)
                DFTools_ArcGIS.ZipGDB(split_threshold_utm_gdb,split_threshold_utm_zip)

    else: pass


    # Export Shapefiles....................................................

    if make_shapefile == 'YES':

        print('     Exporting Shapefiles...')

        shapedir_name = i+"_shapefiles"
        shapedir = os.path.join(workingdir,shapedir_name)
        if not os.path.exists (shapedir): os.mkdir(shapedir)

        arcpy.env.workspace = modelcalcs_gdb
        feat_list_utm = arcpy.ListFeatureClasses()

        for feat_utm in feat_list_utm:
            out_shp_name = str(feat_utm+'.shp')
            out_shp = os.path.join(shapedir,out_shp_name)
            if arcpy.Exists(out_shp):
                arcpy.Delete_management(out_shp)
            arcpy.FeatureClassToShapefile_conversion(feat_utm,shapedir)

            if generate_meta == 'YES':

                in_xml_name = str(feat_utm+'.xml')
                in_xml = os.path.join(estimates_xml_dir,in_xml_name)
                out_xml_name = str(feat_utm+'.shp.xml')
                out_xml = os.path.join(shapedir,out_xml_name)
                if os.path.exists(in_xml):
                    shutil.copy(in_xml,out_xml)

        arcpy.env.workspace = threshold_utm_gdb
        thresh_list_utm = arcpy.ListFeatureClasses()

        for feat_utm in thresh_list_utm:
            out_shp_name = str(feat_utm+'.shp')
            out_shp = os.path.join(shapedir,out_shp_name)
            if arcpy.Exists(out_shp):
                arcpy.Delete_management(out_shp)
            arcpy.FeatureClassToShapefile_conversion(feat_utm,shapedir)

            if generate_meta == 'YES':

                in_xml_name = str(feat_utm+'.xml')
                in_xml = os.path.join(threshold_xml_dir,in_xml_name)
                out_xml_name = str(feat_utm+'.shp.xml')
                out_xml = os.path.join(shapedir,out_xml_name)

                if os.path.exists(in_xml):
                    shutil.copy(in_xml,out_xml)

        print('     Zipping Shapefiles...')

        shapefiles_zip_name = 'Shapefiles.zip'
        shapefiles_zip = os.path.join(workingdir,shapefiles_zip_name)
        shapefiles_zip_backup = os.path.join(backup_webdir,shapefiles_zip_name)
        shapefiles_zip_backup_main = os.path.join(backup_main_webdir,shapefiles_zip_name)
        if os.path.exists(shapefiles_zip_backup_main):
            os.remove(shapefiles_zip_backup_main)

        shutil.make_archive('Shapefiles','zip',shapedir)

    #ZIP GDBS FOR EXPORT........................................................

    if generate_meta == 'YES' and zip_gdbs == 'YES':

        print('     Adding README and XML files to Zipped Estimates Geodatabase and Shapefiles...')

        readme_name = 'PostFireDFEstimates_README.pdf'
        readme = os.path.join(server_dir,readme_name)

        threshold_readme_name = 'PostFireDFThresholdEstimates_README.pdf'
        threshold_readme = os.path.join(server_dir,threshold_readme_name)


        zipobj = zipfile.ZipFile(modelcalcs_zip,'a')
        zipobj.write(readme, readme_name,zipfile.ZIP_DEFLATED)
        for infile in glob.glob(estimates_xml_dir+"/*"):
            filename = os.path.basename(infile)
            zipobj.write(infile, os.path.join( os.path.basename(estimates_xml_dir_name), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
        zipobj.close()

        zipobj = zipfile.ZipFile(threshold_utm_zip,'a')
        zipobj.write(threshold_readme, threshold_readme_name,zipfile.ZIP_DEFLATED)
        for infile in glob.glob(threshold_xml_dir+"/*"):
            filename = os.path.basename(infile)
            zipobj.write(infile, os.path.join( os.path.basename(threshold_xml_dir_name), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
        zipobj.close()

        if split_thresholds == 'YES':
            for threshold_split_duration in threshold_duration_list:
                threshold_split_duration_string = str(threshold_split_duration)+'min'
                split_threshold_utm_zip_name = i+'_threshold_'+str(threshold_split_duration)+'min_utm.zip'
                split_threshold_utm_zip= os.path.join(workingdir,split_threshold_utm_zip_name)

                zipobj = zipfile.ZipFile(split_threshold_utm_zip,'a')
                zipobj.write(threshold_readme, threshold_readme_name,zipfile.ZIP_DEFLATED)
                for infile in glob.glob(threshold_xml_dir+"/*"):
                    filename = os.path.basename(infile)
                    zipobj.write(infile, os.path.join( os.path.basename(threshold_xml_dir_name), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
                zipobj.close()

        if make_shapefile == 'YES':
            zipobj = zipfile.ZipFile(shapefiles_zip,'a')
            zipobj.write(readme, readme_name,zipfile.ZIP_DEFLATED)
            zipobj.write(threshold_readme, threshold_readme_name,zipfile.ZIP_DEFLATED)
            zipobj.close()
        else: pass

        zipobj = zipfile.ZipFile(threshold_wgs_zip,'a')
        zipobj.write(threshold_readme, threshold_readme_name,zipfile.ZIP_DEFLATED)
        zipobj.close()

    else: pass


    if generate_threshguide == 'YES'and zip_gdbs == 'YES':
        zipobj = zipfile.ZipFile(threshold_utm_zip,'a')
        zipobj.write(basin_threshold_text, basin_threshold_text_name,zipfile.ZIP_DEFLATED)
        zipobj.write(segment_threshold_text, segment_threshold_text_name,zipfile.ZIP_DEFLATED)
        zipobj.close()

        zipobj = zipfile.ZipFile(shapefiles_zip,'a')
        zipobj.write(basin_threshold_text, basin_threshold_text_name,zipfile.ZIP_DEFLATED)
        zipobj.write(segment_threshold_text, segment_threshold_text_name,zipfile.ZIP_DEFLATED)
        zipobj.close()

        if split_thresholds == 'YES':
            for threshold_split_duration in threshold_duration_list:
                threshold_split_duration_string = str(threshold_split_duration)+'min'
                split_threshold_utm_zip_name = i+'_threshold_'+str(threshold_split_duration)+'min_utm.zip'
                split_threshold_utm_zip= os.path.join(workingdir,split_threshold_utm_zip_name)
                zipobj = zipfile.ZipFile(split_threshold_utm_zip,'a')
                zipobj.write(basin_threshold_text, basin_threshold_text_name,zipfile.ZIP_DEFLATED)
                zipobj.write(segment_threshold_text, segment_threshold_text_name,zipfile.ZIP_DEFLATED)
                zipobj.close()

    else: pass

    # ZIP ESTIMATES AND THRESHOLD SYMBOLOGY......................................

    if zip_symbology == 'YES' and zip_gdbs == 'YES':

        print('     Adding Symbology to Zipped Estimates Geodatabase and Threshold Geodatabases...')

        zipobj = zipfile.ZipFile(modelcalcs_zip,'a')
        for infile in glob.glob(estimates_symbology_dir+"/*"):
            filename = os.path.basename(infile)
            zipobj.write(infile, os.path.join( os.path.basename(estimates_symbology_dir_name), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
        zipobj.close()

        zipobj = zipfile.ZipFile(threshold_utm_zip,'a')
        for infile in glob.glob(threshold_symbology_dir+"/*"):
            filename = os.path.basename(infile)
            zipobj.write(infile, os.path.join( os.path.basename(threshold_symbology_dir_name), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
        zipobj.close()

        if split_thresholds == 'YES':
            for threshold_split_duration in threshold_duration_list:
                threshold_split_duration_string = str(threshold_split_duration)+'min'
                split_threshold_utm_zip_name = i+'_threshold_'+str(threshold_split_duration)+'min_utm.zip'
                split_threshold_utm_zip= os.path.join(workingdir,split_threshold_utm_zip_name)

                zipobj = zipfile.ZipFile(split_threshold_utm_zip,'a')
                for infile in glob.glob(threshold_symbology_dir+"/*"):
                    filename = os.path.basename(infile)
                    zipobj.write(infile, os.path.join( os.path.basename(threshold_symbology_dir_name), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
                zipobj.close()


    if zip_gdbs == 'YES':
        fire_zip_name_string = str.replace(fire_name_full_text,' ','')
        fire_zip_name_string = str.replace(fire_zip_name_string,'FireName=','')

        out_zip_all_name = state_abbrev+'_'+fire_year+'_'+fire_zip_name_string+'_'+i+'_'+str(year)+str(month)+str(day)+'_'+str(hour)+str(minute)+'.zip'
        out_zip_all = os.path.join(workingdir,out_zip_all_name)
        out_zip_all_backup = os.path.join(backup_dir,out_zip_all_name)
        out_zip_all_backup_main = os.path.join(backup_main_dir,out_zip_all_name)
        z = zipfile.ZipFile(out_zip_all, "w")
        z.write(threshold_utm_zip_name)
        z.write(modelcalcs_zip_name)
        z.close()

        zipobj = zipfile.ZipFile(out_zip_all,'a')
        zipobj.write(readme, readme_name,zipfile.ZIP_DEFLATED)
        zipobj.write(threshold_readme, threshold_readme_name,zipfile.ZIP_DEFLATED)
        zipobj.close()

    shutil.copyfile(out_zip_all,webdownload_zip)


    # GENERATE TEXT FILE.........................................................

    if server_copy == 'YES' and make_webtext == 'YES':
        print('     Generating Text File for Web...')

        fire_webinfo = os.path.join(workingdir,i+"_webinfo.txt")
        fire_webinfo_backup = os.path.join(backup_webdir,i+'_webinfo.txt')
        fire_webinfo_backup_main = os.path.join(backup_main_webdir,i+'_webinfo.txt')

        target = open(fire_webinfo,'a')
        target.write("Watch Streams = "+watch_stream_check+'\n')
        target.write('Status = '+status+'\n')
        target.write('Disclaimer = '+disclaimer+'\n')
        target.close()

    else: pass
##
##
##    if server_copy == 'YES' and make_webtext == 'YES':
##        print('     Generating Text File for Web...')
##
##        lat, lon = DFTools_ArcGIS.CentroidLatLon(centroid_feat)
##
##        perim_area_array = arcpy.da.TableToNumPyArray(perim_feat,'Shape_Area')
##        total_area_m2 = perim_area_array["Shape_Area"].sum()
##        total_area_km2 = total_area_m2 / 1000000.0
##
##
##        if arcpy.Exists(db_feat):
##            db_check = 'Yes'
##        else:
##            db_check = 'No'
##
##        fire_webinfo = os.path.join(workingdir,i+"_webinfo.txt")
##        fire_webinfo_backup = os.path.join(backup_dir,i+'_webinfo.txt')
##
##        target = open(fire_webinfo,'wt')
##        target.write("Fire Name = "+fire_name_full+'\n')
##        target.write("Fire Location = "+fire_location+'\n')
##        target.write("Fire Start Date = "+fire_start_date+'\n')
##        target.write("Lat / Lon = "+str(lat)+','+str(lon)+'\n')
##        target.write("Fire Size (km^2) = "+str("%.1f" % total_area_km2)+'\n')
##        target.write("Debris Basins = "+db_check+'\n')
##        target.write("Watch Streams = "+watch_stream_check+'\n')
##        target.close()
##    else: pass
##
##    if server_copy == 'YES' and make_booktext == 'YES':
##
##        print('     Generating Text File for Bookkeeping...')
##        analyst = os.getenv('username')
##        timestamp_gmt = time.strftime('%Y-%m-%d %H:%M:%S', now)
##        fire_bookinfo_name = 'DFAssessment_AnalyzedPerimeters.txt'
##        fire_bookinfo = os.path.join(perim_dir,fire_bookinfo_name)
##        target = open(fire_bookinfo,'a')
##        bookkeep_string = i+','+fire_name_full+','+fire_location+','+fire_start_date+','+str(lat)+'N,'+str(lon)+'W,'+str(int(total_area_km2))+','+timestamp_gmt+','+analyst
##        target.write(bookkeep_string+'\n')
##        target.close()
##
##    else: pass


    if server_copy == 'YES' and append_perim == 'YES':
        print('     Appending Perimeter to AnalyzedPerimeters.gdb...')

        append_perim_feat_name = 'DFAssessment_Perims_'+str(fire_year)
        append_perim_feat = os.path.join(perim_gdb,append_perim_feat_name)
        add_perim_feat = os.path.join(perim_gdb,perim_feat_name)

        arcpy.CopyFeatures_management(perim_feat,add_perim_feat)

        if arcpy.Exists(append_perim_feat):
            arcpy.Append_management(perim_feat,append_perim_feat,"NO_TEST")
        else:
            arcpy.CopyFeatures_management(perim_feat,append_perim_feat)

    else: pass

    # BACKUP ZIPPED GDBS

    if server_copy == 'YES':
        if zip_gdbs == 'YES':
            print('     Backing Up Zipped Data to Server Address: '+backup_dir+'...')
            shutil.copyfile(firein_zip,firein_zip_backup)
            shutil.copyfile(firein_zip,firein_zip_backup_main)

            shutil.copyfile(modelcalcs_zip,modelcalcs_zip_backup)
            shutil.copyfile(modelcalcs_zip,modelcalcs_zip_backup_main)

            shutil.copyfile(threshold_utm_zip,threshold_utm_zip_backup)
            shutil.copyfile(threshold_utm_zip,threshold_utm_zip_backup_main)

            shutil.copyfile(out_zip_all,out_zip_all_backup)
            shutil.copyfile(out_zip_all,out_zip_all_backup_main)

            if project_web == 'YES':
                shutil.copyfile(modelcalcs_web_zip,modelcalcs_web_zip_backup)
                shutil.copyfile(modelcalcs_web_zip,modelcalcs_web_zip_backup_main)

                shutil.copyfile(threshold_wgs_zip,threshold_wgs_zip_backup)
                shutil.copyfile(threshold_wgs_zip,threshold_wgs_zip_backup_main)

                if zip_gdbs == 'YES':
                    shutil.copyfile(webdownload_zip,webdownload_zip_backup)
                    shutil.copyfile(webdownload_zip,webdownload_zip_backup_main)

                else: pass
            else: pass
            if make_shapefile == 'YES':
                shutil.copyfile(shapefiles_zip,shapefiles_zip_backup)
                shutil.copyfile(shapefiles_zip,shapefiles_zip_backup_main)
            else: pass
            if make_webtext == 'YES':
                shutil.copyfile(fire_webinfo,fire_webinfo_backup)
                shutil.copyfile(fire_webinfo,fire_webinfo_backup_main)
            else: pass
            if generate_threshguide == 'YES':
                shutil.copyfile(basin_threshold_text,basin_threshold_text_backup)
                shutil.copyfile(basin_threshold_text,basin_threshold_text_backup_main)

                shutil.copyfile(segment_threshold_text,segment_threshold_text_backup)
                shutil.copyfile(segment_threshold_text,segment_threshold_text_backup_main)

                shutil.copyfile(fire_guidance_file,fire_guidance_backup_file)
                shutil.copyfile(fire_guidance_xlsx_file,fire_guidance_xlsx_backup_file)

                shutil.copyfile(nws_contact_file,nws_contact_backup_file)

            else: pass

        if split_thresholds == 'YES':
            for threshold_split_duration in threshold_duration_list:
                threshold_split_duration_string = str(threshold_split_duration)+'min'
                split_threshold_utm_zip_name = i+'_Threshold_'+str(threshold_split_duration)+'min_utm.zip'
                split_threshold_utm_zip= os.path.join(workingdir,split_threshold_utm_zip_name)
                split_threshold_utm_zip_backup = os.path.join(backup_dir,split_threshold_utm_zip_name)
                split_threshold_utm_zip_backup_main = os.path.join(backup_main_dir,split_threshold_utm_zip_name)
                shutil.copyfile(split_threshold_utm_zip,split_threshold_utm_zip_backup)
                shutil.copyfile(split_threshold_utm_zip,split_threshold_utm_zip_backup_main)

    else: pass

    if generate_threshguide == 'YES':

        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('')
        print('  Basin-Scale Thresholds for Email Guidance:')
        print('')
        print('   YEAR 1:')
        for dur in threshold_duration_list:
            dur_index = threshold_duration_list.index(dur)
            print('     '+str(dur)+'-minute: '+str(basin_threshold_y1_email_list_SI[dur_index])+' mm/h, or '+str(basin_threshold_y1_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(basin_threshold_y1_email_list_RI[dur_index])+' years')
        print('')
        print('   YEAR 2:')
        for dur in threshold_duration_list:
            dur_index = threshold_duration_list.index(dur)
            print('     '+str(dur)+'-minute: '+str(basin_threshold_y2_email_list_SI[dur_index])+' mm/h, or '+str(basin_threshold_y2_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(basin_threshold_y2_email_list_RI[dur_index])+' years')
        print('')


        print('  Segment-Scale Thresholds for Email Guidance:')
        print('')
        print('   YEAR 1:')
        for dur in threshold_duration_list:
            dur_index = threshold_duration_list.index(dur)
            print('     '+str(dur)+'-minute: '+str(segment_threshold_y1_email_list_SI[dur_index])+' mm/h, or '+str(segment_threshold_y1_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(segment_threshold_y1_email_list_RI[dur_index])+' years')
        print('')

        print('   YEAR 2:')
        for dur in threshold_duration_list:
            dur_index = threshold_duration_list.index(dur)
            print('     '+str(dur)+'-minute: '+str(segment_threshold_y2_email_list_SI[dur_index])+' mm/h, or '+str(segment_threshold_y2_email_list_ENG[dur_index])+' inches in '+str(dur)+' minutes, RI = '+str(segment_threshold_y2_email_list_RI[dur_index])+' years')
        print('')

        if server_copy == 'YES':

            print('  NWS Contact Information')
            print('')

            nws_contact_target = open(nws_contact_file,'r')
            lines = nws_contact_target.readlines()
            for line in lines:
                line = line.replace('\n','')
                print(line)
            nws_contact_target.close()
            print('')

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

print('')
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Step 3 Results:')
print('    Processing Successful')
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('')
