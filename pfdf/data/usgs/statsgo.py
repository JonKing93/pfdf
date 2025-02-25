"""
Functions to acquire soil data from the STATSGO archive
----------
This module provides functions to load soil data from the STATSGO archive (Schwarz
and Alexander, 1995). In brief, STATSGO is an archive of soil data fields for map units
spanning the continental US, and you can learn more here:
https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187

The original STATSGO archive was distributed as a collection of Shapefiles, but some of
the archive's data fields have since been reformatted as cloud-optimized GeoTiff (COG)
rasters. This module is intended to load data from these COG reformatted datasets.
Currently, the following data fields are supported:

    * KFFACT: Soil Kf-factors (inches per hour), and
    * THICK: Soil thickness (inches)

Most users should start with the `read` function. This function allows you to load data
from a STATSGO data field within a specified bounding box. Advanced users may also be
interested in the `download` function, which downloads a COG data file; and the `query`
function, which return ScienceBase catalog information for various STATSGO datasets.

Source Archive: https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187
COG Collection: https://www.sciencebase.gov/catalog/item/675083c6d34ea60e894354ad

References:
Schwarz, G.E. and Alexander, R.B., 1995, Soils data for the Conterminous United States
Derived from the NRCS State Soil Geographic (STATSGO) Data Base. [Original title: State
 Soil Geographic (STATSGO) Data Base for the Conterminous United States.]:
 U.S. Geological Survey data release, https://doi.org/10.5066/P94JAULO.
----------
Data:
    read        - Loads data from a STATSGO field as a Raster object
    download    - Downloads the COG data file for a STATSGO field

Item Info:
    fields      - Returns a pandas.DataFrame with information on the supported fields
    url         - Returns the ScienceBase URLs for items in the STATSGO COG collection
    query       - Returns ScienceBase metadata on a STATSGO item as a JSON dict

Internal:
    _validate_field - Checks that a queried STATSGO field is supported
    _url            - Returns the URL for a STATSGO field
    _s3_url         - Extracts an S3 data URI from ScienceBase JSON metadata
"""

from __future__ import annotations

import typing

from pfdf._utils import dataframe
from pfdf._validate import core as cvalidate
from pfdf._validate import projection as pvalidate
from pfdf.data._utils import requests
from pfdf.errors import DataAPIError, MissingAPIFieldError
from pfdf.raster import Raster

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Literal, Optional

    from pandas import DataFrame

    from pfdf.typing.core import Pathlike, timeout
    from pfdf.typing.raster import BoundsInput

    Field = Literal["KFFACT", "THICK"]


#####
# STATSGO Fields
#####


def fields() -> DataFrame:
    """
    Returns a pandas.DataFrame describing the supported STATSGO fields
    ----------
    fields()
    Returns a pandas.DataFrame describing the STATSGO fields supported by this module.
    The index entries are the names of supported fields. Each row provides the
    description, units, and URL to the ScienceBase catalog item for the field.
    ----------
    Outputs:
        pandas.DataFrame: Documents the supported STATSGO fields
            index (str): The name of each field
            Description (str): A description of each field
            Units (str): Reports the units of each field
            URL (str): The URL to the ScienceBase item for each field
    """

    fields = ("Name", "Description", "Units", "URL")
    table = (
        (
            "KFFACT",
            "Soil KF-factors",
            "inches per hour",
            "https://www.sciencebase.gov/catalog/item/6750c172d34ed8d3858534d8",
        ),
        (
            "THICK",
            "Soil thickness",
            "inches",
            "https://www.sciencebase.gov/catalog/item/675721b9d34e5c5dfd05c575",
        ),
    )
    return dataframe.table(table, columns=fields[1:])


def _validate_field(field: Any) -> Field:
    "Checks that an input STATSGO field is supported"

    supported = [field.lower() for field in fields().index.to_list()]
    field = cvalidate.option(field, "field", supported)
    return field.upper()


#####
# API queries
#####


def _url(field: Field) -> str:
    "Returns the URL for a STATSGO field"
    return fields().loc[field]["URL"]


def url(field: Optional[Field] = None) -> str:
    """
    Returns the URLs to ScienceBase items for the STATSGO dataset
    ----------
    url()
    Returns the URL to the ScienceBase STATSGO collection item. This item is the parent
    of the individual STATSGO data field rasters, and it links to the ScienceBase items
    for the supported STATSGO data fields.

    url(field)
    Returns the URL to the ScienceBase item for the queried STATSGO field. Supported
    field include: KFFACT, and THICK.
    ----------
    Inputs:
        field: A STATSGO field whose ScienceBase item URL should be returned

    Outputs:
        str: The URL to a ScienceBase item in the STATSGO archive
    """

    # If there is no field, then return the collection item
    if field is None:
        return "https://www.sciencebase.gov/catalog/item/675083c6d34ea60e894354ad"

    # Otherwise, return the URL for the field
    field = _validate_field(field)
    return _url(field)


