perimeter_ID_field_name = "Perim_ID"


def utmzone(perimeter, centroid, dissolved, utm, zone):
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