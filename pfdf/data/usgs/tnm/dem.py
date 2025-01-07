"""
Acquire digital elevation model (DEM) datasets from the USGS National Map
----------
This module contains functions to acquire DEM datasets from the USGS National Map. The
module supports DEM datasets in a variety of resolutions, including 1/3 arc-second
(~10 meters), 1 arc-second (~30 meters), and 1 meter, as well as other legacy resolutions.
We recommend the 1/3 arc-second as a good starting point for most pfdf users.

Most users should use the `read` function to acquire DEM data. This function will read
data from a DEM dataset within a bounding box and return the dataset as a Raster object.
Although DEMs are often distributed as tiles, the `read` function handles all tiling
and mosaiking steps automatically. As such, users do not need to know whether their area 
of interest spans one or more tiles - instead, you can simply provide a bounding box, 
and the `read` routine will handle the rest.

This module identifies DEM datasets using short resolution strings, as opposed to
fully qualified TNM dataset names. The resolution strings are easier to type than
the full names, and are typically the main distinction between different DEMs. The most
commonly used resolutions are:

"1/3 arc-second": (Recommended) Nominal 10 meter resolution
"1 arc-second": Nominal 30 meter resolution
"1 meter": 1 meter resolution

and the module also supports the following legacy and/or spatially limited DEMs:

"1/9 arc-second": Legacy dataset with nominal 3 meter resolution
"2 arc-second": Alaska only. Nominal 60 meter resolution
"5 meter": Alaska only.

This module also includes several low-level functions for interacting with the TNM API.
Advanced users may find this useful for designing advanced DEM acquisition routines.
----------
Data:
    read            - Returns DEM data as a Raster object

Resolutions:
    resolutions     - Returns a dict mapping resolutions onto fully qualified TNM names
    dataset         - Returns the fully qualified TNM name for a dataset

Low-level API:
    query           - Sends a low-level API query for the TNM dataset
    ntiles          - Returns the total number of DEM tiles that match the search criteria
    tiles           - Returns info on DEM tiles that match the search criteria

Internal:
    _tile_info      - Extracts relevant tile info from TNM product info
    _query_tiles    - Gets tile info for a data read
    _validate_tiles - Checks the number of tiles is valid for a data read
    _tile_metadata  - Builds RasterMetadata objects for tiles with overlapping pixels
    _edges          - Computes the minimum and maximum bound along an axis
    _preallocate    - Preallocates a numpy array for a data read
    _read_tiles     - Reads tile data into the final data array
"""

from __future__ import annotations

import typing
from datetime import date
from math import inf
from pathlib import Path

import numpy as np

from pfdf._utils import merror, pixel_limits
from pfdf._validate.core import option
from pfdf.data._utils import validate
from pfdf.data.usgs.tnm import _validate, api
from pfdf.errors import CRSError, NoTNMProductsError, TooManyTNMProductsError
from pfdf.projection import BoundingBox
from pfdf.raster import Raster, RasterMetadata

if typing.TYPE_CHECKING:
    from typing import Any, Optional

    from pfdf.typing.core import MatrixArray, timeout
    from pfdf.typing.raster import BoundsInput

    TileInfo = dict[str, Any]
    TileMetadata = dict[str, RasterMetadata]

#####
# Supported resolutions
#####


def resolutions():
    """
    A dict mapping resolutions onto fully qualified TNM dataset names
    ----------
    resolutions()
    Returns a dict mapping supported resolution strings onto their fully qualified TNM
    dataset names.
    ----------
    Outputs:
        dict: Maps resolutions onto TNM dataset names
    """

    return {
        "1/3 arc-second": "National Elevation Dataset (NED) 1/3 arc-second Current",
        "1 arc-second": "National Elevation Dataset (NED) 1 arc-second Current",
        "1 meter": "Digital Elevation Model (DEM) 1 meter",
        "1/9 arc-second": "National Elevation Dataset (NED) 1/9 arc-second",
        "2 arc-second": "National Elevation Dataset (NED) Alaska 2 arc-second Current",
        "5 meter": "Alaska IFSAR 5 meter DEM",
    }


