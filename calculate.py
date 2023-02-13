perimeter_ID_field_name = "Perim_ID"


def utm(perimeter, centroid, in_centroid, dissolved, utmzone, utmfind, pc_utmzone)
    """
    Inputs:
        perimeter (str): The path to the arcpy Feature holding the fire perimeter
        dissolved (str): The path to the arcpy Feature in which to output the
            dissolved / merged perimeter.
        centroid (str): The path to the arcpy Feature in which to output the
            centroid of the fire perimeter
        in_centroid (str)
        utmzone (str)
        utmfind (str)
        pc_utmzone (str)
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

    # Project the centroid into UTM
    arcpy.management.Project(centroid, utmfind, utmzone)

    # Project the centroid into UTM and return the zone
    arcpy.management.Project(centroid, centroid, utm)
    arcpy.analysis.Identity(centroid, utm, zone)
    zone = arcpy.da.TableToNumPyArray(zone, "ZONE")
    zone = zone[0][0]   # ??????? Is this necessary
    return int(zone)