"""
dem  Functions involving the DEM
"""

def extract(dem, extent):
    """
    dem.extract  Extracts a digital elevation model for the fire perimeter
    ----------
    dem.extract(dem)
    ----------
    Inputs:
        dem (arcpy Feature): A digital elevation model that includes the fire perimeter
        extent (arcpy Feature): The extent box for the DEM

    
    """

    # Get the spatial reference
    describe = arcpy.Describe(dem_feature)
    reference = describe.SpatialReference

    # Project the extent box into the same projection as the DEM
    arcpy.management.Project(demextent, )


