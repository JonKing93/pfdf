"""
Functions for low level interactions with the LANDFIRE LFPS API
----------
The functions in this module are intended to support developer interactions with the
LFPS API. In particular, these functions provide support for initiating and querying
LFPS jobs. Most users will not need these functions, but developers may find them
useful for troubleshooting API interactions and for designing custom data acquisition
routines.
----------
URLs:
    lfps_url    - Returns the base URL for the LFPS API
    job_url     - Returns the API URL for a given job

Jobs:
    submit_job  - Submits a job to the LFPS API and returns the job ID
    query_job   - Queries an LFPS job and returns the job info as a JSON dict
    job_status  - Returns the status code for a queried job
"""

from __future__ import annotations

import typing

import pfdf._validate.core as cvalidate
from pfdf.data._utils import validate
from pfdf.data.landfire import _api

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import strs, timeout
    from pfdf.typing.raster import BoundsInput

#####
# URLs
#####


def lfps_url() -> str:
    """
    Returns the base URL for the LANDFIRE LFPS geoprocessing server
    ----------
    lfps_url()
    Returns the base URL for the LFPS. This URL is used for queries that are not job
    specific, most notably for submitting new job requests.
    ----------
    Outputs:
        str: The base URL for the LFPS API
    """
    return _api.lfps_url()


def job_url(id: str) -> str:
    """
    Returns the URL for an LFPS job
    ----------
    job_url(id)
    Returns the API URL for the job with the specified ID. These URLs are typically
    used for querying job-specific information.
    ----------
    Inputs:
        id: A job ID

    Outputs:
        str: The URL for the indicated job
    """
    return lfps_url() + "jobs/" + id


#####
# Jobs
#####


def submit_job(
    layers: strs,
    bounds: Optional[BoundsInput] = None,
    *,
    timeout: Optional[timeout] = 10,
) -> str:
    """
    Submits a job to the LANDFIRE Product Service (LFPS) and returns the job ID
    ----------
    submit_job(layers)
    Submits a job for the indicated LFPS data layers. You can find a list of LFPS layer
    names here: https://lfps.usgs.gov/helpdocs/productstable.html
    The `layers` input may be a string, or a sequence of strings. Returns the job ID
    upon successful job submission.

    submit_job(..., bounds)
    Submits a job for data within the given bounding box. The `bounds` input may be any
    BoundingBox-like input, and must have a CRS. The LFPS job will restrict layer data
    to this bounding box.

    submit_job(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        layers: The LFPS layer names of datasets included in the job
        bounds: The bounding box for the job's datasets
        timeout: The maximum time in seconds to connect to the LFPS server

    Outputs:
        str: The job ID for the newly submitted job
    """

    # Validate and build the parameter dict
    params = {"Layer_List": validate.strings(layers, "layers", delimiter=";")}
    if bounds is not None:
        params["Area_of_Interest"] = validate.bounds(bounds, delimiter=" ")

    # Submit the job and return the job ID
    url = lfps_url() + "submitJob"
    response = _api.json(url, params, timeout)
    return _api.field(response, "jobId", "job ID")


def query_job(id: str, *, timeout: Optional[timeout] = 10, strict: bool = True) -> dict:
    """
    Returns LFPS job info as a JSON dict
    ----------
    query_job(id)
    query_job(id, *, strict=False)
    Queries the indicated LFPS job, and returns the job's info as a JSON dict. Raises
    an error if the JSON response includes error messages. Alternatively, set strict=False
    to also return JSON responses that contain errors. This can be useful for
    troubleshooting the API.

    query_job(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        id: The ID of the job that should be queried
        strict: True (default) to raise an error if the JSON includes error messages.
            False to return JSON responses that include error messages.
        timeout: The maximum time in seconds to connect to the LFPS server

    Outputs:
        dict: The job's information as a JSON dict
    """

    # Query the job
    cvalidate.string(id, "id")
    url = job_url(id)
    job = _api.json(url, {}, timeout)

    # Optionally stop if there were errors
    if strict and "error" in job:
        _api.report_job_error(job["error"], id)
    return job


def job_status(id: str, *, timeout: Optional[timeout] = 10) -> str:
    """
    Returns the status code for an LFPS job
    ----------
    job_status(id)
    Returns the status code for the queried job.

    job_status(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        id: The ID of the job whose status should be queried
        timeout: The maximum number of seconds to connect to the LFPS server

    Outputs:
        str: The status of the queried job
    """
    response = query_job(id, timeout=timeout)
    return _api.status(response)
