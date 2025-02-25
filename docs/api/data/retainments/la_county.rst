data.retainments.la_county module
=================================

.. _pfdf.data.retainments.la_county:

.. py:module:: pfdf.data.retainments.la_county

Functions to load debris retainment feature locations for Los Angeles County, California, USA.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - :ref:`download <pfdf.data.retainments.la_county.download>`
      - Downloads a geodatabase of debris retainment Point features to the local filesystem
    * - :ref:`data_url <pfdf.data.retainments.la_county.data_url>`
      - Returns the download URL for the retainment dataset

----

.. _pfdf.data.retainments.la_county.download:

.. py:function:: download(*, parent = None, name = None, timeout = 15)
    :module: pfdf.data.retainments.la_county

    Downloads a geodatabase of debris retainment locations for Los Angeles County, CA

    .. dropdown:: Download Retainments

        ::

            download()

        Downloads a geodatabase (gdb) holding the Point locations of debris retainment features in Los Angeles county. Returns the path to the downloaded dataset. By default, the dataset will be named ``la-county-retainments.gdb`` and will be located in the current folder. The dataset is intended for use with commands like :ref:`Raster.from_points <pfdf.raster.Raster.from_points>`, which supports reading data from geodatabases and does not require an ESRI license. Raises an error if the geodatabase already exists on the file system.

    .. dropdown:: File Path

        ::

            download(..., *, parent)
            download(..., *, name)

        Options for downloading the geodatabase. The ``parent`` option is the path to the parent folder where the geodatabase should be downloaded. If a relative path, then ``parent`` is interpreted relative to the current folder. Use ``name`` to set the name of the downloaded geodatabase. Rases an error if the path to the geodatabase already exists.

    .. dropdown:: HTTP Connection

        ::

            download(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LA County data server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case server queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **parent** (*Path-like*) -- The path to the parent folder where the geodatabase should be downloaded. Defaults to the current folder.
        * **name** (*str*) -- The name for the downloaded geodatabase. Defaults to ``la-county-retainments.gdb``
        * **timeout** (*scalar | vector*) -- A maximum number of seconds to connect with the LA County data server

    :Outputs:
        *Path* -- The path to the downloaded geodatabase


.. _pfdf.data.retainments.la_county.data_url:

.. py:function:: data_url()
    :module: pfdf.data.retainments.la_county

    Returns the URL for the debris basin download

    ::

        data_url()

    Returns the URL for the debris retainment dataset. This dataset does not use an API, so the URL provides direct access to the dataset as a zip archive.

    :Outputs:
        *str* -- The URL for the downloadable dataset