# This step of the code seems to implement the algorithm that determines the
# stream network.

# Import my modules
import notify
import fire
import geodatabase
import parameters
import dftools

# Import external modules
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
from contextlib import contextmanager
import sys, os

# Notify console of current step
notify.step1()

# Create folders
os.mkdir(paths.output)
os.mkdir(paths.backup)
os.mkdir(paths.scratch)
os.mkdir(paths.kernel)

# Set up arcpy.
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('spatial')
arcpy.env.workspace = paths.output
arcpy.env.overwriteOutput = True

# Create logfile
# !!!!!!!!!!!!!!!!! Needs updating
if options.log
    logfile = log.create(working_dir, parameters.logfile)

# Begin processing the fire. Notify console and logfile
notify.processing(fire.id)
if parameters.make_logfile:
    log.write(logfile, fire.id, 'Start Step 1')

# Clear saved variables from ArcPy
arcpy.env.overwriteOutput = True
arcpy.ClearEnvironment("cellSize")
arcpy.ClearEnvironment("extent")
arcpy.ClearEnvironment("snapRaster")
arcpy.ClearEnvironment("mask")
arcpy.env.scratchWorkspace = paths.arcpy_scratch

# !!!!!!!!!!!!!
# Should add overwrite check here

# !!!!!!!!!!!!!
# Check that input files exist and are valid


# CALCULATIONS

# Get UTM zone of the centroid of the fire perimeter
zone = calculate.utmzone(paths.perimeter, paths.dissolved, paths.centroid, 
                         paths.utm, paths.zone)

# Notify console. Get the feature and Describe object for the zone
notify.zone(zone)
utm_feature = os.path.join(paths.projection, f"UTMZone_{zone}_Perim_Feat")
utm_describe = arcpy.Describe(utm_feature)
utm_reference = utm_describe.SpatialReference

# Calculate the box of extent
notify.rectangle()
calculate.extent(paths.perimeter, paths.perimeter_nad83, paths.box_feature,
                utm_reference, paths.box_feature, paths.box_raster, parameters.cellsize)

# Check for a DEM for the fire. Extract one if it does not exist
if arcpy.Exists(paths.firedem):
    notify.dem(exists=True)
else:
    notify.dem(exists=False)
    calculate.dem(paths.perimeter, )


                 
                 





# Extract the DEM if it does not exist
if arcpy.Exists(paths.firedem):
    notify.dem(exist=True)
else:
    notify.dem(exist=False)
    dem.extract(paths.dem, paths.demextent)


# EXTRACT DEM~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # IDENTIFY DEM TILES




        arcpy.Project_management(extentbox_feat,extentbox_dem_ref_feat,dem_ref_sr)

        dem_ref_layer = os.path.join(temp_gdb,dem_ref_feat_name+'.lyr')

        extent_demtiles_feat_name = i+'_extent_demtiles_feat'
        extent_demtiles_feat = os.path.join(temp_gdb,extent_demtiles_feat_name)

        arcpy.MakeFeatureLayer_management(dem_ref_feat,dem_ref_layer)
        arcpy.SelectLayerByLocation_management(dem_ref_layer, "INTERSECT",extentbox_dem_ref_feat,'','NEW_SELECTION')
        arcpy.CopyFeatures_management(dem_ref_layer,extent_demtiles_feat)

        dem_array_import = arcpy.da.TableToNumPyArray(extent_demtiles_feat, ('FILE_ID'))

        ndems = len(dem_array_import)

        dem_array = dem_array_import['FILE_ID']

        dem_list_import = dem_array.tolist()

        dem_list = []

        for dem_string in dem_list_import:
            dem_string2 = str(dem_string)
            dem_list.append(dem_string2)

        print('     Burn area intersects '+str(ndems)+' DEM Tile(s)...')

        for dem_tile in dem_list:

            dem_index = dem_list.index(dem_tile)

            dem_tile_name = str(dem_tile)

            temp_dem_name = i+'_dem_temp'
            temp_dem = os.path.join(temp_gdb,temp_dem_name)

            print('         Processing DEM Tile = '+dem_tile_name+'...')

            raw_dem_name = 'grd'+dem_tile_name+'_13'

            dem_dir = os.path.join(server_dir,'NED_10m',dem_tile_name)

            in_dem_tile = os.path.join(dem_dir,raw_dem_name)
            out_dem_tile = os.path.join(temp_gdb,dem_tile_name)

            if dem_index == 0:
                arcpy.Copy_management(in_dem_tile,temp_dem)
            else:
                arcpy.Mosaic_management(in_dem_tile,temp_dem)

        print('         Projecting DEM Data...')

        arcpy.ProjectRaster_management(temp_dem,dem,utm_spatial_ref,'BILINEAR',10,'','')

    if arcpy.Exists(db_feat):
        print('     Debris Basins Found...')
    else:
        print('     Searching for Debris Basins...')

        db_gdb_name = 'DebrisBasins.gdb'
        db_gdb = os.path.join(server_dir,db_gdb_name)

        temp_db_feat_name = 'z_'+i+"_db_feat"
        temp_db_feat = os.path.join(temp_gdb,db_feat_name)

        server_db_feat_name = 'WesternUS_db_feat'
        server_db_feat = os.path.join(db_gdb,server_db_feat_name)

        DFTools_ArcGIS.ExtractFeaturesDiffProj(extentbox_feat,server_db_feat,temp_db_feat)

        result = arcpy.GetCount_management(temp_db_feat)
        db_count = int(result.getOutput(0))

        if db_count == 0:
            arcpy.Delete_management(temp_db_feat)
            print('         No Debris Basins Found...')
        else:
            print('         '+str(db_count)+' Debris Basins Identified..')
            arcpy.CopyFeatures_management(temp_db_feat,db_feat)

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
        print("         Burn Severity Projection = "+sev_spatial_ref.name)
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

    if (dem_project_check == "Fail") or (sev_project_check == "Fail") or (perim_project_check == "Fail") or (db_project_check == "Fail"):
        project_check = "Fail"
    else:
        project_check = "Pass"

    if project_check == "Fail":
        print("     WARNING: Input Data Projections are not all "+utm_spatial_ref.name+", Reprojecting Datasets...")
        print("         DEM Projection Check = "+dem_project_check)

        if dem_project_check == "Fail":
            print("             Projecting DEM to UTM...")
            z_dem = temp_gdb+"\\z"+i+"_dem"
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
            print("         Burn Severity Projection Check = "+sev_project_check)
            if sev_project_check == "Fail":
                print("             Projecting Burn Severity Raster to UTM...")
                arcpy.env.cellSize = dem
                arcpy.env.extent = dem
                arcpy.env.snapRaster = dem
                z_sev = os.path.join(temp_gdb,i+'_sev')
                arcpy.Copy_management(sev, z_sev)
                arcpy.Delete_management(sev)
                arcpy.ProjectRaster_management(z_sev, sev, dem, "NEAREST", cell_res)
            else:
                pass
        else:
            pass

        if arcpy.Exists(sev):
            print("         dNBR Projection Check = "+dnbr_project_check)
            if dnbr_project_check == "Fail":
                print("             Projecting dNBR Raster to UTM...")
                arcpy.env.cellSize = dem
                arcpy.env.extent = dem
                arcpy.env.snapRaster = dem
                z_dnbr = temp_gdb+"\\z"+i+"_dnbr"
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
            z_perim_feat = temp_gdb+"\\z"+i+"_perim_feat"
            arcpy.Copy_management(perim_feat, z_perim_feat)
            arcpy.Delete_management(perim_feat)
            arcpy.Project_management(z_perim_feat, perim_feat, dem)
        else:
            pass

        if arcpy.Exists(db_feat):
            print("         Debris Basin Projection Check = "+db_project_check)
            if db_project_check == "Fail":
                print("             Projecting Debris Basin Feature Class to UTM...")
                z_db_feat_name = "z"+i+"_db_feat"
                z_db_feat = os.path.join(temp_gdb,z_db_feat_name)
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

    if arcpy.Exists(sev):
        sev_cols = arcpy.GetRasterProperties_management(sev,'COLUMNCOUNT')
        sev_rows = arcpy.GetRasterProperties_management(sev,'ROWCOUNT')
    else:
        sev_cols = -9999
        sev_rows = -9999

    if arcpy.Exists(dnbr):
        dnbr_cols = arcpy.GetRasterProperties_management(dnbr,'COLUMNCOUNT')
        dnbr_rows = arcpy.GetRasterProperties_management(dnbr,'ROWCOUNT')
    else:
        dnbr_cols = -9999
        dnbr_rows = -9999

    print('         Input DEM is '+str(dem_rows)+' Rows X '+str(dem_cols)+' Columns')

    if arcpy.Exists(sev):
        print('         Input Burn Severity Raster is '+str(sev_rows)+' Rows X '+str(sev_cols)+' Columns')
    else:
        print('         No Burn Severity Data in Input Geodatabase')

    if arcpy.Exists(dnbr):
        print('         Input DNBR Raster is '+str(dnbr_rows)+' Rows X '+str(dnbr_cols)+' Columns')
    else:
        print('         No dNBR Data in Input Geodatabase')

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
        arcpy.Delete_management(dem)
        if arcpy.Exists(sev):
            arcpy.Copy_management(sev,sev_orig)
            arcpy.Delete_management(sev)
        else:
            pass

        if arcpy.Exists(dnbr):
            arcpy.Copy_management(dnbr,dnbr_orig)
            arcpy.Delete_management(dnbr)
        else:
            pass

        arcpy.env.overwriteOutput = True
        arcpy.env.cellSize = extentbox
        arcpy.env.extent = extentbox
        arcpy.env.snapRaster = extentbox

        out_dem = Raster(extentbox) * Raster(dem_orig)
        out_dem.save(dem)

        if arcpy.Exists(sev_orig):
            out_sev = Raster(extentbox) * Raster(sev_orig)
            out_sev.save(sev)
        else:
            pass

        if arcpy.Exists(dnbr_orig):
            out_dnbr = Raster(extentbox) * Raster(dnbr_orig)
            out_dnbr.save(dnbr)
        else:
            pass

        dem_cols = arcpy.GetRasterProperties_management(dem,'COLUMNCOUNT')
        dem_rows = arcpy.GetRasterProperties_management(dem,'ROWCOUNT')

        if arcpy.Exists(sev):
            sev_cols = arcpy.GetRasterProperties_management(sev,'COLUMNCOUNT')
            sev_rows = arcpy.GetRasterProperties_management(sev,'ROWCOUNT')
        else:
            pass

        if arcpy.Exists(dnbr):
            dnbr_cols = arcpy.GetRasterProperties_management(dnbr,'COLUMNCOUNT')
            dnbr_rows = arcpy.GetRasterProperties_management(dnbr,'ROWCOUNT')
        else:
            pass

        print('         Processed DEM is '+str(dem_rows)+' Rows X '+str(dem_cols)+' Columns')

        if arcpy.Exists(sev):
            print('         Processed Burn Severity Raster is '+str(sev_rows)+' Rows X '+str(sev_cols)+' Columns')
        else:
            pass

        if arcpy.Exists(dnbr):
            print('         Processed DNBR Raster is '+str(dnbr_rows)+' Rows X '+str(dnbr_cols)+' Columns')
        else:
            pass

    arcpy.env.overwriteOutput = True
    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

