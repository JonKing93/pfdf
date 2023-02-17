import arcpy
import numpy
import scipy
from scipy import stats

import os
from arcpy import env
from arcpy import gp
from arcpy import sa
from arcpy.sa import *
import DFTools_TauDEM_PRO as DFTools_TauDem

import shutil
import zipfile
import glob

def Extract_Severity(i,perim_feat,sev,dem,temp_gdb):

    perim = os.path.join(temp_gdb,i+"_perim")
    perim_null = os.path.join(temp_gdb,"z"+i+"_perim")
    perim_bin = os.path.join(temp_gdb,i+"_perbin")
    zburn = os.path.join(temp_gdb,"z"+i+"_burn")
    burn = os.path.join(temp_gdb,i+"_burn")

    burn_null = os.path.join(temp_gdb,i+"_bnull")
    burn_bin = os.path.join(temp_gdb,i+"_burnbin")

    perim_sev = os.path.join(temp_gdb,i+"_psev")
    low = os.path.join(temp_gdb,i+"_low")
    mod = os.path.join(temp_gdb,i+"_mod")
    high = os.path.join(temp_gdb,i+"_high")
    hm = os.path.join(temp_gdb,i+"_hm")
    hm_null = os.path.join(temp_gdb,i+"_hmnull")
    hm_bin = os.path.join(temp_gdb,i+"_hmbin")

    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    dem_info = arcpy.Raster(dem)
    cell_res = dem_info.meanCellHeight

    arcpy.AddField_management(perim_feat, "Perim_ID", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    arcpy.CalculateField_management(perim_feat, "Perim_ID", "1", "PYTHON", "")

    arcpy.FeatureToRaster_conversion(perim_feat, "Perim_ID", perim)

    out_perim_null = IsNull(perim)
    out_perim_null.save(perim_null)

    out_perim_bin = Con(Raster(perim_null) > 0, 0, 1)
    out_perim_bin.save(perim_bin)

    out_zburn = Con(Raster(sev) >= 2, 1)
    out_zburn.save(zburn)
    out_burn = Raster(zburn) * Raster(perim)
    out_burn.save(burn)

    out_perim_sev = Raster(sev) * Raster(perim)
    out_perim_sev.save(perim_sev)

    out_low = Con(Raster(perim_sev) == 2, 1)
    out_low.save(low)
    out_mod = Con(Raster(perim_sev) == 3, 1)
    out_mod.save(mod)
    out_high = Con(Raster(perim_sev) == 4, 1)
    out_high.save(high)
    out_hm = Con(Raster(perim_sev) >= 3, 1)
    out_hm.save(hm)


def Extract_SlopesGreaterThan(i,slp,slope_value_list):

    for slope_value in slope_value_list:

        (slp_path,slp_name) = os.path.split(slp)
        slp = os.path.join(slp_path,slp_name)
        sval_name = (slp_name+"_"+str(slope_value))
        sval = os.path.join(slp_path,sval_name)
        sval_bin = os.path.join(slp_path,slp_name+"_"+str(slope_value)+"bin")
        out_sval = Con(Raster(slp) >= slope_value, 1)
        out_sval.save(sval)
        out_sval_bin = Con((IsNull(sval)) > 0, 0, 1)
        out_sval_bin.save(sval_bin)


def Extract_SlopesBetween(i,slp,slope_between_list):
    min_slp = slope_between_list[0]
    max_slp = slope_between_list[1]

    (slp_path,slp_name) = os.path.split(slp)
    slp_between_name = i+'_s'+str(min_slp)+'_'+str(max_slp)
    slp_between = os.path.join(slp_path,slp_between_name)

    slp_between_bin_name = i+'_s'+str(min_slp)+'_'+str(max_slp)+'_bin'
    slp_between_bin = os.path.join(slp_path,slp_between_bin_name)

    out_slp_between = Con((Raster(slp) >= min_slp) & (Raster(slp) <= max_slp), 1)
    out_slp_between.save(slp_between)
    out_slp_between_bin = Con((IsNull(slp_between)) > 0, 0, 1)
    out_slp_between_bin.save(slp_between_bin)






def Upslope_Pct(in_upbinary,out_raster_pct,facc):

    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("spatial")
    workingdir = os.getcwd()
    env.workspace = workingdir

    arcpy.env.overwriteOutput = True

    (in_upbinary_path, in_upbinary_name) = os.path.split(in_upbinary)

    out_raster = (Raster(in_upbinary) / Raster(facc)) * 100.0
    out_raster.save(out_raster_pct)

def Upslope_Prop(in_upbinary,out_raster_prop,facc):

    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("spatial")
    workingdir = os.getcwd()
    env.workspace = workingdir

    arcpy.env.overwriteOutput = True

    (in_upbinary_path, in_upbinary_name) = os.path.split(in_upbinary)

    out_raster = Raster(in_upbinary) / Raster(facc)
    out_raster.save(out_raster_prop)


def Upslope_Mean(in_upsum,out_raster,facc):

    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("spatial")
    workingdir = os.getcwd()
    env.workspace = workingdir

    arcpy.env.overwriteOutput = True

    (in_upsum_path, in_upsum_name) = os.path.split(in_upsum)


    out_upslope_mean = Raster(in_upsum) / Raster(facc)
    out_upslope_mean.save(out_raster)

def Upslope_Area_m2(in_upbinary,out_aream2,cell_res):


    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("spatial")
    workingdir = os.getcwd()
    env.workspace = workingdir

    arcpy.env.overwriteOutput = True

    (upbinary_path, up_binary_name) = os.path.split(in_upbinary)

    out_upslope_m2 = Raster(in_upbinary) * cell_res * cell_res
    out_upslope_m2.save(out_aream2)



def Upslope_Area_km2(in_upbinary,out_areakm2,cell_res):

    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("spatial")
    workingdir = os.getcwd()
    env.workspace = workingdir

    arcpy.env.overwriteOutput = True

    (in_upbinary_path, in_upbinary_name) = os.path.split(in_upbinary)

    (upbinary_path, up_binary_name) = os.path.split(in_upbinary)

    out_upslope_km2 = (Raster(in_upbinary) * cell_res * cell_res) / 1000000.0
    out_upslope_km2.save(out_areakm2)


def AddNumericStatToTable(in_stat_raster,in_zone_raster,in_zone_feature,stat_table,column_name,stat_name,data_type):

    arcpy.CheckOutExtension("3D")
    arcpy.CheckOutExtension("spatial")
    workingdir = os.getcwd()
    env.workspace = workingdir

    arcpy.env.overwriteOutput = True

    stat_table = ZonalStatisticsAsTable(in_zone_raster, "VALUE", in_stat_raster, stat_table, "DATA", stat_name)

    arcpy.JoinField_management(in_zone_feature, "Segment_ID", stat_table, "VALUE", stat_name)
    arcpy.AddField_management(in_zone_feature, column_name, data_type, "", 2, "", "", "NULLABLE", "NON_REQUIRED", "")

    with arcpy.da.UpdateCursor(in_zone_feature, [stat_name,column_name]) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

##    arcpy.CalculateField_management(in_zone_feature, column_name, calc_field_stat, "PYTHON", "")
    delete_string = "Join_Count;TARGET_FID;"+stat_name
    arcpy.DeleteField_management(in_zone_feature, delete_string)


def ReplaceNull(in_raster,out_raster,replace_value,data_value):

    (in_raster_path,in_raster_name) = os.path.split(in_raster)
    out_isnull_name = in_raster_name+'_null'
    out_isnull = os.path.join(in_raster_path,out_isnull_name)

    out_null = IsNull(in_raster)
    out_null.save(out_isnull)

    out_raster_bin = Con(Raster(out_isnull) > 0, replace_value, data_value)
    out_raster_bin.save(out_raster)

def CalcMaxValue(prefix,zone_array,uniqueid_array,value_array,id_array,workingdir):

    import numpy
    import scipy
    from scipy import stats
    from scipy.stats import itemfreq

    zone_min = min(zone_array)
    zone_max = max(zone_array)

    unique_zone_count = scipy.stats.itemfreq(zone_array)

    n_zone = len(unique_zone_count)

    summary_table = numpy.zeros( (n_zone,4) )


    for j in range(0,n_zone,1):
        zone = unique_zone_count[j,0]
        zone_true = zone_array == zone

        zone_true_values = value_array[zone_true]
        zone_true_ids = id_array[zone_true]

        zone_max_value = max(zone_true_values)

        zone_true_unique_ids = uniqueid_array[zone_true]



        zone_max_value_true = zone_true_values == zone_max_value
        zone_max_value_uniqueid_tiecheck = zone_true_unique_ids[zone_max_value_true]
        zone_max_value_uniqueid = zone_max_value_uniqueid_tiecheck[0]
        zone_max_value_id_tiecheck = zone_true_ids[zone_max_value_true]
        zone_max_value_id = zone_max_value_id_tiecheck[0]

        summary_table[j, 0] = zone_max_value_uniqueid
        summary_table[j, 1] = zone
        summary_table[j, 2] = zone_max_value
        summary_table[j, 3] = zone_max_value_id

    summary_max_txt_file = os.path.join(workingdir,prefix+"_PtSummary_Max.txt")

    target = open(summary_max_txt_file,'wb')
    target.write('Calc_PtEstID,Calc_Zone,Calc_Value,Calc_ID\n')

    for k in range(0,len(summary_table),1):
        print_str = str(int(summary_table[k,0]))+','+str(int(summary_table[k,1]))+','+str(int(summary_table[k,2]))+','+str(int(summary_table[k,3]))+'\n'
        target.write(print_str)
    target.close

    return summary_max_txt_file

def CalcMinValue(prefix,zone_array,uniqueid_array,value_array,id_array,workingdir):

    import numpy
    import scipy
    from scipy import stats
    from scipy.stats import itemfreq

    zone_min = min(zone_array)
    zone_max = max(zone_array)

    unique_zone_count = scipy.stats.itemfreq(zone_array)

    n_zone = len(unique_zone_count)

    summary_table = numpy.zeros( (n_zone,4) )


    for j in range(0,n_zone,1):
        zone = unique_zone_count[j,0]
        zone_true = zone_array == zone

        zone_true_values = value_array[zone_true]
        zone_true_ids = id_array[zone_true]

        zone_true_unique_ids = uniqueid_array[zone_true]

        zone_min_value = min(zone_true_values)

        zone_min_value_true = zone_true_values == zone_min_value
        zone_min_value_id_tiecheck = zone_true_ids[zone_min_value_true]
        zone_min_value_uniqueid_tiecheck = zone_true_unique_ids[zone_min_value_true]
        zone_min_value_uniqueid = zone_min_value_uniqueid_tiecheck[0]
        zone_min_value_id = zone_min_value_id_tiecheck[0]


        summary_table[j, 0] = zone_min_value_uniqueid
        summary_table[j, 1] = zone
        summary_table[j, 2] = zone_min_value
        summary_table[j, 3] = zone_min_value_id

    summary_min_txt_file = os.path.join(workingdir,prefix+"_PtSummary_Min.txt")

    target = open(summary_min_txt_file,'wb')
    target.write('Calc_PtEstID,Calc_Zone,Calc_Value,Calc_ID\n')

    for k in range(0,len(summary_table),1):
        print_str = str(int(summary_table[k,0]))+','+str(int(summary_table[k,1]))+','+str(int(summary_table[k,2]))+','+str(int(summary_table[k,3]))+'\n'
        target.write(print_str)
    target.close

    return summary_min_txt_file


def CalcPixelLength(in_fdir,out_fdir_length,workingdir):

    fdir_info = arcpy.Raster(in_fdir)
    cell_res = fdir_info.meanCellHeight

    [fdir_path,fdir_name] = os.path.split(in_fdir)

    length_remap = os.path.join(workingdir,fdir_name+"_FDirLengthRemap.txt")

    target = open(length_remap,'wb')
    target.write("1 : 10000\n")
    target.write("2 : 14142\n")
    target.write("4 : 10000\n")
    target.write("8 : 14142\n")
    target.write("16 : 10000\n")
    target.write("32 : 14142\n")
    target.write("64 : 10000\n")
    target.write("128 : 14142\n")
    target.close()

    zlength_calc = os.path.join(fdir_path,fdir_name+"zlcalc")
    zlength_calc2 = os.path.join(fdir_path,fdir_name+"zlcalc2")


    outzlength_calc = arcpy.sa.ReclassByAStent_pathCIIFile(in_fdir,length_remap,"NODATA")
    outzlength_calc.save(zlength_calc)
    outzlength_calc2 = (Raster(zlength_calc) / 10000.0)
    outzlength_calc2.save(zlength_calc2)

    outlength_calc3 = Raster(zlength_calc2) * cell_res
    outlength_calc3.save(out_fdir_length)


def ExtractFeaturesDiffProj(extent, basins, clipped):
    """
    !!!!!!!!!
    This has been moved and refactored into calculate.clip
    """

    ### Other inputs
    extent_projected
    clipped_raw
    ###

    # Get the spatial references
    extent_projection = arcpy.Describe(basins).spatialReference
    basins_projection = arcpy.Describe(basins).spatialReference

    # Project the extent box into the same system as the basins. Clip the 
    # basins to the fire extentbox, then project the clipped basins back into
    # the projection of the original extent box
    arcpy.Project_management(extent, extent_projected, basins_projection)
    arcpy.Clip_analysis(basins, extent_projected, clipped_raw)
    arcpy.Project_management(clipped_raw, clipped, extent_projection)
    arcpy.Delete_management(clipped_raw)



def ExtractRasterDiffProj(in_extent_raster,in_extract_raster,out_extract_raster):

    [in_extract_raster_path,in_extract_raster_name] = os.path.split(in_extract_raster)
    [in_extent_raster_path,in_extent_raster_name] = os.path.split(in_extent_raster)

    in_extent_raster_desc = arcpy.Describe(in_extent_raster)
    in_extent_raster_spatial_ref = in_extent_raster_desc.SpatialReference
    in_extent_raster_cell_res = in_extent_raster_desc.meanCellHeight

    in_extract_raster_desc = arcpy.Describe(in_extract_raster)
    in_extract_raster_spatial_ref = in_extract_raster_desc.SpatialReference
    in_extract_raster_cell_res = in_extract_raster_desc.meanCellHeight

    in_extract_box_raster_name = in_extract_raster_name+'_box'
    in_extract_box_raster = os.path.join(in_extent_raster_path,in_extract_box_raster_name)

    out_z_extract_raster_name = 'z'+in_extract_raster_name
    out_z_extract_raster = os.path.join(in_extent_raster_path,out_z_extract_raster_name)

    arcpy.ProjectRaster_management(in_extent_raster,in_extract_box_raster,in_extract_raster_spatial_ref,'MAJORITY',in_extract_raster_cell_res)

    outzextract = Raster(in_extract_raster) * Raster(in_extract_box_raster)
    outzextract.save(out_z_extract_raster)

    arcpy.ProjectRaster_management(out_z_extract_raster,out_extract_raster,in_extent_raster_spatial_ref,'NEAREST',in_extent_raster_cell_res)

    arcpy.Delete_management(out_z_extract_raster)

def ZipGDB(in_gdb, out_gdbzip):
   if (os.path.exists(out_gdbzip)):
      os.remove(out_gdbzip)

   zipobj = zipfile.ZipFile(out_gdbzip,'w')

   for infile in glob.glob(in_gdb+"/*"):
        filename = os.path.basename(infile)
        if filename.endswith('.lock'):
            pass
        else:
            zipobj.write(infile, os.path.join( os.path.basename(in_gdb), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
      #print ("Zipping: "+infile)

   zipobj.close()

def ZipGDBAppend(in_gdb, out_gdbzip):

   zipobj = zipfile.ZipFile(out_gdbzip,'a')

   for infile in glob.glob(in_gdb+"/*"):
        filename = os.path.basename(infile)
        if filename.endswith('.lock'):
            pass
        else:
            zipobj.write(infile, os.path.join( os.path.basename(in_gdb), os.path.basename(infile) ),zipfile.ZIP_DEFLATED)
      #print ("Zipping: "+infile)

   zipobj.close()

def CentroidLatLon(in_feat):
    desc = arcpy.Describe(in_feat)
    shapefieldname = desc.ShapeFieldName

    rows = arcpy.SearchCursor(in_feat, r'', \
                              r'GEOGCS["GCS_WGS_1984",' + \
                              'DATUM["D_WGS_1984",' + \
                              'SPHEROID["WGS_1984",6378137,298.257223563]],' + \
                              'PRIMEM["Greenwich",0],' + \
                              'UNIT["Degree",0.017453292519943295]]')


    for row in rows:
        feat = row.getValue(shapefieldname)
        pnt = feat.getPart()

        out_lat = "%.2f" % pnt.Y
        out_lon = "%.2f" % pnt.X

    return (out_lat, out_lon)

def AddSymbolizedFeatureToMap(data,symb_lyr,mapdoc,project,scratch_path,transparency):
    [data_path,data_name] = os.path.split(data)

    data_lyr_name = data_name+'.lyrx'
    data_lyr = os.path.join(scratch_path,data_lyr_name)

    arcpy.MakeFeatureLayer_management(data,data_lyr)
    arcpy.ApplySymbologyFromLayer_management(data_lyr,symb_lyr)

    data_symb_lyr_name = data_name+'_symb.lyrx'
    data_symb_lyr = os.path.join(scratch_path,data_symb_lyr_name)
    arcpy.SaveToLayerFile_management(data_lyr,data_symb_lyr,'ABSOLUTE')

    dataLyr = arcpy.mp.LayerFile(data_symb_lyr)
    mapdoc.addLayer(dataLyr,'TOP')
    dataLyr.transparency = transparency
    project.save()

def AddSymbolizedRasterToMap(data,symb_lyr,mapdoc,project,scratch_path,transparency):
    [data_path,data_name] = os.path.split(data)

    data_lyr_name = data_name+'.lyrx'
    data_lyr = os.path.join(scratch_path,data_lyr_name)

    arcpy.MakeRasterLayer_management(data,data_lyr)
    arcpy.ApplySymbologyFromLayer_management(data_lyr,symb_lyr)

    data_symb_lyr_name = data_name+'_symb.lyrx'
    data_symb_lyr = os.path.join(scratch_path,data_symb_lyr_name)
    arcpy.SaveToLayerFile_management(data_lyr,data_symb_lyr,'ABSOLUTE')

    dataLyr = arcpy.mp.LayerFile(data_symb_lyr)
    mapdoc.addLayer(dataLyr,'TOP')
    dataLyr.transparency = transparency
    project.save()


def addThresholdLegendFields(in_feat,duration,field_list):  #field_list = [acc_at_p,int_at_p,acc_atp_legend,int_at_p_legend]
    dur_h = duration / 60
    if duration == 15:

        with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] <= 3:
                    row[2] = '<3'
                elif (row[0] > 3) and (row[0] <= 4):
                    row[2] = '3 - 4'
                elif (row[0] > 4) and (row[0] <= 5):
                    row[2] = '4 - 5'
                elif (row[0] > 5) and (row[0] <= 6):
                    row[2] = '5 - 6'
                elif (row[0] > 6) and (row[0] <= 7):
                    row[2] = '6 - 7'
                elif (row[0] > 7) and (row[0] <= 8):
                    row[2] = '7 - 8'
                elif (row[0] > 8) and (row[0] <= 9):
                    row[2] = '8 - 9'
                elif (row[0] > 9) and (row[0] <= 10):
                    row[2] = '9 - 10'
                elif (row[0] > 10):
                    row[2] = '>10'
                else:
                    pass

                cursor.updateRow(row)

        with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] <= 3:
                    row[3] = '<'+str(3 / dur_h)
                elif (row[0] > 3) and (row[0] <= 4):
                    row[3] = str(3.0 / dur_h)+' - '+str(4.0 / dur_h)
                elif (row[0] > 4) and (row[0] <= 5):
                    row[3] = str(4.0 / dur_h)+' - '+str(5.0 / dur_h)
                elif (row[0] > 5) and (row[0] <= 6):
                    row[3] = str(5.0 / dur_h)+' - '+str(6.0 / dur_h)
                elif (row[0] > 6) and (row[0] <= 7):
                    row[3] = str(6.0 / dur_h)+' - '+str(7.0 / dur_h)
                elif (row[0] > 7) and (row[0] <= 8):
                    row[3] = str(7.0 / dur_h)+' - '+str(8.0 / dur_h)
                elif (row[0] > 8) and (row[0] <= 9):
                    row[3] = str(8.0 / dur_h)+' - '+str(9.0 / dur_h)
                elif (row[0] > 9) and (row[0] <= 10):
                    row[3] = str(9.0 / dur_h)+' - '+str(10.0 / dur_h)
                elif (row[0] > 10):
                    row[3] = '>'+str(10.0 / dur_h)
                else:
                    pass

                cursor.updateRow(row)

    if duration == 30:

        with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] <= 6:
                    row[2] = '<6'
                elif (row[0] > 6) and (row[0] <= 8):
                    row[2] = '6 - 8'
                elif (row[0] > 8) and (row[0] <= 10):
                    row[2] = '8 - 10'
                elif (row[0] > 10) and (row[0] <= 12):
                    row[2] = '10 - 12'
                elif (row[0] > 12) and (row[0] <= 14):
                    row[2] = '12 - 14'
                elif (row[0] > 14) and (row[0] <= 16):
                    row[2] = '14 - 16'
                elif (row[0] > 16) and (row[0] <= 18):
                    row[2] = '16 - 18'
                elif (row[0] > 18) and (row[0] <= 20):
                    row[2] = '18 - 20'
                elif (row[0] > 20):
                    row[2] = '>20'
                else:
                    pass

                cursor.updateRow(row)

        with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] <= 6:
                    row[3] = '<'+str(6 / dur_h)
                elif (row[0] > 6) and (row[0] <= 8):
                    row[3] = str(6.0 / dur_h)+' - '+str(8.0 / dur_h)
                elif (row[0] > 8) and (row[0] <= 10):
                    row[3] = str(8.0 / dur_h)+' - '+str(10.0 / dur_h)
                elif (row[0] > 10) and (row[0] <= 12):
                    row[3] = str(10.0 / dur_h)+' - '+str(12.0 / dur_h)
                elif (row[0] > 12) and (row[0] <= 14):
                    row[3] = str(12.0 / dur_h)+' - '+str(14.0 / dur_h)
                elif (row[0] > 14) and (row[0] <= 16):
                    row[3] = str(14.0 / dur_h)+' - '+str(16.0 / dur_h)
                elif (row[0] > 16) and (row[0] <= 18):
                    row[3] = str(16.0 / dur_h)+' - '+str(18.0 / dur_h)
                elif (row[0] > 18) and (row[0] <= 20):
                    row[3] = str(18.0 / dur_h)+' - '+str(20.0 / dur_h)
                elif (row[0] > 20):
                    row[3] = '>'+str(20.0 / dur_h)
                else:
                    pass

                cursor.updateRow(row)

    if duration == 60:

        with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] <= 12:
                    row[2] = '<12'
                elif (row[0] > 12) and (row[0] <= 16):
                    row[2] = '12 - 16'
                elif (row[0] > 16) and (row[0] <= 20):
                    row[2] = '16 - 20'
                elif (row[0] > 20) and (row[0] <= 24):
                    row[2] = '20 - 24'
                elif (row[0] > 24) and (row[0] <= 28):
                    row[2] = '24 - 28'
                elif (row[0] > 28) and (row[0] <= 32):
                    row[2] = '28 - 32'
                elif (row[0] > 32) and (row[0] <= 36):
                    row[2] = '32 - 36'
                elif (row[0] > 36) and (row[0] <= 40):
                    row[2] = '36 - 40'
                elif (row[0] > 40):
                    row[2] = '>40'
                else:
                    pass

                cursor.updateRow(row)

        with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
            for row in cursor:
                if row[0] == None:
                    pass
                elif row[0] <= 12:
                    row[3] = '<'+str(12 / dur_h)
                elif (row[0] > 12) and (row[0] <= 16):
                    row[3] = str(12.0 / dur_h)+' - '+str(16.0 / dur_h)
                elif (row[0] > 16) and (row[0] <= 20):
                    row[3] = str(16.0 / dur_h)+' - '+str(20.0 / dur_h)
                elif (row[0] > 20) and (row[0] <= 24):
                    row[3] = str(20.0 / dur_h)+' - '+str(24.0 / dur_h)
                elif (row[0] > 24) and (row[0] <= 28):
                    row[3] = str(24.0 / dur_h)+' - '+str(28.0 / dur_h)
                elif (row[0] > 28) and (row[0] <= 32):
                    row[3] = str(28.0 / dur_h)+' - '+str(32.0 / dur_h)
                elif (row[0] > 32) and (row[0] <= 36):
                    row[3] = str(32.0 / dur_h)+' - '+str(36.0 / dur_h)
                elif (row[0] > 36) and (row[0] <= 40):
                    row[3] = str(36.0 / dur_h)+' - '+str(40.0 / dur_h)
                elif (row[0] > 40):
                    row[3] = '>'+str(40.0 / dur_h)
                else:
                    pass

                cursor.updateRow(row)


