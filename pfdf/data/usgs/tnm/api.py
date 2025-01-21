"""
Functions that query the TNM API
----------
This module provides functions to support low-level queries to the TNM API. This module
is mostly intended for developers who want to acquire datasets not directly supported
by pfdf, or who need to troubleshoot API responses. The TNM API is structured around
product records, so in addition to generic API queries, this module provides functions
to (1) return the total number of products in a query, and (2) return product info as
JSON dicts.

The TNM API uses a paging+offset system to limit the total number of products returned 
per query. As such, the API will never return more than 1000 products per query, even if
the query encompasses many more products. The paging system also inherits various quirks
from the ScienceBase API, such as the requirement that the `max` paging be a multiple
of 5 whenever `offset` is greater than 100. To circumvent these limitations, we
recommend most developers work via the "products" function. This function handles most 
of the paging functionality under-the-hood, implementing multiple API calls as allowed
and needed, thereby allowing developers to focus on simply acquiring needed products.

By contrast, the "query" function provides very low-level access to the API. This
function sends a single API query (regardless of the number of products), and does not
implement any paging functionality. As such, this function is mostly intended for
troubleshooting API responses, and is not recommended for general workflows.

You can find additional API documentation here: https://apps.nationalmap.gov/tnmaccess/
Note that this module specifically leverages the "Products" service. See the
documentation of that service for lists of fully qualified dataset names, supported file 
formats, and other parameters.
----------
Functions:
    api_url     - Returns the URL for the TNM API
    query       - Submits a single query to the TNM API and returns the response JSON
    nproducts   - Returns the total number of TNM products in a query
    products    - Returns info on queried products as a list of JSON dicts

Internal:
    _ntotal     - Extracts the total number of products from a query response
    _parse_max  - Determines a value of the `max` paging parameter to support generic offsets
    _items      - Extracts product info from a query response
"""

from __future__ import annotations

import typing
from math import ceil

from pfdf.data._utils import requests, validate
from pfdf.data.usgs.tnm import _validate
from pfdf.errors import DataAPIError, MissingAPIFieldError, TooManyTNMProductsError

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import strs, timeout
    from pfdf.typing.raster import BoundsInput

# Outage URLs
_TNM_OUTAGES = "https://stats.uptimerobot.com/gxzRZFARLZ"  # TNM outages
_SB_OUTAGES = "https://www.sciencebase.gov/catalog/status"  # ScienceBase outages


#####
# User functions
#####


def api_url() -> str:
    """
    Returns the URL for the TNM API
    ----------
    api_url()
    Returns the URL for the TNM API
    ----------
    Outputs:
        str: The URL for the TNM API
    """
    return "https://tnmaccess.nationalmap.gov/api/v1/products"


def query(
    datasets: strs,
    *,
    bounds: Optional[BoundsInput] = None,
    huc: Optional[str] = None,
    formats: Optional[strs] = None,
    max: Optional[int] = None,
    offset: Optional[int] = None,
    timeout: Optional[timeout] = 60,
    strict: bool = True,
) -> dict:
    """
    Queries TNM and returns the response as a JSON dict
    ----------
    query(datasets)
    Makes a single query to the TNM API and returns the response as a JSON dict. By
    default, raises an error if the response contains error messages, but see below to
    disable this behavior. The `datasets` should be a string or list of strings.

    query(..., *, bounds)
    query(..., *, huc)
    Optionally queries datasets within the indicated bounding box and/or hydrologic
    unit. The `bounds` input should be a BoundingBox-like input with a CRS. The `huc`
    input should be 2, 4, or 8-digit hydrologic unit code as a string (not an int). When
    using these parameters, the query will only return products that intersect these
    features. If you provide both bounds and huc, then only products that intersect both
    features will be returned.

    query(..., *, formats)
    Only queries datasets that match the specified file formats.

    query(..., *, max)
    query(..., *, offset)
    Specifies paging parameters for the query. The `max` is the maximum number of
    products that can be returned in the query - this value cannot exceed 1000. The
    `offset` is the number of products that should be skipped before the first product
    is read. Note that these parameters will generate an error if offset is greater than
    100 and max is not a multiple of 5.

    query(..., *, strict=False)
    Does not raise an error if the response contains error messages, and instead returns
    the response. This option may be useful for troubleshooting unexpected API errors.

    query(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        datasets: A string or list of strings indicating the datasets that should queried
        bounds: A bounding box in which products should be queried
        huc: A hydrologic unit code in which products should be queried
        formats: The file formats that should be queried
        max: The maximum number of products that should be returned by the query
        offset: The number of products to skip before returning product info
        strict: True (default) to raise an error if the response JSON contains error
            messages. False to not raise an error and return the JSON dict.
        timeout: The maximum number of seconds to connect with the TNM server

    Outputs:
        dict: TNM product info as a JSON dict
    """

    # Validate and build parameter dict
    params = {"datasets": validate.strings(datasets, "datasets")}
    if bounds is not None:
        params["bbox"] = validate.bounds(bounds)
    if huc is not None:
        params["polyCode"], params["polyType"] = _validate.huc(huc)
    if formats is not None:
        params["prodFormats"] = validate.strings(formats, "formats")
    if max is not None:
        params["max"] = _validate.max(max, "max")
    if offset is not None:
        params["offset"] = _validate.count(offset, "offset", allow_zero=True)

    # Make the query
    params["outputFormat"] = "JSON"
    servers = ["TNM", "ScienceBase"]
    outages = [_TNM_OUTAGES, _SB_OUTAGES]
    response = requests.json(api_url(), params, timeout, servers, outages)

    # Optionally stop if there were errors
    if strict and ("errors" in response) and len(response["errors"]) > 0:
        errors = response["errors"]
        if isinstance(errors, dict) and "message" in errors:
            message = (
                f"TNM reported the following error for the API query:\n"
                f"{errors['message']}"
            )
        else:
            message = "TNM reported an error for the API query"
        raise DataAPIError(message)
    return response


