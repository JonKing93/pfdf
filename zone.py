"""
zone  Calculates the UTM zone
"""

import notify
from paths import in_perim_dissolve as dissolved
from paths import in_perim_centroid as centroid

def utm():
    """
    zone.utm  Returns the UTM zone of the perimeter.
    ----------
    (zone) = zone.utm(perimeter)
    Returns an arcpy Feature and Describe object that record the UTM zone of the
    fire perimeter.
    ----------
    Inputs:
        perimeter (ArcPy Feature [1]): The feature for the fire perimeter

    Outputs:
        zone (int): The UTM zone of the fire perimeter
    """

    # Notify console of current process
    notify.calculating_extent()

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

    # Remove all other fields from the perimeter
    fields = acrpy.ListFields(perimeter)
    for field in fields:
        name = field.name
        if name not in keep:
            acrpy.management.DeleteField(perimeter, name)

    # Add a field for the fire perimeter ID
    id = "Perim_ID"
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
    arcpy.management.Project(centroid, paths.utmfind, paths.utmzone)

    # Return the UTM zone of the centroid
    arcpy.analysis.Identity(paths.utmfind, paths.utmzone, paths.centroid_utmzone)
    zone = arcpy.da.TableToNumPyArray(paths.centroid_utmzone, "ZONE")
    zone = zone[0][0] # ???????? Is this necessary
    return int(zone)
    