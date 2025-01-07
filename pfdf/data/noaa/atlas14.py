"""
Acquire data from NOAA Atlas 14
----------
This module provides functions to access precipitation frequency estimates (PFEs) from 
NOAA Atlas 14. Most users will want to use the `download` command, which returns a .csv 
file with PFEs at a given lat-lon coordinate. This module also provides commands that
return API URLs, which advanced users may find useful for generating custom queries.
----------
Data:
    download    - Downloads a .csv file of precipitation frequency estimates for a coordinate

URLs:
    base_url    - Returns the base URL for the NOAA Atlas 14 data API
    query_url   - Returns the URL used to query NOAA Atlas 14 for a specific PFE statistic

Internal:
    _validate_statistic - Checks a PFE statistic is valid

"""

from __future__ import annotations

import typing
from pathlib import Path

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.data._utils import requests

if typing.TYPE_CHECKING:
    from typing import Any, Literal, Optional

    from pfdf.typing.core import Pathlike, scalar, timeout

    Statistic = Literal["mean", "upper", "lower", "all"]
    Data = Literal["depth", "intensity"]
    Series = Literal["pds", "ams"]


def base_url() -> str:
    """
    Returns the base URL for the NOAA Atlas 14 data API
    ----------
    base_url()
    Returns the base URL for the NOAA Atlas 14 data API.
    ----------
    Outputs:
        str: The base URL for the NOAA Atlas 14 data API
    """
    return "https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new"


def _validate_statistic(statistic: Any) -> str:
    "Checks that a statistic option is valid"

    return validate.option(
        statistic, "statistic", allowed=["mean", "upper", "lower", "all"]
    )


def query_url(statistic: Statistic = "mean") -> str:
    """
    Returns the URL used to query a NOAA Atlas 14 PFE statistic
    ----------
    query_url(statistic)
    Returns the URL used to query a NOAA Atlas 14 PFE statistic. Supported statistics
    include:

    "mean": The mean PFE (default)
    "upper": Upper bound of the 90% confidence interval
    "lower": Lower bound of the 90% confidence interval
    "all": Mean, upper and lower PFE
    ----------
    Inputs:
        statistic: The PFE statistic that should be queried

    Outputs:
        str: The URL used to query the indicated PFE statistic
    """

    # Get the statistic file key
    statistic = _validate_statistic(statistic)
    if statistic == "mean":
        key = "_mean"
    elif statistic == "upper":
        key = "_uppr"
    elif statistic == "lower":
        key = "_lwr"
    else:
        key = ""

    # Build the query url
    return f"{base_url()}/fe_text{key}.csv"


def download(
    lat: scalar,
    lon: scalar,
    path: Optional[Pathlike] = None,
    *,
    statistic: Statistic = "mean",
    data: Data = "intensity",
    series: Series = "pds",
    overwrite: bool = False,
    timeout: Optional[timeout] = 10,
) -> Path:
    """
    Downloads a .csv file with precipitation frequency estimates for a given point
    ----------
    download(lat, lon)
    Downloads a .csv file with precipitation frequency estimates for the given point.
    The `lat` and `lon` coordinates should be provided in decimal degrees, and `lon`
    should be on the interval [-180, 180]. By default, downloads mean PFEs of
    precipitation intensity for partial duration time series. See below for alternative
    options.

    Returns the path to the downloaded csv file as output. By default, this command will
    download the dataset to the current folder, and the data file will be named
    "noaa-atlas14-mean-pds-intensity.csv". Raises an error if the file already exists.
    (And see the following syntax for additional file options).

    download(..., path)
    download(..., *, overwrite=True)
    Options for the downloaded file. Use the `path` input to specify an alternative
    file path for the downloaded file. By default, raises an error if this path already
    exists. Set overwrite=True to allow the downloaded file to overwrite existing files.

    download(..., *, statistic)
    download(..., *, data)
    download(..., *, series)
    Specify the type of data that should be downloaded. Supported values are as follows:

    *Statistic*
    mean: Mean PFE values (default)
    upper: Upper bound of the 90% confidence interval
    lower: Lower bound of the 90% confidence interval
    all: Mean, upper, and lower

    *Data*
    intensity: Values are precipitation intensities (default)
    depth: Values are precipitation depths

    *Series*
    pds: PFEs estimated from partial duration time series (default)
    ams: PFEs estimated from annual maximum time series

    Note that if you do not specify a path for the downloaded file, then the download
    file will follow the naming scheme: "noaa-atlas14-<statistic>-<series>-<data>.csv"

    download(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the NOAA Atlas 14 data
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        lat: The latitude of the query point in decimal degrees
        lon: The longitude of the query point in decimal degrees on the interval [-180, 180]
        path: The file path for the downloaded data file
        overwrite: True to allow the downloaded file to replace an existing file.
            False (default) to not allow overwriting
        statistic: The type of PFE statistic to download. Options are "mean", "upper",
            "lower", and "all"
        data: The type of PFE values to download. Options are "intensity" and "depth"
        series: The type of time series to derive PFE values from. Options are
            "pds" (partial duration), and "ams" (annual maximum).
        timeout: The maximum number of seconds to connect with the data server

    Outputs:
        Path: The Path to the downloaded data file
    """

    # Validate coordinates and query parameters
    lat = validate.scalar(lat, "lat", dtype=real)
    validate.inrange(lat, "lat", -90, 90)
    lon = validate.scalar(lon, "lon", dtype=real)
    validate.inrange(lon, "lon", -180, 180)
    data = validate.option(data, "data", allowed=["depth", "intensity"])
    series = validate.option(series, "series", allowed=["pds", "ams"])

    # Validate the output file path
    if path is None:
        path = Path.cwd() / f"noaa-atlas14-{statistic}-{series}-{data}.csv"
    path = validate.output_file(path, overwrite)

    # Build the query URL and parameters
    url = query_url(statistic)
    params = {"lat": float(lat), "lon": float(lon), "data": data, "series": series}

    # Download the dataset
    response = requests.content(url, params, timeout, "NOAA PFDS")
    path.write_bytes(response)
    return path
