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
    print('     Calculating Relevant Extent Data....')

def utmzone(utmzone):
    print(f"         Burn Area Located in UTM Zone {zone}...")

def rectangle():
    print('         Creating Extent Rectangle...')

def dem(*, exists):
    if not isinstance(exists, bool):
        raise TypeError('The "exists" input must be a bool')
    elif exists:
        print('     DEM Exists, Skipping NED Extraction...')
    else:
        print('     Extracting DEM Data...')

def tiles(tiles):
    ndems = len(tiles)
    print(f"     Burn area intersects {ndems} DEM Tile(s)")
    print(f"     Processing DEM tiles...")

def projecting():
        print('         Projecting DEM Data to UTM...')


