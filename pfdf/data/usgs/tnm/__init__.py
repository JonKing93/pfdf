"""
Access data from the USGS National Map (TNM)
----------
This package provides access to the USGS National Map. Most users will want to begin
with the `dem` module, which provides access to digital elevation model data for a
variety of resolutions. Some users may also be interested in the `nhd` module - this
module provides access to the National Hydrologic Dataset, most notably watershed
boundaries for queried hydrologic unit codes (HUCs).

The data module should be sufficient for most users, but advanced users may also be
interested in the `api` module, which provides utilities for low-level interactions with
the TNM API. Developers may find this useful for accessing TNM datasets not directly
supported by pfdf, or to implement custom data acquisition routines.
----------
Modules:
    dem         - Acquire digital elevation model (DEM) datasets
    nhd         - Acquire hydrologic unit (HU) data from the National Hydrologic Dataset
    api         - Make low-level queries to the TNM API

Internal:
    _validate   - Functions to validate TNM API parameters
"""

from pfdf.data.usgs.tnm import api, dem, nhd
