"""
Utilities for acquiring common datasets
----------
This package contains routines used to acquire datasets commonly used with pfdf. Users
should not feel obligated to use these specific datasets. Instead, this package is
intended to simplify the data acquisition process for certain common workflows. This
package is by no means comprehensive, and we welcome suggestions for additional
datasets. Please contact the developers if you'd like to see additional datasets
supported here.

The data acquisition utilities are organized into subpackages by different data
providers. Currently, these include:

* landfire: Includes existing vegetation type (EVT) rasters
* noaa: Includes precipitation frequencies from NOAA Atlas 14
* retainments: Locations of debris retainment features, and
* usgs: Various USGS datasets, including DEMs, STATSGO soil data, and HUC boundaries

Most datasets are ultimately accessed via a `read` and/or `download` function. A `read`
function will usually read a raster dataset from a data server, and return the dataset
as a Raster object. A `download` function will download one or more files onto the
local file system. This is more common for vector feature datasets, and datasets that
bundle multiple rasters.

Many of these data subpackages also include low-level functions for querying data
provider APIs. Most users will not need these API utilities, but developers may find
them useful for acquiring datasets not directly supported by pfdf, as well as for
troubleshooting API responses.
----------
Subpackages:
    landfire    - Modules to acquire LANDFIRE datasets
    noaa        - Modules to acquire NOAA datasets
    retainments - Modules to acquire debris retainment feature locations
    usgs        - Modules to acquire USGS datasets

Internal:
    _utils      - Utility modules used throughout the package
"""

from pfdf.data import landfire, noaa, retainments, usgs
