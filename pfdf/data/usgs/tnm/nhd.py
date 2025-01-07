"""
Acquire hydrologic unit (HU) data from the National Hydrologic Dataset
----------
This module provides functions to access hydrologic unit (HU) data from the National
Hydrologic Dataset. Most users will want the `download` method, which downloads the
data bundle for a HU-4 or HU-8 code to the local filesystem.

Although the download queries are limited to HU4 and HU8 codes, the actual data
bundles contain data for the 2-16 digit HUs associated with the queried HUC. We
recommend HUC10s as a good starting point for many pfdf analyses. To obtain data for a
HUC10 boundary, first download the data bundle for the associated HU8 code. Then, open
the HU10 dataset from the data bundle, and extract the data for the relevant HUC10.

This module also includes a "product" function, which returns product info for a queried 
HU4 or HU8 code. Advanced users may find this useful for designing custom data
acquisition routines.
----------
Data:
    download    - Downloads the data bundle for a HUC4 or HUC8 unit

TNM API:
    dataset     - Returns the fully-qualified TNM name for the NHD dataset
    products    - Returns product info for a HUC4 or HUC8

Internal:
    _no_huc_error   - Raises an informative error when a matching HUC cannot be found
"""

from __future__ import annotations

import typing

from pfdf._validate import core as cvalidate
from pfdf.data._utils import requests, unzip
from pfdf.data.usgs.tnm import _validate, api
from pfdf.errors import InvalidJSONError, NoTNMProductsError

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import Literal, NoReturn, Optional

    from pfdf.typing.core import Pathlike, timeout

    Format = Literal["Shapefile", "GeoPackage", "FileGDB"]


def dataset() -> str:
    """
    Returns the fully qualified TNM name for the NHD dataset
    ----------
    dataset()
    Returns the fully qualified TNM name for the NHD dataset.
    ----------
    Outputs:
        str: The fully qualified TNM name for the NHD dataset
    """
    return "National Hydrography Dataset (NHD) Best Resolution"


def product(huc: str, *, format="Shapefile", timeout: Optional[timeout] = 60) -> dict:
    """
    Returns the product info for the queried HUC
    ----------
    product(huc)
    product(huc, *, format)
    Returns TNM product info for a queried HUC4 or HUC8 as a JSON dict. Raises a
    NoTNMProductsError if there is no hydrologic unit with a matching code. Note that
    `huc` should be a string, rather than an int. This is to preserve leading zeros in
    hydrologic unit codes. By default, returns info for the HUCs Shapefile product. Use
    the `format` option to return info for a different file format. Supported file
    formats include "Shapefile", "GeoPackage" and "FileGDB". Note that pfdf supports
    reading from File Geodatabases without requiring an ESRI license.

    product(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        huc: A string representing an HU4 or HU8 code
        format: The file format that should be queried. Options are "Shapefile",
            "GeoPackage", and "FileGDB"
        timeout: The maximum number of seconds to connect to the TNM server

    Outputs:
        dict: The TNM product info for the queried HUC as a JSON dict
    """

    # Validate HUC and format. Only HUC4 and HUC8 are permitted
    huc, _ = _validate.huc48(huc)
    format = _validate.nhd_format(format)

    # Query the API for matching items. Note that JSON fails when the HUC is invalid
    try:
        products = api.products(
            dataset(),
            huc=huc,
            formats=format,
            max_queries=1,
            max_per_query=500,
            timeout=timeout,
        )
    except InvalidJSONError:
        _no_huc_error(huc)

    # Locate the matching product
    key = f"Hydrological Unit (HU) {len(huc)} - {huc}"
    for product in products:
        if key in product["title"]:
            return product

    # Error if the HUC was not found
    _no_huc_error(huc)


def _no_huc_error(huc) -> NoReturn:
    "Informative error when a HUC code is invalid"
    raise NoTNMProductsError(
        f"Could not locate a matching hydrologic unit. "
        f"The HUC ({huc}) may not be a valid code."
    ) from None


def download(
    huc: str,
    path: Optional[Pathlike] = None,
    *,
    format="Shapefile",
    timeout: Optional[timeout] = 60,
) -> Path:
    """
    Downloads an HU4 or HU8 data bundle
    ----------
    download(huc)
    Downloads the data bundle for a HU4 or HU8 code to the local filesystem. Raises an
    error if a matching HUC cannot be found. By default, downloads a Shapefile data
    bundle into a folder named "huc4-<code>" or "huc8-<code>" in the current directory,
    but see below for oath path options. Note that `huc` should be a string
    representing a HUC, rather than an int. This is to preserve leading zeros in the HUC.

    download(..., path)
    Specifies the path for the downloaded data bundle. If a relative path, then the path
    is interpreted relative to the current directory. Raises an error if the path
    already exists.

    download(..., *, format)
    Downloads a data bundle in the indicated file format. Supported options include:
    "Shapefile" (default)", "GeoPackage", and "FileGDB". Note that pfdf routines support
    all three format types, and that reading from a file geodatabase does not require
    an ESRI license.

    download(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        huc: A string of the HU4 or HU8 code whose data bundle should be downloaded
        path: The path to the downloaded data folder. Defaults to "huc4-<code>" or
            "huc8-<code> in the current folder, as appropriate.
        format: The file format that should be download. Options are "Shapefile",
            "GeoPackage", and "FileGDB"
        timeout: The maximum number of seconds to connect to the TNM server
    """

    # Validate
    huc, huc_type = _validate.huc48(huc)
    path = cvalidate.output_folder(path, default=f"{huc_type}-{huc}")

    # Find the HUC record. Download and unzip the dataset
    record = product(huc, format=format, timeout=timeout)
    url = record["downloadURL"]
    data = requests.content(url, {}, timeout, "TNM staged data")
    unzip(data, path)
    return path
