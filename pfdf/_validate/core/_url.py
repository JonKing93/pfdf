"""
Functions that validate URLs
----------
Functions:
    url     - Checks input is a string with a URL scheme
    http    - Checks the connection to an http(s) URL using requests.head
    timeout - Checks that a connection timeout option is valid
"""

from __future__ import annotations

import typing
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectTimeout, HTTPError, ReadTimeout

import pfdf._validate.core as validate
from pfdf._utils import real
from pfdf.errors import ShapeError

if typing.TYPE_CHECKING:
    from typing import Any

    from pfdf.typing.core import timeout, url


def url(url: Any) -> str:
    "Checks input is a string with a URL scheme. Returns the scheme"

    validate.string(url, "url")
    scheme = urlparse(url).scheme
    if scheme == "":
        raise ValueError(
            "The URL is missing a scheme. Some common schemes are http, https, and "
            "ftp. If you are trying to access a dataset from the internet, be sure to "
            "include `http://` or `https://` at the start of the URL.\n"
            f"URL:  {url}"
        )
    return scheme


def http(url: url, timeout: timeout) -> requests.Response:
    "Checks an HTTP(S) connection using requests.head"

    # Must be HTTP or HTTPS
    scheme = urlparse(url).scheme
    if scheme not in ["http", "https"]:
        raise ValueError(
            f"URL must have an 'http' or 'https' scheme, but it has a '{scheme}' scheme instead.\n"
            f"URL: {url}"
        )

    # Try connecting to the remote server
    try:
        head = requests.head(url, timeout=timeout)
    except ConnectTimeout as error:
        raise ConnectTimeout(
            f"Could not connect to the remote server in the allotted time. Try:\n"
            f"  * Checking your internet connection, and\n"
            f"  * Checking if the remote server is down\n"
            f"If you are on a very slow connection, try increasing the 'timeout' option.\n"
            f"URL: {url}"
        ) from error
    except ReadTimeout as error:
        raise ReadTimeout(
            f"The remote server did not respond in the allotted time. Try checking\n"
            f"if the remote server is down. If the server is fine, but you are on a very\n"
            'slow connection, then try increasing the "timeout" option.\n'
            f"URL: {url}"
        )

    # Validate HTTP response code
    try:
        head.raise_for_status()
    except HTTPError as error:
        raise HTTPError(
            f"There was a problem connecting to the URL. See the above error for more details.\n"
            f"If you received a 404 error, try checking that the URL is spelled correctly.\n"
            f"URL: {url}"
        ) from error
    return head


def timeout(timeout: Any) -> timeout:
    "Checks that connection timeout options are valid"

    # Just exit if None
    if timeout is None:
        return timeout

    # Must be a vector with 1 or 2 positive elements
    timeout = validate.vector(timeout, "timeout", dtype=real)
    if timeout.size > 2:
        raise ShapeError("timeout must have either 1 or 2 elements")
    validate.positive(timeout, "timeout")

    # Must either be float or 2-tuple of floats
    if timeout.size == 1:
        return float(timeout[0])
    else:
        return float(timeout[0]), float(timeout[1])
