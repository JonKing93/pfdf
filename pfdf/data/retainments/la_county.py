"""
Acquire locations of debris retainment basins in Los Angeles County, CA
----------
This module contains functions to download a geodatabase file holding the Point
locations of debris retainment basins within Los Angeles County.
----------
Functions:
    download    - Downloads the geodatabase of Point locations to the local file system
    data_url    - Returns the URL of the downloaded dataset
"""

from __future__ import annotations

import typing
from pathlib import Path

import pfdf._validate.core as validate
from pfdf.data._utils import requests, unzip

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import Pathlike, timeout


def data_url() -> str:
    """
    Returns the URL for the debris basin download
    ----------
    data_url()
    Returns the URL for the debris retainment dataset. This dataset does not use an API,
    so the URL provides direct access to the dataset as a zip archive.
    ----------
    Outputs:
        str: The URL for the downloadable dataset
    """
    return "https://pw.lacounty.gov/sur/nas/landbase/AGOL/Debris_Basin.gdb.zip"


def download(
    *,
    parent: Optional[Pathlike] = None,
    name: Optional[str] = None,
    timeout: Optional[timeout] = 15,
) -> Path:
    """
    Downloads a geodatabase of debris retainment locations for Los Angeles County, CA
    ----------
    download()
    Downloads a geodatabase (gdb) holding the Point locations of debris retainment
    features in Los Angeles county. Returns the path to the downloaded dataset. By
    default, the dataset will be named "la-county-retainments.gdb" and will be located
    in the current folder. The dataset is intended for use with commands like
    "pfdf.raster.Raster.from_points", which supports reading data from geodatabases and
    does not require an ESRI license. Raises an error if the geodatabase already exists
    on the file system.

    download(..., *, parent)
    download(..., *, name)
    Options for downloading the geodatabase. The `parent` option is the path to the
    parent folder where the geodatabase should be downloaded. If a relative path, then
    `parent` is interpreted relative to the current folder. Use `name` to set the name
    of the downloaded geodatabase. Rases an error if the path to the geodatabase already
    exists.

    download(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the LA County data
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        parent: The path to the parent folder where the geodatabase should be downloaded.
            Defaults to the current folder.
        name: The name for the downloaded geodatabase. Defaults to "la-county-retainments.gdb"
        timeout: A maximum number of seconds to connect with the LA County data server

    Outputs:
        Path: The path to the downloaded geodatabase
    """

    path = validate.download_path(
        parent, name, default_name="la-county-retainments.gdb", overwrite=False
    )
    data = requests.content(data_url(), {}, timeout, "LA County data")
    unzip(data, path, item="Debris_Basin.gdb")
    return path
