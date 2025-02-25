Raster class
============

.. _pfdf.raster.Raster:

.. py:class:: Raster
    :module: pfdf.raster

    The *Raster* class is used to manage raster datasets and metadata within pfdf. Each *Raster* object represents a particular raster dataset. The object's properties return the raster's data values and metadata, and the class provides :ref:`methods to build Rasters <api-raster-creation>` from a variety of formats. *Raster* objects implement various :ref:`preprocessing methods <api-preprocess>`, which can clean and prepare a dataset for hazard assessment. Any pfdf routine that computes a new raster will return the dataset as a *Raster* object. Use the :ref:`save method <pfdf.raster.Raster.save>` to save these to file.

    .. dropdown:: Properties

        .. list-table::
            :header-rows: 1

            * - Property
              - Description
            * - 
              - 
            * - **Data Values**
              - 
            * - name            
              - An optional name to identify the raster
            * - values          
              - The data values associated with a raster
            * - dtype           
              - The dtype of the raster
            * - nodata
              - The NoData value associated with the raster
            * - nodata_mask
              - The NoData mask for the raster
            * - data_mask       
              - The valid data mask for the raster
            * - 
              - 
            * - **Shape**
              - 
            * - shape           
              - The shape of the raster array
            * - size            
              - The size (number of elements) in the raster array
            * - height          
              - The number of rows in the raster array
            * - width           
              - The number of columns in the raster array
            * - 
              - 
            * - **CRS**
              - 
            * - crs
              - The coordinate reference system associated with the raster
            * - crs_units
              - The units of the CRS X and Y axes
            * - crs_units_per_m
              - The number of CRS units per meter along the X and Y axes
            * - utm_zone 
              - The UTM zone CRS that contains the raster's center point
            * - 
              - 
            * - **Transform**
              - 
            * - transform
              - A *Transform* object for the raster
            * - affine
              - The ``affine.Affine`` object for the raster's transform
            * - 
              - 
            * - **Bounding Box**
              - 
            * - bounds        
              - A *BoundingBox* object for the raster
            * - left          
              - The spatial coordinate of the raster's left edge
            * - bottom        
              - The spatial coordinate of the raster's bottom edge
            * - right         
              - The spatial coordinate of the raster's right edge
            * - top           
              - The spatial coordinate of the raster's top edge
            * - center        
              - The (X, Y) coordinate of the raster's center
            * - center_x      
              - The X coordinate of the center
            * - center_y      
              - The Y coordinate of the center
            * - orientation   
              - The Cartesian quadrant of the bounding box


    .. dropdown:: Methods

        .. list-table::
            :header-rows: 1

            * - Method
              - Description
            * - 
              - 
            * - **Object Creation**
              -
            * - :ref:`__init__ <pfdf.raster.Raster.__init__>`
              - Returns a raster object for a supported raster input
            * - :ref:`from_file <pfdf.raster.Raster.from_file>`    
              - Creates a Raster from a file-based dataset
            * - :ref:`from_url <pfdf.raster.Raster.from_url>`
              - Creates a Raster for a dataset available via web URL
            * - :ref:`from_rasterio <pfdf.raster.Raster.from_rasterio>`
              - Creates a Raster from a rasterio.DatasetReader object
            * - :ref:`from_array <pfdf.raster.Raster.from_array>`  
              - Creates a Raster object from a numpy array
            * - :ref:`from_pysheds <pfdf.raster.Raster.from_pysheds>`
              - Creates a Raster from a pysheds.sview.Raster object
            * - 
              - 
            * - **From Vector Features**
              -
            * - :ref:`from_points <pfdf.raster.Raster.from_points>`
              - Creates a Raster from point / multi-point features
            * - :ref:`from_polygons <pfdf.raster.Raster.from_polygons>`
              - Creates a Raster from polygon / multi-polygon features
            * - 
              - 
            * - **IO**
              -
            * - :ref:`__repr__ <pfdf.raster.Raster.__repr__>`
              - Returns a string summarizing the Raster
            * - :ref:`save <pfdf.raster.Raster.save>`
              - Saves a raster dataset to file
            * - :ref:`copy <pfdf.raster.Raster.copy>`
              - Creates a copy of the current Raster
            * - :ref:`as_pysheds <pfdf.raster.Raster.as_pysheds>`
              - Returns a Raster as a pysheds.sview.Raster object
            * - 
              - 
            * - **Numeric Preprocessing**
              -
            * - :ref:`fill <pfdf.raster.Raster.fill>`
              - Fills a raster's NoData pixels with the indicated data value
            * - :ref:`find <pfdf.raster.Raster.find>`
              - Returns a boolean raster indicating pixels that match specified values
            * - :ref:`set_range <pfdf.raster.Raster.set_range>`
              - Forces a raster's data pixels to fall within the indicated range
            * -
              -
            * - **Spatial Preprocessing**
              -
            * - :ref:`__getitem__ <pfdf.raster.Raster.__getitem__>`
              - Returns a Raster for the indexed portion of a raster's data array
            * - :ref:`buffer <pfdf.raster.Raster.buffer>`
              - Buffers the edges of a raster by specified distances
            * - :ref:`reproject <pfdf.raster.Raster.reproject>`
              - Reprojects a raster to match a specified CRS, resolution, and grid alignment
            * - :ref:`clip <pfdf.raster.Raster.clip>`
              - Clips a raster to the specified bounds
            * - 
              - 
            * - **Pixel Geometries**
              -
            * - :ref:`dx <pfdf.raster.Raster.dx>`      
              - Change in X-axis coordinate when moving one pixel right
            * - :ref:`dy <pfdf.raster.Raster.dy>`        
              - Change in Y-axis coordinate when moving one pixel down
            * - :ref:`resolution <pfdf.raster.Raster.resolution>` 
              - Returns the resolution of the raster pixels
            * - :ref:`pixel_area <pfdf.raster.Raster.pixel_area>`
              - Returns the area of one pixel
            * - :ref:`pixel_diagonal <pfdf.raster.Raster.pixel_diagonal>`
              - Returns the length of a pixel diagonal
            * - 
              - 
            * - **Comparisons**
              -
            * - :ref:`__eq__ <pfdf.raster.Raster.__eq__>`     
              - True if the second object is a Raster with the same values, nodata, transform, and crs
            * - :ref:`validate <pfdf.raster.Raster.validate>`
              - Checks that a second raster has a compatible shape, transform, and crs
            * - 
              - 
            * - **Metadata Setters**
              -
            * - :ref:`ensure_nodata <pfdf.raster.Raster.ensure_nodata>`
              - Sets a NoData value if the Raster does not already have one
            * - :ref:`override <pfdf.raster.Raster.override>`    
              - Overrides metadata fields with new values


----

Properties
----------

Data Values
+++++++++++

.. py:property:: Raster.name
    
    An optional name to identify the raster

.. py:property:: Raster.values

    A read-only copy of the raster's data array. 
    
    .. tip:: Make a copy if you want to change the array values.

.. py:property:: Raster.dtype

    The dtype of the data array

.. py:property:: Raster.nodata

    The NoData value for the raster

.. _pfdf.raster.Raster.nodata_mask:

.. py:property:: Raster.nodata_mask

    The NoData mask for the raster. True elements are NoData pixels. All other pixels are False.

.. _pfdf.raster.Raster.data_mask:

.. py:property:: Raster.data_mask

    The data mask for the raster. True elements are data pixels. All NoData pixels are False.


Shape
+++++

.. py:property:: Raster.shape
    
    The shape of the raster's data array


