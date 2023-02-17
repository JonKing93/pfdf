"""
ensure  Functions that ensure a condition is met
"""

import arcpy
from numbers import Real

def projection(name, file, target, projected, isrequired=True, israster=False, cellsize=None):
    """
    ensure.projection  Ensure that data is in a target projection
    ----------
    path = ensure.projection(name, path, target, projected)
    Checks if an arcpy Feature is in the correct projection. If not re-projects
    the data in to the target projection. Returns the path to a file holding the
    data in the desired projection. If the feature file does not exist, throws
    an error.

    path = ensure.projection(name, path, target, projected, isrequired=False)
    Indicates that the data file is not required to exist. If the feature does
    not exist, returns the path to the input data file.

    path = ensure.projection(name, path, target, projected, isrequired, israster=True, cellsize)
    Indicates that the input data is raster data, rather than Feature data.
    Requires the user to indicate the cell size of any re-projected data. When
    re-projecting raster data, uses the 'BILINEAR' option.
    ----------
    Inputs:
        name (str): An identifying name for the data set being checked
        path (str): The path to the input arcpy data file being checked
        target (arcpy.spatialReference): A spatialReference object for the 
            requested projection system.
        projected (str): The path to the output arcpy data file if the data
            needs to be re-projected.
        isrequired (bool): True (default) if the function should throw an error
            when the data file is missing. If False, returns the path to the
            input data file when missing.
        israster (bool): True (default) if the input data should be treated as
            an arcpy feature. Set to false to treat input data as a raster
            instead. When set to false, the function requires the user to set
            the "cellSize" input.
        cellsize (float): Indicates the desired cell size of re-projected
            raster data.

    Outputs:
        path (str): The path to a data file using the requested projection 
            system. This will either be the original data file (if already in
            the correct projection), or the "projected" input (if the data
            was re-projected).
    """

    # Ensure cellsize is set for rasters
    if israster:
        if cellsize==None:
            raise TypeError('You must set the "cellsize" input when checking raster data')
        elif not isinstance(cellsize, Real):
            raise TypeError('cellsize must be a float')

    # If missing and required, throw an error. If missing and not required,
    # return the original input file
    if not arcpy.Exists(file):
        if isrequired:
            raise ValueError(f"File does not exist\n\tFile: {file}")
        else:
            return file

    # Get the current projection and notify the console
    projection = arcpy.Describe(file).spatialReference
    print(f"        {name} Projection: {projection.name}")

    # Return the original file if it's already in the correct projection
    if projection.name == target.name:
        return file

    # Otherwise, re-project the file into the target projection
    else:
        print(f"        Projecting {name} to {projection.name}...")
        if israster:
            arcpy.management.ProjectRaster(file, projected, target, 'BILINEAR', cellsize)
        else:
            arcpy.management.Project(file, projected, target)
        return projected