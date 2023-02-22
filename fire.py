"""
fire  Holds metadata about the fire being analyzed

VARIABLES:
    name        - The full name of the fire
    code        - The 3 letter abbreviation
    state       - The 2 letter state abbreviation
    location    - The location of the fire
    year        - The year the fire started
    id          - A 7 letter ID for the fire
"""

from datetime import datetime

name = 'Colorado'
code = 'col'
location = 'Monterey County, CA'
start = datetime(year=2022, month=1, day=21)
id = code + str(start.year)