def query(field: Optional[Field] = None, *, timeout: timeout = 60) -> dict:
    """
    Queries the ScienceBase API for a STATSGO item and returns the response as a JSON dict
    ----------
    query()
    Uses the ScienceBase API to query the parent item for the STATSGO collection. This
    item links to the items for the supported STATSGO data fields. Returns the query
    response as a JSON dict.

    query(field)
    Uses the ScienceBase API to query the catalog item for the indicated STATSGO data
    field. Supported fields include: KFFACT and THICK.

    query(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the ScienceBase data
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        field: The name of a STATSGO data field to query
        timeout: The maximum number of seconds to connect with the ScienceBase server

    Outputs:
        dict: ScienceBase item info as a JSON dict
    """

    return requests.json(
        url=url(field),
        params={"format": "json"},
        timeout=timeout,
        servers="ScienceBase",
        outages="https://www.sciencebase.gov/catalog/status",
    )


#####
# Data access
#####


def download(
    field: Field,
    *,
    parent: Optional[Pathlike] = None,
    name: Optional[str] = None,
    overwrite: bool = False,
    timeout: Optional[timeout] = 60,
) -> Path:
    """
    Downloads the cloud-optimized GeoTiff for a STATSGO field
    ----------
    download(field)
    Downloads the cloud-optimized GeoTiff (COG) for the indicated STATSGO field.
    Supported fields include: KFFACT, and THICK.

    The dataset in the downloaded file spans the Continental US at a nominal 30 meter
    resolution. A downloaded file will require 336MB of disk space. Note that the COG
    format uses compression internally to reduce file size, so reading the full dataset
    into memory will require ~60GB of RAM - significantly more memory than the size of
    the downloaded file.

    Returns the path to the downloaded file as output. By default, downloads a file
    named "STATSGO-<field>.tif" to the current folder. Raises an error if the file
    exists. (And see the following syntax for additional file path options).

    download(..., *, parent)
    download(..., *, name)
    download(..., *, overwrite=True)
    Options for downloading the file. Use the `parent` input to specify the the path to
    the parent folder where the file should be saved. If a relative path, then parent is
    interpreted relative to the current folder. Use `name` to set the name of the
    downloaded file. By default, raises an error if the path for the downloaded file
    already exists. Set overwrite=True to allow the download to overwrite an existing
    file.

    download(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the ScienceBase data
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        field: The name of the STATSGO data field to download
        parent: The path to the parent folder where the file should be saved. Defaults
            to the current folder.
        name: The name for the downloaded file. Defaults to STATSGO-<field>.tif
        overwrite: True to allow the downloaded file to replace an existing file.
            False (default) to not allow overwriting
        timeout: The maximum number of seconds to connect with the ScienceBase server

    Outputs:
        Path: The Path to the downloaded COG file
    """

    # Validate field and output path
    field = _validate_field(field)
    path = cvalidate.download_path(
        parent, name, default_name=f"STATSGO-{field}.tif", overwrite=overwrite
    )

    # Get the download URL and download the dataset
    item = query(field, timeout=timeout)
    url = _s3_url(item, field)
    return requests.download(path, url, {}, timeout, "ScienceBase S3 Data Server")


def read(
    field: Field, bounds: BoundsInput, *, timeout: Optional[timeout] = 60
) -> Raster:
    """
    Reads data from a STATSGO field into memory as a Raster object
    ----------
    read(field, bounds)
    Reads data from the indicated STATSGO field within the provided bounding box.
    Supported fields include: KFFACT and THICK. Note that the `bounds` input should be
    a BoundingBox-like object with a CRS. Returns the loaded dataset as a Raster object.

    read(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the ScienceBase data
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        field: The name of the STATSGO data field from which to load data
        timeout: The maximum number of seconds to connect with the ScienceBase server

    Outputs:
        Raster: The data read from the STATSGO archive
    """

    # Validate field and bounding box
    field = _validate_field(field)
    bounds = pvalidate.bounds(bounds, require_crs=True)

    # Get the S3 URI and load the dataset
    item = query(field, timeout=timeout)
    url = _s3_url(item, field)
    return Raster.from_url(url, bounds=bounds, check_status=False, timeout=timeout)


def _s3_url(item: dict, field: str) -> str:
    "Extracts the S3 URL for a data file from catalog item metadata"

    # Get the files
    if "files" not in item:
        raise MissingAPIFieldError(
            'ScienceBase failed to return "files" metadata for the item'
        )
    files = item["files"]

    # Locate the data file
    filename = f"statsgo-{field.lower()}.tif"
    found_file = False
    for file in files:
        if file["name"].lower() == filename:
            found_file = True
            break

    # Error if the file was not found
    if not found_file:
        raise DataAPIError(
            f"Could not locate the {filename} file in the ScienceBase item info"
        )

    # Extract the S3 URL
    key = "publishedS3Uri"
    if key not in file:
        raise MissingAPIFieldError("ScienceBase failed to return an S3 download Uri")
    return file[key]