.. py:property:: Raster.size
    
    The number of elements in the data array


.. py:property:: Raster.height
    
    The number of rows in the data array


.. py:property:: Raster.width
    
    The number of columns in the data array


CRS
+++

.. py:property:: Raster.crs
  
    The coordinate reference system associated with the raster

.. py:property:: Raster.crs_units
  
    The units of the CRS X and Y axes

.. py:property:: Raster.crs_units_per_m
  
    The number of CRS units per meter along the X and Y axes

.. py:property:: Raster.utm_zone
  
    The UTM zone CRS that contains the raster's center point


Transform
+++++++++

.. py:property:: Raster.transform
  
    A :ref:`Transform <pfdf.projection.Transform>` object for the raster

.. py:property:: Raster.affine
  
    An `affine.Affine <https://pypi.org/project/affine/>`_ object for the raster's transform


Bounding Box
++++++++++++

.. py:property:: Raster.bounds
  
    A :ref:`BoundingBox <pfdf.projection.BoundingBox>` object for the raster

.. py:property:: Raster.left
  
    The spatial coordinate of the raster's left edge

.. py:property:: Raster.bottom
  
    The spatial coordinate of the raster's bottom edge

.. py:property:: Raster.right
  
    The spatial coordinate of the raster's right edge

.. py:property:: Raster.top
  
    The spatial coordinate of the raster's top edge

.. py:property:: Raster.center
  
    The (X, Y) coordinate of the raster's center

.. py:property:: Raster.center_x
  
    The X coordinate of the center

.. py:property:: Raster.center_y
  
    The Y coordinate of the center

.. py:property:: Raster.orientation
  
    The Cartesian quadrant of the bounding box



----

.. _api-raster-creation:

Object Creation
---------------

.. _pfdf.raster.Raster.__init__:

.. py:method:: Raster.__init__(self, raster = None, name = None, isbool = False, ensure_nodata = True, default_nodata = None, casting = "safe")

    Creates a new Raster object

    .. dropdown:: Create Raster

        ::

            Raster(raster)

        Returns the input raster as a *Raster* object. Supports a variety of raster datasets including: the path or URL to a file-based raster, numpy arrays, other pfdf.raster.Raster objects, and pysheds.sview.Raster objects. The input raster should refer to a 2D array with a boolean, integer, or floating dtype - raises Exceptions when this is not the case.

        .. note::

            This constructor will attempt to determine the type of input, and initialize a raster using default option for that input type. Alternatively, you can use the various factory methods to create various types of rasters with additional options. For example, the :ref:`from_array <pfdf.raster.Raster.from_array>` method allows you to create a raster from a numpy array while also including spatial metadata and NoData values. Separately, the :ref:`from_file <pfdf.raster.Raster.from_file>` method allows you to specify the band and file-format driver to use when reading a raster from file.

    .. dropdown:: Named Raster

        ::

            Raster(raster, name)

        Optionally specifies a name for the raster. This can be returned using the ``name`` property, and is used to identify the raster in error messages. Defaults to "raster" if unspecified.

    .. dropdown:: Boolean Raster

        ::

            Raster(..., isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the raster must be equal to 0 or 1. NoData pixels in the raster will be converted to False, regardless of their value.

    .. dropdown:: Empty Object

        ::

            Raster()

        Returns an empty raster object. The attributes of the raster are all set to None. This syntax is typically not useful for users, and is instead intended for developers.

    .. dropdown:: Default NoData

        ::

            Raster(..., *, default_nodata)
            Raster(..., *, default_nodata, casting)
            Raster(..., *, ensure_nodata=False)

        Specifies additional options for NoData values. By default, if the raster file does not have a NoData value, then this routine will set a default NoData value based on the dtype of the raster. Set ``ensure_nodata=False`` to disable this behavior. Alternatively, you can use the ``default_nodata`` option to specify a different default NoData value. The default nodata value should be safely castable to the raster dtype, or use the ``casting`` option to specify other casting rules.

    :Inputs:
        * **raster** (*Raster-like*) -- A supported raster dataset
        * **name** (*str*) -- A name for the input raster. Defaults to 'raster'
        * **isbool** (*bool*) -- True indicates that the raster represents a boolean array. False (default) leaves the raster as its original dtype.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.

    :Outputs:
        *Raster* -- The *Raster* object for the dataset


.. _pfdf.raster.Raster.from_file:

.. py:method:: Raster.from_file(path, name = None, *, driver = None, band = 1, isbool = False, bounds = None, ensure_nodata = True, default_nodata = None, casting = "safe")

    Builds a Raster object from a file-based dataset

    .. dropdown:: Load from file

        ::

            Raster.from_file(path)
            Raster.from_file(path, name)

        Builds a *Raster* from the indicated file. Raises a FileNotFoundError if the file cannot be located. Loads file data when building the object By default, loads all data from band 1, but refer below for additional options. The name input can be used to provide an optional name for the raster, defaults to "raster" if unset. By default, if the file does not have a NoData value, then selects a default value based on the dtype. Refer below for other NoData options.

        Also, by default the method will attempt to use the file extension to detect the file format driver used to read data from the file. Raises an Exception if the driver cannot be determined, but refer below for options to explicitly set the driver. You can also use::

            >>> pfdf.utils.driver.extensions('raster')

        to return a summary of supported file format drivers, and their associated extensions.
    
    .. dropdown:: Windowed Reading

        ::

            Raster.from_file(..., *, bounds)

        Only loads data from a bounded subset of the saved dataset. This option is useful when you only need a small portion of a very large raster, and limits the amount of data loaded into memory. You should also use this option whenever a saved raster is larger than your computer's RAM.

        The "bounds" input indicates a rectangular portion of the saved dataset that should be loaded. If the window extends beyond the bounds of the dataset, then the dataset will be windowed to the relevant bound, but no further. The window may be a BoundingBox, Raster, or a list/tuple/dict convertible to a BoundingBox object.

        .. note::
          
            When filling a window, this command will first read the entirety of one or more data chunks from the file. As such, the total memory usage will temporarily exceed the memory needed to hold just the window. If a raster doesn't use chunks (rare, but possible), then the entire raster will be read into memory before filling the window. In practice, it's important to chunk the data you use for applications.

    .. dropdown:: Specify Band

        ::

            Raster.from_file(..., *, band)

        Specify the raster band to read. Raster bands use 1-indexing (and not the 0-indexing common to Python). Raises an error if the band does not exist.

    .. dropdown:: Boolean Raster

        ::

            Raster.from_file(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.

    .. dropdown:: Default NoData

        ::

            Raster.from_file(..., *, default_nodata)
            Raster.from_file(..., *, default_nodata, casting)
            Raster.from_file(..., *, ensure_nodata=False)

        Specifies additional options for NoData values. By default, if the raster file does not have a NoData value, then this routine will set a default NoData value based on the dtype of the raster. Set ``ensure_nodata=False`` to disable this behavior. Alternatively, you can use the "default_nodata" option to specify a different default NoData value. The default nodata value should be safely castable to the raster dtype, or use the "casting" option to specify other casting rules.

    .. dropdown:: Specify File Format

        ::

            Raster.from_file(..., *, driver)

        Specify the file format driver to use for reading the file. Uses this driver regardless of the file extension. You can also call::

            >>> pfdf.utils.driver.rasters()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses GDAL/OGR) to read raster files, and so additional drivers may work if their associated build requirements are met. A complete list of driver build requirements is available here: `Raster Drivers <https://gdal.org/drivers/raster/index.html>`_

    :Inputs:
        * **path** (*Path-like*) -- A path to a file-based raster dataset
        * **name** (*str*) -- An optional name for the raster
        * **band** (*int*) -- The raster band to read. Uses 1-indexing and defaults to 1
        * **driver** (*str*) -- A file format to use to read the raster, regardless of extension
        * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.
        * **bounds** (*Raster | BoundingBox | tuple | dict*) -- A *Raster* or *BoundingBox* indicating a subset of the saved raster that should be loaded.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.

    :Outputs:
        Raster: A Raster object for the file-based dataset


.. _pfdf.raster.Raster.from_url:

.. py:method:: Raster.from_url(url, name = None, *, check_status = True, timeout = 10, bounds = None, band = 1, isbool = False, ensure_nodata = True, default_nodata = None, casting = "safe", driver = None)

    Creates a Raster object for the dataset at the indicated URL

    .. dropdown:: Load from URL

        ::

            Raster.from_url(url)

        Builds a Raster object for the file at the given URL. Ultimately, this method uses rasterio (and thereby GDAL) to open URLs. As such, many common URL schemes are supported, including: http(s), ftp, s3, (g)zip, tar, etc. Note that although the local "file" URL scheme is theoretically supported, we recommend instead using :ref:`Raster.from_file <pfdf.raster.Raster.from_file>` to build metadata from local file paths.

        If a URL follows an http(s) scheme, uses the `requests library <https://requests.readthedocs.io/en/latest/>`_ to check the URL before loading data. This check is optional (refer below to disable), but typically provides more informative error messages when connection problems occur. Note that the check assumes the URL supports HEAD requests, as is the case for most http(s) URLs. All other URL schemes are passed directly to rasterio.

        After loading the URL, this method behaves nearly identically to the :ref:`Raster.from_file <pfdf.raster.Raster.from_file>` command. Please read that command's documentation for details on the following options: name, bounds, band, isbool, ensure_nodata, default_nodata, casting, and driver.

    .. dropdown:: HTTP Connection Options

        ::

            Raster.from_url(..., *, timeout)
            Raster.from_url(..., *, check_status=False)

        Options that affect the checking of http(s) URLs. Ignored if the URL does not have an http(s) scheme. The ``timeout`` option specifies a maximum time in seconds for connecting to the remote server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case the URL check will never timeout. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

        You can disable the http(s) URL check by setting ``check_status=False``. In this case, the URL is passed directly to rasterio, as like all other URL schemes. This can be useful if the URL does not support HEAD requests, or to limit server queries when you are certain the URL and connection are valid.

    :Inputs:
        * **url** (*str*) -- The URL for a file-based raster dataset
        * **name** (*str*) -- An optional name for the metadata. Defaults to "raster"
        * **timeout** (*scalar | vector*) -- A maximum time in seconds to establish a connection with an http(s) server
        * **check_status** (*bool*) -- True (default) to use "requests.head" to validate http(s) URLs. False to disable this check.
        * **bounds** (*BoundingBox-like*) -- A BoundingBox-like input indicating a subset of the raster that should be loaded.
        * **band** (*int*) -- The raster band to read. Uses 1-indexing and defaults to 1
        * **driver** (*str*) -- A file format to use to read the raster, regardless of extension
        * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.

    :Outputs:
        *Raster* -- A Raster object for the dataset at the URL


.. _pfdf.raster.Raster.from_rasterio:

.. py:method:: Raster.from_rasterio(reader, name = None, *, band = 1, isbool = False, bounds = None, ensure_nodata = True, default_nodata = None, casting = "safe")

    Builds a raster from a rasterio.DatasetReader

    .. dropdown:: Create Raster

        ::

            Raster.from_rasterio(reader)
            Raster.from_rasterio(reader, name)

        Creates a new Raster object from a rasterio.DatasetReader object. Raises a FileNotFoundError if the associated file no longer exists. Uses the file format driver associated with the object to read the raster from file. By default, loads the data from band 1. The name input specifies an optional name for the new Raster object. Defaults to "raster" if unset.

    .. dropdown:: Windowed Reading

        ::
        
            Raster.from_rasterio(..., *, bounds)

        Only loads data from a bounded subset of the saved dataset. This option is useful when you only need a small portion of a very large raster, and limits the amount of data loaded into memory. You should also use this option whenever a saved raster is larger than your computer's RAM.

        The ``bounds`` input indicates a rectangular portion of the saved dataset that should be loaded. If the window extends beyond the bounds of the dataset, then the dataset will be windowed to the relevant bound, but no further. The window may be a BoundingBox, Raster, or a list/tuple/dict convertible to a BoundingBox object.

        .. note::

            When filling a window, this command will first read the entirety of one or more data chunks from the file. As such, the total memory usage will temporarily exceed the memory needed to hold just the window. If a raster doesn't use chunks (rare, but possible), then the entire raster will be read into memory before filling the window. In practice, it's important to chunk the data you use for applications.

    .. dropdown:: Specify Band

        ::

            Raster.from_rasterio(..., band)

        Specifies the file band to read when loading the raster from file. Raster bands use 1-indexing (and not the 0-indexing common to Python). Raises an error if the band does not exist.

    .. dropdown:: Boolean Raster

        ::
            
            Raster.from_rasterio(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.

    .. dropdown:: Default NoData

        ::
        
            Raster.from_rasterio(..., *, default_nodata)
            Raster.from_rasterio(..., *, default_nodata, casting)
            Raster.from_rasterio(..., *, ensure_nodata=False)

        Specifies additional options for NoData values. By default, if the raster file does not have a NoData value, then this routine will set a default NoData value based on the dtype of the raster. Set ``ensure_nodata=False`` to disable this behavior. Alternatively, you can use the "default_nodata" option to specify a different default NoData value. The default nodata value should be safely castable to the raster dtype, or use the "casting" option to specify other casting rules.

    :Inputs:
        * **reader** (*rasterio.DatasetReader*) -- A rasterio.DatasetReader associated with a raster dataset
        * **name** (*str*) -- An optional name for the raster. Defaults to "raster"
        * **band** (*int*) -- The raster band to read. Uses 1-indexing and defaults to 1
        * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.
        * **bounds** (*Raster | BoundingBox | tuple | dict*) -- A *Raster* or *BoundingBox* indicating a subset of the saved raster that should be loaded.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.

    :Outputs:
        *Raster* -- The new Raster object


.. _pfdf.raster.Raster.from_pysheds:

.. py:method:: Raster.from_pysheds(sraster, name = None, isbool = False)

    Creates a Raster from a ``pysheds.sview.Raster`` object

    .. dropdown:: Create Raster

        ::
        
            Raster.from_pysheds(sraster)
            Raster.from_pysheds(sraster, name)

        Creates a new Raster object from a ``pysheds.sview.Raster`` object. Inherits the nodata values, CRS, and transform of the pysheds Raster. Creates a copy of the input raster's data array, so changes to the pysheds raster will not affect the new Raster object, and vice versa. The name input specifies an optional name for the new Raster. Defaults to "raster" if unset.

    .. dropdown:: Boolean Raster

        ::
        
            Raster.from_pysheds(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.

    :Inputs:
        * **sraster** (*pysheds.sview.Raster*) -- The ``pysheds.sview.Raster`` object used to create the new Raster
        * **name** (*str*) -- An optional name for the raster. Defaults to "raster"
        * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.

    :Outputs:
        *Raster* -- The new Raster object


.. _pfdf.raster.Raster.from_array:

.. py:method:: Raster.from_array(array, name = None, *, nodata = None, crs = None, transform = None, bounds = None, spatial = None, casting = "safe", isbool = False, ensure_nodata = True, copy = True)

    Add raster metadata to a raw numpy array

    .. dropdown:: Create Raster

        ::
        
            Raster.from_array(array, name)

        Initializes a Raster object from a raw numpy array. Infers a NoData value from the dtype of the array. The Transform and CRS will both be None. The raster name can be returned using the ``name`` property and is used to identify the raster in error messages. Defaults to 'raster' if unset. Note that the new Raster object holds a copy of the input array, so changes to the input array will not affect the Raster, and vice-versa.

    .. dropdown:: NoData

        ::
        
            Raster.from_array(..., *, nodata)
            Raster.from_array(..., *, nodata, casting)

        Specifies a NoData value for the raster. The NoData value will be set to the same dtype as the array. Raises a TypeError if the NoData value cannot be safely cast to this dtype. Use the casting option to change this behavior. Casting options are as follows:

        * 'no': The data type should not be cast at all
        * 'equiv': Only byte-order changes are allowed
        * 'safe': Only casts which can preserve values are allowed
        * 'same_kind': Only safe casts or casts within a kind (like float64 to float32)
        * 'unsafe': Any data conversions may be done

    .. dropdown:: Spatial Template

        ::
        
            Raster.from_array(..., *, spatial)

        Specifies a Raster object to use as a default spatial metadata template. By default, transform and crs properties from the template will be copied to the new raster. However, refer below for a syntax to override this behavior.

    .. dropdown:: Spatial Keywords

        ::
        
            Raster.from_array(..., *, crs)
            Raster.from_array(..., *, transform)
            Raster.from_array(..., *, bounds)

        Specifies the crs, transform, and/or bounding box that should be associated with the raster. If used in conjunction with the "spatial" option, then any keyword options will take precedence over the metadata in the spatial template. You may only provide one of the transform/bounds inputs - raises an error if both are provided. If the CRS of a Transform or BoundingBox differs from the spatial/keyword CRS, then the Transform or BoundingBox is reprojected to match the other CRS.

    .. dropdown:: Boolean Raster

        ::
        
            Raster.from_array(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the array. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original array must be equal to 0 or 1. NoData pixels in the array will be converted to False, regardless of their value.

    .. dropdown:: Default NoData

        ::
        
            Raster.from_array(..., *, ensure_nodata=False)

        Disables the use of default NoData values. The returned raster's nodata value will be None unless the "nodata" option is specified.

    .. dropdown:: Disable Copying

        ::
        
            Raster.from_array(..., *, copy=False)

        Does not copy the input array when possible. This syntax can save memory when initializing a raster from a very large in-memory array. However, changes to the base array will propagate into the Raster's data value matrix. As such, this syntax is not recommended for most users.

    :Inputs:
        * **array** (*np.ndarray*) -- A 2D numpy array whose data values represent a raster
        * **name** (str**) -- A name for the raster. Defaults to 'raster'
        * **nodata** (*scalar*) -- A NoData value for the raster
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **spatial** (*Raster*) -- A Raster object to use as a default spatial metadata template for the new Raster.
        * **crs** (*CRS-like*) -- A coordinate reference system for the raster transform: An affine transformation for the raster. Mutually exclusive with the "bounds" input
        * **bounds** (*BoundingBox-like*) -- A BoundingBox for the raster. Mutually exclusive with the "transform" input
        * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.
        * **ensure_nodata** (*bool*) -- True (default) to infer a default NoData value from the raster's dtype when a NoData value is not provided. False to disable this behavior.
        * **copy** (*bool*) -- True (default) to build the Raster's data matrix from a copy of the input array. False to build the data matrix from the input array directly.

    :Outputs:
        *Raster* -- A *Raster* object for the array-based raster dataset



----

From Vector Features
--------------------

.. _pfdf.raster.Raster.from_points:

.. py:method:: Raster.from_points(path, field = None, *, dtype = None, field_casting = "safe", nodata = None, casting = "safe", operation = None, bounds = None, resolution = 10, units = "meters", layer = None, driver = None, encoding = None)

    Creates a Raster from a set of point/multi-point features

    .. dropdown:: From Point Features

        ::

            Raster.from_points(path)

        Returns a raster derived from the input point features. The contents of the input file should resolve to a FeatureCollection of Point and/or MultiPoint geometries (and refer below if the file contains multiple layers). The CRS of the output raster is inherited from the input feature file. The default resolution of the output raster is 10 meters, although refer below to specify other resolutions. The bounds of the raster will be the minimal bounds required to contain all input points at the indicated resolution.

        If you do not specify an attribute field, then the returned raster will have a boolean dtype. Pixels containing a point are set to True. All other pixels are set to False. Refer below to build the raster from an data property field instead.

        By default, this method will attempt to guess the intended file format and encoding based on the path extension. Raises an error if the format or encoding cannot be determined. However, refer below for syntax to specify the driver and encoding, regardless of extension. You can also use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: From Data Field

        ::

            Raster.from_points(path, field)
            Raster.from_points(..., *, dtype)
            Raster.from_points(..., *, dtype, field_casting)

        Builds the raster using one of the data property fields for the point features. Pixels that contain a point are set to the value of the data field for that point. If a pixel contains multiple points, then the pixel's value will match the data value of the final point in the set. Pixels that do not contain a point are set to a default NoData value, but refer below for options to specify the NoData value instead.

        The indicated data field must exist in the data properties, and must have an int or float type. By default, the dtype of the output raster will match this type. Use the ``dtype`` option to specify the type of the output raster instead. In this case, the data field values will be cast to the indicated dtype before being used to build the raster. By default, field values must be safely castable to the indicated dtype. Use the ``field_casting`` option to select different casting rules. The ``dtype`` and ``field_casting`` options are ignored if you do not specify a field.

    .. dropdown:: NoData

        ::

            Raster.from_points(..., field, *, nodata)
            Raster.from_points(..., field, *, nodata, casting)

        Specifies the NoData value to use when building the raster from a data attribute field. By default, the NoData value must be safely castable to the dtype of the output raster. Use the ``casting`` option to select other casting rules. NoData options are ignored if you do not specify a field.

    .. dropdown:: Field Operation

        ::

            Raster.from_points(..., field, *, operation)

        Applies the indicated function to the data field values and uses the output values to build the raster. The input function should accept one numeric input, and return one real-valued numeric output. Useful when data field values require a conversion. For example, you could use the following to scale Point values by a factor of 100::

            def times_100(value):
                return value * 100

            Raster.from_points(..., field, operation=times_100)

        Values are converted before they are validated against the ``dtype`` and ``field_casting`` options, so you can also use an operation to implement a custom conversion from data values to the output raster dtype. The operation input is ignored if you do not specify a field.

    .. dropdown:: Windowed Reading

        ::

            Raster.from_points(..., *, bounds)

        Only uses point features contained within the indicated bounds. The returned raster is also clipped to these bounds. This option can be useful when you only need data from a subset of a much larger Point dataset.

    .. dropdown:: Specify Resolution

        ::

            Raster.from_points(path, *, resolution)
            Raster.from_points(path, *, resolution, units)

        Specifies the resolution of the output raster. The resolution may be a scalar positive number, a 2-tuple of such numbers, a Transform, or a Raster object. If a scalar, indicates the resolution of the output raster for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution and the second element is the Y-axis. If a Raster or a Transform, uses the associated resolution. Raises an error if a Raster object does not have a Transform.

        If the resolution input does not have an associated CRS, then the resolution values are interpreted as meters. Use the ``units`` option to interpret resolution values in different units instead. Supported units include: "base" (CRS/Transform base unit), "kilometers", "feet", and "miles". Note that this option is ignored if the input resolution has a CRS.

    .. dropdown:: Multiple Layers

        ::
    
            Raster.from_points(..., *, layer)

        Use this option when the input feature file contains multiple layers. The ``layer`` input indicates the layer holding the relevant Point geometries. This may be either an integer index, or the (string) name of a layer in the input file.

    .. dropdown:: Specify File Format

        ::
    
            Raster.from_points(..., *, driver)
            Raster.from_points(..., *, encoding)

        Specifies the file format driver and encoding used to read the Points feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to read vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_
    
    
    :Inputs:
        * **path** (*Path-like*) -- The path to a Point or MultiPoint feature file
        * **field** (*str*) -- The name of a data property field used to set pixel values. The data field must have an int or float type.
        * **dtype** (*type*) -- The dtype of the output raster when building from a data field. Defaults to int32 or float64, as appropriate.
        * **field_casting** (*str*) -- The type of data casting allowed to occur when converting data field values to a specified output dtype. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **nodata** (*scalar*) -- The NoData value for the output raster.
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", safe" (default), "same_kind", and "unsafe".
        * **operation** (*Callable*) -- A function that should be applied to data field values before they are used to build the raster. Should accept one numeric input and return one real-valued numeric input.
        * **bounds** (*BoundingBox | Raster | tuple | dict*) -- A bounding box indicating the subset of point features that should be used to create the raster.
        * **resolution** (*scalar | vector | Transform | Raster*) -- The desired resolution of the output raster
        * **units** (*str*) -- Specifies the units of the resolution when the resolution input does not have a CRS. Options include: "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet", and "miles"
        * **layer** (*int | str*) -- The layer of the input file from which to load the point geometries
        * **driver** (*str*) -- The file-format driver to use to read the Point feature file
        * **encoding** (*str*) -- The encoding of the Point feature file

    :Outputs:
        *Raster* -- The point-derived raster. Pixels that contain a point are set either to True, or to the value of a data field. All other pixels are NoData.


.. _pfdf.raster.Raster.from_polygons:

.. py:method:: Raster.from_polygons(path, field = None, *, dtype = None, field_casting = "safe", nodata = None, casting = "safe", operation = None, bounds = None, resolution = 10, units = "meters", layer = None, driver = None, encoding = None)

    Creates a Raster from a set of polygon/multi-polygon features

    .. dropdown:: From Polygon Features

        ::

            Raster.from_polygons(path)

        Returns a raster derived from the input polygon features. The contents of the input file should resolve to a FeatureCollection of Polygon and/or MultiPolygon geometries (and refer below if the file contains multiple layers). The CRS of the output raster is inherited from the input feature file. The default resolution of the output raster is 10 meters, although refer below to specify other resolutions. The bounds of the raster will be the minimal bounds required to contain all input polygons at the indicated resolution.

        If you do not specify an attribute field, then the returned raster will have a boolean dtype. Pixels whose centers are in any of the polygons are set to True. All other pixels are set to False. Refer below to build the raster from an data property field instead.

        By default, this method will attempt to guess the intended file format and encoding based on the path extension. Raises an error if the format or encoding cannot be determined. However, refer below for syntax to specify the driver and encoding, regardless of extension. You can also use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: From Data Field

        ::
           
            Raster.from_polygons(path, field)
            Raster.from_polygons(..., *, dtype)
            Raster.from_polygons(..., *, dtype, field_casting)

        Builds the raster using one of the data property fields for the polygon features. Pixels whose centers lie within a polygon are set to the value of the data field for that polygon. If a pixel is in multiple polygons, then the pixel's value will match the data value of the final polygon in the set. Pixels that do no lie within a polygon are set to a default NoData value, but refer below for options to specify the NoData value instead.


        The indicated data field must exist in the data properties, and must have an int or float type. By default, the dtype of the output raster will be int32 or float64, as appropriate. Use the ``dtype`` option to specify the type of the output raster instead. In this case, the data field values will be cast to the  indicated dtype before being used to build the raster. Note that only some numpy dtypes are supported for building a raster from polygons. Supported dtypes are: bool, int16, int32, uint8, uint16, uint32, float32, and float64. Raises an error 
        if you select a different dtype.

        By default, field values must be safely castable to the indicated dtype. Use the  ``field_casting`` option to select different casting rules. The ``dtype`` and ``field_casting`` options are ignored if you do not specify a field.

    .. dropdown:: NoData

        ::

            Raster.from_polygons(..., field, *, nodata)
            Raster.from_polygons(..., field, *, nodata, casting)

        Specifies the NoData value to use when building the raster from a data attribute field. By default, the NoData value must be safely castable to the dtype of the output raster. Use the ``casting`` option to select other casting rules. NoData options are ignored if you do not specify a field.

    .. dropdown:: Field Operation

        ::

            Raster.from_polygons(..., field, *, operation)
        
        Applies the indicated function to the data field values and uses the output values to build the raster. The input function should accept one numeric input, and return one real-valued numeric output. Useful when data field values require a conversion. For example, you could use the following to scale Polygon values by a factor of 100::

            def times_100(value):
                return value * 100

            Raster.from_polygons(..., field, operation=times_100)

        Values are converted before they are validated against the ``dtype`` and ``field_casting`` options, so you can also use an operation to implement a custom conversion from data values to the output raster dtype. The operation input is ignored if you do not specify a field.
        
    .. dropdown:: Windowed Reading

        ::
           
            Raster.from_polygons(..., *, bounds)

        Only uses polygon features that intersect the indicated bounds. The returned raster is also clipped to these bounds. This option can be useful when you only need data from a subset of a much large Polygon dataset.
        
    .. dropdown:: Specify Resolution

        ::

            Raster.from_polygons(..., *, resolution)
            Raster.from_polygons(..., *, resolution, units)

        Specifies the resolution of the output raster. The resolution may be a scalar positive number, a 2-tuple of such numbers, a Transform, or a Raster object. If a scalar, indicates the resolution of the output raster for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution and the second element is the Y-axis. If a Raster or a Transform, uses the associated resolution. Raises an error if a Raster object does not have a Transform.

        If the resolution input does not have an associated CRS, then the resolution values are interpreted as meters. Use the "units" option to interpret resolution values in different units instead. Supported units include: "base" (CRS/Transform base unit), "kilometers", "feet", and "miles". Note that this option is ignored if the input resolution has a CRS.

    .. dropdown:: Multiple Layers

        ::
           
            Raster.from_polygons(..., *, layer)

        Use this option when the input feature file contains multiple layers. The ``layer`` input indicates the layer holding the relevant Polygon geometries. This may be either an integer index, or the (string) name of a layer in the input file.
        
    .. dropdown:: Specify File Format

        ::
           
            Raster.from_polygons(..., *, driver)
            Raster.from_polygons(..., *, encoding)

        Specifies the file format driver and encoding used to read the polygon feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to read vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_

    :Inputs:
        * **path** (*Path-like*) -- The path to a Polygon or MultiPolygon feature file
        * **field** (*str*) -- The name of a data property field used to set pixel values. The data field must have an int or float type.
        * **dtype** (*type*) -- The dtype of the output raster when building from a data field. Defaults to int32 or float64, as appropriate. Supported dtypes are: bool, int16, int32, uint8, uint16, uint32, float32, and float64
        * **field_casting** (*str*) -- The type of data casting allowed to occur when converting data field values to a specified output dtype. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **nodata** (*scalar*) -- The NoData value for the output raster.
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", safe" (default), "same_kind", and "unsafe".
        * **operation** (*Callable*) -- A function that should be applied to data field values before they are used to build the raster. Should accept one numeric input and return one real-valued numeric input.
        * **bounds** (*BoundingBox | Raster | tuple | dict*) -- A bounding box indicating the subset of polygon features that should be used to create the raster.
        * **resolution** (*scalar | vector | Transform | Raster*) -- The desired resolution of the output raster
        * **units** (*str*) -- Specifies the units of the resolution when the resolution input does not have a CRS. Options include: "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet", and "miles"
        * **layer** (*int | str*) -- The layer of the input file from which to load the polygon geometries
        * **driver** (*str*) -- The file-format driver to use to read the Polygon feature file
        * **encoding** (*str*) -- The encoding of the Polygon feature file

    :Outputs:
        *Raster* -- The polygon-derived raster. Pixels whose centers lie within a polygon are set either to True, or to the value of a data field. All other pixels are NoData.
    

----

IO
--

.. _pfdf.raster.Raster.__repr__:

.. py:method:: Raster.__repr__(self)

    Returns a string summarizing the raster

    ::
    
        repr(self)

    Returns a string summarizing key information about the raster. Includes the shape, dtype, NoData, CRS, Transform, and BoundingBox.

    :Outputs:
        *str* -- A string summary of the raster


.. _pfdf.raster.Raster.save:

.. py:method:: Raster.save(self, path, *, driver = None, overwrite = False)

    Save a raster dataset to file

    .. dropdown:: Save Raster

        ::

            self.save(path)
            self.save(path, * overwrite=True)

        Saves the *Raster* to the indicated path. Returns the absolute path to the saved file as output. Boolean rasters will be saved as int8 to accommodate common file format requirements. By default, raises an error if the file already exists. Set overwrite=True to allow the command to replace existing files.

        This syntax will attempt to guess the intended file format based on the path extension, and raises an Exception if the file format cannot be determined. You can use::

            >>> pfdf.utils.driver.extensions('raster')

        to return a summary of the file formats inferred by various extensions. We note that pfdf is tested using the "GeoTIFF" file format driver (.tif extension), and so saving to this format is likely the most robust.


    .. dropdown:: Specify Format

        ::

            self.save(..., *, driver)

        Also specifies the file format driver to use to write the raster file. Uses this format regardless of the file extension. You can use::

            >>> pfdf.utils.driver.rasters()

        to return a summary of file-format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses GDAL) to write raster files, and so additional drivers may work if their associated build requirements are satistfied. You can find a complete overview of GDAL raster drivers and their requirements here: `Raster drivers <https://gdal.org/drivers/raster/index.html>`_
        
    :Inputs: * **path** (*Path | str*) -- The path to the saved output file
             * **overwrite** (*bool*) -- False (default) to prevent the output from replacing existing file. True to allow replacement. 
             * **driver** (*str*) -- The name of the file format driver to use to write the file

    :Outputs: *Path* -- The path to the saved file


.. _pfdf.raster.Raster.copy:

.. py:method:: Raster.copy(self)

    Returns a copy of the current *Raster*

    ::

        self.copy()

    Returns a copy of the current *Raster*. Note that data values are not duplicated in memory when copying a raster. Instead, both *Raster* objects reference the same underlying array.

    :Outputs: *Raster* -- A *Raster* with the same data values and metadata as the current *Raster*


.. _pfdf.raster.Raster.as_pysheds:

.. py:method:: Raster.as_pysheds(self)

    Converts a *Raster* to a ``pysheds.sview.Raster`` object

    ::

        self.as_pysheds()

    Returns the current *Raster* object as a ``pysheds.sview.Raster object``. Note that the pysheds raster will use default values for any metadata that are missing from the *Raster* object. These default values are as follows:

    ========  =======
    Metadata  Default
    ========  =======
    nodata    0
    affine    Affine(1,0,0,0,1,0)
    crs       EPSG 4326
    ========  =======

    Please read the `pysheds documentation <https://mattbartos.com/pysheds/raster.html>`_ for additional details on using these outputs.

    :Outputs: *pysheds.sview.Raster* -- The *Raster* as a ``pysheds.sview.Raster`` object.


----

.. _api-preprocess:

.. _api-numeric-preprocess:

Numeric Preprocessing
---------------------

.. _pfdf.raster.Raster.fill:

.. py:method:: Raster.fill(self, value, *, copy = True)

    Replaces NoData pixels with the indicated value

    .. dropdown:: Fill NoData Pixels

        ::

            self.fill(value)

            Locates NoData pixels in the raster and replaces them with the indicated value. The fill value must be safely castable to the dtype of the raster. The updated raster will no longer have a NoData value, as all NoData pixels will have been replaced. By default, this method creates a copy of the raster's data array before replacing NoData values. As such, other copies of the raster will not be affected (although refer below to fill values wihout copying).

    .. dropdown:: Disable Copying

        :: 

            self.fill(..., *, copy=False)

        Does not copy the raster's data array before replacing NoData values. This can be useful when processing large arrays, but users should note that any objects that derive from the raster's data array (such as copied Raster objects) will also be altered. As such, we recommend only using this option when the array is exclusively used by the current object. Also note that this option is only available when the raster can set the write permissions of its data array. Although this is usually true, it may not be the case if the Raster object was built using an array factory with copy=False.

    :Inputs:
        * **value** (*scalar*) -- The fill value that NoData pixels will be replaced with
        * **copy** (*bool*) -- True (default) to create a copy of the data array before replacing values. False to alter the data array directly.


.. _pfdf.raster.Raster.find:

.. py:method:: Raster.find(self, values: RealArray) -> Self:

    Returns a boolean raster indicating pixels that match specified values

    ::

        self.find(values)

    Searches for the input values within the current raster. Returns a boolean raster the same size as the current raster. True pixels indicate pixels that matched one of the input values. All other pixels are False.

    :Inputs:
        * **values** (*vector*) -- An array of values that the raster values should be compared against.

    :Outputs:
        *Raster* -- A boolean raster. True elements indicate pixels that matched one of the input values. All other pixels are False


.. _pfdf.raster.Raster.set_range:

.. py:method:: Raster.set_range(self, min = None, max = None, fill = False, exclude_bounds = False, *, copy = True)

    Forces a raster's data values to fall within specified bounds

    .. dropdown:: Constrain Data Range

        ::

            self.set_range(min, max)

        Forces the raster's data values to fall within a specified range. The min and max inputs specify lower and upper bounds for the range, and must be safely castable to the dtype of the raster. By default, uses inclusive bounds, although refer below to use exclusive bounds instead. Data values that fall outside these bounds are clipped - pixels less than the lower bound are set to equal the bound, and pixels greater than the upper bound are set to equal that bound. If a bound is None, does not enforce that bound. Raises an error if both bounds are None.

        This method does not alter NoData pixels, even if the NoData value is outside the indicated bounds. By default, this method creates a copy of the raster's data array before replacing out-of-bounds pixels, so copies of the raster are not affected. Refer below to alter this behavior.

    .. dropdown:: Replace with NoData

        ::

            self.set_range(..., fill=True)

        Indicates that pixels outside the bounds should be replaced with the raster's NoData value, instead of being clipped to the appropriate bound. Raises a ValueError if the raster does not have a NoData value.

    .. dropdown:: Exclusive Bounds

        ::

            self.set_range(..., fill=True, exclude_bounds=True)

        Indicates that the bounds should be excluded from the valid range. In this case, data values exactly equal to a bound are also set to NoData. This option is only available when ``fill=True``.

    .. dropdown:: Disable Copying

        ::

            self.set_range(..., *, copy=False)

        Does not copy the raster's data array before replacing out-of-bounds pixels. This can be useful when processing large arrays, but users should note that any objects that derive from the raster's data array (such as copied Raster objects) will also be altered. As such, we recommend only using this option when the array is exclusively used by the current object. Also note that this option is only available when the raster can set the write permissions of its data array. Although this is usually true, it may not be the case if the Raster object was built using an array factory with copy=False.

    :Inputs:
        * **min** (*scalar*) -- A lower bound for the raster
        * **max** (*scalar*) -- An upper bound for the raster
        * **fill** (*bool*) -- If False (default), clips pixels outside the bounds to bounds. If True, replaces pixels outside the bounds with the NoData value
        * **exclude_bounds** (*bool*) -- True to consider the min and max data values as outside of the valid data range. False (default) to consider the min/max as within the valid data range. Only available when ``fill=True``.
        * **copy** (*bool*) -- True (default) to create a copy of the data array before replacing values. False to alter the data array directly.

----

.. _api-spatial-preprocess:

Spatial Preprocessing
---------------------

.. _pfdf.raster.Raster.__getitem__:

.. py:method:: Raster.__getitem__(self, indices)

    Returns a Raster object for the indexed portion of a raster's data array

    ::

        self[rows, cols]

    Returns a Raster object for the indexed portion of the current object's data array. The ``rows`` input should be an index or slice, as would be applied to the first dimension of the current Raster's data array. The ``cols`` input is an int or slice as would be applied to the second dimension. Returns an object with an updated data array and spatial metadata.

    Note that this method does not alter the current object. Instead, it returns a new Raster object for the indexed portion of the array. The data array for the new object is a view of the original array - this routine does not copy data.

    This syntax has several limitations compared to numpy array indexing:

    1. Indexing is not supported when the raster shape includes a 0,
    2. Indices must select at least 1 pixel - empty selections are not supported,
    3. Slices must have a step size of 1 or None,
    4. You must provide indices for exactly 2 dimensions, and
    5. This syntax is limited to the int and slice indices available to Python lists. More advanced numpy indexing methods (such as boolean indices and ellipses) are not supported.

    :Inputs:
        * **rows** (*int | slice*) -- An index or slice for the first dimension of the raster's data array
        * **cols** (*int | slice*) -- An index or slice for the second dimension of the raster's data array

    :Outputs:
        *Raster* -- A Raster object for the indexed portion of the data array


.. _pfdf.raster.Raster.buffer:

.. py:method:: Raster.buffer(self, distance = None, units = "meters", *, left = None, bottom = None, right = None, top = None)

    Buffers the current raster by a specified minimum distance

    .. dropdown:: Buffer

        ::

            self.buffer(distance)
            self.buffer(distance, units)

        Buffers the current raster by the specified minimum distance. Buffering adds a number of NoData pixels to each edge of the raster's data value matrix, such that the number of pixels is as least as long as the specified distance. Raises an error if the raster does not have a NoData value.

        Note that the number of pixels added to the x and y axes can differ if these axes have different resolutions. Also note that if the buffering distance is not a multiple of an axis's resolution, then the actual buffer along that axis will be longer than the input distance. (The discrepancy will be whatever distance is required to round the buffering distance up to a whole number of pixels).

        The input distance must be positive. By default, this distance is interpreted as meters. Use the ``units`` option to provide a buffering distance in other units instead. Supported units include: "pixels" (the number of pixels to buffer along each edge), "base" (CRS/Transform base units), "meters", "kilometers", "feet", and "miles". Note that different units have different metadata requirements, as follows:

        .. list-table::
            :header-rows: 1

            * - Units
              - Required Metadata
            * - pixels
              - None
            * - base
              - Transform only
            * - all others
              - CRS and Transform

    .. dropdown:: Specific Edges

        ::

            self.buffer(*, left)
            self.buffer(*, right)
            self.buffer(*, bottom)
            self.buffer(*, top)

        Specify the distance for a particular direction. The "distance" input is optional (but still permitted) if any of these options are specified. If both the "distance" input and one of these options are specified, then the direction-specific option takes priority. If a direction does not have a distance and the "distance" input is not provided, then no buffering is applied to that direction. The directions refer to the sides of the matrix of data values as follows:

        .. list-table::
          :header-rows: 1

          * - Edge
            - Matrix Index
          * - left
            - ``values[ :,  0]``
          * - right
            - ``values[ :, -1]``
          * - top
            - ``values[ 0,  :]``
          * - bottom
            - ``values[-1,  :]``

        Note that edge-specific buffers are interpreted using whatever units were indicated by the ``units`` option.

    :Inputs:
        * **distance** (*scalar*) -- A default buffer for all sides of the raster.
        * **units** (*str*) -- Specifies the units of the input buffers. Options include: "pixels", "base", "meters" (default), "kilometers", "feet", and "miles"
        * **left** (*scalar*) -- A buffer for the left side of the raster
        * **right** (*scalar*) -- A buffer for the right side of the raster
        * **top** (*scalar*) -- A buffer for the top of the raster
        * **bottom** (*scalar*) -- A buffer for the bottom of the raster


.. _pfdf.raster.Raster.clip:

.. py:method:: Raster.clip(self, bounds)

    Clips a raster to the indicated bounds

    ::

        self.clip(bounds)

    Clips a raster to the indicated spatial bounds. Bounds may be another raster, a BoundingBox object, or a dict/list/tuple representing a BoundingBox. If a clipping bound does not align with the edge of a pixel, clips the bound to the nearest pixel edge. Note that the raster must have a Transform in order to enable clipping.

    If the clipping bounds include areas outside the current raster, then pixels in these areas are set to the raster's NoData value. Raises an error if this occurs, but the raster does not have a NoData value.

    :Inputs:
        * **bounds** (*Raster | BoundingBox | tuple | dict*) -- A Raster or BoundingBox used to clip the current raster.


.. _pfdf.raster.Raster.reproject:

.. py:method:: Raster.reproject(self, template = None, *, crs = None, transform = None, resampling = "nearest", num_threads = 1, warp_mem_limit = 0)

    Reprojects a raster to match the spatial characteristics of another raster

    .. dropdown:: Reproject by Template

        ::

            self.reproject(template)

        Reprojects the current raster to match the spatial characteristics of a template raster. The current raster is projected into the same CRS, resolution, and grid alignment as the template. If either raster does not have a CRS, then the rasters are assumed to have the same CRS. If either raster does not have an affine transform, then the rasters are assumed to have the same resolution and grid alignment.

        If the raster is projected outside of its current bounds, then the reprojected pixels outside the bounds are set to the raster's NoData value. Raises an error if the raster does not have a NoData value. If resampling is required, uses nearest-neighbor interpolation by default, but refer below for additional resampling options.

    .. dropdown:: Reproject by Keyword

        ::

            self.reproject(..., *, crs)
            self.reproject(..., *, transform)

        Specify the crs and/or transform of the reprojected raster. Note that the transform is used to determine reprojected resolution and grid alignment. If you provide one of these keyword options in addition to the 'template' input, then the keyword value will take priority. If using the "transform" input and the transform CRS does not match the template/keyword CRS, then the transform will be reprojected to the appropriate CRS before reprojection.

    .. dropdown:: Resampling Algorithms

        ::

            self.reproject(..., *, resampling)

        Specifies the interpolation algorithm used for resampling. The default is nearest-neighbor interpolation. Other options include bilinear, cubic, cubic-spline, Lanczos-windowed, average, and mode resampling. Additional algorithms may be available depending on your GDAL installation. Read the rasterio documentation for additional details on resampling algorithms and their requirements: `Resampling Algorithms <https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling>`_

    .. dropdown:: Computational Performance

        ::

            self.reproject(..., *, num_threads)
            self.reproject(..., *, warp_mem_limit)

        Specify the number of worker threads and/or memory limit when reprojecting a raster. Reprojection can be computationally expensive, but increasing the number of workers and memory limit can speed up this process. These options are passed directly to rasterio, which uses them to implement the reprojection. Note that the units of warp_mem_limit are MB. By default, uses 1 worker and 64 MB.

    :Inputs:
        * **template** (*Raster*) -- A template Raster that defines the CRS, resolution, and grid alignment of the reprojected raster.
        * **crs** (*CRS-like*) -- The CRS to use for reprojection. Overrides the template CRS
        * **transform** (*Transform-like*) -- The transform used to determe the resolution and grid alignment of the reprojection. Overrides the template transform.
        * **resampling** (*str*) -- The resampling interpolation algorithm to use. Options include 'nearest' (default), 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', and 'mode'. Depending on the GDAL installation, the following options may also be available: 'max', 'min', 'med', 'q1', 'q3', 'sum', and 'rms'.
        * **num_threads** (*int*) -- The number of worker threads used to reproject the raster
        * **warp_mem_limit** (*scalar*) -- The working memory limit (in MB) used to reproject


----

Pixel Geometries
----------------

.. _pfdf.raster.Raster.dx:

.. py:method:: Raster.dx(self, units = "meters")

    Returns the change in the X-axis spatial coordinate when moving one pixel right

    ::
        
        self.dx()
        self.dx(units)

    Returns the change in X-axis spatial coordinate when moving one pixel to the right. By default, returns dx in meters. Use the ``units`` option to return dx in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return dx in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles".

    :Outputs:
        *float* -- The change in X coordinate when moving one pixel right


.. _pfdf.raster.Raster.dy:

.. py:method:: Raster.dy(self, units = "meters")

    Returns the change in the Y-axis spatial coordinate when moving one pixel down

    ::
        
        self.dy()
        self.dy(units)

    Returns the change in Y-axis spatial coordinate when moving one pixel down. By default, returns dy in meters. Use the ``units`` option to return dy in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return dy in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles".

    :Outputs:
        *float* -- The change in Y coordinate when moving one pixel down
        

.. _pfdf.raster.Raster.resolution:

.. py:method:: Raster.resolution(self, units = "meters")

    Returns the raster resolution

    ::
        
        self.resolution()
        self.resolution(units)

    Returns the raster resolution as a tuple with two elements. The first element is the X resolution, and the second element is Y resolution. Note that resolution is strictly positive. By default, returns resolution in meters. Use the ``units`` option to return resolution in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return resolution in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles".

    :Outputs:
        *float, float* -- The X and Y axis pixel resolution
        

.. _pfdf.raster.Raster.pixel_area:

.. py:method:: Raster.pixel_area(self, units = "meters")

    Returns the area of one pixel

    ::
        
        self.pixel_area()
        self.pixel_area(units)

    Returns the area of a raster pixel. By default, returns area in meters^2. Use the ``units`` option to return area in a different unit (squared). Supported units include: "base" (CRS/Transform base unit), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return resolution in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles".

    :Outputs:
        *float* -- The area of a raster pixel
        

.. _pfdf.raster.Raster.pixel_diagonal:

.. py:method:: Raster.pixel_diagonal(self, units = "meters")

    Returns the length of a pixel diagonal

    ::
        
        self.pixel_diagonal()
        self.pixel_diagonal(units)

    Returns the length of a pixel diagonal. By default, returns length in meters. Use the ``units`` option to return length in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units in which to return the length of a pixel diagonal. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles".

    :Outputs:
        *float* -- The area of a raster pixel
        


----

Comparisons
-----------

.. _pfdf.raster.Raster.__eq__:

.. py:method:: Raster.__eq__(self, other)

    Test *Raster* objects for equality

    ::

        self == other

    True if the other input is a *Raster* with the same values, nodata, transform, and crs. Note that NaN values are interpreted as NoData, and so compare as equal. Also note that the rasters are not required to have the same name to test as equal.

    :Inputs: * **other** -- A second input being compared to the *Raster* object

    :Outputs: *bool* -- True if the second input is a *Raster* with the same values, nodata, transform, and crs. Otherwise False.

    
.. _pfdf.raster.Raster.validate:

.. py:method:: Raster.validate(self, raster, name)

    Validates a second raster and its metadata against the current raster

    ::

        self.validate(raster, name)

    Validates an input raster against the current *Raster* object. Checks that the second raster's metadata matches the shape, affine transform, and crs of the current object. If the second raster does not have a affine transform or CRS, sets these values to match the current raster. Raises various errors if the metadata criteria are not met. Otherwise, returns the validated raster dataset as a *Raster* object.

    :Inputs: * **raster** (*Raster-like*) -- The input raster being checked
             * **name** (*str*) -- A name for the raster for use in error messages

    :Outputs: *Raster* -- The validated *Raster* dataset


----

Metadata Setters
----------------

.. _pfdf.raster.Raster.ensure_nodata:

.. py:method:: Raster.ensure_nodata(self, default = None, casting = "safe")

    Ensures a raster has a NoData value, setting a default value if missing

    .. dropdown:: Default Value

        ::

            self.ensure_nodata()

        Checks if the raster has a NoData value. If so, no action is taken. If not, then sets the NoData value to a default determined by the raster's dtype.

    .. dropdown:: Specify Value

        ::

            self.ensure_nodata(default)
            self.ensure_nodata(default, casting)

        Specifies the default NoData value to use if the raster does not have NoData. By default, the NoData value must be safely castable to the dtype of the raster. Use the "casting" option to select other casting rules.

    :Inputs:
        * **default** (*scalar*) -- A default NoData value. This will override the default value determined automatically from the raster dtype.
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".


.. _pfdf.raster.Raster.override:

.. py:method:: Raster.override(self, *, crs = None, transform = None, bounds = None, nodata = None, casting = "safe")

    Overrides current metadata values

    ::

        self.override(*, crs)
        self.override(*, transform)
        self.override(*, bounds)
        self.override(*, nodata)
        self.override(*, nodata, casting)

    Overrides current metadata values and replaces them with new values. The new values must still be valid metadata. For example, the new CRS must be convertible to a rasterio CRS object, the nodata value must be a scalar, etc. By default, requires safe nodata casting - use the casting input to specify a different casting rule. Note that you can only provide one of the "transform" and "bounds" inputs, as these options are mutually exclusive. If providing transform or bounds, and its CRS does not match the current/new CRS, then the transform will be reprojected to the correct CRS before overriding.

    .. important::

        Only use this method if you know what you're doing! This command replaces existing metadata values, but does not ensure that those values are correct. For example, overriding the CRS **will not** reproject the raster. It will merely replace the CRS metadata. As such, incorrect usage of this command will result in rasters with incorrect georeferencing and/or incorrect data masks. Most users should not use this method.

    :Inputs:
        * **crs** (*CRS-like*) -- New CRS metadata for the raster
        * **transform** (*Transform-like*) -- A new affine transform for the raster
        * **nodata** (*scalar*) -- A new NoData value for the raster
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
