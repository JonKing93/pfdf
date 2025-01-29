"""
Access LANDFIRE data products via the LFPS API
----------
The landfire package contains routines for accessing data from the LANDFIRE Product
Service (LFPS). The LFPS provides access to a variety of land use and wildfire datasets
that may be useful for pfdf users. These include existing vegetation type (EVT) rasters,
which are often used to build water and human-development masks, and see the LANDFIRE
data portal for descriptions of additional products: https://landfire.gov/data

Most users will want to start with the `read` and/or `download` functions. The read
function can be used to stream data from one LANDFIRE raster layer within a bounding
box - the read data is returned as a Raster object. Alternatively, use the `download`
command to save a product to the local file system. Unlike the `read` function, the
`download` command can be used to acquire datasets derived from vector features. You can
find a list of available data layer names here: https://lfps.usgs.gov/helpdocs/productstable.html

This package also includes the "api" module, which can be used for low-level
interactions with the LFPS API. Most users will not need this module, but developers
may find it useful for custom data acquisition routines.
----------
Contents:
    read        - Reads a LANDFIRE raster dataset into memory as a Raster object
    download    - Download one or more LANDFIRE data products to the local filesystem
    api         - Module supporting low-level LFPS API calls

Internal modules:
    _api        - Utilities supporting the api module
    _landfire   - Module implementing the read and download functions
    _validate   - Module for validating LFPS parameters
"""

from pfdf.data.landfire import api
from pfdf.data.landfire._landfire import download, read
