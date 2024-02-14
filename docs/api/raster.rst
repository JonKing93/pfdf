pfdf.raster module
==================

.. _pfdf.raster:

.. py:module:: pfdf.raster


.. _pfdf.raster.Raster:

.. py:class:: Raster
    :module: pfdf.raster

    The Raster class is used to manage raster datasets and metadata within pfdf. Each Raster object represents a particular raster dataset. The object's properties return the raster's data values and metadata, and the class provides :ref:`methods to build Rasters <api-raster-creation>` from a variety of formats. Rasters implement various :ref:`preprocessing methods <api-preprocess>`, which can clean and prepare a dataset for hazard assessment. Any pfdf routine that computes a new raster will return the dataset as a Raster object. Use the :ref:`save method <pfdf.raster.Raster.save>` to save these to file.

    .. dropdown:: Properties

        ==============  ===========
        Property        Description
        ==============  ===========
        ..
        **Data**
        ---------------------------
        name            An optional name to identify the raster
        values          The data values associated with a raster
        dtype           The dtype of the raster array
        nodata          The NoData value associated with the raster
        nodata_mask     The NoData mask for the raster
        data_mask       The valid data mask for the raster
        ..
        **Shape**
        ---------------------------
        shape           The shape of the raster array
        size            The size (number of elements) in the raster array
        height          The number of rows in the raster array
        width           The number of columns in the raster array
        ..
        **Spatial**
        ---------------------------
        crs             The coordinate reference system associated with the raster
        transform       The Affine transformation used to map raster pixels to spatial coordinates
        dx              The change in x-axis spatial position when incrementing one column
        dy              The change in y-axis spatial position when incrementing one row
        bounds          A BoundingBox with the spatial coordinates of the raster's edges
        left            The spatial coordinate of the raster's left edge
        right           The spatial coordinate of the raster's right edge
        top             The spatial coordinate of the raster's upper edge
        bottom          The spatial coordinate of the raster's lower edge
        ..
        **Pixels**
        ---------------------------
        pixel_width     The spacing of raster pixels along the X axis in the units of the transform
        pixel_height    The spacing of raster pixels along the Y axis in the units of the transform
        resolution      The spacing of raster pixels along the X and Y axes in the units of the transform
        pixel_area      The area of a raster pixel in the units of the transform squared
        pixel_diagonal  The length of the diagonal of a raster pixel in the units of the transform
        ==============  ===========


    .. dropdown:: Methods

        =======================================================  ===========
        Method                                                   Description
        =======================================================  ===========
        ..
        **Object Creation**
        --------------------------------------------------------------------
        :ref:`__init__ <pfdf.raster.Raster.__init__>`            Returns a raster object for a supported raster input
        :ref:`from_file <pfdf.raster.Raster.from_file>`          Creates a Raster from a file-based dataset
        :ref:`from_array <pfdf.raster.Raster.from_array>`        Creates a Raster object from a numpy array
        :ref:`from_rasterio <pfdf.raster.Raster.from_rasterio>`  Creates a Raster from a rasterio.DatasetReader object
        :ref:`from_pysheds <pfdf.raster.Raster.from_pysheds>`    Creates a Raster from a pysheds.sview.Raster object
        ..
        **From Features**
        --------------------------------------------------------------------
        :ref:`from_points <pfdf.raster.Raster.from_points>`      Creates a Raster from point / multi-point features
        :ref:`from_polygons <pfdf.raster.Raster.from_polygons>`  Creates a Raster from polygon / multi-polygon features
        ..
        **Comparisons**
        --------------------------------------------------------------------
        :ref:`__eq__ <pfdf.raster.Raster.__eq__>`                True if the second object is a Raster with the same values, nodata, transform, and crs
        :ref:`validate <pfdf.raster.Raster.validate>`            Checks that a second raster has a compatible shape, transform, and crs
        ..
        **IO**
        --------------------------------------------------------------------
        :ref:`save <pfdf.raster.Raster.save>`                    Saves a raster dataset to file
        :ref:`copy <pfdf.raster.Raster.copy>`                    Creates a copy of the current Raster
        :ref:`as_pysheds <pfdf.raster.Raster.as_pysheds>`        Returns a Raster as a pysheds.sview.Raster object
        ..
        **Preprocessing**
        --------------------------------------------------------------------
        :ref:`fill <pfdf.raster.Raster.fill>`                    Fills a raster's NoData pixels with the indicated data value
        :ref:`find <pfdf.raster.Raster.find>`                    Returns a boolean raster indicating pixels that match specified values
        :ref:`set_range <pfdf.raster.Raster.set_range>`          Forces a raster's data pixels to fall within the indicated range
        :ref:`buffer <pfdf.raster.Raster.buffer>`                Buffers the edges of a raster by specified distances
        :ref:`reproject <pfdf.raster.Raster.reproject>`          Reprojects a raster to match a specified CRS, resolution, and grid alignment
        :ref:`clip <pfdf.raster.Raster.clip>`                    Clips a raster to the specified bounds
        =======================================================  ===========

----

Properties
----------

Data
++++

.. py:property:: Raster.name
    
    An optional name to identify the raster

.. py:property:: Raster.values

    A read-only copy of the raster's data array. 
    
    .. tip:: Make a copy if you want to change the array values.

