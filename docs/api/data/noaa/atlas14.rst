data.noaa.atlas14 module
========================

.. _pfdf.data.noaa.atlas14:

.. py:module:: pfdf.data.noaa.atlas14

Functions that access precipitation frequency estimates (PFEs) from
`NOAA Atlas 14`_.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - :ref:`download <pfdf.data.noaa.atlas14.download>`
      - Downloads a .csv file or precipitation frequency estimates to the local filesystem.
    * - :ref:`base_url <pfdf.data.noaa.atlas14.base_url>`
      - Returns the base URL for the NOAA Atlas 14 data API
    * - :ref:`query_url <pfdf.data.noaa.atlas14.query_url>`
      - Returns the URL used to query NOAA Atlas 14 for a specific PFE statistic

.. _NOAA Atlas 14: https://hdsc.nws.noaa.gov/pfds/

----

.. _pfdf.data.noaa.atlas14.download:

.. py:function:: download(lat, lon, *, parent = None, name = None, overwrite = False, statistic = "mean", data = "intensity", series = "pds", units = "metric", timeout = 10)
    :module: pfdf.data.noaa.atlas14

    Downloads a .csv file with precipitation frequency estimates for a given point

    .. dropdown:: Download PFEs

        ::

            download(lat, lon)
            
        Downloads a .csv file with precipitation frequency estimates for the given point. The ``lat`` and ``lon`` coordinates should be provided in decimal degrees, and ``lon`` should be on the interval [-180, 180]. By default, downloads mean PFEs of precipitation intensity for partial duration time series. Refer below for alternative options.

        Returns the path to the downloaded csv file as output. By default, this command will download the dataset to the current folder, and the data file will be named ``noaa-atlas14-mean-pds-intensity.csv``. Raises an error if the file already exists. (And refer to the following syntax for additional file options).

    .. dropdown:: File Path

        ::

            download(..., *, parent)
            download(..., *, name)
            download(..., *, overwrite=True)

        Options for downloading the file. Use the ``parent`` input to specify the the path to the parent folder where the file should be saved. If a relative path, then parent is interpreted relative to the current folder. Use ``name`` to set the name of the downloaded file. By default, raises an error if the path for the downloaded file already exists. Set overwrite=True to allow the download to overwrite an existing file.

    .. dropdown:: Data Options

        ::

            download(..., *, statistic)
            download(..., *, data)
            download(..., *, series)
            download(..., *, units)

        Specify the type of data that should be downloaded. Supported values are as follows:

        **statistic**

        * mean: Mean PFEs (default)
        * upper: Upper bound of the 90% confidence interval
        * lower: Lower bound of the 90% confidence interval
        * all: Mean, upper, and lower

        **data**

        * intensity: Values are precipitation intensities (default)
        * depth: Values are precipitation depths

        **series**

        * pds: Returns PFEs estimated from partial duration time series (default)
        * ams: Returns PFEs estimated from annual maximum time series

        **units**

        * metric: PFEs returned in mm or mm/hour (default)
        * english: PFEs returned in inches or inches/hour

        .. note::

            If you do not specify a path for the downloaded file, then the downloaded file will follow the naming scheme: ``noaa-atlas14-<statistic>-<series>-<data>-<units>.csv``

    .. dropdown:: HTTP Connection

        ::

            download(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the NOAA Atlas 14 data server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **lat** (*scalar*) -- The latitude of the query point in decimal degrees
        * **lon** (*scalar*) -- The longitude of the query point in decimal degrees on the interval [-180, 180]
        * **parent** (*Pathlike*) -- The path to the parent folder where the file should be saved. Defaults to the current folder.
        * **name** (*str*) -- The name for the downloaded file. Defaults to ``noaa-atlas14-<statistic>-<series>-<data>-<units>.csv``
        * **overwrite** (*bool*) -- True to allow the downloaded file to replace an existing file. False (default) to not allow overwriting
        * **statistic** (*"mean" | "upper" | "lower" | "all"*) -- The type of PFE statistic to download. Options are "mean", "upper", "lower", and "all"
        * **data** (*"intensity" | "depth"*) -- The type of PFE values to download. Options are "intensity" and "depth"
        * **series** (*"pds" | "ams"*) -- The type of time series to derive PFE values from. Options are "pds" (partial duration), and "ams" (annual maximum).
        * **units** (*"metric" | "english"*) -- The units that PFE values should use. Options are "metric" and "english"
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect with the data server

    :Outputs:
        *Path* -- The Path to the downloaded data file


.. _pfdf.data.noaa.atlas14.base_url:

.. py:function:: base_url()
    :module: pfdf.data.noaa.atlas14

    Returns the base URL for the NOAA Atlas 14 data API

    ::

        base_url()

    Returns the base URL for the NOAA Atlas 14 data API.

    :Outputs:
        *str* -- The base URL for the NOAA Atlas 14 data API


.. _pfdf.data.noaa.atlas14.query_url:

.. py:function:: query_url(statistic = "mean")
    :module: pfdf.data.noaa.atlas14

    Returns the URL used to query a NOAA Atlas 14 PFE statistic

    ::

        query_url(statistic)

    Returns the URL used to query a NOAA Atlas 14 PFE statistic. Supported statistics include:

    .. list-table::
        :header-rows: 1

        * - Statistic
          - Description
        * - mean
          - Mean PFE (default)
        * - upper
          - Upper bound of the 90% confidence interval
        * - lower
          - Lower bound of the 90% confidence interval
        * - all
          - Mean, upper and lower PFE
