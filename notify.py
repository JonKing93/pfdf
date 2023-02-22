"""
notify  Functions that print notifications to the console

FUNCTIONS:
    step1       - Notifies console that step 1 is beginning
    importing   - Notifies console that modules are being imported
    processing  - Notifies console that a particular fire is being processed
"""

from datetime import datetime

def step1():
    print("Post-Fire Debris-Flow Hazard Assessment: Step 1 - Estimate Modeled Stream Network")

def processing(fire):
    start = datetime.now()
    print(f'Processing Fire: {fire}')
    print(f'  Processing started at {start.hour}:{start.minute} GMT')

def calculating_extent():
    print('    Calculating Relevant Extent Data....')

def utmzone(utmzone):
    print(f"    Burn Area Located in UTM Zone {utmzone}...")

def rectangle():
    print('    Creating Extent Rectangle...')

def dem(*, exists):
    if not isinstance(exists, bool):
        raise TypeError('The "exists" input must be a bool')
    elif exists:
        print('    DEM Exists, Skipping NED Extraction...')
    else:
        print('    Extracting DEM Data...')

def tiles(tiles):
    ndems = len(tiles)
    print(f"        Burn area intersects {ndems} DEM Tile(s)")
    print(f"        Processing DEM tiles...")

def projecting():
        print('        Projecting DEM Data to UTM...')

def basins(*, exist):
    if not isinstance(exist, bool):
        raise TypeError('The "exist" input must be a bool')
    elif exist:
        print('    Debris Basins Found...')
    else:
        print('    Searching for Debris Basins...')

def nBasins(nBasins):
    if nBasins==0:
        print('        No Debris Basins Found...')
    else:
        print(f"        {nBasins} Debris Basins Identified...")

def projections():
    print("    Checking Projections...")

def projected(projection):
    print(f"    All Input Data Projected as {projection.name}")
    print("    Continuing Processing...")

def extent(shared=None):
    if shared==None:
        print("    Checking DEM, Severity and dNBR Extents...")
    elif shared:
        print('        DEM, Severity, and dNBR Share Common Extent, Continuing Processing...')
    else:
        print('        Regridding Rasters to Common Extent...')

def soil():
    print("    Extracting Soils Data...")

def missing_soil(field, file):
    print(f'        WARNING: Soil {field} May Contain Missing Data, Manual Editing of {file} May Be Required...')

def burn():
    print('    Defining Burned Area...')