# EXTRACT SOILS DATA~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print("     Extracting Soils Data...")

    in_soils_feat_name = 'STATSGO_US_NAD27_Albers'
    in_soils_gdb_name = 'STATSGO_Soils.gdb'
    in_soils_gdb = os.path.join(server_dir,in_soils_gdb_name)
    in_soils_feat = os.path.join(in_soils_gdb,in_soils_feat_name)

    in_soils2_feat_name = in_soils_feat_name
    in_soils2_feat = os.path.join(temp_gdb,in_soils2_feat_name)

    fire_soils_feat_name = i+'_soils_feat'
    fire_soils_feat = os.path.join(firein_gdb,fire_soils_feat_name)

    DFTools_ArcGIS.ExtractFeaturesDiffProj(extentbox_feat,in_soils_feat,fire_soils_feat)

    soils_list = ['KFFACT','THICK']

    soil_check_list = [0] * len(soils_list)

    for soil_prop in soils_list:

        soil_prop_index = soils_list.index(soil_prop)

        zsoil_name = i+'_z'+soil_prop
        zsoil = os.path.join(temp_gdb,zsoil_name)

        soil_name = i+'_'+soil_prop
        soil = os.path.join(firein_gdb,soil_name)

        soil_area_name = i+'_'+soil_prop+'_area'
        soil_area = os.path.join(temp_gdb,soil_area_name)

        soil_prop_array = arcpy.da.TableToNumPyArray(fire_soils_feat,soil_prop)
        min_prop_value = soil_prop_array[soil_prop].min()

        if min_prop_value <= 0:
            print('         WARNING: Soil '+soil_prop+' May Contain Missing Data, Manual Editing of '+fire_soils_feat+' May Be Required...')
            soil_warn_list_string = '    WARNING: Soil '+soil_prop+' May Contain Missing Data, Manual Editing of '+fire_soils_feat+' May Be Required...'
            soil_check_list[soil_prop_index] = 0
        else:
            print('         Soil '+soil_prop+' Data Verified')
            soil_warn_list_string = '    '+i+': Soil '+soil_prop+' Data Verified, No Manual Editing Required...'
            soil_check_list[soil_prop_index] = 1

        soil_warn_list.append(soil_warn_list_string)

        if min(soil_check_list) == 0:
            soil_check = 0
        else:
            soil_check = 1