def dataset(resolution: Any) -> str:
    """
    Returns the fully-qualified TNM name for a resolution string.
    ----------
    dataset(resolution)
    Returns the fully-qualified TNM name for the provided resolution string.
    ----------
    Inputs:
        resolution: A supported DEM resolution string

    Outputs:
        str: The fully qualified TNM dataset name for the resolution
    """

    datasets = resolutions()
    resolution = option(resolution, "resolution", allowed=datasets.keys())
    return datasets[resolution]


#####
# API queries
#####


def query(
    bounds: Optional[BoundsInput] = None,
    resolution: str = "1/3 arc-second",
    *,
    huc: Optional[str] = None,
    max: Optional[int] = None,
    offset: Optional[int] = None,
    timeout: Optional[timeout] = 60,
    strict: bool = True,
) -> dict:
    """
    Low level TNM API query for a DEM dataset
    ----------
    query(bounds, resolution)
    Performs a single API query for the indicated DEM dataset and bounding box and
    returns the response as a JSON dict. `bounds` is optional - if provided, it should
    be a BoundingBox-like input with a CRS. `resolution` should be a supported DEM
    resolution string. Defaults to "1/3 arc-second" if unspecified.

    query(..., *, huc)
    Queries DEM tiles that intersect a provided 2, 4, or 8-digit hydrologic unit code.
    Note the HUC should be a string, rather than an int.

    query(..., *, max)
    query(..., *, offset)
    Sets the paging parameters for the query. The `max` cannot be greater than 1000.
    Aside from this requirement, this command will not process the paging parameters in
    any way.

    query(..., *, strict=False)
    By default, raises an error if the JSON response contains error messages. Set
    strict=False to disable this behavior and instead return the JSON response. Useful
    for troubleshooting unexpected errors in the API.

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
        bounds: The bounding box in which DEM data should be queried
        resolution: The DEM dataset that should be queried. Defaults to 1/3 arc-second
        huc: A 2, 4, or 8-digit hydrologic unit in which DEM data should be queried
        max: The maximum number of tiles the API should return
        offset: The number of tiles to skip
        strict: True (default) to raise an error if the response JSON contains an error
            message. False to disable the error and return the response.
        timeout: The maximum number of seconds to connect to the TNM API

    Outputs:
        dict: The API response as a JSON dict
    """
    name = dataset(resolution)
    return api.query(
        name,
        bounds=bounds,
        huc=huc,
        max=max,
        offset=offset,
        timeout=timeout,
        strict=strict,
    )


def ntiles(
    bounds: Optional[BoundsInput] = None,
    resolution: str = "1/3 arc-second",
    *,
    huc: Optional[str] = None,
    timeout: Optional[timeout] = 60,
) -> int:
    """
    Returns the number of DEM tiles matching the search criteria
    ----------
    ntiles(bounds)
    ntiles(bounds, resolution)
    Returns the number of DEM tiles that intersect the indicated bounding box. `bounds`
    should be a BoundingBox-like input with a CRS. If unspecified, returns all tiles
    in the queried dataset. By default, returns the number of tiles in the 1/3 arc-second
    dataset. Use `resolution` to specify a different DEM dataset instead.

    ntiles(..., *, huc)
    Returns the number of DEM tiles that intersect the indicated hydrologic unit code.
    The `huc` should be a 2, 4, or 8-digit hydrologic unit code as a string. If you
    provide both `bounds` and `huc`, returns the total number of DEM tiles that intersect
    both the bounding box and the HUC.

    ntiles(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        bounds: A bounding box in which to search for DEM tiles
        resolution: The DEM dataset to search. Defaults to 1/3 arc-second
        huc: A hydrologic unit code in which to search for DEM tiles
        timeout: The maximum number of seconds to connect to the TNM server

    Outputs:
        int: The total number of DEM tiles in the search results
    """

    name = dataset(resolution)
    return api.nproducts(name, bounds=bounds, huc=huc, timeout=timeout)


