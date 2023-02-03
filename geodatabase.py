"""
geodatabase  Utilities that help set up geodatabase files for Step 1.

FUNCTIONS:
    name    - Returns the name of a fire-specific geodatabase file
    locate  - Returns the path to a geodatabase file
    create  - Creates a geodatabase file if one does not already exist
"""

import os.path
# import arcpy


def name(fire, gdb):
    """
    geodatabase.name  Returns the name of a fire-specific geodatabase
    ----------
    name = geodatabase.name(fire, gdb)
    Returns the name of a fire-specific geodatabase. Creates the name by
    appending the fire name to the geodatabase name (separated by an underscore). 
    Adds a '.gdb' extension if the geodatabase tag does not end with one.
    ----------
    Inputs:
        fire (str): The name of the fire. Often includes the fire name and location.
        gdb (str): A name describing the contents of the geodatabase.

    Outputs:
        name (str): The name of the geodatabase file
    """

    name = fire + '_' + gdb
    if not name.endswith('.gdb'):
        name = name + '.gdb'
    return name

def path(folder, fire, gdb):
    """
    geodatabase.path  Returns the path to a fire-specific geodatabase
    ----------
    path = geodatabase.path(folder, fire, gdb)
    Returns the path to a fire-specific geodatabase located in the indicated
    folder. The name of the geodatabase is the fire name appended to the
    geodatabase description (separated by an underscore). Adds a '.gdb'
    extension if the geodatabase description does not end with one.
    ----------
    Inputs:
        folder (str): The path to the folder that should contain the geodatabase
        fire (str): The name of the fire. Often includes the fire name and location
        gdb (str): A name describing the contents of the geodatabase.

    Outputs:
        path (str): The path to the geodatabase file in the folder
    """

    file = name(fire, gdb)
    path = os.path.join(folder, file)
    return path

def create(folder, fire, gdb):
    """
    geodatabase.create  Creates a fire-dependent geodatabase in the specified folder
    ----------
    path = geodatabase.create(folder, fire, gdb)
    Checks for a fire-dependent geodatabase in the indicated folder. If the
    geodatabase does not exist, creates a new one.
    ----------
    Inputs:
        folder (str): The path to the folder that should contain the geodatabase
        fire (str): The name of the fire. Often includes the fire name and location
        gdb (str): A name describing the contents of the geodatabase.

    Outputs:
        path (str): The path to the geodatabase file in the folder
    """

    file = name(fire, gdb)
    path = path(folder, fire, gdb)
    if not os.path.exists(path):
        arcpy.CreateFileGDB_management(folder, file, 'CURRENT')
    return path