# DETERMINING BURNED AREA~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('     Defining Burned Area...')

    perim_dissolve_feat_name = i+'_perim_dissolve_feat_UTM'
    perim_dissolve_feat = os.path.join(temp_gdb,perim_dissolve_feat_name)

    arcpy.Dissolve_management(perim_feat,perim_dissolve_feat,'Perim_ID')

    arcpy.DeleteFeatures_management(perim_feat)
    arcpy.CopyFeatures_management(perim_dissolve_feat,perim_feat)

    perim_name = i+'_perim'
    perim = os.path.join(temp_gdb,perim_name)

    arcpy.AddField_management(perim_feat,'Fire_ID','TEXT','','',20,'Fire_ID')
    arcpy.AddField_management(perim_feat,'Fire_Name','TEXT','','',50,'Fire_Name')
    arcpy.AddField_management(perim_feat,'Start_Date','TEXT','','',20,'Start_Date')
    arcpy.AddField_management(perim_feat,'State_Name','TEXT','','',20,'State_Name')
    arcpy.AddField_management(perim_feat,'Area_km2','DOUBLE')
    arcpy.AddField_management(perim_feat,'Acres','DOUBLE')

    fire_info_field_list = ['Fire_ID','Fire_Name','Start_Date','State_Name','Shape_Area','Area_km2','Acres']
    with arcpy.da.UpdateCursor(perim_feat, fire_info_field_list) as cursor:
        for row in cursor:
            row[0] = i
            row[1] = fire_name_full
            row[2] = fire_start_date
            row[3] = fire_state_name
            row[5] = row[4] / 1000000
            row[6] = row[4] / 4046.86
            cursor.updateRow(row)

    arcpy.FeatureToPoint_management(perim_dissolve_feat, centroid_feat)

    perim_buff_feat_name = i+'_perim_buff'+str(perim_buffer_dist_m)+'m_feat'
    perim_buff_feat = os.path.join(temp_gdb,perim_buff_feat_name)

    perim_buff_name = i+'_perim_buff'+str(perim_buffer_dist_m)+'m'
    perim_buff = os.path.join(temp_gdb,perim_buff_name)

    perim_buff_null_name = i+'_perim_buff'+str(perim_buffer_dist_m)+'m_null'
    perim_buff_null = os.path.join(temp_gdb,perim_buff_null_name)

    perim_buff_bin_name = i+'_perim_buff'+str(perim_buffer_dist_m)+'m_bin'
    perim_buff_bin = os.path.join(temp_gdb,perim_buff_bin_name)

    arcpy.Buffer_analysis(perim_feat,perim_buff_feat,perim_buffer_dist_m,'FULL','','ALL','Perim_ID')
    arcpy.AddField_management(perim_buff_feat, "PerimBuff_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    perim_buff_id_field_list = ['PerimBuff_ID']
    with arcpy.da.UpdateCursor(perim_buff_feat, perim_buff_id_field_list) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight

    arcpy.FeatureToRaster_conversion(perim_buff_feat,'PerimBuff_ID',perim_buff,dem)

    out_perim_buff_null = IsNull(perim_buff)
    out_perim_buff_null.save(perim_buff_null)

    out_perim_buff_bin = Con(Raster(perim_buff_null) > 0, 0, 10)
    out_perim_buff_bin.save(perim_buff_bin)

    perim_null = os.path.join(temp_gdb,i+"_perimnull")
    perim_bin =  os.path.join(temp_gdb,i+"_perbin")
    zburn =  os.path.join(temp_gdb,i+"_zburn")
    burn =  os.path.join(temp_gdb,i+"_burn")

    z1burn_bin =  os.path.join(temp_gdb,i+"_z1bbin")
    z2burn_bin =  os.path.join(temp_gdb,i+"_z2bbin")
    burn_bin =  os.path.join(temp_gdb,i+"_burnbin")

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight

    arcpy.FeatureToRaster_conversion(perim_feat, "Perim_ID", perim)

    if segment_guess == 'PERIM':

        out_perim_null = IsNull(perim)
        out_perim_null.save(perim_null)

        out_perim_bin = Con(Raster(perim_null) > 0, 0, 1)
        out_perim_bin.save(perim_bin)

    else:
        arcpy.Copy_management(perim,perim_bin)


    if segment_guess == 'NO_PERIM':
        z_dem_name = i+'_z_dem'
        z_dem = os.path.join(temp_gdb,z_dem_name)
        arcpy.Copy_management(dem,z_dem)
        arcpy.Delete_management(dem)

        out_dem = Raster(perim) * Raster(z_dem)
        out_dem.save(dem)

# CALCULATE SLOPE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('     Calculating Slope (%)...')
    slppct_name = i+'_slppct'
    slppct = os.path.join(temp_gdb,slppct_name)
    out_slppct = Slope(dem,"PERCENT_RISE")
    out_slppct.save(slppct)

    slpdeg_name = i+'_slpdeg'
    slpdeg = os.path.join(temp_gdb,slpdeg_name)
    out_slpdeg = Slope(dem,"DEGREE")
    out_slpdeg.save(slpdeg)

# CALCULATE HILLSHADE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('     Calculating Shaded Relief...')
    shd_name = i+"_shd"
    shd = os.path.join(firein_gdb,i+"_shd")
    out_shd = Hillshade(dem)
    out_shd.save(shd)


# CALC PRE-FIRE dNBR and Severity~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    arcpy.ClearEnvironment('mask')

    if pre_fire == 'YES':

        print('     Running Pre-Fire Scenario...')

        #BARC Thresholds

        print('         Calculating Pre-Fire BARC4 Thresholds...')

        if barc_threshold == 'CALC':

            mtbs_perim_feat_name = 'WesternUS_MTBS_Perim_20012014'
            mtbs_perim_feat = os.path.join(mtbs_gdb,mtbs_perim_feat_name)

            mtbs_meta_table_name = 'WesternUS_MTBS_Metadata_20012014'
            mtbs_meta_table = os.path.join(mtbs_gdb,mtbs_meta_table_name)

            barc_thresholds = DFTools_PreFire.ExtractBarcThresholds(i,perim_feat,temp_gdb,mtbs_perim_feat,mtbs_meta_table,mtbs_perim_distance_km)

            barc_low_threshold = barc_thresholds[0]
            barc_mod_threshold = barc_thresholds[1]
            barc_high_threshold = barc_thresholds[2]

            print('             Median Regional BARC Thresholds:')
            print('                 Low = '+str(barc_low_threshold))
            print('                 Moderate = '+str(barc_mod_threshold))
            print('                 High = '+str(barc_high_threshold))

            arcpy.env.extent = dem

        else:
            dnbr_unburned = 25
            barc_low_threshold = dnbr_low
            barc_mod_threshold = dnbr_mod
            barc_high_threshold = dnbr_high

            print('             Defined BARC Thresholds:')
            print('                 Low = '+str(barc_low_threshold))
            print('                 Moderate = '+str(barc_mod_threshold))
            print('                 High = '+str(barc_high_threshold))
        #DNBR Parameters

        print('         Extracting Pre-Fire dNBR parameters...')

        us_evt_name = 'us_'+str(evt_version)+'evt'
        us_evt = os.path.join(evt_gdb,us_evt_name)

        fire_parameters = DFTools_PreFire.ExtractParameters(i,perim,us_evt)
        fire_kappa = fire_parameters[0]
        fire_lambda = fire_parameters[1]
        fire_dnbr_fit = fire_parameters[2]
        fire_rdnbr_fit = fire_parameters[3]

        #Simulate DNBR

        for percentile in prefire_percentile_list:

            percentile_100 = int(round(percentile * 100,0))
            percentile_100_string = str('%.0f' % percentile_100)

            print('         Simulating dNBR for Weibull Percentile = '+str(percentile)+'...')

            percentile_100 = int(round(percentile * 100,0))
            percentile_100_string = str('%.0f' % percentile_100)


            evt_simdnbr_adj_name = i+'_SimDNBR_P'+percentile_100_string+'_adj'
            evt_simdnbr_adj = os.path.join(temp_gdb,evt_simdnbr_adj_name)

            evt_simdnbr_name = i+'_SimDNBR_P'+percentile_100_string
            evt_simdnbr = os.path.join(firein_gdb,evt_simdnbr_name)

            SimDataList = DFTools_PreFire.SimDNBRSev(i,fire_lambda,fire_kappa,percentile,evt_simdnbr,evt_simdnbr_adj,barc_thresholds)

            simdnbr = SimDataList[0]
            simsev = SimDataList[1]

    if arcpy.Exists(sev):
        out_zburn = Con(Raster(sev) >= 2, 1)
        out_zburn.save(zburn)
        out_burn = Raster(zburn) * Raster(perim)
        out_burn.save(burn)

        out_z2burn_bin = IsNull(burn)
        out_z2burn_bin.save(z2burn_bin)
        out_burn_bin = Con(Raster(z2burn_bin) > 0, 0, 1)
        out_burn_bin.save(burn_bin)

    else:
        arcpy.Copy_management(perim,burn)
        arcpy.Copy_management(perim_bin,burn_bin)

# CALCULATE FLOW DIRECTION, ACCUMULATION AND RELIEF USING TAUDEM~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('     Routing Flow Using TauDEM...')

    # CONVERT DEM TO TIF

    arcpy.env.compression = "NONE"
    if segment_guess == 'NO_PERIM':
        arcpy.env.mask = perim
    arcpy.RasterToOtherFormat_conversion(dem, scratch, "TIFF")

    os.chdir(scratch)

######################
# I moved this here. It probably shouldn't stay here.
    # Define a function to suppress console outut
    @contextmanager
    def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
######################

    with suppress_stdout():

        # REMOVE PITS
        dem_taudem_name = i+"_dem.tif"
        dem_taudem = os.path.join(scratch,dem_taudem_name)

        fel_taudem_name = i+"_fel.tif"
        fel_taudem = os.path.join(scratch,fel_taudem_name)

        pitremove_cmd = "PitRemove -z "+dem_taudem_name+" -fel "+fel_taudem_name
        os.system(pitremove_cmd)

        # CALC D8 FLOW DIRECTION
        fdird8_taudem_name = i+"_d8.tif"
        fdird8_taudem = os.path.join(scratch,fdird8_taudem_name)

        sd8_taudem_name = i+"_sd8.tif"
        sd8_taudem = os.path.join(scratch,sd8_taudem_name)

        d8fdir_cmd = "D8FlowDir -fel "+fel_taudem_name+" -p "+fdird8_taudem_name+" -sd8 "+sd8_taudem_name
        os.system(d8fdir_cmd)

        # CALC D8 UPSLOPE AREA
        aread8_taudem_name = i+"_aread8.tif"
        aread8_taudem = os.path.join(scratch,aread8_taudem_name)

        aread8_cmd = "AreaD8 -p "+fdird8_taudem_name+" -ad8 "+aread8_taudem_name+" -nc"
        os.system(aread8_cmd)

        # CALC D-INFINITY FLOW DIRECTION
        dinfang_taudem_name = i+"_ang.tif"
        dinfang_taudme = os.path.join(scratch,dinfang_taudem_name)

        dinfslp_taudem_name = i+"_dinfslp.tif"
        dinfslp_taudme = os.path.join(scratch,dinfslp_taudem_name)

        dinffdir_cmd = "DinfFlowdir -fel "+fel_taudem_name+" -ang "+dinfang_taudem_name+" -slp "+dinfslp_taudem_name
        os.system(dinffdir_cmd)

        # CALC D-INFINITY UPSLOPE AREA
        areadinf_taudem_name = i+"_sca.tif"
        areadinf_taudem = os.path.join(scratch,areadinf_taudem_name)

        areadinf_cmd = "AreaDinf -ang "+dinfang_taudem_name+" -sca "+areadinf_taudem_name+" -nc"
        os.system(areadinf_cmd)

        # CALC D-INFINITY BASED RELIEF BUT TRANSLATING TO D8 USING THRESHOLD = 0.49 (TARBOTON PERSONAL COMM.)
        reliefd8_taudem_name = i+"_reliefd8.tif"
        relief_taudem = os.path.join(scratch,reliefd8_taudem_name)

        dinfdistup_cmd = "DinfDistUp -ang "+dinfang_taudem_name+" -fel "+fel_taudem_name+" -du "+reliefd8_taudem_name+" -m max v -nc -thresh 0.49"
        os.system(dinfdistup_cmd)

        # CALC D-INFINITY BASED FLOW LENGTH BUT TRANSLATING TO D8 USING THRESHOLD = 0.49 (TARBOTON PERSONAL COMM.)
        lengthd8_taudem_name = i+"_lend8.tif"
        lengthd8_taudem = os.path.join(scratch,lengthd8_taudem_name)

        lengthd8_cmd = "DinfDistUp -ang "+dinfang_taudem_name+" -fel "+fel_taudem_name+" -du "+lengthd8_taudem_name+" -m max h -nc -thresh 0.49"
        os.system(lengthd8_cmd)

    os.chdir(workingdir)

    # TRANSLATE THE TAUDEM D8 FLOW DIRECTION INTO ARCGIS D8 FLOW DIRECTIONS

    print('     Converting TauDEM Derivatives to ArcGIS Rasters...')

    fdir_taudem_arc = os.path.join(temp_gdb,i+"_taud8")
    fdir = os.path.join(firein_gdb,i+"_fdir")
    facc = os.path.join(firein_gdb,i+"_facc")
    relief = os.path.join(firein_gdb,i+"_relief")
    flen = os.path.join(temp_gdb,i+"_flen")

    arcpy.Copy_management(fdird8_taudem,fdir_taudem_arc)
    arcpy.Copy_management(aread8_taudem,facc)
    arcpy.Copy_management(relief_taudem,relief)
    arcpy.Copy_management(lengthd8_taudem,flen)

    # FLOW DIRECTION
    print('     Translating TauDEM Flow Direction...')

    fdir_remap = workingdir+"\\"+i+"_TauDEM_FDirRemap.txt"

    target = open(fdir_remap,'wt')
    target.write("1 : 1\n")
    target.write("2 : 128\n")
    target.write("3 : 64\n")
    target.write("4 : 32\n")
    target.write("5 : 16\n")
    target.write("6 : 8\n")
    target.write("7 : 4\n")
    target.write("8 : 2\n")
    target.close()
    outfdir = arcpy.sa.ReclassByASCIIFile(fdir_taudem_arc,fdir_remap,"NODATA")
    outfdir.save(fdir)


    if segment_guess == 'NO_PERIM':
        z_fdir_name = i+'_z_d8'
        z_fdir = os.path.join(temp_gdb,z_fdir_name)
        arcpy.Copy_management(fdir,z_fdir)
        arcpy.Delete_management(fdir)

        out_fdir = Raster(perim) * Raster(z_fdir)
        out_fdir.save(fdir)

        z_facc_name = i+'_z_facc'
        z_facc = os.path.join(temp_gdb,z_facc_name)
        arcpy.Copy_management(facc,z_facc)
        arcpy.Delete_management(facc)

        out_facc = Raster(perim) * Raster(z_facc)
        out_facc.save(facc)

    facc_cl_name = i+'_facc_cl'
    facc_cl = os.path.join(temp_gdb,facc_cl_name)

    if segment_guess == 'NO_PERIM':
        arcpy.env.mask = perim

    out_facc_cl = Con(Raster(facc) >= max_acc,0,1)
    out_facc_cl.save(facc_cl)

    # BURNED AREA FLOW ACCUMULATION
    print('     Accumulating Burned Area...')

    burn_bin = os.path.join(temp_gdb,i+"_burnbin")
    burn_bin_taudem_name = i+"_burnbin.tif"
    burn_bin_taudem = os.path.join(scratch,burn_bin_taudem_name)

    bslp = os.path.join(temp_gdb,i+"_bslp")
    bslp_taudem_name = i+"_bslp.tif"
    bslp_taudem = os.path.join(scratch,bslp_taudem_name)

    arcpy.env.compression = "NONE"
    arcpy.RasterToOtherFormat_conversion(burn_bin, scratch, "TIFF")

    os.chdir(scratch)

    burn_aread8_taudem_name = i+"_baread8.tif"
    burn_aread8_taudem = os.path.join(scratch,burn_aread8_taudem_name)

    with suppress_stdout():

        burn_aread8_cmd = "AreaD8 -p "+fdird8_taudem_name+" -ad8 "+burn_aread8_taudem_name+" -wg "+burn_bin_taudem_name+" -nc"
        os.system(burn_aread8_cmd)

    os.chdir(workingdir)

    z_bacc = os.path.join(temp_gdb,'z'+i+'_bacc')
    z2_bacc_null = os.path.join(temp_gdb,'z2'+i+'_bacc')
    bacc = os.path.join(temp_gdb,i+'_bacc')
    bacc_bin = os.path.join(temp_gdb,i+'_baccbin')

    arcpy.Copy_management(burn_aread8_taudem,bacc)

    if segment_guess == 'NO_PERIM':
        z_bacc_name = i+'_z_bacc'
        z_bacc = os.path.join(temp_gdb,z_bacc_name)
        arcpy.Copy_management(bacc,z_bacc)
        arcpy.Delete_management(bacc)

        out_bacc = Raster(perim) * Raster(z_bacc)
        out_bacc.save(bacc)

    # ALL STREAMS BETWEEN MIN AND MAX ACCUM THRESHOLDS

    print("     Defining Stream Network...")

    if segment_guess == 'NO_PERIM':
        arcpy.env.mask = perim

    z_strm_name = i+'_zstrm'
    z_strm = os.path.join(temp_gdb,z_strm_name)

    strm_binary_name = i+'_strm_bin'
    strm_binary = os.path.join(temp_gdb,strm_binary_name)

    hill_binary_name = i+'_hill_bin'
    hill_binary = os.path.join(temp_gdb,hill_binary_name)

    zbin_allstrm_link_feat_name = "z"+i+"_alllink_feat"
    zbin_allstrm_link_feat = os.path.join(temp_gdb,zbin_allstrm_link_feat_name)

    z_link_name = i+'_zlink'
    z_link = os.path.join(temp_gdb,z_link_name)

    z_link_feat_name = i+'_zlink_feat'
    z_link_feat = os.path.join(temp_gdb,z_link_feat_name)

    dense_link_feat_name = i+'_denselink_feat'
    dense_link_feat = os.path.join(temp_gdb,dense_link_feat_name)

    bin_allstrm_link_name = i+"_alllink"
    bin_allstrm_link = os.path.join(temp_gdb,bin_allstrm_link_name)

    bin_allstrm_link_feat_name = i+"_alllink_feat"
    bin_allstrm_link_feat = os.path.join(temp_gdb,bin_allstrm_link_feat_name)

    if segment_guess == 'NO_PERIM':
        arcpy.env.mask = perim
        out_z_strm = Con((Raster(facc) >= min_acc) & (Raster(bacc) > burn_acc_threshold), 1)
        out_z_strm.save(z_strm)

    else:
        out_z_strm = Con((Raster(facc) >= min_acc) & (Raster(bacc) > burn_acc_threshold), 1)
        out_z_strm.save(z_strm)

    DFTools_ArcGIS.ReplaceNull(z_strm,strm_binary,0,1)
    DFTools_ArcGIS.ReplaceNull(z_strm,hill_binary,1,0)

    if segment_guess == 'NO_PERIM':
        arcpy.env.mask = perim

    arcpy.ResetEnvironments()
    arcpy.env.cellSize = dem
    arcpy.env.snapRaster = dem
    arcpy.env.extent = perim

    out_z_link = StreamLink(z_strm,fdir)
    out_z_link.save(z_link)

    arcpy.RasterToPolyline_conversion(z_strm,z_link_feat,'','','NO_SIMPLIFY')

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

    z_dense_pts_name = 'z'+i+'_dense_pts_feat'
    z_dense_pts = os.path.join(temp_gdb,z_dense_pts_name)

    segment_length_string = str(max_segment_length_m)+' Meters'
    arcpy.GeneratePointsAlongLines_management(z_link_feat,z_dense_pts,'DISTANCE',segment_length_string)
    arcpy.SplitLineAtPoint_management(z_link_feat,z_dense_pts,dense_link_feat,'2')

    arcpy.AddField_management(dense_link_feat, "Segment_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    dense_link_id_field_list = ['OBJECTID','Segment_ID']
    with arcpy.da.UpdateCursor(dense_link_feat, dense_link_id_field_list) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(dense_link_feat, "arcid;grid_code;from_node;to_node")

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

    arcpy.PolylineToRaster_conversion(dense_link_feat,'Segment_ID',bin_allstrm_link)

    out_bin_allstrm_link_feat = StreamToFeature(bin_allstrm_link,fdir,bin_allstrm_link_feat,'NO_SIMPLIFY')
    arcpy.AddField_management(bin_allstrm_link_feat, "Segment_ID", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    segment_id_field_list = ['grid_code','Segment_ID']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, segment_id_field_list) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "arcid;grid_code")

    bin_allstrm = os.path.join(temp_gdb,i+"_allstrm")
    bin_allstrm_ord = temp_gdb+"\\"+i+"_allord"
    bin_allstrm_ord_feat = temp_gdb+"\\"+i+"_allord_feat"
    out_bin_allstrm_ord = StreamOrder(bin_allstrm_link, fdir, "STRAHLER")
    out_bin_allstrm_ord.save(bin_allstrm_ord)

    StreamToFeature(bin_allstrm_ord,fdir,bin_allstrm_ord_feat,"NO_SIMPLIFY")

    # CHECK TO SEE IF THERE ARE DEBRIS BASINS, IF YES, THEN FIND STREAMS BELOW BASINS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # DEBRIS BASIN FLOW ROUTING
    db_check = 0
    db_feat = os.path.join(firein_gdb,i+"_db_feat")

    db = os.path.join(temp_gdb,i+"_db")
    db_acc = os.path.join(temp_gdb,i+"_dbacc")
    db_strm = os.path.join(temp_gdb,i+"_dbstrm")
    db_strm_feat = os.path.join(temp_gdb,i+"_dbstrm_feat")
    db_nonstrm = os.path.join(temp_gdb,i+"_ndbstrm")
    db_bin = os.path.join(temp_gdb,i+"_dbbin")
    zdb_null = os.path.join(temp_gdb,i+"_zdbnull")

    if arcpy.Exists(db_feat):
        db_check = 1
        print("     Calculating Streams Below Debris Basins...")
        dem_info = arcpy.Raster(dem)
        cell_res = dem_info.meanCellHeight
        arcpy.env.cellSize = dem
        arcpy.env.extent = dem
        arcpy.DeleteField_management(db_feat,'DB_ID')
        arcpy.AddField_management(db_feat,'DB_ID','LONG')

        db_id_field_list = ['DB_ID']
        with arcpy.da.UpdateCursor(db_feat, db_id_field_list) as cursor:
            for row in cursor:
                row[0] = 1
                cursor.updateRow(row)

        arcpy.FeatureToRaster_conversion(db_feat, 'DB_ID', db, dem)

        out_zdb_null = IsNull(db)
        out_zdb_null.save(zdb_null)

        out_db_bin = Con(Raster(zdb_null) > 0, 0, 1)
        out_db_bin.save(db_bin)

        arcpy.env.compression = "NONE"
        arcpy.RasterToOtherFormat_conversion(db_bin, scratch, "TIFF")

        os.chdir(scratch)

        db_taudem_name = i+"_dbbin.tif"
        db_taudem = scratch+"\\"+db_taudem_name

        db_acc_taudem_name = i+"_dbacc.tif"
        db_acc_taudem = scratch+"\\"+db_acc_taudem_name

        with suppress_stdout():

            db_acc_cmd = "AreaD8 -p "+fdird8_taudem_name+" -ad8 "+db_acc_taudem_name+" -wg "+db_taudem_name+" -nc"
            os.system(db_acc_cmd)

        arcpy.Copy_management(db_acc_taudem,db_acc)

        db_acc = os.path.join(temp_gdb,i+"_dbacc")
        db_acc_bin = os.path.join(temp_gdb,i+"_dbaccb")

        out_db_acc_bin = Con(Raster(db_acc) > 0, 1, 0)
        out_db_acc_bin.save(db_acc_bin)

        out_db_strm = Con(Raster(db_acc) > 0, 1)
        out_db_strm.save(db_strm)

        StreamToFeature(db_strm,fdir, db_strm_feat,"NO_SIMPLIFY")

        out_debrisbasins = os.path.join(modelcalcs_gdb,i+"_db_feat")
        arcpy.Copy_management(db_feat, out_debrisbasins, "")
        out_db_strm_feat = os.path.join(firein_gdb,i+"_dbstream_feat")
        arcpy.Copy_management(db_strm_feat, out_db_strm_feat, "")

    else:

        db_acc = os.path.join(temp_gdb,i+"_dbacc")
        db_acc_bin = os.path.join(temp_gdb,i+"_dbaccb")

        arcpy.Copy_management(bin_allstrm_link, db_strm)

        StreamToFeature(db_strm,fdir, db_strm_feat,"NO_SIMPLIFY")
        out_db_acc_bin = Con(Raster(facc) > 0, 1, 0)
        out_db_acc_bin.save(db_acc_bin)

    arcpy.Copy_management(bin_allstrm_link, bin_allstrm)

# BUILD KERNEL FILE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#Set your window sizes:
    print("     Building Kernel File(s) For Confinement Analysis...")
    min_ncells = 3 #For a 3x3, enter 3, for a 5x5, enter 5
    max_ncells = 9

    step = 2 # Step between windows, must be even.  3 x 3 and 5 x 5 = step of 2, 3x3 to 7x7 step =4
    #
    neighborhood_list = arange(min_ncells, max_ncells+1, step)
    #neighborhood_list = [5]

    for j in neighborhood_list:

        nrows = j
        ncols = j

        neighborhood = np.zeros((j,j),dtype=int)

        center_row = ((nrows + 1) / 2) - 1
        center_col = ((ncols + 1) / 2) - 1

        diagonal_main = np.copy(neighborhood)
        np.fill_diagonal(diagonal_main, 1)

        diagonal_sub = np.rot90(diagonal_main)

        horizontal = np.ones((1,ncols),dtype=int)
        horizontal_shape = np.shape(horizontal)
        horizontal_nrows = horizontal_shape[0]
        horizontal_ncols = horizontal_shape[1]

        file = kerneldir+"\\"+"Horizontal_Full_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(horizontal_ncols)+" "+str(horizontal_nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, horizontal_nrows,1):
            print_string = str(horizontal[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir4_full = kerneldir+"\\"+"FDIR4_Full_"+str(j)+"x"+str(j)+".txt"
        fdir64_full = kerneldir+"\\"+"FDIR64_Full_"+str(j)+"x"+str(j)+".txt"
        shutil.copyfile(file,fdir4_full)
        shutil.copyfile(file,fdir64_full)

        horizontal_half_left = np.copy(horizontal)
        for k_col in range(0,j,1):
            if k_col >= center_col:
                horizontal_half_left[0,k_col] = 0
            else:
                pass

        file = kerneldir+"\\"+"Horizontal_Half_Left_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(horizontal_ncols)+" "+str(horizontal_nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, horizontal_nrows,1):
            print_string = str(horizontal_half_left[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir64_upright = kerneldir+"\\"+"FDIR4_UpRt_"+str(j)+"x"+str(j)+".txt"
        fdir4_upleft = kerneldir+"\\"+"FDIR4_UpLt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir64_upright)
        shutil.copy(file,fdir4_upleft)


        horizontal_half_right = np.copy(horizontal)
        for k_col in range(0,j,1):
            if k_col <= center_col:
                horizontal_half_right[0,k_col] = 0
            else:
                pass

        file = kerneldir+"\\"+"Horizontal_Half_Right_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(horizontal_ncols)+" "+str(horizontal_nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, horizontal_nrows,1):
            print_string = str(horizontal_half_right[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir4_upright = kerneldir+"\\"+"FDIR4_UpRt_"+str(j)+"x"+str(j)+".txt"
        fdir64_upleft = kerneldir+"\\"+"FDIR4_UpLt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir4_upright)
        shutil.copy(file,fdir64_upleft)

    # VERTICAL

        vertical = np.ones((nrows,1),dtype=int)
        vertical_shape = np.shape(vertical)
        vertical_nrows = vertical_shape[0]
        vertical_ncols = vertical_shape[1]

        file = kerneldir+"\\"+"Vertical_Full_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(vertical_ncols)+" "+str(vertical_nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(vertical[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir1_full = kerneldir+"\\"+"FDIR1_Full_"+str(j)+"x"+str(j)+".txt"
        fdir16_full = kerneldir+"\\"+"FDIR16_Full_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir1_full)
        shutil.copy(file,fdir16_full)

        vertical_half_top = np.copy(vertical)
        for j_row in range(0,j,1):
            if j_row >= center_row:
                vertical_half_top [j_row,0] = 0
            else:
                pass

        file = kerneldir+"\\"+"Vertical_Half_Top_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(vertical_ncols)+" "+str(vertical_nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(vertical_half_top[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir1_upright = kerneldir+"\\"+"FDIR1_UpRt_"+str(j)+"x"+str(j)+".txt"
        fdir16_upleft = kerneldir+"\\"+"FDIR16_UpLt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir1_upright)
        shutil.copy(file,fdir16_upleft)

        vertical_half_bottom = np.copy(vertical)
        for j_row in range(0,j,1):
            if j_row <= center_row:
                vertical_half_bottom[j_row,0] = 0
            else:
                pass

        file = kerneldir+"\\"+"Vertical_Half_Bottom_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(vertical_ncols)+" "+str(vertical_nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(vertical_half_bottom[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir1_upleft = kerneldir+"\\"+"FDIR1_UpLt_"+str(j)+"x"+str(j)+".txt"
        fdir16_upright = kerneldir+"\\"+"FDIR16_UpRt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir1_upleft)
        shutil.copy(file,fdir16_upright)

    # DIAGONAL

        file = kerneldir+"\\"+"Diagonal_Main_Full_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(ncols)+" "+str(nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(diagonal_main[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir8_full = kerneldir+"\\"+"FDIR8_Full_"+str(j)+"x"+str(j)+".txt"
        fdir128_full = kerneldir+"\\"+"FDIR128_Full_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir8_full)
        shutil.copy(file,fdir128_full)

        file = kerneldir+"\\"+"Diagonal_Sub_Full_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(ncols)+" "+str(nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(diagonal_sub[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir32_full = kerneldir+"\\"+"FDIR32_Full_"+str(j)+"x"+str(j)+".txt"
        fdir2_full = kerneldir+"\\"+"FDIR2_Full_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir32_full)
        shutil.copy(file,fdir2_full)

        diagonal_main_half_top = np.copy(diagonal_main)
        for j_row in range(0,j,1):
            for k_col in range(0,j,1):
                if j_row >= center_row:
                    diagonal_main_half_top[j_row,k_col] = 0
                else:
                    pass

        file = kerneldir+"\\"+"Diagonal_Main_Half_Top_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(ncols)+" "+str(nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(diagonal_main_half_top[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir8_upleft = kerneldir+"\\"+"FDIR8_UpLt_"+str(j)+"x"+str(j)+".txt"
        fdir128_upright = kerneldir+"\\"+"FDIR128_UpRt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir8_upleft)
        shutil.copy(file,fdir128_upright)

        diagonal_sub_half_bottom = np.rot90(diagonal_main_half_top)

        file = kerneldir+"\\"+"Diagonal_Sub_Half_Bottom_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(ncols)+" "+str(nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(diagonal_sub_half_bottom[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir32_upright = kerneldir+"\\"+"FDIR32_UpRt_"+str(j)+"x"+str(j)+".txt"
        fdir2_upleft = kerneldir+"\\"+"FDIR2_UpLt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir32_upright)
        shutil.copy(file,fdir2_upleft)

        diagonal_sub_half_top = np.copy(diagonal_sub)
        for j_row in range(0,j,1):
            for k_col in range(0,j,1):
                if j_row >= center_row:
                    diagonal_sub_half_top[j_row,k_col] = 0
                else:
                    pass

        file = kerneldir+"\\"+"Diagonal_Sub_Half_Top_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(ncols)+" "+str(nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(diagonal_sub_half_top[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir32_upleft = kerneldir+"\\"+"FDIR32_UpLt_"+str(j)+"x"+str(j)+".txt"
        fdir2_upright = kerneldir+"\\"+"FDIR2_UpRt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir32_upleft)
        shutil.copy(file,fdir2_upright)

        diagonal_main_half_bottom = np.rot90(diagonal_sub_half_bottom)

        file = kerneldir+"\\"+"Diagonal_Main_Half_Bottom_"+str(j)+"x"+str(j)+".txt"
        fdata = open(file, 'wt')
        header_string = str(ncols)+" "+str(nrows)
        fdata.write('%s\n' % header_string)

        for n in range(0, vertical_nrows,1):
            print_string = str(diagonal_main_half_bottom[n,0:])
            print_string = str.replace(print_string,"[","")
            print_string = str.replace(print_string,"]","")
            fdata.write('%s\n' % print_string)
        fdata.close()

        fdir8_upright = kerneldir+"\\"+"FDIR8_UpRt_"+str(j)+"x"+str(j)+".txt"
        fdir128_upleft = kerneldir+"\\"+"FDIR128_UpLt_"+str(j)+"x"+str(j)+".txt"
        shutil.copy(file,fdir8_upright)
        shutil.copy(file,fdir128_upleft)


# CALCULATE CONFINEMENT~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print("     Calculating Confinement...")

    k = 9

    # FLOW DIRECTION REFERENCE FOR ARCGIS D8
    #   32      64      128 (y - 1)
    #   16      -       1   (y)
    #   8       4       2   (y+1)
    #   (x - 1) (x)     (x+1)

    # x = column, y = row

    fdir1_upright = "Irregular "+kerneldir+"\\"+"FDIR1_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir1_upleft = "Irregular "+kerneldir+"\\"+"FDIR1_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir2_upright = "Irregular "+kerneldir+"\\"+"FDIR2_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir2_upleft = "Irregular "+kerneldir+"\\"+"FDIR2_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir4_upright = "Irregular "+kerneldir+"\\"+"FDIR4_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir4_upleft = "Irregular "+kerneldir+"\\"+"FDIR4_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir8_upright = "Irregular "+kerneldir+"\\"+"FDIR8_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir8_upleft = "Irregular "+kerneldir+"\\"+"FDIR8_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir16_upright = "Irregular "+kerneldir+"\\"+"FDIR16_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir16_upleft = "Irregular "+kerneldir+"\\"+"FDIR16_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir32_upright = "Irregular "+kerneldir+"\\"+"FDIR32_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir32_upleft = "Irregular "+kerneldir+"\\"+"FDIR32_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir64_upright = "Irregular "+kerneldir+"\\"+"FDIR4_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir64_upleft = "Irregular "+kerneldir+"\\"+"FDIR4_UpLt_"+str(k)+"x"+str(k)+".txt"

    fdir128_upright = "Irregular "+kerneldir+"\\"+"FDIR128_UpRt_"+str(k)+"x"+str(k)+".txt"
    fdir128_upleft = "Irregular "+kerneldir+"\\"+"FDIR128_UpLt_"+str(k)+"x"+str(k)+".txt"

    f1rt = temp_gdb+"\\"+i+"_f1rt_"+str(k)
    f1lt = temp_gdb+"\\"+i+"_f1lt_"+str(k)
    f2rt = temp_gdb+"\\"+i+"_f2rt_"+str(k)
    f2lt = temp_gdb+"\\"+i+"_f2lt_"+str(k)
    f4rt = temp_gdb+"\\"+i+"_f4rt_"+str(k)
    f4lt = temp_gdb+"\\"+i+"_f4lt_"+str(k)
    f8rt = temp_gdb+"\\"+i+"_f8rt_"+str(k)
    f8lt = temp_gdb+"\\"+i+"_f8lt_"+str(k)
    f16rt = temp_gdb+"\\"+i+"_f16rt_"+str(k)
    f16lt = temp_gdb+"\\"+i+"_f16lt_"+str(k)
    f32rt = temp_gdb+"\\"+i+"_f32rt_"+str(k)
    f32lt = temp_gdb+"\\"+i+"_f32lt_"+str(k)
    f64rt = temp_gdb+"\\"+i+"_f64rt_"+str(k)
    f64lt = temp_gdb+"\\"+i+"_f64lt_"+str(k)
    f128rt = temp_gdb+"\\"+i+"_f128rt_"+str(k)
    f128lt = temp_gdb+"\\"+i+"_f128lt_"+str(k)

    arcpy.gp.FocalStatistics_sa(dem, f1rt, fdir1_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f1lt, fdir1_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f2rt, fdir2_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f2lt, fdir2_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f4rt, fdir4_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f4lt, fdir4_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f8rt, fdir8_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f8lt, fdir8_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f16rt, fdir16_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f16lt, fdir16_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f32rt, fdir32_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f32lt, fdir32_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f64rt, fdir64_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f64lt, fdir64_upleft, "MAXIMUM", "DATA")

    arcpy.gp.FocalStatistics_sa(dem, f128rt, fdir128_upright, "MAXIMUM", "DATA")
    arcpy.gp.FocalStatistics_sa(dem, f128lt, fdir128_upleft, "MAXIMUM", "DATA")


    z_fd1_upright = temp_gdb+"\\z"+i+"1upr_"+str(k)
    z_fd1_upleft = temp_gdb+"\\z"+i+"1upl_"+str(k)

    outfd1uprt = Con(Raster(fdir) == 1, f1rt, 0)
    outfd1uprt.save(z_fd1_upright)
    outfd1uplt = Con(Raster(fdir) == 1, f1lt, 0)
    outfd1uplt.save(z_fd1_upleft)

    z_fd2_upright = temp_gdb+"\\z"+i+"2upr_"+str(k)
    z_fd2_upleft = temp_gdb+"\\z"+i+"2upl_"+str(k)

    outfd2uprt = Con(Raster(fdir) == 2, f2rt, 0)
    outfd2uprt.save(z_fd2_upright)
    outfd2uplt = Con(Raster(fdir) == 2, f2lt, 0)
    outfd2uplt.save(z_fd2_upleft)

    z_fd4_upright = temp_gdb+"\\z"+i+"4upr_"+str(k)
    z_fd4_upleft = temp_gdb+"\\z"+i+"4upl_"+str(k)

    outfd4uprt = Con(Raster(fdir) == 4, f4rt, 0)
    outfd4uprt.save(z_fd4_upright)
    outfd4uplt = Con(Raster(fdir) == 4, f4lt, 0)
    outfd4uplt.save(z_fd4_upleft)

    z_fd8_upright = temp_gdb+"\\z"+i+"8upr_"+str(k)
    z_fd8_upleft = temp_gdb+"\\z"+i+"8upl_"+str(k)

    outfd8uprt = Con(Raster(fdir) == 8, f8rt, 0)
    outfd8uprt.save(z_fd8_upright)
    outfd8uplt = Con(Raster(fdir) == 8, f8lt, 0)
    outfd8uplt.save(z_fd8_upleft)

    z_fd16_upright = temp_gdb+"\\z"+i+"16upr_"+str(k)
    z_fd16_upleft = temp_gdb+"\\z"+i+"16upl_"+str(k)

    outfd16uprt = Con(Raster(fdir) == 16, f16rt, 0)
    outfd16uprt.save(z_fd16_upright)
    outfd16uplt = Con(Raster(fdir) == 16, f16lt, 0)
    outfd16uplt.save(z_fd16_upleft)

    z_fd32_upright = temp_gdb+"\\z"+i+"32pr_"+str(k)
    z_fd32_upleft = temp_gdb+"\\z"+i+"32upl_"+str(k)

    outfd32uprt = Con(Raster(fdir) == 32, f32rt, 0)
    outfd32uprt.save(z_fd32_upright)
    outfd32uplt = Con(Raster(fdir) == 32, f32lt, 0)
    outfd32uplt.save(z_fd32_upleft)

    z_fd64_upright = temp_gdb+"\\z"+i+"64upr_"+str(k)
    z_fd64_upleft = temp_gdb+"\\z"+i+"64upl_"+str(k)

    outfd64uprt = Con(Raster(fdir) == 64, f64rt, 0)
    outfd64uprt.save(z_fd64_upright)
    outfd64uplt = Con(Raster(fdir) == 64, f64lt, 0)
    outfd64uplt.save(z_fd64_upleft)

    z_fd128_upright = temp_gdb+"\\z"+i+"128upr_"+str(k)
    z_fd128_upleft = temp_gdb+"\\z"+i+"128upl_"+str(k)

    outfd128uprt = Con(Raster(fdir) == 128, f1rt, 0)
    outfd128uprt.save(z_fd128_upright)
    outfd128uplt = Con(Raster(fdir) == 128, f1lt, 0)
    outfd128uplt.save(z_fd128_upleft)

    z_up_right = temp_gdb+"\\"+i+"_zuprt_"+str(k)
    z_up_left = temp_gdb+"\\"+i+"_zuplt_"+str(k)


    out_z_up_right = Raster(z_fd1_upright) + Raster(z_fd2_upright) + Raster(z_fd4_upright) + Raster(z_fd8_upright)+ Raster(z_fd16_upright) + Raster(z_fd32_upright) + Raster(z_fd64_upright) + Raster(z_fd128_upright)
    out_z_up_right.save(z_up_right)

    out_z_up_left = Raster(z_fd1_upleft) + Raster(z_fd2_upleft) + Raster(z_fd4_upleft) + Raster(z_fd8_upleft)+ Raster(z_fd16_upleft) + Raster(z_fd32_upleft) + Raster(z_fd64_upleft) + Raster(z_fd128_upleft)
    out_z_up_left.save(z_up_left)

    zlength_calc = temp_gdb+"\\"+i+"zlcalc"
    zlength_calc2 = temp_gdb+"\\"+i+"zlcalc2"
    length_calc = temp_gdb+"\\"+i+"_lcalc"
    length_remap = scratch+"\\"+i+"_FDirLengthRemap.txt"

    target = open(length_remap,'wt')
    target.write("1 : 10\n")
    target.write("2 : 14\n")
    target.write("4 : 10\n")
    target.write("8 : 14\n")
    target.write("16 : 10\n")
    target.write("32 : 14\n")
    target.write("64 : 10\n")
    target.write("128 : 14\n")
    target.close()

    outlength_calc = arcpy.sa.ReclassByASCIIFile(fdir,length_remap,"NODATA")
    outlength_calc.save(zlength_calc)
    outlength_calc2 = (Raster(zlength_calc) / 10)
    outlength_calc2.save(zlength_calc2)

    length_adjust = cell_res * k
    outlength_calc3 = Times(zlength_calc2, length_adjust)
    outlength_calc3.save(length_calc)

    delta_r = temp_gdb+"\\"+i+"_deltar_"+str(k)
    delta_l = temp_gdb+"\\"+i+"_deltal_"+str(k)

    theta_r = temp_gdb+"\\"+i+"_thetar_"+str(k)
    theta_l = temp_gdb+"\\"+i+"_thetal_"+str(k)
    theta_rc = temp_gdb+"\\"+i+"_thetarc_"+str(k)
    theta_lc = temp_gdb+"\\"+i+"_thetalc_"+str(k)
    theta_c = temp_gdb+"\\"+i+"_thetac_"+str(k)
    theta_ca = temp_gdb+"\\"+i+"_thetaca_"+str(k)

    out_delta_r = Raster(z_up_right) - Raster(dem)
    out_delta_r.save(delta_r)
    out_delta_l = Raster(z_up_left) - Raster(dem)
    out_delta_l.save(delta_l)

    out_theta_r = (ATan((Raster(delta_r)) / Raster(length_calc))) * (360 / (2 * 3.14159))
    out_theta_r.save(theta_r)

    out_theta_l = (ATan(Raster(delta_l) / Raster(length_calc))) * (360 / (2 * 3.14159))
    out_theta_l.save(theta_l)

    out_theta_rc = 90 - Raster(theta_r)
    out_theta_rc.save(theta_rc)
    out_theta_lc = 90 - Raster(theta_l)
    out_theta_lc.save(theta_lc)

    out_theta_c = Raster(theta_lc) + Raster(theta_rc)
    out_theta_c.save(theta_c)

    out_theta_ca = Raster(theta_l) + (0.5 * Raster(theta_c))
    out_theta_ca.save(theta_ca)

# CALCULATE DEVELOPED AREAS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print("     Determining Developed Areas...")

    box30 = os.path.join(temp_gdb,i+"_box30")
    box = os.path.join(temp_gdb,i+"_box")
    box_feat = os.path.join(temp_gdb,i+"_boxfeature")

    state_dev30 = os.path.join(landfire_gdb,state_abbrev+"_Developed")
    dev30 = os.path.join(temp_gdb,i+"_dev30")
    z_dev = os.path.join(temp_gdb,'z'+i+"_dev")
    dev = os.path.join(temp_gdb,i+"_dev")
    nondev =  os.path.join(temp_gdb,i+"_nondev")

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

    out_box = Con(Raster(dem) > 0, 1)
    out_box.save(box)

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem

    out_z_dev = Raster(box) * Raster(state_dev30)
    out_z_dev.save(z_dev)

    DFTools_ArcGIS.ReplaceNull(z_dev,dev,0,z_dev)

    out_nondev = Con(Raster(dev) > 0, 0, 1)
    out_nondev.save(nondev)

    dev_upsum_name = i+'_dev_upsum'
    dev_upsum = os.path.join(temp_gdb,dev_upsum_name)

    with suppress_stdout():

        DFTools_TauDEM.TauDem_UpSum(fdird8_taudem,dev,dev_upsum,scratch,cell_res)

# SUMMARIZE STATISTICS FOR STREAM SEGMENTS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    #CONTRIBUTING AREA
    print('     Summarizing Flow Accumulation (N Cells) For Stream Segments...')
    facc_segmentstats = temp_gdb+"\\"+i+"_facc_segmentstats"
    facc_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", facc, facc_segmentstats, "DATA", "MINIMUM")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", facc_segmentstats, "VALUE", "MIN")
    arcpy.AddField_management(bin_allstrm_link_feat, "facc", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(bin_allstrm_link_feat, "UpArea_km2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    uparea_field_list = ['MIN','facc','UpArea_km2']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, uparea_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
                row[2] = (row[0] * cell_res * cell_res) / 1000000
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MIN")

    facc_cl_segment_stats = temp_gdb+"\\"+i+"_facc_cl_segmentstats"
    facc_cl_segment_stats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", facc_cl, facc_cl_segment_stats, "DATA", "MINIMUM")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", facc_cl_segment_stats, "VALUE", "MIN")
    arcpy.AddField_management(bin_allstrm_link_feat, "Acc_Cl", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    facc_cl_field_list = ['MIN','Acc_Cl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, facc_cl_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MIN")


    #BURNED CONTRIBUTING AREA
    print('     Summarizing Burned Characteristics For Stream Segments...')
    bacc_segmentstats = temp_gdb+"\\"+i+"_bacc_segmentstats"
    bacc_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", bacc, bacc_segmentstats, "DATA", "MINIMUM")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", bacc_segmentstats, "VALUE", "MIN")
    arcpy.AddField_management(bin_allstrm_link_feat, "bacc", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(bin_allstrm_link_feat, "UpBurnArea_km2", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    upburnarea_field_list = ['MIN','bacc','UpBurnArea_km2']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, upburnarea_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
                row[2] = (row[0] * cell_res * cell_res) / 1000000
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MIN")

    #BURNED LENGTH
    bbin_segmentstats = temp_gdb+"\\"+i+"_bbin_segmentstats"
    bbin_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", burn_bin, bbin_segmentstats, "DATA", "MAJORITY")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", bbin_segmentstats, "VALUE", "MAJORITY")
    arcpy.AddField_management(bin_allstrm_link_feat, "burn_bin", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    burnbin_field_list = ['MAJORITY','burn_bin']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, burnbin_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MAJORITY")

    #STREAM ORDER
    print('     Determining Stream Order...')
    ord_segmentstats = temp_gdb+"\\"+i+"_order_segmentstats"
    ord_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", bin_allstrm_ord, ord_segmentstats, "DATA", "MAJORITY")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", ord_segmentstats, "VALUE", "MAJORITY")
    arcpy.AddField_management(bin_allstrm_link_feat, "StrmOrder", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

##    arcpy.CalculateField_management(bin_allstrm_link_feat, "StrmOrder", "!MAJORITY!", "PYTHON", "")

    strmord_field_list = ['MAJORITY','StrmOrder']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, strmord_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)
    arcpy.DeleteField_management(bin_allstrm_link_feat, "MAJORITY")

    #SLOPE
    print('     Summarizing Mean Gradient (%) For Stream Segments...')
    slppct_segmentstats = temp_gdb+"\\"+i+"_slppct_segmentstats"
    slppct_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", slppct, slppct_segmentstats, "DATA", "MEAN")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", slppct_segmentstats, "VALUE", "MEAN")
    arcpy.AddField_management(bin_allstrm_link_feat, "slppct", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

##    arcpy.CalculateField_management(bin_allstrm_link_feat, "slppct", "!MEAN!", "PYTHON", "")

    slppct_field_list = ['MEAN','slppct']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, slppct_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MAJORITY")
    arcpy.DeleteField_management(bin_allstrm_link_feat, "MEAN")

    #CONFINEMENT
    print('     Summarizing Mean Confinement Angle For Stream Segments...')
    conf_segmentstats = temp_gdb+"\\"+i+"_conf_segmentstats"
    conf_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", theta_c, conf_segmentstats, "DATA", "MEAN")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", conf_segmentstats, "VALUE", "MEAN")
    arcpy.AddField_management(bin_allstrm_link_feat, "conf", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

##    arcpy.CalculateField_management(bin_allstrm_link_feat, "conf", "!MEAN!", "PYTHON", "")

    conf_field_list = ['MEAN','conf']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, conf_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MEAN")


    #DEVELOPEMENT = DevCl, 1 = Non-Developed, 0 = Developed

    print('     Determining if Stream Segment Is Within or Below a Developed Area...')
    devsum_segmentstats = temp_gdb+"\\"+i+"_devsum_segmentstats"
    devsum_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", dev_upsum, devsum_segmentstats, "DATA", "MEAN")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", devsum_segmentstats, "VALUE", "MEAN")
    arcpy.AddField_management(bin_allstrm_link_feat, "DevSum", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    devsum_field_list = ['MEAN','DevSum']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat, devsum_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "DevCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    dev_fields = ['DevSum','DevCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,dev_fields) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            elif row[0] >= dev_sum_threshold:
                row[1] = 0
            else:
                row[1] = 1
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MEAN")
    arcpy.DeleteField_management(bin_allstrm_link_feat, "DevSum")

    print('     Determining if Stream Segment Is Within Burn Perimeter...')
    perim_segmentstats = temp_gdb+"\\"+i+"_perim_segmentstats"
    perim_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", perim_bin, perim_segmentstats, "DATA", "MAJORITY")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", perim_segmentstats, "VALUE", "MAJORITY")
    arcpy.AddField_management(bin_allstrm_link_feat, "Perim", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    perim_fields = ['MAJORITY','Perim']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,perim_fields) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MAJORITY")

    print('     Determining if Stream Segment Is Within Buffered Burn Perimeter...')
    perim_buff_segmentstats = temp_gdb+"\\"+i+"_perim_buff_segmentstats"
    perim_buff_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", perim_buff_bin, perim_buff_segmentstats, "DATA", "MAJORITY")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", perim_buff_segmentstats, "VALUE", "MAJORITY")
    arcpy.AddField_management(bin_allstrm_link_feat, "Perim_BuffCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    perimbuff_fields = ['MAJORITY','Perim_BuffCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,perimbuff_fields) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "MAJORITY")
    arcpy.DeleteField_management(bin_allstrm_link_feat, "MAJORITY")

    #DEBRIS BASIN = DBCl, 1 = No Debris Basin, 0 = Debris Basin
    print('     Determining if Stream Segment Is Above Identified Debris Retention Basin...')
    db_segmentstats = temp_gdb+"\\"+i+"_db_segmentstats"
    db_segmentstats = ZonalStatisticsAsTable(bin_allstrm_link, "VALUE", db_acc_bin, db_segmentstats, "DATA", "SUM")
    arcpy.JoinField_management(bin_allstrm_link_feat, "Segment_ID", db_segmentstats, "VALUE", "SUM")
    arcpy.AddField_management(bin_allstrm_link_feat, "DBSum", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.AddField_management(bin_allstrm_link_feat, "DBCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    if arcpy.Exists(db_feat):

        dbsum_fields = ['SUM','DBSum']
        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,dbsum_fields) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                else:
                    row[1] = row[0]
                cursor.updateRow(row)

        arcpy.DeleteField_management(bin_allstrm_link_feat, "SUM")

    else:
        dbsum_fields = ['DBSum']
        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,dbsum_fields) as cursor:
            for row in cursor:
                row[0] = 0
                cursor.updateRow(row)


    db_fields = ['DBSum','DBCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,db_fields) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            elif row[0] > db_sum_threshold:
                row[1] = 0
            else:
                row[1] = 1
            cursor.updateRow(row)

    arcpy.DeleteField_management(bin_allstrm_link_feat, "DBSum")
    arcpy.DeleteField_management(bin_allstrm_link_feat, "MIN")

#DETERMINE IF THEY ARE MODEL WORTHY....~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    print('     Determining if Stream Segment Should Be Included in Debris-Flow Modeling...')

    # Calc
    arcpy.AddField_management(bin_allstrm_link_feat, "AreaCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    areacl_fields = ['Acc_Cl','AreaCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,areacl_fields) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[1] = row[0]
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "BurnCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    burncl_fields = ['burn_bin','BurnCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,burncl_fields) as cursor:
        for row in cursor:
            if row[0] == 1:
                row[1] = 1
            else:
                row[1] = 0
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "PerimCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    perimcl_fields = ['Perim','PerimCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,perimcl_fields) as cursor:
        for row in cursor:
            if row[0] == 1:
                row[1] = 100
            else:
                row[1] = 0
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "PctBurn", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    pct_burn_field_list = ['bacc','facc','PctBurn']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,pct_burn_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[2] = row[0] / row[1]
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "PctBurnCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    pctburn_fields = ['PctBurn','PctBurnCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,pctburn_fields) as cursor:
        for row in cursor:
            if row[0] >= pct_burn_threshold:
                row[1] = 1
            else:
                row[1] = 0
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "ConfineCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    confine_fields = ['conf','ConfineCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,confine_fields) as cursor:
        for row in cursor:
            if row[0] <= confine_threshold_degree:
                row[1] = 1
            else:
                row[1] = 0
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "SlopeCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    slope_fields = ['slppct','SlopeCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,slope_fields) as cursor:
        for row in cursor:
            if row[0] >= slope_threshold_pct:
                row[1] = 1
            else:
                row[1] = 0
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "MorphCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    morphcl_field_list = ['SlopeCl','ConfineCl','MorphCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,morphcl_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[2] = row[0] * row[1]
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "NonDevCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    nondevcl_field_list = ['DBCl','DevCl','NonDevCl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,nondevcl_field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            else:
                row[2] = row[0] * row[1]
            cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "InsidePerim_Cl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    inside_cl_field_list = ['DevCl','MorphCl','PerimCl','AreaCl','DBCl','InsidePerim_Cl']
    with arcpy.da.UpdateCursor(bin_allstrm_link_feat,inside_cl_field_list) as cursor:
        for row in cursor:
            if None in row[0:5]:
                pass
            else:
                row[5] = ((row[0] * row[1]) + row[2]) * row[3] * row[4]
            cursor.updateRow(row)


    arcpy.AddField_management(bin_allstrm_link_feat, "OutsidePerim_Cl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    outside_cl_field_list = ['Perim_BuffCl','ConfineCl','SlopeCl','DBCl','AreaCl','DevCl','PctBurnCl','OutsidePerim_Cl']

    if segment_guess == 'PERIM':
        #outside_expression = "(!Perim_BuffCl! + !ConfineCl! + !SlopeCl!)  * !DBCl! * !AreaCl! * !DevCl! * !PctBurnCl!"
        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,outside_cl_field_list) as cursor:
            for row in cursor:
                if None in row[0:7]:
                    pass
                else:
                    row[7] = (row[0] + row[1] + row[2]) * row[3] * row[4] * row[5] * row[6]
                cursor.updateRow(row)
    else:
        #outside_expression = "!ConfineCl! * !SlopeCl! * !DBCl! * !AreaCl! * !DevCl!"
        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,outside_cl_field_list) as cursor:
            for row in cursor:
                if None in row[0:7]:
                    pass
                else:
                    row[7] = row[1] * row[2] * row[3] * row[4] * row[5]
                cursor.updateRow(row)

    arcpy.AddField_management(bin_allstrm_link_feat, "zModCl", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    zModCl_field_list = ['InsidePerim_Cl','OutsidePerim_Cl','zModCl']

    if segment_guess == 'PERIM':

        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,zModCl_field_list) as cursor:
            for row in cursor:
                if None in row[0:2]:
                    pass
                else:
                    row[2] = row[0] + row[1]
                cursor.updateRow(row)
    else:

        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,zModCl_field_list) as cursor:
            for row in cursor:
                if None in row[0:2]:
                    pass
                else:
                    row[2] = row[1]
                cursor.updateRow(row)


    arcpy.AddField_management(bin_allstrm_link_feat, "ModelClass", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    modcl_fields = ['zModCl','ModelClass']
    if segment_guess == 'PERIM':

        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,modcl_fields) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] >= 12:
                    row[1] = 1
                else:
                    row[1] = 0
                cursor.updateRow(row)
    else:
        with arcpy.da.UpdateCursor(bin_allstrm_link_feat,modcl_fields) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                else:
                    row[1] = row[0]
                cursor.updateRow(row)

# COPY RESULTS TO INPUT DATABASE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    print('     Preparing Stream Network for Manual Verification...')


    step1_strm_feat = os.path.join(firein_gdb,i+'_step1_strm_feat')
    step1_strm_feat_copy = os.path.join(firein_gdb,i+'_step1_strm_feat_PREEDITCOPY')
    arcpy.Copy_management(bin_allstrm_link_feat, step1_strm_feat)
    arcpy.Copy_management(bin_allstrm_link_feat, step1_strm_feat_copy)

# BUILD STREAM WORK APRX

    print('     Building APRX for Manual Verification...')

    blank_aprx_name = 'StreamWork_Template.aprx'
    blank_aprx = os.path.join(streamwork_symbology_dir,blank_aprx_name)

    streamwork_aprx_name = i+'_streamwork.aprx'
    streamwork_aprx = os.path.join(workingdir,streamwork_aprx_name)

    shutil.copyfile(blank_aprx,streamwork_aprx)

    streamworkAPRX = arcpy.mp.ArcGISProject(streamwork_aprx)

    streamworkmap = streamworkAPRX.listMaps()[0]

    #DEFINE SYMBOLOGY LAYERS

    streamwork_segment_symbology_name = 'StreamWork_ModelClass.lyr'
    streamwork_segment_symbology = os.path.join(streamwork_symbology_dir,streamwork_segment_symbology_name)

    streamwork_perim_symbology_name = 'StreamWork_Perim.lyr'
    streamwork_perim_symbology = os.path.join(streamwork_symbology_dir,streamwork_perim_symbology_name)

    streamwork_db_symbology_name = 'StreamWork_DebrisBasin.lyr'
    streamwork_db_symbology = os.path.join(streamwork_symbology_dir,streamwork_db_symbology_name)

    streamwork_soils_symbology_name = 'StreamWork_Soils.lyr'
    streamwork_soils_symbology = os.path.join(streamwork_symbology_dir,streamwork_soils_symbology_name)

    streamwork_shd_symbology_name = 'StreamWork_HillShade.lyr'
    streamwork_shd_symbology = os.path.join(streamwork_symbology_dir,streamwork_shd_symbology_name)

    DFTools_ArcGIS.AddSymbolizedRasterToMap(shd,streamwork_shd_symbology,streamworkmap,streamworkAPRX,scratch,0)

    if soil_check == 1:
        pass
    else:
        DFTools_ArcGIS.AddSymbolizedFeatureToMap(fire_soils_feat,streamwork_soils_symbology,streamworkmap,streamworkAPRX,scratch,40)
    if db_check == 1:
        DFTools_ArcGIS.AddSymbolizedFeatureToMap(db_feat,streamwork_db_symbology,streamworkmap,streamworkAPRX,scratch,0)
    else:
        pass

    DFTools_ArcGIS.AddSymbolizedFeatureToMap(perim_feat,streamwork_perim_symbology,streamworkmap,streamworkAPRX,scratch,0)

    DFTools_ArcGIS.AddSymbolizedFeatureToMap(step1_strm_feat,streamwork_segment_symbology,streamworkmap,streamworkAPRX,scratch,0)


# MAKE TEXT FILES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if make_webtext == 'YES':
        print('     Generating Text File for Web...')

        lat, lon = DFTools_ArcGIS.CentroidLatLon(centroid_feat)

        perim_area_array = arcpy.da.TableToNumPyArray(perim_feat,'Shape_Area')
        total_area_m2 = perim_area_array["Shape_Area"].sum()
        total_area_km2 = total_area_m2 / 1000000.0

        if arcpy.Exists(db_feat):
            db_check = 'Yes'
        else:
            db_check = 'No'

        fire_webinfo = os.path.join(workingdir,i+"_webinfo.txt")
        fire_webinfo_backup = os.path.join(backup_dir,i+'_webinfo.txt')

        target = open(fire_webinfo,'wt')
        target.write("Fire Name = "+fire_name_full+'\n')
        target.write("Fire Location = "+fire_location+'\n')
        target.write("Fire Start Date = "+fire_start_date+'\n')
        target.write("Lat / Lon = "+str(lat)+','+str(lon)+'\n')
        target.write("Fire Size (km^2) = "+str("%.1f" % total_area_km2)+'\n')
        target.write("Debris Basins = "+db_check+'\n')
        target.write("State = "+fire_state_name+'\n')
        target.close()
    else: pass

    if make_booktext == 'YES':

        print('     Generating Text File for Bookkeeping...')
        analyst = os.getenv('username')
        timestamp_gmt = time.strftime('%Y-%m-%d %H:%M:%S', now)
        fire_bookinfo_name = 'DFAssessment_AnalyzedPerimeters.txt'
        fire_bookinfo = os.path.join(perim_dir,fire_bookinfo_name)
        target = open(fire_bookinfo,'a')
        bookkeep_string = i+','+fire_name_full+','+fire_location+','+fire_start_date+','+str(lat)+'N,'+str(lon)+'W,'+str(int(total_area_km2))+','+timestamp_gmt+','+analyst
        target.write(bookkeep_string+'\n')
        target.close()

    else: pass



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

    print(" Processing Finished at "+str(hour)+":"+str(minute)+" GMT")

    if log_modelrun == 'YES':
        string = 'Finished Step 1'
        write_log(logfile,i,string)

    arcpy.env.overwriteOutput = True
    arcpy.ClearEnvironment("cellSize")
    arcpy.ClearEnvironment("extent")
    arcpy.ClearEnvironment("snapRaster")
    arcpy.ClearEnvironment("mask")
    arcpy.ResetEnvironments()

print('')
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('Step 1 Analysis Results: ')

for soil_string in soil_warn_list:
    print(soil_string)
print('    Perform Manual Verification of Stream Network, Then Proceed to Step 2')
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('')