def nproducts(
    datasets: strs,
    *,
    bounds: Optional[BoundsInput] = None,
    huc: Optional[str] = None,
    formats: Optional[strs] = None,
    timeout: Optional[timeout] = 60,
) -> int:
    """
    Returns the total number of TNM products that match the search criteria
    ----------
    nproducts(datasets)
    Returns the total number of products in the indicated datasets. This can be much
    larger than the "max" paging parameter, which is capped at 1000. This function is
    mostly intended to help developers determine how many API queries will be required
    to retrieve all the products matching the search criteria. Note that `datasets`
    should be a string or list of strings indicating fully qualified TNM dataset names.

    nproducts(..., *, bounds)
    nproducts(..., *, huc)
    Returns the total number of products that intersect the indicated bounding box or
    HUC. These inputs are optional. The `bounds` should be a BoundingBox-like input with
    a CRS. The `huc` should be 2, 4, or 8-digit hydrologic unit code as a string (not
    an int). If you provide both bounds and huc, then returns the total number of
    products that intersect both the bounds and the huc.

    nproducts(..., *, formats)
    Returns the total number of search result products that match the indicated file
    formats. The `formats` may be a string, or a list of strings. If using a list, the
    returned number will be the number of products that match at least 1 of the
    indicated formats.

    nproducts(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        datasets: The fully qualified names of TNM datasets that should be queried
        bounds: A bounding box in which to search for products
        huc: A hydrologic unit code in which to search for products
        formats: The file formats to search for
        timeout: The maximum number of seconds to connect to the TNM API

    Outputs:
        int: The total number of TNM products that match the search results
    """

    info = query(
        datasets,
        bounds=bounds,
        huc=huc,
        formats=formats,
        max=1,
        offset=0,
        timeout=timeout,
    )
    return _ntotal(info)