.. py:property:: Raster.dtype

    The dtype of the data array

.. py:property:: Raster.nodata

    The NoData value for the raster

.. py:property:: Raster.nodata_mask

    The NoData mask for the raster. True elements are NoData pixels. All other pixels are False.

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


Spatial
+++++++


.. py:property:: Raster.crs
    
    The coordinate reference system associated with the raster.


.. py:property:: Raster.transform
    
    The Affine transformation used to map raster pixels to spatial coordinates.


.. py:property:: Raster.dx
    
    The change in x-axis spatial position when incrementing one column, or NaN is there is no transform.


.. py:property:: Raster.dy
    
    The change in y-axis spatial position when incrementing one row, or NaN is there is no transform.


.. py:property:: Raster.bounds
    
    A ``rasterio.coords.BoundingBox`` with the spatial coordinates of the raster's edges. All coordinates will be NaN if there is no transform.


.. py:property:: Raster.left
    
    The spatial coordinate of the raster's left edge, or NaN is there is no transform.


.. py:property:: Raster.right
    
    The spatial coordinate of the raster's right edge, or NaN is there is no transform.


.. py:property:: Raster.top
    
    The spatial coordinate of the raster's upper edge, or NaN is there is no transform.


.. py:property:: Raster.bottom
    
    The spatial coordinate of the raster's lower edge, or NaN is there is no transform.


Pixels
++++++

.. py:property:: Raster.pixel_width
    
    The (strictly positive) spacing of raster pixels along the X axis in the units of the transform. NaN if there is no transform.

.. py:property:: Raster.pixel_height
    
    The (strictly positive) spacing of raster pixels along the Y axis in the units of the transform. NaN if there is no transform.

.. py:property:: Raster.resolution
    
    The (strictly positive) spacing of raster pixels along the X and Y axes in the units of the transform. Both values are NaN if there is no transform.

.. py:property:: Raster.pixel_area
    
    The area of a raster pixel in the units of the transform squared. NaN if there is no transform.

.. py:property:: Raster.pixel_diagonal
    
    The length of the diagonal of a raster pixel in the units of the transform. NaN if there is no transform.


.. _api-raster-creation:

Object Creation
---------------

.. _pfdf.raster.Raster.__init__:

