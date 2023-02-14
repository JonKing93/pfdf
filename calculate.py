perimeter_ID_name = "Perimeter_ID"
extent_code_field_name = "Extent_Code"


def utmzone(perimeter, stripped, dissolved, centroid, utm, zone):
    """
    calculate.utmzone  Returns the UTM zone of the centroid of the fire perimeter
    ----------
    zone = calculate.utmzone(perimeter, stripped, dissolved, centroid, utm, zone)
    Returns the UTM zone for a fire perimeter. Begins by copying the input 
    perimeter(s) to a scratch workspace and stripping all non-required fields.
    Dissolves all perimeter polygons into a single (possibly multi-part) polygon
    and determines the centroid of that polygon. Projects the centroid into UTM,
    and returns the UTM zone as an int.
    ----------
    Inputs:
        perimeter (str): The path to the input arcpy Feature holding the fire perimeter(s)
        stripped (str): The path to the output arcpy feature holding the fire
            perimeter(s) stripped of all non-required fields.
        dissolved (str): The path to the output arcpy feature with the dissolved
            fire perimeter.
        centroid (str): The path to the output arcpy feature holding the
            centroid of the fire perimeter
        utm (str): The path to the input arcpy feature used to define UTM zones
        zone (str): The path to the output arcpy feature holding the UTM zone of
            the centroid of the fire perimeter.

    Outputs:
        zone (int): The UTM zone of the centroid of the fire perimeter

    Saves:
        Files matching the paths of the dissolved, centroid, and zone inputs.
    """

    # Dissolve (merge) polygons into a single fire-perimeter polygon. Get the
    # centroid of this polygon
    arcpy.management.Dissolve(perimeter, dissolved)
    arcpy.management.FeatureToPoint(dissolved, centroid)

    # Project the centroid to UTM. Identify the zone it's in
    arcpy.management.Project(centroid, centroid, utm)
    arcpy.analysis.Identity(centroid, utm, zone)

    # Return zone as an int
    zones = arcpy.da.TableToNumPyArray(zone, "ZONE")
    zone = zones["ZONE"][0]
    return int(zone)

def extent(perimeter, perimeter_nad83, box, utmzone, box_raster, cellsize):
    """
    calculate.extent  Calculates the box of extent for the fire perimeter
    ----------
    calculate.extent(perimeter, perimeter_nad83, box, utmzone, box_raster, cellsize)
    Finds a rectangular bounding box of minimum area to surround the fire
    perimeter. Adds a buffer so the fire perimeter is not on the very edge of
    the extent box. Converts the extent box to a raster in a UTM projection.
    ----------
    Inputs:
        perimeter (str): The path to the arcpy Feature holding the fire perimeter
        perimeter_nad83 (str): The path to the arcpy Feature in which to output 
            the fire perimeter projected into the NAD83 coordinate system.
        box (str): The path to the arcpy Feature in which to output the UTM
            projected extent box.
        utmzone (str): The SpatialReference field of the UTM zone 
        box_raster (str): The path to the file in which to save the raster
            version of the extent box.
        cellsize (float): The resolution (in meters) to use when converting to raster.

    Saves:
        Files matching the names of the perimeter_nad83, box, and box_raster inputs 
    """

    # Project the fire perimeter into GCS North American 1983 (NAD83)
    if arcpy.Describe(perimeter).SpatialReference == 'GCS_North_American_1983':
        arcpy.management.CopyFeatures(perimeter, perimeter_nad83)
    else:
        arcpy.management.Project(perimeter, perimeter_nad83,
              "GEOGCS['GCS_North_American_1983',"
            + "DATUM['D_North_American_1983',"
            + "SPHEROID['GRS_1980',6378137.0,298.257222101]],"
            + "PRIMEM['Greenwich',0.0],"
            + "UNIT['Degree',0.0174532925199433]]"
        )

    # Get a rectangular bounding box that contains the fire perimeter. Place a 
    # buffer around the edges so the fire perimeter is not on the very edge
    arcpy.management.MinimumBoundingGeometry(perimeter_nad83, box, 'RECTANGLE_BY_AREA', 'ALL')
    arcpy.analysis.Buffer(box, box, 0.02)

    # Add a field for the fire extent
    field = extent_code_field_name
    arcpy.management.AddField(box, field, "SHORT")

    # ??????????
    with arcpy.da.UpdateCursor(box, field) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)

    # Project the extent box back into UTM. Convert to raster
    arcpy.management.Project(box, box, utmzone)
    arcpy.conversion.PolygonToRaster(box, field, box_raster, 'CELL_CENTER', cellsize=cellsize)
    
def demlist(dem, box, box_dem, dem_layer, tiles):
    """
    """

    # Project the extent box into the projection used by the DEM
    projection = arcpy.Describe(dem).SpatialReference
    arcpy.Project(box, box_dem, projection)

    # Create a layer where the DEM intersects the extent box.
    arcpy.management.MakeFeatureLayer(dem, dem_layer)
    arcpy.management.SelectLayerByLocation(dem_layer, "INTERSECT", box_dem)

    # ??? tiles? Get a list of DEM tiles
    arcpy.management.CopyFeatures(dem_layer, firedem)
    firedem = arcpy.da.TableToNumPyArray(firedem, "FILE_ID")
    firedem = firedem['FILE_ID']
    






