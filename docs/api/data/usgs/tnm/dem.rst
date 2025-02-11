data.usgs.tnm.dem module
========================

.. _pfdf.data.usgs.tnm.dem:

.. py:module:: pfdf.data.usgs.tnm.dem

Functions to load digital elevation model (DEM) data from the USGS National Map.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - 
      -
    * - **Load Data**
      -
    * - :ref:`read <pfdf.data.usgs.tnm.dem.read>`
      - Loads DEM data into memory as a :ref:`Raster object <pfdf.raster.Raster>`
    * -
      -
    * - **Resolutions**
      -
    * - :ref:`resolutions <pfdf.data.usgs.tnm.dem.resolutions>`
      - Returns a dict mapping resolutions onto fully qualified TNM names
    * - :ref:`dataset <pfdf.data.usgs.tnm.dem.dataset>`
      - Returns the fully qualified TNM name for a dataset
    * - 
      -
    * - **Low-level API**
      -
    * - :ref:`query <pfdf.data.usgs.tnm.dem.query>`
      - Sends a low-level API query for the TNM dataset
    * - :ref:`ntiles <pfdf.data.usgs.tnm.dem.ntiles>`
      - Returns the total number of DEM tiles that match the search criteria
    * - :ref:`tiles <pfdf.data.usgs.tnm.dem.tiles>`
      - Returns info on DEM tiles that match the search criteria
      
.. py:currentmodule:: pfdf.data.usgs.tnm.dem

----

Load Data
---------

.. _pfdf.data.usgs.tnm.dem.read:

.. py:function:: read(bounds, resolution = "1/3 arc-second", *, max_tiles = 10, timeout = 60)

    Reads data from a DEM dataset into memory as a Raster object

    .. dropdown:: Read Data

        ::

            read(bounds)
            read(bounds, resolution)

        Reads data within the bounding box from the current 1/3 arc-second DEM and returns the results as a Raster object. Automatically mosaics raster data spread across multiple DEM tiles. The ``bounds`` should be a BoundingBox-like object with a CRS. Raises an error if the bounding box intersects more than 10 DEM tiles, but see the ``max_tiles`` option below to raise this limit.

        By default, reads data from the 1/3 arc-second DEM dataset. Use the ``resolution`` option to read from a different dataset instead. Supported resolutions include: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, and 5 meter. Note that all tiles being read must use the same CRS. Raises an error if this is not the case. This restriction is usually most relevant for the 1 meter dataset, which uses different CRS for data in different UTM zones. If you are reading data from the 1 meter dataset, then check that your bounding box does not span more than 1 UTM zone.

    .. dropdown:: Max Tiles

        ::

            read(..., *, max_tiles)

        Specifies the maximum number of tiles allowed to intersect with the BoundingBox. Raises an error if more tiles intersect the bounding box. This option is intended to prevent users from accidentally downloading data from very large areas. The default ``max_tiles`` is set to 10, which should prevent data reads for the 1/3 arc-second DEM from spanning more than 3 degrees of latitude and longitude. You can increase ``max_tiles`` up to a value of 500 to permit data reads from larger areas.

    .. dropdown:: Connection Timeout

        ::

            read(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **bounds** (*BoundingBox-like*) -- The bounding box in which DEM data should be read
        * **resolution** (*str*) -- The DEM dataset to read data from
        * **max_tiles** (*int*) -- The maximum number of DEM tiles allowed to intersect the bounding box
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the TNM server

    :Outputs:
        *Raster* -- The data read from the DEM dataset


----

Resolutions
-----------

.. _pfdf.data.usgs.tnm.dem.resolutions:

.. py:function:: resolutions():

    A dict mapping resolutions onto fully qualified TNM dataset names

    ::

        resolutions()

    Returns a dict mapping supported resolution strings onto their fully qualified TNM dataset names.

    :Outputs:
        *dict* --Maps resolutions onto TNM dataset names



.. _pfdf.data.usgs.tnm.dem.dataset:

.. py:function:: dataset(resolution)

    Returns the fully-qualified TNM name for a resolution string.

    ::

        dataset(resolution)

    Returns the fully-qualified TNM name for the provided resolution string. Supported resolution strings include: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, and 5 meter.

    :Inputs:
        * **resolution** (*str*) -- A supported DEM resolution string

    :Outputs:
        *str* -- The fully qualified TNM dataset name for the resolution


----

Low-level API
-------------

.. _pfdf.data.usgs.tnm.dem.query:

.. py:function:: query(bounds = None, resolution = "1/3 arc-second", *, huc = None, max = None, offset = None, timeout = 60, strict = True)

    Low level TNM API query for a DEM dataset

    .. dropdown:: Query DEM

        ::

            query(bounds, resolution)

        Performs a single API query for the indicated DEM dataset and bounding box and returns the response as a JSON dict. ``bounds`` is optional - if provided, it should be a BoundingBox-like input with a CRS. By default, queries the 1/3 arc-second DEM dataset. Use the ``resolution`` input to query a different DEM instead. Supported resolutions include: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, and 5 meter.

    .. dropdown:: Filter by HUC

        ::

            query(..., *, huc)

        Queries DEM tiles that intersect a provided 2, 4, or 8-digit hydrologic unit code. Note the HUC should be a string, rather than an int.

    .. dropdown:: Paging Parameters

        ::

            query(..., *, max)
            query(..., *, offset)

        Sets the paging parameters for the query. The ``max`` cannot be greater than 1000. Aside from this requirement, this command will not process the paging parameters in any way.

    .. dropdown:: Allow Errors

        ::

            query(..., *, strict=False)

        By default, raises an error if the JSON response contains error messages. Set strict=False to disable this behavior and instead return the JSON response. Useful for troubleshooting unexpected errors in the API.

    .. dropdown:: Connection Timeout

        ::

            query(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **bounds** (*BoundingBox-like*) -- The bounding box in which DEM data should be queried
        * **resolution** (*str*) -- The DEM dataset that should be queried. Defaults to 1/3 arc-second
        * **huc** (*str*) -- A 2, 4, or 8-digit hydrologic unit in which DEM data should be queried
        * **max** (*int*) -- The maximum number of tiles the API should return
        * **offset** (*int*) -- The number of tiles to skip
        * **strict** (*bool*) -- True (default) to raise an error if the response JSON contains an error message. False to disable the error and return the response.
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the TNM API

    :Outputs:
        *dict* -- The API response as a JSON dict



.. _pfdf.data.usgs.tnm.dem.ntiles:

.. py:function:: ntiles(bounds = None, resolution = "1/3 arc-second", *, huc = None, timeout = 60)

    Returns the number of DEM tiles matching the search criteria

    .. dropdown:: Count Tiles

        ::

            ntiles(bounds)
            ntiles(bounds, resolution)

        Returns the number of DEM tiles that intersect the indicated bounding box. ``bounds`` should be a BoundingBox-like input with a CRS. If unspecified, returns all tiles in the queried dataset. By default, returns the number of tiles in the 1/3 arc-second DEM dataset. Use ``resolution`` to specify a different DEM dataset instead. Supported resolutions include: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, and 5 meter.

    .. dropdown:: Filter by HUC

        ::

            ntiles(..., *, huc)

        Returns the number of DEM tiles that intersect the indicated hydrologic unit code. The ``huc`` should be a 2, 4, or 8-digit hydrologic unit code as a string. If you provide both ``bounds`` and ``huc``, returns the total number of DEM tiles that intersect both the bounding box and the HUC.

    .. dropdown:: Connection Timeout

        ::

            ntiles(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **bounds** (*BoundingBox-like*) -- A bounding box in which to search for DEM tiles
        * **resolution** (*str*) -- The DEM dataset to search. Defaults to 1/3 arc-second
        * **huc** (*str*) -- A hydrologic unit code in which to search for DEM tiles
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the TNM server

    :Outputs:
        *int* -- The total number of DEM tiles in the search results


.. _pfdf.data.usgs.tnm.dem.tiles:

.. py:function:: tiles(bounds = None, resolution = "1/3 arc-second", *, huc = None, max_queries = 1, max_tiles = None, max_per_query = 500, offset = 0, timeout = 60)

    Returns info on the queried DEM tiles

    .. dropdown:: Query Tile Info

        ::

            tiles(bounds)
            tiles(bounds, resolution)

        Returns info on DEM tiles that intersect the provided bounding box. The ``bounds`` should be a BoundingBox-like input with a CRS. If no bounding box is provided, returns info on all DEM tiles in the dataset. By default, queries the 1/3 arc-second dataset, but use ``resolution`` to specify a different dataset. Supported resolutions include: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, and 5 meter.

        Returns a list with one element per queried DEM tile. Each element is a dict with the following keys:

        * title (str): The tile title
        * publication_date (datetime): The date the tile was published
        * download_url (str): A URL providing read/download access to the dataset
        * sciencebase_id (str): The ScienceBase catalog item ID associated with the tile
        * sciencebase_url (str): The URL of the ScienceBase landing page for the tile
        * filename (str): The name of the tile file
        * format (str): The format of the tile file (typically GeoTiff)
        * nbytes (int): The total size of the tile file in bytes
        * bounds (BoundingBox): An EPSG:4326 BoundingBox for the tile's extent
        * extent (str): Short description of the tile's extent

        By default, this command limits itself to a single API query with a maximum of 500 search results, so will raise an error if the search results contain more than 500 tiles. See the ``max_queries`` and ``max_per_query`` options below to raise these limits.

    .. dropdown:: Filter by HUC

        ::

            tiles(..., *, huc)

        Returns info on tiles that intersect the given hydrologic unit. The ``huc`` should be a 2, 4, or 8-digit hydrologic unit code as a string. If you provide both ``bounds`` and ``huc``, returns info on tiles that intersect both the bounding box and the HUC.

    .. dropdown:: Limit Queries

        ::

            tiles(..., *, max_per_query)
            tiles(..., *, max_queries)

        Options to increase the number of returned tiles. Use ``max_per_query`` to specify the maximum number of products that the API can return per query. This is essentially the "max" paging parameter, but will automatically adjust to account for any paging parameter constraints. This value cannot exceed 1000. Note that the ScienceBase API (which is used by TNM's API) can sometimes time out for larger values of max_per_query. If you are receiving frequent HTTP 503 "Bad Gateway" errors, try reducing max_per_query to a smaller value.

        Use ``max_queries`` to specify the maximum number of API queries allowed to retrieve tile info. In general, retrieving N tiles will require ``ceil(N / max_per_query)`` API queries. Increasing this option can allow the command to retrieve info on more than 1000 tiles. You can also set max_queries=None to allow any number of API queries (and thereby retrieve any number of tiles). However, we strongly recommend checking the total number of tiles (using the ``ntiles`` function) before setting max_queries to None. This is because the maximum number of API queries will become unbounded, and making too many queries in a short period of time could result in rate limiting.

    .. dropdown:: Select Tiles

        ::

            tiles(..., *, max_tiles)
            tiles(..., *, offset)

        Specify how many tiles, and which tiles, should be retrieved. Use ``max_tiles`` to specify the maximum number of search results whose info should be retrieved. Once this value is reached, all remaining search results are skipped. This input is essentially a more generalized "max" paging parameter. Unlike the paging parameter, ``max_tiles`` does not need to be a multiple of 5, and may also retrieve more than 1000 products (across multiple API queries). By default, max_tiles is set to None, which allows the command to retrieve info on any number of tiles.

        By default, this command begins retrieving tile info at the first search result. Use ``offset`` to skip the first N tile before beginning to retrieve product info. You can combine offset with max_tiles to implement custom paging schemes. The offset must be less than the total number of tiles.

    .. dropdown:: Connection Timeout

        ::

            tiles(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **bounds** (*BoundingBox-like*) -- A bounding box in which to search for DEM tiles
        * **resolution** (*str*) -- The DEM dataset to search. Defaults to 1/3 arc-second
        * **huc** (*str*) -- A hydrologic unit code in which to search for DEM tiles
        * **max_per_query** (*int*) -- The maximum number of tiles that should be retrieved per API query
        * **max_queries** (*int*) -- The maximum allowed number of API queries
        * **max_tiles** (*int*) -- The maximum number of tiles whose info should be retrieved
        * **offset** (*int*) -- The number of tiles to skip before retrieving product infos
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the TNM server

    :Outputs:
        *list[dict]* -- The info for each tile in the search results. Each element is a dict with the following keys:

        * title (*str*): The tile title
        * publication_date (*datetime*): The date the tile was published
        * download_url (*str*): A URL providing read/download access to the dataset
        * sciencebase_id (*str*): The ScienceBase catalog item ID associated with the tile
        * sciencebase_url (*str*): The URL of the ScienceBase landing page for the tile
        * filename (*str*): The name of the tile file
        * format (*str*): The format of the tile file (typically GeoTiff)
        * nbytes (*int*): The total size of the tile file in bytes
        * bounds (*BoundingBox*): An EPSG:4326 BoundingBox for the tile's extent
        * extent (*str*): Short description of the tile's extent