def tiles(
    bounds: Optional[BoundsInput] = None,
    resolution: str = "1/3 arc-second",
    *,
    huc: Optional[str] = None,
    max_queries: Optional[int] = 1,
    max_tiles: Optional[int] = None,
    max_per_query: int = 500,
    offset: int = 0,
    timeout: Optional[timeout] = 60,
) -> TileInfo:
    """
    Returns info on the queried DEM tiles
    ----------
    tiles(bounds)
    tiles(bounds, resolution)
    Returns info on DEM tiles that intersect the provided bounding box. The `bounds`
    should be a BoundingBox-like input with a CRS. If no bounding box is provided,
    returns info on all DEM tiles in the dataset. By default, queries the 1/3 arc-second
    dataset, but use `resolution` to specify a different dataset.

    Returns a list with one element per queried DEM tile. Each element is a dict with
    the following keys:
        title (str): The tile title
        publication_date (datetime): The date the tile was published
        download_url (str): A URL providing read/download access to the dataset
        sciencebase_id (str): The ScienceBase catalog item ID associated with the tile
        sciencebase_url (str): The URL of the ScienceBase landing page for the tile
        filename (str): The name of the tile file
        format (str): The format of the tile file (typically GeoTiff)
        nbytes (int): The total size of the tile file in bytes
        bounds (BoundingBox): An EPSG:4326 BoundingBox for the tile's extent
        extent (str): Short description of the tile's extent

    By default, this command limits itself to a single API query with a maximum of
    500 search results, so will raise an error if the search results contain more than
    500 tiles. See the `max_queries` and `max_per_query` options below to raise these
    limits.

    tiles(..., *, huc)
    Returns info on tiles that intersect the given hydrologic unit. The `huc` should be
    a 2, 4, or 8-digit hydrologic unit code as a string. If you provide both `bounds`
    and `huc`, returns info on tiles that intersect both the bounding box and the HUC.

    tiles(..., *, max_per_query)
    tiles(..., *, max_queries)
    Options to increase the number of returned tiles. Use `max_per_query` to specify
    the maximum number of products that the API can return per query. This is essentially
    the "max" paging parameter, but will automatically adjust to account for any paging
    parameter constraints. This value cannot exceed 1000. Note that the ScienceBase API
    (which is used by TNM's API) can sometimes time out for larger values of max_per_query.
    If you are receiving frequent HTTP 503 "Bad Gateway" errors, try reducing max_per_query
    to a smaller value.

    Use `max_queries` to specify the maximum number of API queries allowed to retrieve
    tile info. In general, retrieving N tiles will require `ceil(N / max_per_query)`
    API queries. Increasing this option can allow the command to retrieve info on more
    than 1000 tiles. You can also set max_queries=None to allow any number of API
    queries (and thereby retrieve any number of tiles). However, we strongly
    recommend checking the total number of tiles (using the `ntiles` function)
    before setting max_queries to None. This is because the maximum number of API
    queries will become unbounded, and making too many queries in a short period of time
    could result in rate limiting.

    tiles(..., *, max_tiles)
    tiles(..., *, offset)
    Specify how many tiles, and which tiles, should be retrieved. Use
    `max_tiles` to specify the maximum number of search results whose info should be
    retrieved. Once this value is reached, all remaining search results are skipped.
    This input is essentially a more generalized "max" paging parameter. Unlike the
    paging parameter, `max_tiles` does not need to be a multiple of 5, and may also
    retrieve more than 1000 products (across multiple API queries). By default,
    max_tiles is set to None, which allows the command to retrieve info on any
    number of tiles.

    By default, this command begins retrieving tile info at the first search result.
    Use `offset` to skip the first N tile before beginning to retrieve product info.
    You can combine offset with max_tiles to implement custom paging schemes. The offset
    must be less than the total number of tiles.

    tiles(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        bounds: A bounding box in which to search for DEM tiles
        resolution: The DEM dataset to search. Defaults to 1/3 arc-second
        huc: A hydrologic unit code in which to search for DEM tiles
        max_per_query: The maximum number of tiles that should be retrieved per API query
        max_queries: The maximum allowed number of API queries
        max_tiles: The maximum number of tiles whose info should be retrieved
        offset: The number of tiles to skip before retrieving product infos
        timeout: The maximum number of seconds to connect with the TNM server

    Outputs:
        list[dict]: The info for each tile in the search results. Each element is a dict
            with the following keys:

            title (str): The tile title
            publication_date (datetime): The date the tile was published
            download_url (str): A URL providing read/download access to the dataset
            sciencebase_id (str): The ScienceBase catalog item ID associated with the tile
            sciencebase_url (str): The URL of the ScienceBase landing page for the tile
            filename (str): The name of the tile file
            format (str): The format of the tile file (typically GeoTiff)
            nbytes (int): The total size of the tile file in bytes
            bounds (BoundingBox): An EPSG:4326 BoundingBox for the tile's extent
            extent (str): Short description of the tile's extent
    """

    name = dataset(resolution)
    tiles = api.products(
        name,
        bounds=bounds,
        huc=huc,
        max_queries=max_queries,
        max_products=max_tiles,
        max_per_query=max_per_query,
        offset=offset,
        timeout=timeout,
    )
    return [_tile_info(tile) for tile in tiles]