.. py:method:: Raster.__init__(self, raster = None, name = None, isbool = False)
    
    Creates a new Raster object

    .. dropdown:: Create Raster

        ::

            Raster(raster)

        Returns the input raster as a Raster object. Supports a variety of raster datasets including: the path to a file-based raster, numpy arrays, other pfdf.raster.Raster objects, and pysheds.sview.Raster objects. The input raster should refer to a 2D array with a boolean, integer, or floating dtype - raises Exceptions when this is not the case.

        .. note:: 

            This constructor will attempt to determine the type of input and initialize a raster using default option for that input type. However, the various factory methods provide additional options for creating Rasters from specific formats. For example, :ref:`from_array <pfdf.raster.Raster.from_array>` includes options to add metadata values to an array, and :ref:`from_file <pfdf.raster.Raster.from_file>` allows you to specify the band and file format driver.

    .. dropdown:: Named Raster

        :: 

            Raster(raster, name)

        Optionally specifies a name for the raster. This can be returned using the ``name`` property. Defaults to "raster" if unspecified.

    .. dropdown:: Boolean Raster

        :: 

            Raster(..., isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the raster must be equal to 0 or 1. NoData pixels in the raster will be converted to False, regardless of their value.

    .. dropdown:: Empty Object

        ::

            Raster()

        Returns an empty raster object. The attributes of the raster are all set to None. This syntax is mostly intended for developers.

    :Inputs: * **raster** (*Raster-like*) -- A supported raster dataset
                * **name** (*str*) -- An optional name for the input raster. Defaults to 'raster'
                * **isbool** (*bool*) -- True indicates that the raster represents a boolean array. False (default) leaves the raster as its original dtype.

    :Outputs: *Raster* -- The Raster object for the dataset


.. _pfdf.raster.Raster.from_array:

.. py:method:: Raster.from_array(array, name = None, *, nodata = None, transform = None, crs = None, spatial = None, casting = "safe", isbool = False)
    :staticmethod:

    Creates a Raster from a numpy array, optionally including metadata

    .. dropdown:: Create Raster

        ::

            Raster.from_array(array, name)

        Initializes a Raster object from a raw numpy array. The NoData value, transform, and crs for the returned object will all be None. The raster name can be returned using the ".name" property and is used to identify the raster in error messages. Defaults to 'raster' if unset. Note that the new Raster object holds a copy of the input array, so changes to the input array will not affect the Raster, and vice-versa.

    .. dropdown:: NoData

        ::

            Raster.from_array(..., *, nodata)
            Raster.from_array(..., *, nodata, casting)

        Specifies a NoData value for the raster. The NoData value will be casted to the same dtype as the array. Raises a TypeError if the NoData value cannot be casted to this dtype. By default, requires safe casting. Use the casting option to change this behavior. Casting options are as follows:
        
        * 'no': The data type should not be cast at all
        * 'equiv': Only byte-order changes are allowed
        * 'safe': Only casts which can preserve values are allowed
        * 'same_kind': Only safe casts or casts within a kind (like float64 to float32)
        * 'unsafe': Any data conversions may be done

    .. dropdown:: Spatial Template

        ::

            Raster.from_array(..., *, spatial)

        Specifies a Raster object to use as a default spatial metadata template. By default, transform and crs properties from the template will be copied to the new raster. However, see below for a syntax to override this behavior.

    .. dropdown:: Spatial Keywords

        ::

            Raster.from_array(..., *, transform)
            Raster.from_array(..., *, crs)

        Specifies the crs and/or transform that should be associated with the raster. If used in conjunction with the "spatial" option, then any keyword options will take precedence over the metadata in the spatial template.

        The transform specifies the affine transformation used to map pixel indices to spatial points, and should be an ``affine.Affine`` object. Common ways to obtain such an object are using the ``transform`` property from rasterio and Raster objects, via the ``affine`` property of pysheds rasters, or via the Affine class itself.

        The crs is the coordinate reference system used to locate spatial points. This input should a ``rasterio.crs.CRS object``, or convertible to such an object. CRS objects can be obtained using the ``crs`` property from rasterio or Raster objects, and see also the `rasterio documentation <https://rasterio.readthedocs.io/en/stable/api/rasterio.crs.html#rasterio.crs.CRS>`_ for building these objects from formats such as well-known text (WKT) and PROJ4 strings.

    .. dropdown:: Boolean Raster

        ::

            Raster.from_array(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.

    :Inputs: * **array** (*ndarray*) -- A 2D numpy array whose data values represent a raster
             * **name** (*str*) -- A name for the raster. Defaults to 'raster'
             * **nodata** (*scalar*) -- A NoData value for the raster
             * **casting** (*"no" | "equiv" | "safe" | "same_kind" | "unsafe"*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. 
             * **spatial** (*Raster*) -- A Raster object to use as a default spatial metadata template for the new Raster.
             * **transform** (*affine.Affine*) -- An affine transformation for the raster
             * **crs** (*rasterio.crs.CRS*) -- A coordinate reference system for the raster
             * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.

    :Outputs: *Raster* -- A raster object for the array-based raster dataset


.. _pfdf.raster.Raster.from_file:

.. py:method:: Raster.from_file(path, name = None, *, driver = None, band = 1, isbool = False, window = None)
    :staticmethod:

    Builds a Raster object from a file-based dataset

    .. dropdown:: Load from file

        ::

            Raster.from_file(path)
            Raster.from_file(path, name)

        Builds a Raster from the indicated file. Raises a FileNotFoundError if the file cannot be located. Loads file data when building the object. By default, loads all data from band 1, but see below for additional options. The name input can be used to provide an optional name for the raster,defaults to "raster" if unset.

        Also, by default the method will attempt to use the file extension to detect the file format driver used to read data from the file. Raises an Exception if the driver cannot be determined, but see below for options to explicitly set the driver. You can also use::

            >>> pfdf.utils.driver.extensions('raster')

        to return a summary of supported file format drivers, and their associated
        extensions.


    .. dropdown:: Specify Band

        ::

            Raster.from_file(..., *, band)

        Specify the raster band to read. Raises an error if the band does not exist.

        .. note:: Raster bands use 1-indexing, rather than the 0-indexing common to Python.


    .. dropdown:: Windowed Reading

        ::

            Raster.from_file(..., *, window)

        Only loads data from a windowed subset of the saved dataset. This option is useful when you only need a small portion of a very large raster, and limits the amount of data loaded into memory. You should also use this option whenever a saved raster is larger than your computer's RAM.

        The ``window`` input indicates a rectangular portion of the saved dataset that should be loaded. If the window extends beyond the bounds of the dataset, then the dataset will be windowed to the relevant bound, but no further. The window may either be a Raster object, or a vector with 4 elements. If a raster, then this method will load the portion of the dataset that contains the bounds of the window raster.

        If the window is a vector, then the elements should indicate, in order: 
        
        1. The index of the left-most column, 
        2. The index of the upper-most row, 
        3. Width (the number of columns), and 
        4. Height (the number of rows) 
        
        All four elements must be positive integers. Width and height cannot be zero. 

        .. attention::

            When filling a window, this command will first read the entirety of one or more data chunks from the file. As such, the total memory usage will temporarily exceed the memory needed to hold just the window. If a raster doesn't use chunks (rare, but possible), then the entire raster will be read into memory before filling the window. In practice, it's important to chunk the data you use for applications.


    .. dropdown:: Specify File Format

        ::

            Raster.from_file(..., *, driver)

        Specify the file format driver to use for reading the file. Uses this driver regardless of the file extension. You can also call::

            >>> pfdf.utils.driver.rasters()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses GDAL/OGR) to read raster files, and so additional drivers may work if their associated build requirements are met. A complete list of driver build requirements is available here: `Raster Drivers <https://gdal.org/drivers/raster/index.html>`_


    .. dropdown:: Boolean Raster

        ::

            Raster.from_file(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.
    
    :Inputs: * **path** (*Path | str*) -- A path to a file-based raster dataset
            * **name** (*str*) -- An optional name for the raster
            * **band** (*int*) -- The raster band to read. Uses 1-indexing and defaults to 1
            * **driver** (*str*) -- A file format to use to read the raster, regardless of extension
            * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.

    :Outputs: *Raster* -- A Raster object for the file-based dataset

    
.. _pfdf.raster.Raster.from_rasterio:

.. py:method:: Raster.from_rasterio(reader, name = None, *, band = 1, isbool = False, window = None)
    :staticmethod:

    Builds a raster from a rasterio.DatasetReader

    .. dropdown:: Create Raster

        ::

            Raster.from_rasterio(reader)
            Raster.from_rasterio(reader, name)
            
        Creates a new Raster object from a rasterio.DatasetReader object. Raises a
        FileNotFoundError if the associated file no longer exists. Uses the file
        format driver associated with the object to read the raster from file.
        By default, loads the data from band 1. The name input specifies an optional
        name for the new Raster object. Defaults to "raster" if unset.


    .. dropdown:: Specify Band

        ::

            Raster.from_rasterio(..., band)

        Specifies the file band to read when loading the raster from file. Raises an
        error if the band does not exist.

        .. note:: Raster bands use 1-indexing, rather than the 0-indexing common to Python.


    .. dropdown:: Windowed Reading

        ::

            Raster.from_rasterio(..., *, window)

        Only loads data from a windowed subset of the saved dataset. This option is useful when you only need a small portion of a very large raster, and limits the amount of data loaded into memory. You should also use this option whenever a saved raster is larger than your computer's RAM.

        The ``window`` input indicates a rectangular portion of the saved dataset that should be loaded. If the window extends beyond the bounds of the dataset, then the dataset will be windowed to the relevant bound, but no further. The window may either be a Raster object, or a vector with 4 elements. If a raster, then this method will load the portion of the dataset that contains the bounds of the window raster.

        If the window is a vector, then the elements should indicate, in order: 
        
        1. The index of the left-most column, 
        2. The index of the upper-most row, 
        3. Width (the number of columns), and 
        4. Height (the number of rows) 
        
        All four elements must be positive integers. Width and height cannot be zero. 

        .. attention::

            When filling a window, this command will first read the entirety of one or more data chunks from the file. As such, the total memory usage will temporarily exceed the memory needed to hold just the window. If a raster doesn't use chunks (rare, but possible), then the entire raster will be read into memory before filling the window. In practice, it's important to chunk the data you use for applications.


    .. dropdown:: Boolean Raster

        ::
            
            Raster.from_rasterio(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.

    :Inputs: * **reader** (*rasterio.DatasetReader*) -- A rasterio.DatasetReader associated with a raster dataset
             * **name** (*str*) -- An optional name for the raster. Defaults to "raster"
             * **band** (*int*) -- The raster band to read. Uses 1-indexing and defaults to 1
             * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.

    :Outputs: *Raster* -- The new Raster object


.. _pfdf.raster.Raster.from_pysheds:

.. py:method:: Raster.from_pysheds(sraster, name = None, isbool = False)
    :staticmethod:

    Creates a Raster from a ``pysheds.sview.Raster`` object

    .. dropdown:: Create Raster

        ::

            Raster.from_pysheds(sraster)
            Raster.from_pysheds(sraster, name)

        Creates a new Raster object from a pysheds.sview.Raster object. Inherits the nodata values, CRS, and transform of the pysheds Raster. Creates a copy of the input raster's data array, so changes to the pysheds raster will not affect the new Raster object, and vice versa. The name input specifies an optional name for the new Raster. Defaults to "raster" if unset.

    .. dropdown:: Boolean Raster

        ::

            Raster.from_pysheds(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The newly created raster will have a bool dtype and values, and its NoData value will be set to False. When using this option, all data pixels in the original file must be equal to 0 or 1. NoData pixels in the file will be converted to False, regardless of their value.

    :Inputs: * **sraster** (*pysheds.sview.Raster*) -- The pysheds.sview.Raster object used to create the new Raster
             * **name** (*str*) -- An optional name for the raster. Defaults to "raster"
             * **isbool** (*bool*) -- True to convert the raster to a boolean array, with nodata=False. False (default) to leave the raster as the original dtype.

    :Outputs: *Raster* -- The new Raster object


From Vector Features
--------------------

.. _pfdf.raster.Raster.from_points:

.. py:method:: Raster.from_points(path, *, field = None, fill = None, resolution = 1, layer = None, driver = None, encoding = None)
    :staticmethod:

    Creates a Raster from a set of point/multi-point features

    .. dropdown:: Boolean Raster

        ::

            Raster.from_points(path)
            Raster.from_points(path, *, layer)

        Returns a boolean raster derived from the input point features. Pixels containing a point are set to True. All other pixels are set to False. The CRS of the output raster is inherited from the input feature file. The default resolution of the output raster is 1 (in the units of the CRS), although see below for options for other resolutions. The bounds of the raster will be the minimal bounds required to contain all input points at the indicated resolution.

        The contents of the input file should resolve to a FeatureCollection of Point and/or MultiPoint geometries. If the file contains multiple layers, you can use the "layer" option to indicate the layer that holds the polygon geometries. This may either be an integer index, or the name of the layer in the input file.

        By default, this method will attempt to guess the intended file format and encoding based on the path extension. Raises an error if the format or encoding cannot be determined. However, see below for syntax to specify the driver and encoding, regardless of extension. You can also use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.


    .. dropdown:: From Data Field

        ::

            Raster.from_points(..., *, field)
            Raster.from_points(..., *, field, fill)

        Builds the raster using the indicated field of the point-feature data properties. The specified field must exist in the data properties, and must be an int or float type. The output raster will have a float dtype, regardless of the type of the data field, and the NoData value will be NaN. Pixels that contain a point are set to the value of the data field for that point. If a pixel contains multiple points, then the pixel's value will match the data field of the final point in the set. By default, all pixels not in a point are set as Nodata (NaN). Use the "fill" option to specify a default data value for these pixels instead.

    .. dropdown:: Specify Resolution

        ::

           Raster.from_points(path, *, resolution)

        Specifies the resolution of the output raster. The resolution may be a scalar positive number, a 2-tuple of such numbers, or a Raster object. If a scalar, indicates the resolution of the output raster (in the units of the CRS) for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution and the second element is the Y-axis. If a Raster, uses the resolution of the raster, or raises an error if the raster does not have a transform.

    .. dropdown:: Specify File Format

        ::

            Raster.from_points(..., *, driver)
            Raster.from_points(..., *, encoding)

        Specifies the file format driver and encoding used to read the Points feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()
            
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to read vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_.
    
    :Inputs: * **path** (*Path | str*) -- The path to a Point or MultiPoint feature file
             * **field** (*str*) -- The name of a data property field used to set pixel values. The data field must have an int or float type.
             * **fill** (*scalar*) -- A default fill value for rasters built using a data field. Ignored if field is None.
             * **resolution** (*Raster | scalar | [scalar, scalar]*) -- The desired resolution of the output raster
             * **layer** (*int*) -- The layer of the input file from which to load the point geometries
             * **driver** (*str*) -- The file-format driver to use to read the Point feature file
             * **encoding** (*str*) -- The encoding of the Point feature file

    :Outputs: *Raster* -- The point-derived raster. Pixels that contain a point are set either to True, or to the value of a data field. All other pixels are either a fill value or NoData (False or NaN).
    

.. _pfdf.raster.Raster.from_polygons:

.. py:method:: Raster.from_polygons(path, *, field = None, fill = None, resolution = 1, layer = None, driver = None, encoding = None)
    :staticmethod:

    Creates a Raster from a set of polygon/multi-polygon features

    .. dropdown:: Boolean Raster

        ::

            Raster.from_polygons(path)
            Raster.from_polygons(path, *, layer)

        Returns a boolean raster derived from the input polygon features. Pixels whose centers are in any of the polygons are set to True. All other pixels are set to False. The CRS of the output raster is inherited from the input feature file. The default resolution of the output raster is 1 (in the units of the polygon's CRS), although see below for options for other resolutions. The bounds of the raster will be the minimal bounds required to contain all input polygons at the indicated resolution.

        The contents of the input file should resolve to a FeatureCollection of Polygon and/or MultiPolygon geometries. If the file contains multiple layers, you can use the "layer" option to indicate the layer that holds the polygon geometries. This may either be an integer index, or the name of the layer in the input file.

        By default, this method will attempt to guess the intended file format and encoding based on the path extension. Raises an error if the format or encoding cannot be determined. However, see below for syntax to specify the driver and encoding, regardless of extension. You can also use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: From Data Field

        ::

            Raster.from_polygons(..., *, field)
            Raster.from_polygons(..., *, field, fill)

        Builds the raster using the indicated field of the polygon data properties. The specified field must exist in the data properties, and must be an int or float type. The output raster will have a float dtype, regardless of the type of the data field, and the NoData value will be NaN. Pixels whose centers are in a polygon are set to the value of the data field for that polygon. If a pixel is in multiple  overlapping polygons, then the pixel's value will match the data field of the final polygon in the set. By default, all pixels not in a polygon are set as Nodata (NaN). Use the  "fill" option to specify a default data value for these pixels instead.

    .. dropdown:: Specify Resolution

        ::

            Raster.from_polygons(path, *, resolution)

        Specifies the resolution of the output raster. The resolution may be a scalar positive number, a 2-tuple of such numbers, or a Raster object. If a scalar, indicates the resolution of the output raster (in the units of the CRS) for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution and the second element is the Y-axis. If a Raster, uses the resolution of the raster, or raises an error if the raster does not have a transform.

    .. dropdown:: Specify File Format

        ::

            Raster.from_polygons(..., *, driver)
            Raster.from_polygons(..., *, encoding)

        Specifies the file format driver and encoding used to read the polygon feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to read vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_.

    :Inputs: * **path** (*Path | str*) -- The path to a Polygon or MultiPolygon feature file
             * **field** (*str*) -- The name of a data property field used to set pixel values. The data field must have an int or float type.
             * **fill** (*scalar*) ---A default fill value for rasters built using a data field. Ignored if field is None.
             * **resolution** (*Raster | scalar | [scalar, scalar]*) -- The desired resolution of the output raster
             * **layer** (*int*) -- The layer of the input file from which to load the point geometries
             * **driver** (*str*) -- The file-format driver to use to read the Point feature file
             * **encoding** (*str*) -- The encoding of the Point feature file

    :Outputs: *Raster* -- The polygon-derived raster. Pixels whose centers are in a polygon are set either to True, or to the value of a data field. All other pixels are either a fill value or NoData (False or NaN).
    

Comparisons
-----------

.. _pfdf.raster.Raster.__eq__:

.. py:method:: Raster.__eq__(self, other)

    Test Raster objects for equality

    ::

        self == other

    True if the other input is a Raster with the same values, nodata, transform, and crs. Note that NaN values are interpreted as NoData, and so compare as equal. Also note that the rasters are not required to have the same name to test as equal.

    :Inputs: * **other** -- A second input being compared to the Raster object

    :Outputs: *bool* -- True if the second input is a Raster with the same values, nodata, transform, and crs. Otherwise False.

    
.. _pfdf.raster.Raster.validate:

.. py:method:: Raster.validate(self, raster, name)

    Validates a second raster and its metadata against the current raster

    ::

        self.validate(raster, name)

    Validates an input raster against the current Raster object. Checks that the second raster's metadata matches the shape, affine transform, and crs of the current object. If the second raster does not have a affine transform or CRS, sets these values to match the current raster. Raises various RasterErrors if the metadata criteria are not met. Otherwise, returns the validated raster dataset as a Raster object.

    :Inputs: * **raster** (*Raster-like*) -- The input raster being checked
             * **name** (*str*) -- A name for the raster for use in error messages

    :Outputs: *Raster* -- The validated Raster dataset


IO
--

.. _pfdf.raster.Raster.save:

.. py:method:: Raster.save(self, path, *, driver = None, overwrite = False)

    Save a raster dataset to file

    .. dropdown:: Save Raster

        ::

            self.save(path)
            self.save(path, * overwrite=True)

        Saves the Raster to the indicated path. Boolean rasters will be saved as "int8" to accommodate common file format requirements. In the default state, the method will raise a FileExistsError if the file already exists. Set overwrite=True to enable the replacement of existing files.

        This syntax will attempt to guess the intended file format based on the path extension, and raises an Exception if the file format cannot be determined. You can use::

            >>> pfdf.utils.driver.extensions('raster')

        to return a summary of the file formats inferred by various extensions.

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

.. _pfdf.raster.Raster.copy:

.. py:method:: Raster.copy(self)

    Returns a copy of the current Raster

    ::

        self.copy()

    Returns a copy of the current Raster. Note that data values are not duplicated in memory when copying a raster. Instead, both Rasters reference the same underlying array.

    :Outputs: *Raster* -- A Raster with the same data values and metadata as the current Raster



.. _pfdf.raster.Raster.as_pysheds:

.. py:method:: Raster.as_pysheds(self)

    Converts a Raster to a pysheds.sview.Raster object

    ::

        self.as_pysheds()

    Returns the current Raster object as a ``pysheds.sview.Raster object``. Note that the pysheds raster will use default values for any metadata that are missing from the Raster object. These default values are as follows:

    ========  =======
    Metadata  Default
    ========  =======
    nodata    0
    affine    Affine(1,0,0,0,1,0)
    crs       EPSG 4326
    ========  =======

    Please see the `pysheds documentation <https://mattbartos.com/pysheds/raster.html>`_ for additional details on using these outputs.

    :Outputs: *pysheds.sview.Raster* -- The Raster as a ``pysheds.sview.Raster`` object.


.. _api-preprocess:

Preprocessing
-------------

.. _pfdf.raster.Raster.fill:

.. py:method:: Raster.fill(self, value)

    Replaces NoData pixels with the indicated value

    ::

        self.fill(value)

    Locates NoData pixels in the raster and replaces them with the indicated value. The fill value must be safely castable to the dtype of the raster. Note that this method creates a copy of the raster's data array before replacing NoData values. As such, other copies of the raster will not be affected. Also note that the updated raster will no longer have a NoData value, as all NoData pixels will have been replaced.

    :Inputs: * **value** (*scalar*) -- The fill value that NoData pixels will be replaced with


.. _pfdf.raster.Raster.find:

.. py:method:: Raster.find(self, values)

    Returns a boolean raster indicating pixels that match specified values

    ::

        self.find(values)

    Searches for the input values within the current raster. Returns a boolean raster the same size as the current raster. True pixels indicate pixels that matched one of the input values. All other pixels are False.

    :Inputs: * **values** (*vector*) -- An array of values that the raster values should be compared against.

    :Outputs: *Raster* -- A boolean raster. True elements indicate pixels that matched one of the input values. All other pixels are False

    

.. _pfdf.raster.Raster.set_range:

.. py:method:: Raster.set_range(self, min = None, max = None, fill = False, nodata = None, casting = "safe")

    Forces a raster's data values to fall within specified bounds

    .. dropdown:: Constrain Data Range

        ::

            self.set_range(min, max)

        
        Forces the raster's data values to fall within a specified range. The min and max inputs specify inclusive lower and upper bounds for the range, and must be safely castable to the dtype of the raster. Data values that fall outside these bounds are clipped - pixels less than the lower bound are set to equal the bound, and pixels greater than the upper bound are set to equal that bound. If a bound is None, does not enforce that bound. Raises an error if both bounds are None. Note that the min and max inputs must be safely castable to the dtype of the raster.

        This method creates a copy of the raster's data values before replacing out-of-bounds pixels, so copies of the raster are not affected. Also, the method does not alter NoData pixels, even if the NoData value is outside of the indicated bounds.

    .. dropdown:: Replace with NoData

        ::

            self.set_range(..., fill=True)

        Indicates that pixels outside the bounds should be replaced with the raster's NoData value, instead of being clipped to the appropriate bound. Raises a ValueError if the raster does not have a NoData value, although see the next syntax for options to resolve this.

    .. dropdown:: Specify Missing NoData

        ::

            self.set_range(..., fill=True, nodata)
            self.set_range(..., fill=True, nodata, casting)

        Specifies a NoData value when using the "fill" option for a raster that does not have a NoData value. These inputs are ignored when fill=False. If fill=True, then they are only available if the raster does not have a NoData value - otherwise, raises an error. By default, the nodata value must be safely castable to the raster dtype. Use the "casting" input to allow other casting options.

    :Inputs: * **min** (*scalar*) -- A lower bound for the raster
             * **max** (*scalar*) -- An upper bound for the raster
             * **fill** (*bool*) -- If False (default), clips pixels outside the bounds to bounds. If True, replaces pixels outside the bounds with the NoData value
             * **nodata** (*scalar*) -- A NoData value for when fill=True and the raster does not have a NoData value. Ignored if fill=False
             * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".


.. _pfdf.raster.Raster.buffer:

.. py:method:: Raster.buffer(self, distance = None, *, left = None, bottom = None, right = None, top = None, pixels = False, nodata = None, casting = "safe")

    Buffers the current raster by a specified minimum distance

    .. dropdown:: Buffer

        ::

            self.buffer(distance)

        Buffers the current raster by the specified minimum distance and returns the buffered raster. Buffering adds a number of NoData pixels to each edge of the raster's data value matrix, such that the number of pixels is as least as long as the specified distance. If the specified distance is not a multiple of an axis's resolution, then the buffering distance along that axis will be longer than the input distance. Also note that the number of pixels added to the x and y axes can differ if these axes have different resolutions.

        The input distance cannot be negative, and should be in the same units as the raster's affine transformation. In practice, this is often units of meters. Raises an error if the raster does not have an affine transformation, but see below for an option that does not require a transform. Similarly, the default syntax requires the raster to have a NoData value, but see below for a syntax that relaxes this requirement.


    .. dropdown:: Specific Edges

        ::

            self.buffer(*, left)
            self.buffer(*, right)
            self.buffer(*, bottom)
            self.buffer(*, top)

        Specify the distance for a particular direction. The "distance" input is optional (but still permitted) if any of these options are specified. If both the "distance" input and one of these options are specified, then the direction-specific option takes priority. If a direction does not have a distance and the "distance" input is not provided, then no buffering is applied to that direction.

    .. dropdown:: Buffer by pixels

        ::

            self.buffer(..., *, pixels=True)

        Indicates that the units of the input distances are in pixels, rather than the units of the raster's transform. When using this option, the raster no longer requires an affine transformation. Non-integer pixel buffers are rounded up to the next highest integer.

    .. dropdown:: Specify missing NoData

        ::

            self.buffer(..., *, nodata)
            self.buffer(..., *, nodata, casting)

        Specifies a NoData value to use for the buffer pixels. You may only use this option when the raster does not already have a NoData value - raises a ValueError if this is not the case. The buffered raster will have its NoData value set to this value. By default, raises an error if the NoData value cannot be safely casted to the dtype of the raster. Use the casting option to implement different casting requirements.

    :Inputs: * **distance** (*scalar*): A default buffer for all sides of the raster.
             * **left** (*scalar*) -- A buffer for the left side of the raster
             * **right** (*scalar*) -- A buffer for the right side of the raster
             * **top** (*scalar*) -- A buffer for the top of the raster
             * **bottom** (*scalar*) -- A buffer for the bottom of the raster
             * **pixels** (*bool*) -- True if input distances are in units of pixels. False (default) if input distances are in the units of the transform.
             * **nodata** (*scalar*) -- A NoData value used for buffered pixels when a raster does not already have a NoData value.
             * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
             

.. _pfdf.raster.Raster.reproject:

.. py:method:: Raster.reproject(self, template = None, *, crs = None, transform = None, nodata = None, casting = "safe", resampling = "nearest", num_threads = 1, warp_mem_limit = 0)

    Reprojects a raster to match the spatial characteristics of another raster

    .. dropdown:: Reproject by Template

        ::

            self.reproject(template)

        Reprojects the current raster to match the spatial characteristics of a template raster. The current raster is projected into the same CRS, resolution, and grid alignment as the template. If either raster does not have a CRS, then the rasters are assumed to have the same CRS. If either raster does not have an affine transform, then the rasters are assumed to have the same resolution and grid alignment.

        If the raster is projected outside of its current bounds, then the reprojected pixels outside the bounds are set to the raster's NoData value. Raises an error if the raster does not have a NoData value, although see below for a syntax to resolve this. If resampling is required, uses nearest-neighbor interpolation by default, but see below for additional resampling options.

    .. dropdown:: Reproject by Keyword

        ::

            self.reproject(..., *, crs)
            self.reproject(..., *, transform)

        Specify the crs and/or transform used to reproject the alignment. Note that the transform is used to determine reprojected resolution and grid alignment. If you provide one of these keyword options in addition to the 'template' input, then the keyword value will take priority.


    .. dropdown:: Specify Missing NoData

        ::

            self.reproject(..., *, nodata)
            self.reproject(..., *, nodata, casting)

        Specfies a NoData value to use for reprojection. You can only provide this option if the raster does not already have a NoData value. Otherwise raises an Exception. The NoData value must be castable to the dtype of the raster being reprojected. By default, only safe casting is allowed. Use the casting option to enforce different casting rules.

    .. dropdown:: Resampling Algorithms

        ::

            self.reproject(..., *, resampling)

        Specifies the interpolation algorithm used for resampling. The default is nearest-neighbor interpolation. Other options include bilinear, cubic, cubic-spline, Lanczos-windowed, average, and mode resampling. Additional algorithms may be available depending on your GDAL installation. See the rasterio documentation for additional details on resampling algorithms and their requirements: `Resampling Algorithms <https://rasterio.readthedocs.io/en/stable/api/rasterio.enums.html#rasterio.enums.Resampling>`_
    

    .. dropdown:: Computational Performance

        ::

            self.reproject(..., *, num_threads)
            self.reproject(..., *, warp_mem_limit)

        Specify the number of worker threads and/or memory limit when reprojecting a raster. Reprojection can be computationally expensive, but increasing the number of workers and memory limit can speed up this process. These options are passed directly to rasterio, which uses them to implement the reprojection. Note that the units of warp_mem_limit are MB. By default, uses 1 worker and 64 MB.

    :Inputs: * **template** (*Raster*) -- A template Raster that defines the CRS, resolution, and grid alignment of the reprojected raster.
            * **crs** (*rasterio.coords.CRS*) -- The CRS to use for reprojection. Overrides the template CRS
            * **transform** (*affine.Affine*) -- The transform used to determe the resolution and grid alignment of the reprojection. Overrides the template transform.
            * **nodata** (*scalar*) -- A NoData value for rasters that do not already have a NoData value 
            * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
            * **resampling** (*str*) -- The resampling interpolation algorithm to use. Options include 'nearest' (default), 'bilinear', 'cubic', 'cubic_spline', 'lanczos', 'average', and 'mode'. Depending on the GDAL installation, the following options may also be available: 'max', 'min', 'med', 'q1', 'q3', 'sum', and 'rms'.
            * **num_threads** (*int*) -- The number of worker threads used to reproject the raster
            * **warp_mem_limit** (*float*) -- The working memory limit (in MB) used to reproject


.. _pfdf.raster.Raster.clip:

.. py:method:: Raster.clip(self, bounds = None, *, left = None, bottom = None, right = None, top = None, nodata = None, casting = "safe")

    Clips a raster to the indicated bounds

    .. dropdown:: Clip

        ::

            self.clip(bounds)

        Clips a raster to the spatial bounds of a second raster. If a clipping bound does not align with the edge of a pixel, clips the bound to the nearest pixel edge. Both rasters must have the same CRS - if either raster does not have a CRS, then they are assumed to be the same. Similarly, if either raster does not have a transform, then the two rasters are assumed to have the same transform.

        If the clipping bounds include areas outside the current raster, then pixels in these areas are set to the raster's NoData value. Raises an error if this occurs, but the raster does not have a NoData value. (And see below for a syntax to resolve this).

    .. dropdown:: Specific Edges

        ::

            self.clip(..., *, left)
            self.clip(..., *, bottom)
            self.clip(..., *, right)
            self.clip(..., *, top)

        Specifies the clipping bounds for a particular edge of the raster. The "bounds" input is not required if at least one of these keyword options is provided. If the "bounds" input is not provided, then any unspecified edges are set to their current bounds, so are not clipped. If "bounds" is provided, then any keyword bounds will take priority over the bounds of the clipping raster. As with the "bounds" input, keyword bounds must align with the current raster's grid.

        Keyword bounds must also match the orientation of the current raster. For example, if the raster's left spatial coordinate is less than its right coordinate, then the left clipping bound must be less than the right clipping bound. But if the raster's left spatial coordinate is greater than its right coordinate, then the left clipping bound must be greater than the right clipping bound. Same for the top and bottom edges.

    .. dropdown:: Specify Missing NoData

        ::

            self.clip(..., *, nodata)
            self.clip(..., *, nodata, casting)

        Specfies a NoData value to use when clipping a raster outside of its original bounds. You can only provide this option if the raster does not already have a NoData value, otherwise raises an Exception. The NoData value must be castable to the dtype of the raster being reprojected. By default, only safe casting is allowed. Use the casting option to enable different casting rules.

    :Inputs: * **bounds** (*Raster*) -- A second raster whose bounds will be used to clip the current raster
             * **left** (*scalar*) -- The bound for the left edge of the clipped raster
             * **right** (*scalar*) -- The bound for the right edge of the clipped raster
             * **bottom** (*scalar*) -- The bound for the bottom edge of the clipped raster
             * **top** (*scalar*) -- The bound for the top edge of the clipped raster
             * **nodata** (*scalar*) -- A NoData value for rasters that do not have a NoData value
             * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the Raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
