data.usgs.tnm.api module
========================

.. _pfdf.data.usgs.tnm.api:

.. py:module:: pfdf.data.usgs.tnm.api

Functions supporting low-level TNM API calls.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - :ref:`api_url <pfdf.data.usgs.tnm.api.api_url>`
      - Returns the URL for the TNM API
    * - :ref:`query <pfdf.data.usgs.tnm.api.query>`
      - Submits a single query to the TNM API and returns the response JSON
    * - :ref:`nproducts <pfdf.data.usgs.tnm.api.nproducts>`
      - Returns the total number of TNM products in a query
    * - :ref:`products <pfdf.data.usgs.tnm.api.products>`
      - Returns info on queried products as a list of JSON dicts

.. py:currentmodule:: pfdf.data.usgs.tnm.api

----

.. _pfdf.data.usgs.tnm.api.api_url:

.. py:function:: api_url()

    Returns the URL for the TNM API

    ::

        api_url()

    :Outputs:
        *str* -- The URL for the TNM API



.. _pfdf.data.usgs.tnm.api.query:

.. py:function:: query(datasets, *, bounds = None, huc = None, formats = None, max = None, offset = None, timeout = 60, strict = True)

    Queries TNM and returns the response as a JSON dict

    .. dropdown:: Query API

        ::

            query(datasets)

        Makes a single query to the TNM API and returns the response as a JSON dict. By default, raises an error if the response contains error messages, but see below to disable this behavior. The ``datasets`` should be a string or list of strings.

    .. dropdown:: Spatial Filters

        ::

            query(..., *, bounds)
            query(..., *, huc)

        Optionally queries datasets within the indicated bounding box and/or hydrologic unit. The ``bounds`` input should be a BoundingBox-like input with a CRS. The ``huc`` input should be 2, 4, or 8-digit hydrologic unit code as a string (not an int). When using these parameters, the query will only return products that intersect these features. If you provide both bounds and huc, then only products that intersect both features will be returned.

    .. dropdown:: File Formats

        ::

            query(..., *, formats)

        Only queries datasets that match the specified file formats.

    .. dropdown:: Paging Parameters

        ::

            query(..., *, max)
            query(..., *, offset)

        Specifies paging parameters for the query. The ``max`` is the maximum number of products that can be returned in the query - this value cannot exceed 1000. The ``offset`` is the number of products that should be skipped before the first product is read. Note that these parameters will generate an error if offset is greater than 100 and max is not a multiple of 5.

    .. dropdown:: Allow Errors

        ::

            query(..., *, strict=False)

        Does not raise an error if the response contains error messages, and instead returns the response. This option may be useful for troubleshooting unexpected API errors.

    .. dropdown:: Connection Timeout

        ::

            query(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **datasets** (*str | list[str]*) -- A string or list of strings indicating the datasets that should queried
        * **bounds** (*BoundingBox-like*) -- A bounding box in which products should be queried
        * **huc** (*str*) -- A hydrologic unit code in which products should be queried
        * **formats** (*str | list[str]*) -- The file formats that should be queried
        * **max** (*int*) -- The maximum number of products that should be returned by the query
        * **offset** (*int*) -- The number of products to skip before returning product info
        * **strict** (*bool*) -- True (default) to raise an error if the response JSON contains error messages. False to not raise an error and return the JSON dict.
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the TNM server

    :Outputs:
        *dict* -- TNM product info as a JSON dict




.. _pfdf.data.usgs.tnm.api.nproducts:

.. py:function:: nproducts(datasets, *, bounds = None, huc = None, formats = None, timeout = 60)

    Returns the total number of TNM products that match the search criteria

    .. dropdown:: Count Products

        ::

            nproducts(datasets)

        Returns the total number of products in the indicated datasets. This can be much larger than the ``max`` paging parameter, which is capped at 1000. This function is mostly intended to help developers determine how many API queries will be required to retrieve all the products matching the search criteria. Note that ``datasets`` should be a string or list of strings indicating fully qualified TNM dataset names.

    .. dropdown:: Spatial Filters

        ::

            nproducts(..., *, bounds)
            nproducts(..., *, huc)

        Returns the total number of products that intersect the indicated bounding box or HUC. These inputs are optional. The ``bounds`` should be a BoundingBox-like input with a CRS. The ``huc`` should be 2, 4, or 8-digit hydrologic unit code as a string (not an int). If you provide both bounds and huc, then returns the total number of products that intersect both the bounds and the huc.

    .. dropdown:: File Formats

        ::

            nproducts(..., *, formats)

        Returns the total number of search result products that match the indicated file formats. The ``formats`` may be a string, or a list of strings. If using a list, the returned number will be the number of products that match at least 1 of the indicated formats.

    .. dropdown:: Connection Timeout

        ::

            nproducts(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **datasets** (*str | list[str]*) -- The fully qualified names of TNM datasets that should be queried
        * **bounds** (*BoundingBox-like*) -- A bounding box in which to search for products
        * **huc** (*str*) -- A hydrologic unit code in which to search for products
        * **formats** (*str | list[str]*) -- The file formats to search for
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the TNM API

    :Outputs:
        *int* -- The total number of TNM products that match the search results



.. _pfdf.data.usgs.tnm.api.products:

.. py:function:: products(datasets, *, bounds = None, huc = None, formats = None, max_queries = 1, max_products = None, max_per_query = 500, offset = 0, timeout = 60)

    Returns info on TNM products meeting the search criteria

    .. dropdown:: Query Product Info

        ::

            products(datasets)

        Returns info on all products in the queried datasets. Returns a list with one element per product. Each element is a JSON dict with the product's information.

        By default, this command limits itself to a single API query with a maximum of 500 search results, so will raise an error if the search results contain more than 500 products. See the ``max_queries`` and ``max_per_query`` options below to raise these limits.

    .. dropdown:: Spatial Filters

        ::

            products(..., *, bounds)
            products(..., *, huc)

        Restricts the search results to products intersecting a provided bounding box and/or hydrologic unit code. Both inputs are optional, but can help limit API queries for bounded domains. The ``bounds`` should be a BoundingBox-like input with a CRS, and ``huc`` should be a 2, 4, or 8-digit hydrologic unit code as a string (not an int). If you provide both bounds and huc, then the search is limited to products that intersect both the bounds and the huc.

    .. dropdown:: File Format

        ::

            products(..., *, formats)

        Restricts search results to products in one of the requested file formats. The ``formats`` may be a string or list of strings. If using a list of strings, then the search results will include all products that match at least one of the indicated file formats.

    .. dropdown:: Paging Parameters

        ::

            products(..., *, max_per_query)
            products(..., *, max_queries)

        Options to increase the number of returned products. Use ``max_per_query`` to specify the maximum number of products that the API can return per query. This is essentially the "max" paging parameter, but will automatically adjust to account for any paging parameter constraints. This value cannot exceed 1000. Note that the ScienceBase API (which is used by TNM's API) can sometimes time out for larger values of max_per_query. If you are receiving frequent HTTP 503 "Bad Gateway" errors, try reducing max_per_query to a smaller value.

        Use ``max_queries`` to specify the maximum number of API queries allowed to retrieve product info. In general, retrieving N products will require ``ceil(N / max_per_query)`` API queries. Increasing this option can allow the command to retrieve info on more than 1000 products. You can also set max_queries=None to allow any number of API queries (and thereby retrieve any number of products). However, we strongly recommend checking the total number of products (using the ``nproducts`` function) before setting max_queries to None. This is because the maximum number of API queries will become unbounded, and making too many queries in a short period of time could result in rate limiting.

    .. dropdown:: Select Products

        ::

            products(..., *, max_products)
            products(..., *, offset)

        Specify how many products, and which products, should be retrieved. Use ``max_products`` to specify the maximum number of search results whose info should be retrieved. Once this value is reached, all remaining search results are skipped. This input is essentially a more generalized "max" paging parameter. Unlike the paging parameter, ``max_products`` does not need to be a multiple of 5, and may also retrieve more than 1000 products (across multiple API queries). By default, max_products is set to None, which allows the command to retrieve info on any number of products.

        By default, this command begins retrieving product info at the first search result. Use ``offset`` to skip the first N products before beginning to retrieve product info. You can combine offset with max_products to implement custom paging schemes. The offset must be less than the total number of products.

    .. dropdown:: Connection Timeout

        ::

            products(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **datasets** (*str | list[str]*) -- The fully qualified names of TNM datasets that should be searched
        * **bounds** (*BoundingBox-like*) -- A bounding box in which to search for products
        * **huc** (*str*) -- A hydrologic unit code in which to search for products
        * **formats** (*str | list[str]*) -- The file formats to search for
        * **max_per_query** (*int*) -- The maximum number of products that should be retrieved per API query
        * **max_queries** (*int*) -- The maximum allowed number of API queries
        * **max_products** (*int*) -- The maximum number of products whose info should be retrieved
        * **offset** (*int*) -- The number of products to skip before retrieving product infos
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the TNM server

    :Outputs:
        *list[dict]* -- Information on the queried products. The list will contain one element per retrieved product. Each element is a JSON dict of the product's info
