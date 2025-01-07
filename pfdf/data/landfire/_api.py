"""
Small utilities for working with responses from the LFPS API
----------
Contents:
    lfps_url            - Returns the base LFPS URL
    json                - Sends a LFPS request and returns the response as JSON
    field               - Returns a field from a LFPS response
    report_job_error    - Provides info on a failed job query
    status              - Extracts job status from a query
"""

from __future__ import annotations

import typing

from pfdf.data._utils import requests
from pfdf.errors import DataAPIError, MissingAPIFieldError

if typing.TYPE_CHECKING:
    from typing import Any, NoReturn

    from pfdf.typing.core import timeout


def lfps_url() -> str:
    "Returns the base URL for the LANDFIRE LFPS geoprocessing server"
    return "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/"


def json(url: str, params: dict, timeout: timeout) -> dict:
    "Sends a request to the LFPS server and returns the response as JSON"
    params["f"] = "json"
    return requests.json(url, params, timeout, "LANDFIRE LFPS")


def field(response: dict, field: str, description: str) -> Any:
    "Returns a field from an LFPS JSON response"
    if field not in response or response[field] == "":
        raise MissingAPIFieldError(f"LANDFIRE LFPS failed to return the {description}")
    return response[field]


def report_job_error(error: dict, id: str) -> NoReturn:
    "Provides info on a failed job query"

    # Informative error if the job does not exist
    if "message" in error:
        message = error["message"]
        if "Job not found on server" in message:
            raise ValueError(
                f"The queried job ({id}) does not exist on the LFPS server.\n"
                f"Try checking that the job ID is spelled correctly.\n"
                f"If you submitted the job a while ago, "
                f"then the job may have been deleted."
            )

        # Otherwise, provide as much error info as possible
        else:
            raise DataAPIError(
                f"LANDFIRE LFPS reported the following error in the API query "
                f"for job {id}:\n{message}",
            )
    else:
        raise DataAPIError(
            f"LANDFIRE LFPS reported an error in the API query for job {id}"
        )


def status(job: dict) -> str:
    "Extracts job status from a query"
    return field(job, "jobStatus", "job status")