def addPLegendFields(in_feat,field_list): #field_list = [P,PCl,PCl_Legend]

    with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            elif row[0] <= 0.20:
                row[1] = 1
                row[2] = '0-20%'
            elif (row[0] > 0.20) and (row[0] <= 0.40):
                row[1] = 2
                row[2] = '20-40%'
            elif (row[0] > 0.40) and (row[0] <= 0.60):
                row[1] = 3
                row[2] = '40-60%'
            elif (row[0] > 0.60) and (row[0] <= 0.80):
                row[1] = 4
                row[2] = '60-80%'
            elif (row[0] > 0.80) and (row[0] <= 1.00):
                row[1] = 5
                row[2] = '80-100%'
            cursor.updateRow(row)


def addVolumeLegendFields(in_feat,field_list): #field_list = [Volume,VCl,VCl_Legend]
    with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            elif row[0] <= 1000:
                row[1] = 1
                row[2] = '<1,000'
            elif (row[0] > 1000) and (row[0] <= 10000):
                row[1] = 2
                row[2] = '1,000-10,000'
            elif (row[0] > 10000) and (row[0] <= 100000):
                row[1] = 3
                row[2] = '10,000-100,000'
            elif row[0] > 100000:
                row[1] = 4
                row[2] = '>100,000'

            cursor.updateRow(row)

def addCombinedLegendFields(in_feat,field_list): #field_list = [pcl_field,vcl_field,combhaz_field]
    with arcpy.da.UpdateCursor(in_feat,field_list) as cursor:
        for row in cursor:
            if row[0] == None:
                pass
            elif row[0] <= 3:
                row[1] = 1
                row[2] = 'Low'
            elif (row[0] > 3) and (row[0] <= 6):
                row[1] = 2
                row[2] = 'Moderate'
            elif row[0] > 6:
                row[1] = 3
                row[2] = 'High'

            cursor.updateRow(row)