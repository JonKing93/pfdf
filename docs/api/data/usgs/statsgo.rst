data.usgs.statsgo module
========================

.. _pfdf.data.usgs.statsgo:

.. py:module:: pfdf.data.usgs.statsgo

Functions to load data from the STATSGO archive. Specifically, these functions load data from the `STATSGO COG collection <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_, which reformatted select data fields from the `source  STATSGO archive <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_ as cloud-optimized GeoTiff (COG) rasters. Currently, the supported data fields include: KFFACT, and THICK.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * -
      -
    * - **Load Data**
      -
    * - :ref:`read <pfdf.data.usgs.statsgo.read>`
      - Loads data from a STATSGO field as a Raster object
    * - :ref:`download <pfdf.data.usgs.statsgo.download>`
      - Downloads the COG data file for a STATSGO field
    * -
      -
    * - **Item Info**
      - 
    * - :ref:`fields <pfdf.data.usgs.statsgo.fields>`
      - Returns a `pandas.DataFrame`_ with information on the supported fields
    * - :ref:`url <pfdf.data.usgs.statsgo.url>`
      - Returns the ScienceBase URLs for items in the STATSGO COG collection
    * - :ref:`query <pfdf.data.usgs.statsgo.query>`
      - Returns ScienceBase metadata on a STATSGO item as a JSON dict

.. py:currentmodule:: pfdf.data.usgs.statsgo

.. _pandas.DataFrame:

----

Load Data
---------

.. _pfdf.data.usgs.statsgo.read:

.. py:function:: read(field, bounds, *, timeout = 60)

    Reads data from a STATSGO field into memory as a Raster object

    .. dropdown:: Read Data

        ::

            read(field, bounds)

        Reads data from the indicated STATSGO field within the provided bounding box. Supported fields include: KFFACT and THICK. Note that the ``bounds`` input should be a BoundingBox-like object with a CRS. Returns the loaded dataset as a Raster object.

    .. dropdown:: Connection Timeout

        ::

            read(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the ScienceBase data server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **field** (*str*) -- The name of the STATSGO data field from which to load data
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the ScienceBase server

    :Outputs:
        *Raster* -- The data loaded from the STATSGO archive



.. _pfdf.data.usgs.statsgo.download:

.. py:function:: download(field, *, parent = None, name = None, overwrite = False, timeout = 60)

    Downloads the cloud-optimized GeoTiff for a STATSGO field

    .. dropdown:: Download Data

        ::

            download(field)
            
        Downloads the cloud-optimized GeoTiff (COG) for the indicated STATSGO field. Supported fields include: KFFACT, and THICK.

        The dataset in the downloaded file spans the Continental US at a nominal 30 meter resolution. A downloaded file will require 336MB of disk space. Note that the COG format uses compression internally to reduce file size, so reading the full dataset into memory will require ~60GB of RAM - significantly more memory than the size of the downloaded file.

        Returns the path to the downloaded file as output. By default, downloads a file named ``STATSGO-<field>.tif`` to the current folder. Raises an error if the file exists. (And refer to the following syntax for additional file path options).

    .. dropdown:: File Path

        ::

            download(..., *, parent)
            download(..., *, name)
            download(..., *, overwrite=True)

        Options for downloading the file. Use the ``parent`` input to specify the the path to the parent folder where the file should be saved. If a relative path, then parent is interpreted relative to the current folder. Use ``name`` to set the name of the downloaded file. By default, raises an error if the path for the downloaded file already exists. Set overwrite=True to allow the download to overwrite an existing file.

    .. dropdown:: Connection Timeout

        ::

            download(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the ScienceBase data server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **field** (*str*) -- The name of the STATSGO data field to download
        * **parent** (*Path-like*) -- The path to the parent folder where the file should be saved. Defaults to the current folder.
        * **name** (*str*) -- The name for the downloaded file. Defaults to STATSGO-<field>.tif
        * **overwrite** (*bool*) -- True to allow the downloaded file to replace an existing file. False (default) to not allow overwriting
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the ScienceBase server

    :Outputs:
        *Path* -- The Path to the downloaded COG file

----

Item Info
---------

.. _pfdf.data.usgs.statsgo.fields:

.. py:function:: fields() -> DataFrame:

    Returns a `pandas.DataFrame`_ describing the supported STATSGO fields

    ::

        fields()

    Returns a `pandas.DataFrame`_ describing the STATSGO fields supported by this module. The index entries are the names of supported fields. Each row provides the description, units, and URL to the ScienceBase catalog item for the field.

    :Outputs:
        *pandas.DataFrame* -- Documents the supported STATSGO fields

        * index (*str*) -- The name of each field
        * Description (*str*) -- A description of each field
        * Units (*str*) -- Reports the units of each field
        * URL (*str*) -- The URL to the ScienceBase item for each field



.. _pfdf.data.usgs.statsgo.url:

.. py:function:: url(field = None)

    Returns the URLs to ScienceBase items for the STATSGO dataset

    .. dropdown:: Collection URL

        ::

            url()

        Returns the URL to the ScienceBase STATSGO collection item. This item is the parent of the individual STATSGO data field rasters, and it links to the ScienceBase items for the supported STATSGO data fields.

    .. dropdown:: Field URL

        ::

            url(field)

        Returns the URL to the ScienceBase item for the queried STATSGO field. Supported field include: KFFACT, and THICK.

    :Inputs:
        * **field** (*str*) -- A STATSGO field whose ScienceBase item URL should be returned

    :Outputs:
        *str* -- The URL to a ScienceBase item in the STATSGO archive



.. _pfdf.data.usgs.statsgo.query:

.. py:function:: query(field = None, *, timeout = 60)

    Queries the ScienceBase API for a STATSGO item and returns the response as a JSON dict

    .. dropdown:: Query Collection

        ::

            query()

        Uses the ScienceBase API to query the parent item for the STATSGO collection. This item links to the items for the supported STATSGO data fields. Returns the query response as a JSON dict.

    .. dropdown:: Query Field

        ::

            query(field)

        Uses the ScienceBase API to query the catalog item for the indicated STATSGO data field. Supported fields include: KFFACT and THICK.

    .. dropdown:: Connection Timeout

        ::

            query(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the ScienceBase data server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **field** (*str*) -- The name of a STATSGO data field to query
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the ScienceBase server

    :Outputs:
        *dict* -- ScienceBase item info as a JSON dict

    