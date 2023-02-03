"""
notify  Functions that print notifications to the console

FUNCTIONS:
    step1       - Notifies console that step 1 is beginning
    importing   - Notifies console that modules are being imported
    processing  - Notifies console that a particular fire is being processed
"""

def step1():
    print("Post-Fire Debris-Flow Hazard Assessment: Step 1 - Estimate Modeled Stream Network")

def importing():
    print("Importing Modules...")

def processing(fire):
    print(f'Processing Fire: {fire}')
