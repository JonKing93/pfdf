data.usgs.tnm.nhd module
========================

.. _pfdf.data.usgs.tnm.nhd:

.. py:module:: pfdf.data.usgs.tnm.nhd

Functions to load hydrologic unit (HU) datasets from the USGS National Hydrologic Dataset (NHD).

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - :ref:`download <pfdf.data.usgs.tnm.nhd.download>`
      - Downloads the data bundle for a HUC4 or HUC8 unit to the local filesystem
    * - :ref:`dataset <pfdf.data.usgs.tnm.nhd.dataset>`
      - Returns the fully-qualified TNM name for the NHD dataset
    * - :ref:`product <pfdf.data.usgs.tnm.nhd.product>`
      - Returns TNM product info for a HUC4 or HUC8

----

.. _pfdf.data.usgs.tnm.nhd.download:

.. py:function:: download(huc, *, parent = None, name = None, format="Shapefile", timeout = 60)

    Downloads an HU4 or HU8 data bundle

    .. dropdown:: Download Data

        ::

            download(huc)

        Downloads the data bundle for a HU4 or HU8 code to the local filesystem. Raises an error if a matching HUC cannot be found. By default, downloads a Shapefile data bundle into a folder named ``huc4-<code>`` or ``huc8-<code>`` in the current directory, but see below for other path options. Note that ``huc`` should be a string representing a HUC, rather than an int. This is to preserve leading zeros in the HUC. Returns the path to the downloaded data folder as output.

    .. dropdown:: File Path

        ::

            download(..., *, parent)
            download(..., *, name)

        Options for downloading the the data bundle. The ``parent`` option is the path to the parent folder where the data bundle should be downloaded. If a relative path, then parent is interpreted relative to the current folder. Use ``name`` to set the name of the downloaded data bundle. Rases an error if the path to the data bundle already exists.

    .. dropdown:: File Format

        ::

            download(..., *, format)

        Downloads a data bundle in the indicated file format. Supported options include: "Shapefile" (default)", "GeoPackage", and "FileGDB". Note that pfdf routines support all three format t an ESRI license.

    .. dropdown:: Connection Timeout

        ::

            download(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **huc** (*str*) -- A string of the HU4 or HU8 code whose data bundle should be downloaded
        * **parent** (*Path-like*) -- The path to the parent folder where the data bundle should be downloaded. Defaults to the current folder.
        * **name** (*str*) -- The name for the downloaded data bundle. Defaults to huc4-<code> or huc8-<code>, as appropriate
        * **format** (*str*) -- The file format that should be download. Options are "Shapefile", "GeoPackage", and "FileGDB"
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the TNM server

    :Outputs:
        *Path* -- The path to the downloaded data bundle



.. _pfdf.data.usgs.tnm.nhd.dataset:

.. py:function:: dataset()

    Returns the fully qualified TNM name for the NHD dataset

    ::

        dataset()

    :Outputs:
        *str* -- The fully qualified TNM name for the NHD dataset
        



.. _pfdf.data.usgs.tnm.nhd.product:

.. py:function:: product(huc, *, format="Shapefile", timeout = 60)

    Returns the product info for the queried HUC

    .. dropdown:: Query Product Info

        ::

            product(huc)
            product(huc, *, format)

        Returns TNM product info for a queried HUC4 or HUC8 as a JSON dict. Raises a
        NoTNMProductsError if there is no hydrologic unit with a matching code. Note that ``huc`` should be a string, rather than an int. This is to preserve leading zeros in hydrologic unit codes. By default, returns info for the HUCs Shapefile product. Use the ``format`` option to return info for a different file format. Supported file formats include "Shapefile", "GeoPackage" and "FileGDB". Note that pfdf supports reading from File Geodatabases without requiring an ESRI license.

    .. dropdown:: Connection Timeout

        ::

            product(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the TNM server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeo This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **huc** (*str*) -- A string representing an HU4 or HU8 code
        * **format** (*str*) -- The file format that should be queried. Options are "Shapefile", "GeoPackage", and "FileGDB"
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the TNM server

    :Outputs:
        *dict* -- The TNM product info for the queried HUC as a JSON dict

