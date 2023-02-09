"""
zone  Calculates the UTM zone
"""

import notify

def utm():
    """
    zone.utm  Returns the UTM zone of the perimeter.
    ----------
    (feature, describe) = zone.utm(perimeter)
    Returns an arcpy Feature and Describe object that record the UTM zone of the
    fire perimeter.
    ----------
    Inputs:
        perimeter (ArcPy Feature [1]): The feature for the fire perimeter

    Outputs:
        feature (ArcPy Feature [1]): The feature for the UTM zone
        describe (ArcPy Describe [1]): A Describe object for the UTM zone
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
    