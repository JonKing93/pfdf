"""
Acquire datasets released by the US Geological Survey (https://www.usgs.gov/)
----------
This package contains routines to acquire a variety of USGS datasets. These include
digital elevation models (DEMs) and hydrologic unit (HU) boundaries from the USGS
National Map, as well as soil KF-factors and soil thickness data from the STATSGO soil
characteristic archive. Additional datasets may also be added upon request.

Currently, the package is organized into the `tnm` subpackage (used to access products
from The National Map - including DEMs, HUCs, and low-level APIs), and the `statsgo` 
module (used to access the soil characteristic archive).
----------
Contents:
    tnm     - Modules used to access datasets from the National Map (DEMs, HUCs)
    statsgo - Functions to acquire data from the STATSGO soil characteristic archive
"""

from pfdf.data.usgs import statsgo, tnm
