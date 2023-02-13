perimeter_ID_field_name = "Perim_ID"
extent_code_field_name = "Extent_Code"


def utmzone(perimeter, dissolved, centroid, utm, zone):
    """
    calculate.utmzone  Returns the UTM zone of the centroid of the fire perimeter
    ----------
    zone = calculate.utmzone(perimeter, dissolved, centroid, utm, zone)
    Returns the UTM zone for a fire perimeter. Proceeds by dissolving the fire
    perimeter into a single polygon and then determining the centroid of that
    polygon. Projects the centroid into UTM and returns the zone as an int.
    ----------
    Inputs:
        perimeter (str): The path to the arcpy Feature holding the fire perimeter
        dissolved (str): The path to the arcpy Feature in which to output the
            dissolved / merged perimeter.
        centroid (str): The path to the arcpy Feature in which to output the
            centroid of the fire perimeter
        utm (str): The path to the arcpy feature used to define UTM zones
        zone (str): The path to the arcpy feature holding the UTM zone of the
            centroid of the fire perimeter.

    Outputs:
        zone (int): The UTM zone of the centroid of the fire perimeter

    Saves:
        Files matching the paths of the dissolved, centroid, and zone inputs.
    """

    # Reset arcpy environment
    arcpy.env.overwriteOutput = True
    arcpy.ClearEnvironment("cellSize")
    arcpy.ClearEnvironment("extent")
    arcpy.ClearEnvironment("snapRaster")
    arcpy.ClearEnvironment("mask")
    arcpy.ResetEnvironments()

    # Get the set of fields to retain in the perimeter
    objectids = ("OBJECTID", "OBJECTID_1", "OBJECTID_12")
    shapes = ("SHAPE", "Shape", "Shape_Area", "Shape_Length")
    keep = objectids + shapes

    # Remove all other fields from the perimeter feature
    fields = arcpy.ListFields(perimeter)
    for field in fields:
        name = field.name
        if name not in keep:
            acrpy.management.DeleteField(perimeter, name)

    # Add a field for the fire perimeter ID
    id = perimeter_ID_field_name
    arcpy.management.AddField(perimeter, id, "SHORT")

    # Merge the perimeter
    with arcpy.da.UpdateCursor(perimeter, id) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)
    arcpy.management.Dissolve(perimeter, dissolved, id)

    # Get the centroid of the perimeter
    arcpy.management.FeatureToPoint(dissolved, centroid)

    # Project the centroid into UTM and return the zone
    arcpy.management.Project(centroid, centroid, utm)
    arcpy.analysis.Identify(centroid, utm, zone)
    zone = arcpy.da.TableToNumPyArray(zone, "ZONE")
    zone = zone[0][0]   # ??????? Is this necessary
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
    