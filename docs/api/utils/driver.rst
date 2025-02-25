utils.driver module
===================

.. _pfdf.utils.driver:

.. py:module:: pfdf.driver

    Utilities for working with file format drivers.

    .. list-table::
        :header-rows: 1

        * - Function
          - Description
        * -
          -
        * - **Driver Info**
          -
        * - :ref:`vectors <pfdf.utils.driver.vectors>`
          - Returns a pandas data frame summarizing available vector drivers
        * - :ref:`rasters <pfdf.utils.driver.rasters>`
          - Returns a pandas data frame summarizing available raster drivers
        * - :ref:`info <pfdf.utils.driver.info>`
          - Returns a summary of the queried driver
        * -
          -
        * - **File Extensions**
          -
        * - :ref:`extensions <pfdf.utils.driver.extensions>`
          - Returns a pandas data frame with the drivers inferred from various extensions
        * - :ref:`from_path <pfdf.utils.driver.from_path>`
          - Summarize the driver inferred from a specified file path
        * - :ref:`from_extension <pfdf.utils.driver.from_extension>`
          - Summarize the driver inferred from an input file extension


    The driver module contains functions with information about the file-format drivers used to read and save raster and vector-feature files. The pfdf package uses rasterio andd fiona to write raster and vector files, respectively. These libraries support a variety of file formats, which can be selected using an optional "driver" input. Users can return a summary of the available drivers using the :ref:`vectors <pfdf.utils.driver.vectors>` and :ref:`rasters <pfdf.utils.driver.rasters>` functions. Note that these summaries are for drivers expected to work by default - that is, they do not require the installation of external libraries.

    When a driver is not provided, pfdf will attempt to determine the appropriate file format using the file extension. Use the :ref:`extensions <pfdf.utils.driver.extensions>` command for a summary of the drivers inferred from various extensions. Alternatively, use the :ref:`from_path <pfdf.utils.driver.from_path>` or :ref:`from_extension <pfdf.utils.driver.from_extension>` command to return a summary of the driver inferred from a specific file path or extension.

----

Driver Info
-----------

.. _pfdf.utils.driver.rasters:

.. py:function:: rasters()
    :module: pfdf.utils.driver

    Returns a pandas.DataFrame summarizing available raster drivers

    ::

        rasters()

    Returns a ``pandas.DataFrame`` summarizing the raster drivers expected to work in all cases. Essentially, these are the raster drivers that do not require installing any additional libraries. The summary includes a description and the associated file extensions for each raster driver.

    :Outputs: *pandas.DataFrame* -- A summary of raster drivers. Columns are as follows:

            * index (*str*): The name of each driver
            * Description (*str*): A description of each driver
            * Extensions (*str*): The file extensions associated with each driver


.. _pfdf.utils.driver.vectors:

.. py:function:: vectors()
    :module: pfdf.utils.driver

    Returns a pandas.DataFrame summarizing available vector feature drivers

    ::

        vectors()

    
    Returns a ``pandas.DataFrame`` summarizing the vector feature drivers expected to work in all cases. Essentially, these are the vector feature drivers that do not require installing any additional libraries. The summary includes a description and
    the associated file extensions for each vector feature driver.

    :Outputs: *pandas.DataFrame* -- A summary of vector feature drivers. Columns are as follows:

            * index (*str*): The name of each driver
            * Description (*str*): A description of each driver
            * Extensions (*str*): The file extensions associated with each driver


.. _pfdf.utils.driver.info:

.. py:function:: info(driver)
    :module: pfdf.utils.driver

    Returns a pandas data frame summarizing a queried driver

    ::

        info(driver)

    Returns a ``pandas.DataFrame`` summarizing the input driver. The summary includes a description, and list of associated file extensions. Raises a ValueError if the driver name is not recognized.

    :Inputs: * **driver** (*str*) -- The name of a driver

    :Outputs: *pandas.DataFrame* -- The driver summary. Columns are as follows:

            * index (*str*): The name of the driver
            * Description (*str*): A description
            * Extensions (*str*): File extensions associated with the driver


----

File Extensions
---------------

.. _pfdf.utils.driver.extensions:

.. py:function:: extensions(type)
    :module: pfdf.utils.driver

    Summarizes the drivers inferred from recognized file extensions

    ::

        extensions(type='vector')
        extensions(type='raster')

    Returns a ``pandas.DataFrame`` summarizing the drivers inferred from various file extensions for the indicated type of file. These summaries indicate the drivers that are inferred when a driver is not provided as input to a file saving command. Each summary consists of a file extension, driver, and description of the driver.

    :Inputs: * **type** (*"vector" | "raster"*): The type of file

    :Outputs: *pandas.DataFrame* -- A summary of the drivers inferred from various file extensions. Columns are as follows:

            * index (*str*): A file extension
            * Driver (*str*): The driver inferred from the file extension
            * Description (*str*): A description of the driver



.. _pfdf.utils.driver.from_path:

.. py:function:: from_path(path, type = None)
    :module: pfdf.utils.driver.from_path

    Returns information about the driver inferred from a given file path

    .. dropdown:: Parse path

        ::
            
            from_path(path)

        Returns a pandas.DataFrame summarizing the driver inferred from the input file path. Returns None if the file path has an unrecognized extension. Attempts to determine whether the file path is intended for a raster file or vector feature file. Raises a ValueError if the path ends in a ".xml", as this extension is associated with both raster and vector feature drivers, and so requires the "type" input (refer to the next syntax).

    .. dropdown:: Specify file type

        ::

            from_path(path, type='vector')
            from_path(path, type='raster')

        Also specifies whether the file path is intended for a raster or vector feature file. Returns None if the file has an unrecognized extension for the indicated type of file. So most paths with raster extensions will return None when type='vector', and vice versa.

    :Inputs: * **path** (*Path | str*) -- A file path whose driver should be inferred
             * **type** (*"vector" | "raster"*) -- The type of file

    :Outputs: *pandas.DataFrame | None* -- A pandas.DataFrame summarizing the inferred driver, or None if the driver cannot be determined. DataFrame columns are as follows:

            * index (*str*): The name of the driver
            * Description (*str*): A description of the driver
            * Extensions (*str*): The file extensions associated with the driver


.. _pfdf.utils.driver.from_extension:

.. py:function:: from_extension(ext, type = None)
    :module: pfdf.utils.driver

    Returns information about the driver inferred from a given file extension

    .. dropdown:: Parse extension

        ::

            from_extension(ext)

        Returns a ``pandas.DataFrame`` summarizing the driver inferred from the input file extension. Returns None if the extension is unrecognized. Adds a "." to the input extension if the extension does not begin with one. Attempts to determine whether the extension is intended for a raster file or vector feature file. Raises a ValueError if the extension is ".xml", as this extension is associated with both raster and vector feature drivers, and so requires the "type" input (refer to the next syntax).

    .. dropdown:: Specify file type

        ::

            from_extension(ext, type='vector')
            from_extension(ext, type='raster')

        Also specifies whether the extension is intended for a raster or vector feature file. Returns None if the extension is unrecognized for the indicated type of file. So most raster extensions will return None when type='vector', and vice versa.

    :Inputs: * **ext** (*str*) -- A file extension whose driver should be inferred
             * **type** (*"vector" | "raster"*) -- The type of file

    :Outputs: *pandas.DataFrame | None* -- A pandas.DataFrame summarizing the inferred driver or None if the driver cannot be determined. DataFrame columns are:

            * index (*str*): The name of the driver
            * Description (*str*): A description of the driver
            * Extensions (*str*): The file extensions associated with the driver

