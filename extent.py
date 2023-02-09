"""
extent  Calculates the box of extent
"""

def calculate(utmzone, perimeter, dd, box, extent_dd, analysis, extent, cell_res):

    # Get the spatial and UTM references for the perimeter
    perim_ref = arcpy.Describe(perimeter).SpatialReference
    utm_ref = utmzone.SpatialReference

    # ???? Something about the projection
    if perim_ref.name = "GCS_North_American_1983":
        arcpy.management.CopyFeatures(perimeter, dd)
    else:
        arcpy.management.Project(perimeter, dd, 
              "GEOGCS['GCS_North_American_1983',"
            + "DATUM['D_North_American_1983',"
            + "SPHEROID['GRS_1980',6378137.0,298.257222101]],"
            + "PRIMEM['Greenwich',0.0],"
            + "UNIT['Degree',0.0174532925199433]]"
        )

    # Get the edges of the extent box
    describe = arcpy.Describe(dd).extent
    left = describe.XMin
    bottom = describe.YMin
    top = describe.YMax
    right = describe.XMax.ex

    # Get the corners
    lowerleft = describe.lowerLeft
    lowerright = describe.lowerRight
    upperright = describe.upperRight
    upperleft = describe.upperLeft

    # ?????
    arcpy.management.MinimumBoundingGeometry(dd, box, 'RECTANGLE BY AREA', 'ALL')
    arcpy.analysis.Buffer(dd, extent_dd, 0.02)
    field = "Extent_Code"
    arcpy.management.AddField(extent_dd, field, "SHORT")

    # ???????
    with arcpy.da.UpdateCursor(extent_dd, field) as cursor:
        for row in cursor:
            row[0] = 1
            cursor.updateRow(row)

    # ???????
    arcpy.management.Project(extent_dd, analysis, utm_ref)
    arcpy.conversion.PolygonToRaster(analysis, field, extent, 'CELL_CENTER', '', cell_res)