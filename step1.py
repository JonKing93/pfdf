# This step of the code seems to implement the algorithm that determines the
# stream network.

# My modules
import paths
import parameters
import options
import notify
import calculate
import ensure

# External modules
import arcpy
import os.path

# Notify console of current step
notify.step1()

# Set up arcpy.
arcpy.CheckOutExtension('3D')
arcpy.CheckOutExtension('spatial')
arcpy.env.overwriteOutput = True

# !!!!!!!!!
# Eventually should reexamine early parts of the original script
# for example, check that files exist, make the log file, set overwrite options, etc

# Get UTM zone of the centroid of the fire perimeter
utmzone = calculate.utmzone(paths.perimeter, paths.utm, paths.dissolved,
                         paths.centroid, paths.centroid_utm, paths.zone)

# Notify console. Get the spatial reference for the zone
notify.utmzone(utmzone)
utmzone = os.path.join(paths.projection, f"UTMZone_{utmzone}_Perim_Feat")
utmzone = arcpy.Describe(utmzone).spatialReference

# Calculate the box of extent
notify.rectangle()
calculate.extent(paths.perimeter, paths.bounds, paths.extent_feature,
                 parameters.extent_buffer, paths.extent_raster, parameters.cellsize)

# Use existing fire-perimeter DEM data if it exists
if arcpy.Exists(paths.firedem_existing):
    notify.dem(exists=True)
    paths.firedem = paths.firedem_existing

# Otherwise, need to create fire DEM. Identify DEM tiles containing the fire perimeter
else:
    notify.dem(exists=False)
    tiles = calculate.firetiles(paths.extent_feature, paths.reference_tiles,
                                paths.projected, paths.intersect, paths.firetiles)
    notify.tiles(tiles)

    # Get the folders holding the DEM tiles for the fire area
    demfolders = []
    for tile in tiles:
        folder = f"grd{tile}_13"
        path = os.path.join(paths.demdata, tile, folder)
        demfolders.append(path)

    # Create a raster mosaic from the DEM tiles and project into the UTM zone
    calculate.mosaic(demfolders, paths.mosaic)
    notify.projecting()
    arcpy.management.ProjectRaster(paths.mosaic, paths.firedem, utmzone,
                                   'BILINEAR', parameters.cellsize)

# Use existing debris-basins for the fire if they exist
if arcpy.Exists(paths.basins_existing):
    notify.basins(exist=True)
    paths.basins = paths.basins_existing