def _tile_info(tile: dict) -> TileInfo:
    "Extracts relevant tile info from TNM product info"

    # Build BoundingBox
    bounds = tile["boundingBox"]
    bounds = BoundingBox(
        bounds["minX"], bounds["minY"], bounds["maxX"], bounds["maxY"], crs=4326
    )

    # Get download URL and extract filename
    url = tile["downloadURL"]
    filename = Path(url).name

    # Organize info
    return {
        # General metadata
        "title": tile["title"],
        "publication_date": date.fromisoformat(tile["publicationDate"]),
        # Data source
        "download_url": url,
        "sciencebase_id": tile["sourceId"],
        "sciencebase_url": f"https://www.sciencebase.gov/catalog/item/{tile['sourceId']}",
        # File info
        "filename": filename,
        "format": tile["format"],
        "nbytes": tile["sizeInBytes"],
        # Spatial metadata
        "bounds": bounds,
        "extent": tile["extent"],
    }


#####
# Data acquisition
#####


def read(
    bounds: BoundsInput,
    resolution: str = "1/3 arc-second",
    *,
    max_tiles: int = 10,
    timeout: Optional[timeout] = 60,
) -> Raster:
    """
    Reads data from a DEM dataset into memory as a Raster object
    ----------
    read(bounds)
    Reads data within the bounding box from the current 1/3 arc-second DEM and returns
    the results as a Raster object. Automatically mosaiks raster data spread across
    multiple DEM tiles. The `bounds` should be a BoundingBox-like object with a CRS.
    Raises an error if the bounding box intersects more than 10 DEM tiles, but see
    the `max_tiles` option below to raise this limit.

    read(..., resolution)
    Reads data from the indicated DEM dataset. Please see the `resolutions` function
    for supported resolutions. Note that all tiles being read must use the same CRS.
    Raises an error if this is not the case. This restriction is usually most relevant
    for the 1 meter dataset, which uses different CRS for data in different UTM zones.
    If you are reading data from the 1 meter dataset, then check that your bounding
    box does not span more than 1 UTM zone.

    read(..., *, max_tiles)
    Specifies the maximum number of tiles allowed to intersect with the BoundingBox.
    Raises an error if more tiles intersect the bounding box. This option is intended to
    prevent users from accidentally downloading data from very large areas. The default
    `max_tiles` is set to 10, which should prevent data reads for the 1/3 arc-second DEM
    from spanning more than 3 degrees of latitude and longitude. You can increase
    `max_tiles` up to a value of 500 to permit data reads from larger areas.

    read(..., *, timeout)
    Specifies a maximum time in seconds for connecting to the TNM
    server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case server queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        bounds: The bounding box in which DEM data should be read
        resolution: The DEM dataset to read data from
        max_tiles: The maximum number of DEM tiles allowed to intersect the bounding box
        timeout: The maximum number of seconds to connect to the TNM server

    Outputs:
        Raster: The read data from the DEM dataset
    """

    # Validate
    bounds = validate.bounds(bounds, as_string=False)
    max_tiles = _validate.count(max_tiles, "max_tiles", max=500)

    # Query DEM tiles. Informative error if there are too many tiles, or no tiles
    info = _query_tiles(bounds, resolution, timeout)
    ntiles = len(info)
    _validate_ntiles(ntiles, max_tiles)

    # Get the URL and RasterMetadata for each tile with overlapping data.
    metadatas = _tile_metadata(info, bounds)

    # Get the metadata for the final read array
    left, right = _edges(metadatas, min_edge="left", max_edge="right")
    bottom, top = _edges(metadatas, min_edge="bottom", max_edge="top")
    metadata = next(iter(metadatas.values()))  # First metadata object in the dict
    metadata = metadata.clip((left, bottom, right, top))

    # Build the final data array and Raster
    values = _preallocate(metadata)
    _read_tiles(metadatas, metadata, values)
    return Raster.from_array(
        values, nodata=metadata.nodata, spatial=metadata, copy=False
    )