def products(
    datasets: strs,
    *,
    bounds: Optional[BoundsInput] = None,
    huc: Optional[str] = None,
    formats: Optional[strs] = None,
    max_queries: Optional[int] = 1,
    max_products: Optional[int] = None,
    max_per_query: int = 500,
    offset: int = 0,
    timeout: Optional[timeout] = 60,
) -> list[dict]:
    """
    Returns info on TNM products meeting the search criteria
    ----------
    products(datasets)
    Returns info on all products in the queried datasets. Returns a list with one
    element per product. Each element is a JSON dict with the product's information.

    By default, this command limits itself to a single API query with a maximum of
    500 search results, so will raise an error if the search results contain more than
    500 products. See the `max_queries` and `max_per_query` options below to raise these
    limits.

    products(..., *, bounds)
    products(..., *, huc)
    Restricts the search results to products intersecting a provided bounding box and/or
    hydrologic unit code. Both inputs are optional, but can help limit API queries for
    bounded domains. The `bounds` should be a BoundingBox-like input with a CRS, and
    `huc` should be a 2, 4, or 8-digit hydrologic unit code as a string (not an int).
    If you provide both bounds and huc, then the search is limited to products that
    intersect both the bounds and the huc.

    products(..., *, formats)
    Restricts search results to products in one of the requested file formats. The
    `formats` may be a string or list of strings. If using a list of strings, then the
    search results will include all products that match at least one of the indicated
    file formats.

    products(..., *, max_per_query)
    products(..., *, max_queries)
    Options to increase the number of returned products. Use `max_per_query` to specify
    the maximum number of products that the API can return per query. This is essentially
    the "max" paging parameter, but will automatically adjust to account for any paging
    parameter constraints. This value cannot exceed 1000. Note that the ScienceBase API
    (which is used by TNM's API) can sometimes time out for larger values of max_per_query.
    If you are receiving frequent HTTP 503 "Bad Gateway" errors, try reducing max_per_query
    to a smaller value.

    Use `max_queries` to specify the maximum number of API queries allowed to retrieve
    product info. In general, retrieving N products will require `ceil(N / max_per_query)`
    API queries. Increasing this option can allow the command to retrieve info on more
    than 1000 products. You can also set max_queries=None to allow any number of API
    queries (and thereby retrieve any number of products). However, we strongly
    recommend checking the total number of products (using the `nproducts` function)
    before setting max_queries to None. This is because the maximum number of API
    queries will become unbounded, and making too many queries in a short period of time
    could result in rate limiting.

    products(..., *, max_products)
    products(..., *, offset)
    Specify how many products, and which products, should be retrieved. Use
    `max_products` to specify the maximum number of search results whose info should be
    retrieved. Once this value is reached, all remaining search results are skipped.
    This input is essentially a more generalized "max" paging parameter. Unlike the
    paging parameter, `max_products` does not need to be a multiple of 5, and may also
    retrieve more than 1000 products (across multiple API queries). By default,
    max_products is set to None, which allows the command to retrieve info on any
    number of products.

    By default, this command begins retrieving product info at the first search result.
    Use `offset` to skip the first N products before beginning to retrieve product info.
    You can combine offset with max_products to implement custom paging schemes. The
    offset must be less than the total number of products.

    products(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        datasets: The fully qualified names of TNM datasets that should be searched
        bounds: A bounding box in which to search for products
        huc: A hydrologic unit code in which to search for products
        formats: The file formats to search for
        max_per_query: The maximum number of products that should be retrieved per API query
        max_queries: The maximum allowed number of API queries
        max_products: The maximum number of products whose info should be retrieved
        offset: The number of products to skip before retrieving product infos
        timeout: The maximum number of seconds to connect with the TNM server

    Outputs:
        list[dict]: Information on the queried products. The list will contain one
            element per retrieved product. Each element is a JSON dict of the product's info
    """

    # Validate
    max_queries = _validate.upper_bound(max_queries, "max_queries")
    max_products = _validate.upper_bound(max_products, "max_products")
    max_per_query = _validate.max_per_query(max_per_query)
    offset = _validate.count(offset, "offset", allow_zero=True)

    # Make the initial query
    max, padding = _parse_max(max_products, max_per_query)
    info = query(
        datasets,
        bounds=bounds,
        huc=huc,
        formats=formats,
        max=max,
        offset=offset,
        timeout=timeout,
    )

    # Get the total number of search results, the number of products that need to be
    # retrieved, and the number of API queries needed
    ntotal = _ntotal(info)
    nproducts = min(ntotal, max_products)
    nqueries = ceil(nproducts / max_per_query)

    # Error if the offset is too large
    if offset >= ntotal:
        raise IndexError(
            f"offset must be less than the total number of search results ({ntotal}), "
            f"but the input offset ({offset}) is not. "
        )

    # Error if too many API queries are needed
    elif nqueries > max_queries:
        raise TooManyTNMProductsError(
            f"There are {nproducts} TNM products that match the search criteria.\n"
            f"You have allowed {max_per_query} products per query, so retrieving all\n"
            f"these products will require {nqueries} TNM API queries, which is greater\n"
            f"than the maximum allowed number of queries ({max_queries}).\n"
            f"Try restricting the search or increase max_queries and/or max_per_query."
        )

    # Collect the product infos, making additional API queries as needed
    products = _items(info, max, padding)
    for _ in range(1, nqueries):
        nproducts -= max_per_query  # The number of products remaining
        max, padding = _parse_max(nproducts, max_per_query)
        offset += max_per_query
        info = query(
            datasets, bounds=bounds, huc=huc, max=max, offset=offset, timeout=timeout
        )
        products += _items(info, max, padding)
    return products


#####
# Utilities
#####


def _ntotal(info: dict) -> int:
    "Extracts the total number of search results for a query"

    if "total" not in info or not isinstance(info["total"], int):
        raise MissingAPIFieldError("TNM failed to return a total product count")
    return info["total"]


def _parse_max(nproducts: int, max_per_query: int) -> tuple[int, int]:
    """Determines a value for the `max` paging parameter that (1) is a multiple of 5,
    and (2) minimizes the total number of products queried. Note that the multiple of 5
    rule is required to support values of the `offset` parameter greater than 100. This
    is actually a quirk of the ScienceBase API that percolates to TNM."""

    max = min(nproducts, max_per_query)
    remainder = max % 5
    if remainder == 0:
        return max, 0
    else:
        padding = 5 - remainder
        max = max + padding
        return max, padding


def _items(info: dict, max: int, padding: int) -> list[dict]:
    "Extracts product info from a query"

    # Extract the return products
    if "items" not in info:
        raise MissingAPIFieldError("TNM failed to return product information")
    items = info["items"]

    # Account for (1) padded entries and (2) fewer than max items
    nitems = len(items)
    max_items = max - padding
    stop = min(nitems, max_items)
    return items[:stop]