# Otherwise, search for known basins in the fire extent box
else:
    notify.basins(exist=False)
    calculate.clip(paths.extent_feature, paths.basins_dataset, paths.projected, paths.clipped)
    nBasins = int(arcpy.management.GetCount(paths.clipped).getOutput(0))
    notify.nBasins(nBasins)

    # If there are basins in the extent, save them as the basins for the fire
    if nBasins > 0:
        arcpy.management.CopyFeatures(paths.clipped, paths.basins)

    # Ensure inputs use the same projection. Start by noting dataset characteristics
    notify.projections()
    names = ["Burn Perimeter", "DEM", "Debris Basins", "Burn Severity", "dNBR"]
    files = ["extent_feature", "firedem", "basins", "severity", "dnbr"]
    toUTM = ["extent_utm", "dem_utm", "basins_utm", "severity_utm", "dnbr_utm"]
    required = [True, True, False, False, False]
    israster = [False, True, False, True, True]

    # Re-project any inputs that are not in UTM
    for (name, file, newfile, required, israster) in zip(names, files, toUTM, required, israster):
        path = getattr(paths, file)
        reprojected = getattr(paths, newfile)
        utmpath = ensure.projection(name, path, utmzone, reprojected, required, israster, parameters.cellsize)
        setattr(paths, files, utmpath)
    notify.projected(utmzone)

    # Get the sizes of the input rasters
    notify.extent()
    dem_size      = calculate.rasterSize(dem)
    severity_size = calculate.rasterSize(severity, required=False)
    dnbr_size     = calculate.rasterSize(dnbr, required=False)

    # Check if input rasters need to be regridded
    regrid_severity = True
    regrid_dnbr = True
    if severity_size == dem_size:
        regrid_severity = False
    if dnbr_size == dem_size:
        regrid_dnbr = False

    # Notify console whether regridding is necessary.
    if (not regrid_severity) and (not regrid_dnbr):
        notify.extent(shared=True)
    else:
        notify.extent(shared=False)

        # Regrid rasters
        bounds = Raster(paths.extent_raster)
        paths.dem = calculate.regrid("DEM", paths.dem, bounds, paths.dem_regrid)
        if regrid_severity:
            paths.severity = calculate.regrid(paths.severity, bounds, paths.severity_regrid)
        if regridDNBR:
            paths.dnbr = calculate.regrid(paths.dnbr, bounds, paths.dnbr_regrid)
        notify.extent(shared=True)

    # Extract soil data. Clip soil database to fire perimeter
    notify.soils()
    calculate.clip(paths.extent_feature, paths.soil_database, paths.soil)

    # Check for missing soil data. Notify console if missing
    soil_properties = ["KFFACT", "THICK"]
    for property in soil_properties:
        values = arcpy.da.TableToNumPyArray(paths.soil, property)
        if np.amin(values) <= 0:
            notify.missing_soil(property, paths.soil)

    # Define the burned area. Use the dissolved polygons as the perimeter
    notify.burn()
    paths.perimeter = paths.dissolved

    # List metadata fields and values that should be added to the perimeter
    fields = ["ID",   "Name", "Location", "Start_Date"]
    types =  ["TEXT", "TEXT", "TEXT", "DATE"]
    values = [fire.id, fire.name, fire.location, fire.start]

    # Add the metadata values
    for (field, type, value) in zip(fields, types, values):
        arcpy.management.AddField(paths.perimeter, field, type)
        with arcpy.da.UpdateCursor(paths.perimeter, field) as cursor:
            row = next(cursor)
            row = value
            cursor.updateRow(row)

    # Buffer the fire perimeter
    arcpy.analysis.Buffer(paths.perimeter, paths.buffered,
                          parameters.perim_buffer_dist_m, dissolve_option='ALL')

    # Convert the perimeter and buffered perimeter to rasters using the DEM's grid
    arcpy.env.cellSize = paths.firedem
    arcpy.env.snapRaster = paths.firedem
    arcpy.conversion.FeatureToRaster(paths.buffered, 'OBJECTID', paths.buffered_raster)
    arcpy.conversion.FeatureToRaster(paths.perimeter, 'OBJECTID', paths.perimeter_raster)

    # Save missing data masks for the rasters. Use 0, 10 for the buffered mask
    arcpy.ddd.Reclassify(paths.buffered_raster, "VALUE", "NoData 0;1 10", paths.buffered_mask)
    if segment_guess == "PERIM":
        arcpy.ddd.Reclassify(paths.perimeter_raster, "VALUE", "NoData 0", paths.mask)

    # If not using the perimeter mask, fill DEM values outside the perimeter with NoData
    else:
        paths.mask = paths.perimeter_raster
        dem_masked = Raster(paths.perimeter_raster) * Raster(paths.firedem)
        dem_masked.save(paths.firedem_masked)
        paths.firedem = paths.firedem_masked

    # Calculate slope
    notify.slope()
    slope = arcpy.sa.Slope(paths.firedem, "PERCENT_RISE")
    slope.save(paths.slope)

    # Calculate hillshade
    notify.hillshade()
    hillshade = arcpy.sa.Hillshade(paths.firedem)
    hillshade.save(paths.hillshade)

    # If there is a burn severity map, clip to the fire perimeter. Locate
    # burned areas.
    if arcpy.Exists(paths.severity):
        severity = Raster(paths.severity) * Raster(paths.perimeter_raster)
        isburned = severity >= 2
        isburned.save(paths.isburned)

        # Also locate missing data values
        ismissing = arcpy.sa.IsNull(severity)
        hasdata = arcpy.sa.Con(ismissing, 0, 1)
        hasdata.save(paths.hasburndata)

    # Otherwise, use the fire perimeter directly as the burn masks
    else:
        paths.isburned = paths.perimeter_raster
        paths.hasburndata = paths.mask

    # Convert DEM to TIF for use with TauDEM.
    arcpy.env.compression = "NONE"
    if segment_guess == "NO_PERIM":
        arcpy.env.extent = paths.perimeter_raster
    arcpy.conversion.RasterToOtherFormat(paths.firedem, paths.firedem_tiff, "TIFF")

    # Remove pits
    pitremove = f"PitRemove -z {paths.firedem} -fel {paths.pitfilled}"
    os.system(pitremove)

    # Calculate D8 and D-infinity flow directions
    d8flow = f"D8FlowDir -fel {paths.pitfilled} -p {paths.d8flow} -sd8 {paths.d8slope}"
    os.system(d8flow)
    diflow = f"DinfFlowDir -fel {paths.pitfilled} -ang {paths.diflow} -slp {paths.dislope}"
    os.system(diflow)

    # Calculate D8 upslope area. Also get relief and length (vertical and
    # horizontal components of the longest flow path). Relief and length are
    # based on D-Infinity flow outputs - use a threshold of 0.49 so that the
    # processing of these outputs mimics a D8 flow model.
    area = f"AreaD8 -p {paths.d8flow} -ad8 {paths.d8area} -nc"
    os.system(area)
    relief = f"DinfDistUp -ang {paths.diflow} -fel {paths.pitfilled} -du {paths.d8relief} -m max v -nc -thresh 0.49"
    os.system(relief)
    length = f"DinfDistUp -ang {paths.diflow} -fel {paths.pitfilled} -du {paths.d8length} -m max h -nc -thresh 0.49"
    os.system(length)

    # Export TauDEM to ArcGIS workspace
    # !!!!!!!!!!!!!!! This should be removed eventually
    notify.taudem_export()
    export.raster(paths.d8flow, paths.flow)
    export.raster(paths.d8area, paths.area)
    export.raster(paths.d8relief, paths.relief)
    export.raster(paths.d8length, paths.length)

    # Reclassify TauDEM flow directions to mimic ArcPy flow directions
    notify.flow_translation()
    mapping = ";".join(["1 1", "2 128", "3 64", "4 32", "5 16", "6 8", "7 4", "8 2"]) # e.g. from 2 to 128
    arcpy.ddd.Reclassify(paths.d8flow, "VALUE", mapping, paths.flow, "NODATA")

    # Locate upstream area greater within the maximum
    normal_area = Raster(paths.flow) < parameters.max_acc
    normal_area.save(normal_area)

    # Convert burn mask to TIFF
    arcpy.env.compression = "NONE"
    arcpy.conversion.RasterToOtherFormat(paths.hasburndata, paths.hasburn_tiff, "TIFF")

    # Use TauDEM to get the cumulative upslope burned area
    notify.burn_area()
    d8area = f"AreaD8 -p {paths.d8flow} -ad8 {paths.d8burned_area} -wg {paths.hasburn_tiff} -nc"
    os.system(d8area)
    # !!!!!!! Next line should not be required
    export.raster(paths.d8burned_area, paths.burned_area)

    # Define the stream network.
    notify.streams()
    all_area = arcpy.Raster(paths.area)
    burned_area = arcpy.Raster(paths.burned_area)
    streams = arcpy.sa.Con((all_area >= parameters.min_acc) & (burned_area > parameters.burn_acc_threshold), 1)
    streams.save(paths.stream_raster)

    # Get the stream linkages
    arcpy.env.cellSize = dem
    arcpy.env.snapRaster = dem
    arcpy.env.extent = perim
    stream_links = arcpy.sa.StreamLink(paths.streams_raster, paths.flow)

    # Convert stream raster to polyline feature. Place points at fixed intervals
    # along the network and use to split into stream segments.
    arcpy.conversion.RasterToPolyline(paths.streams_raster, paths.streams, simplify="NO_SIMPLIFY")
    interval = f"{parameters.max_segment_length_m} Meters"
    arcpy.management.GeneratePointsAlongLines(paths.streams, paths.stream_points, "DISTANCE", interval)
    arcpy.management.SplitLineAtPoint(paths.streams, paths.stream_points, paths.segments, search_radius="2")
    
    # Assign a segment ID attribute to the segments. The segment ID should match the object ID
    arcpy.management.AddField(paths.segments, "Segment_ID", "LONG",
                 field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED")
    cursorFields = ["OBJECTID", "SEGMENT_ID"]
    with arcpy.da.UpdateCursor(paths.segments, cursorFields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    # Remove unneeded fields
    remove = ["arcid", "grid_code", "from_node", "to_node"]
    arcpy.management.DeleteField(stream.segments, remove)

    # Convert the stream segments back to a raster wherein the raster value is
    # the ID number of the stream segment
    arcpy.env.cellSize = dem
    arcpy.env.extent = dem
    arcpy.env.snapRaster = dem
    arcpy.conversion.PolylineToRaster(paths.segments, "Segment_ID", paths.segment_raster)

    # Convert the stream raster back to a network
    # ????? It seems odd that we convert to raster and then convert right back to feature
    arcpy.sa.StreamToFeature(paths.segment_raster, paths.flow, paths.segments2, "NO_SIMPLIFY")
    arcpy.management.AlterField(paths.segments2, "grid_code", "Segment_ID")

    # Get the stream order number
    strahler = arcpy.sa.StreamOrder(paths.segment_raster, paths.flow, "STRAHLER")
    strahler.save(paths.strahler_raster)
    arcpy.sa.StreamToFeature(paths.strahler_raster, paths.flow, paths.strahler, "NO_SIMPLIFY")




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
