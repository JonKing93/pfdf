data.landfire.api module
========================

.. _pfdf.data.landfire.api:

.. py:module:: pfdf.data.landfire.api

Functions supporting low-level interactions with the `LANDFIRE LFPS API <https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer>`_.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - 
      -
    * - **URLs**
      -
    * - :ref:`lfps_url <pfdf.data.landfire.api.lfps_url>`
      - Returns the base URL for the LFPS API
    * - :ref:`job_url <pfdf.data.landfire.api.job_url>`
      - Returns the API URL for a given job
    * -
      -
    * - **Jobs**
      -
    * - :ref:`submit_job <pfdf.data.landfire.api.submit_job>`
      - Submits a job to the LFPS API and returns the job ID
    * - :ref:`query_job <pfdf.data.landfire.api.query_job>`
      - Queries an LFPS job and returns the job info as a JSON dict
    * - :ref:`job_status <pfdf.data.landfire.api.job_status>`
      - Returns the status code for a queried job

----

URLs
----

.. _pfdf.data.landfire.api.lfps_url:

.. py:function:: lfps_url()
    :module: pfdf.data.landfire.api

    Returns the base URL for the LANDFIRE LFPS geoprocessing server

    ::

        lfps_url()

    Returns the base URL for the LFPS. This URL is used for queries that are not job specific, most notably for submitting new job requests.

    :Outputs:
        *str* -- The base URL for the LFPS API


.. _pfdf.data.landfire.api.job_url:

.. py:function:: job_url(id)
    :module: pfdf.data.landfire.api

    Returns the URL for an LFPS job

    ::

        job_url(id)

    Returns the API URL for the job with the specified ID. These URLs are typically used for querying job-specific information.

    :Inputs:
        * **id** (*str*) -- A job ID

    :Outputs:
        *str* -- The URL for the indicated job

----

Jobs
----

.. _pfdf.data.landfire.api.submit_job:

.. py:function:: submit_job(layers, bounds = None, *, timeout = 10)
    :module: pfdf.data.landfire.api

    Submits a job to the LANDFIRE Product Service (LFPS) and returns the job ID

    .. dropdown:: Submit Job

        ::

            submit_job(layers)

        Submits a job for the indicated LFPS data layers. You can find a list of LFPS layer names here: `LANDFIRE Layers <https://lfps.usgs.gov/helpdocs/productstable.html>`_. The ``layers`` input may be a string, or a sequence of strings. Returns the job ID upon successful job submission.

    .. dropdown:: Bounding Box

        ::

            submit_job(..., bounds)

        Submits a job for data within the given bounding box. The ``bounds`` input may be any BoundingBox-like input, and must have a CRS. The LFPS job will restrict layer data to this bounding box.

    .. dropdown:: Connection Timeout

        ::

            submit_job(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **layers** (*list[str]*) -- The LFPS layer names of datasets included in the job
        * **bounds** (*BoundingBox-like*) -- The bounding box for the job's datasets
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to connect to the LFPS server

    :Outputs:
        *str* -- The job ID for the newly submitted job



.. _pfdf.data.landfire.api.query_job:

.. py:function:: query_job(id, *, timeout = 10, strict = True)
    :module: pfdf.data.landfire.api

    Returns LFPS job info as a JSON dict

    .. dropdown:: Query Job

        ::

            query_job(id)
            query_job(id, *, strict=False)

        Queries the indicated LFPS job, and returns the job's info as a JSON dict. Raises an error if the JSON response includes error messages. Alternatively, set strict=False to also return JSON responses that contain errors. This can be useful for troubleshooting the API.

    .. dropdown:: Connection Timeout

        ::

            query_job(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **id** (*str*) -- The ID of the job that should be queried
        * **strict** (*bool*) -- True (default) to raise an error if the JSON includes error messages. False to return JSON responses that include error messages.
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to connect to the LFPS server

    :Outputs:
        *dict* -- The job's information as a JSON dict



.. _pfdf.data.landfire.api.job_status:

.. py:function:: job_status(id, *, timeout = 10)
    :module: pfdf.data.landfire.api

    Returns the status code for an LFPS job

    .. dropdown:: Query Status

        ::

            job_status(id)

        Returns the status code for the queried job.

    .. dropdown:: Connection Timeout

        ::

            job_status(..., *, timeout)

    Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **id** (*str*) -- The ID of the job whose status should be queried
        * **timeout** (*scalar | vector*) -- The maximum number of seconds to connect to the LFPS server

    :Outputs:
        *str* -- The status of the queried job