#####
# Read utilities
#####


def _query_tiles(bounds: BoundingBox, resolution: Any, timeout: Any) -> TileInfo:
    "Gets tile info for a data read."

    try:
        return tiles(bounds, resolution, max_queries=1, timeout=timeout)
    except TooManyTNMProductsError:
        raise TooManyTNMProductsError(
            "There are over 500 DEM tiles matching the search criteria. "
            "Either reduce the size of the bounding box, or query a different DEM dataset."
        ) from None


def _validate_ntiles(ntiles: int, max_tiles: int) -> None:
    "Checks the number of tiles is valid for a data read"

    if ntiles > max_tiles:
        raise TooManyTNMProductsError(
            f"There are {ntiles} DEM tiles in the search area, which is greater "
            f"the maximum allowed number of tiles ({max_tiles}). Either reduce the "
            f"search bounds to a smaller area, or increase `max_tiles`."
        )
    elif ntiles == 0:
        raise NoTNMProductsError(
            "There are no DEM tiles in the search area. Try using a different bounding "
            "box, or query a different DEM dataset."
        )


def _tile_metadata(tiles: TileInfo, bounds: BoundingBox) -> TileMetadata:
    "Builds metadata objects for tiles with overlapping pixels"

    # ASSUMPTION:
    # We are assuming that all USGS tiles in a common dataset are well behaved.
    # That is, they will have the same resolution, alignment, NoData, and will be
    # oriented in the first quadrant.
    #
    # Tiles in a well behaved data read should also have the same CRS, but this is not
    # guaranteed for USGS DEM tiles (notably, the 1 meter DEM uses different CRS for
    # different UTM zones), so we will need to check this explicitly below.

    # Get the URL and metadata for each tile
    crs = None
    metadatas = {}
    for t, tile in enumerate(tiles):
        url = tile["download_url"]
        metadata = RasterMetadata.from_url(url, bounds=bounds, check_status=False)

        # Skip tiles with no overlapping pixels
        if 0 in metadata.shape:
            continue

        # Require all tiles to have the same CRS.
        if crs is None:
            crs = metadata.crs
        elif metadata.crs != crs:
            raise CRSError(
                f"All the DEM tiles being read must have the same CRS. "
                f"But the CRS of tile 0 ({crs.name}) differs from "
                f"the CRS of tile {t} ({metadata.crs.name})"
            )
        metadatas[url] = metadata

    # Require at least 1 pixel of loaded data
    if len(metadatas) == 0:
        raise NoTNMProductsError(
            "The bounds must cover at least 1 pixel of DEM data. "
            "Try reading data from a larger bounding box."
        )
    return metadatas


def _edges(
    metadatas: dict[str, RasterMetadata], min_edge: str, max_edge: str
) -> tuple[float, float]:
    "Computes the minimum and maximum bound along an axis"

    minval = inf
    maxval = -inf
    for metadata in metadatas.values():
        minval = min(minval, getattr(metadata, min_edge))
        maxval = max(maxval, getattr(metadata, max_edge))
    return minval, maxval


def _preallocate(metadata: RasterMetadata) -> MatrixArray:
    "Preallocates a numpy array for a data read"

    try:
        return np.full(metadata.shape, metadata.nodata, metadata.dtype)
    except Exception as error:
        message = (
            f"Cannot read DEM data because the data array is too large for memory. "
            f"Try reading data from a smaller bounding box, or "
            f"use a lower resolution dataset."
        )
        merror.supplement(error, message)


def _read_tiles(
    tiles: TileMetadata, metadata: RasterMetadata, values: MatrixArray
) -> None:
    "Read tile data into the final array"

    for url in tiles:
        raster = Raster.from_url(url, bounds=metadata.bounds, check_status=False)
        rows, cols = pixel_limits(metadata.affine, raster.bounds)
        rows = slice(*rows)
        cols = slice(*cols)
        values[rows, cols] = raster.values
