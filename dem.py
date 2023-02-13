"""
dem  Functions involving the DEM
"""

from notify import dem_exists, extract_dem

def extract(dem):
    """
    dem.extract  Extract the DEM
    """

    # Notify user whether DEM exists. Exit if it does
    if arcpy.Exists(dem):
        notify.dem(True)
        return
    notify.dem(False)

    # Get the spatial reference
    dem = arcpy.Describe()


