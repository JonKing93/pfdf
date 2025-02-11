RasterMetadata Class
====================

.. _pfdf.raster.RasterMetadata:

.. py:class:: RasterMetadata
    :module: pfdf.raster

    The *RasterMetadata* class is used to load and manage metadata for raster datasets, without loading the raster's data array into memory.

    .. dropdown:: Properties

        .. list-table::
            :header-rows: 1

            * - Property
              - Description
            * -
              -
            * - **Shape**
              -
            * - shape           
              - The shape of the data array
            * - nrows           
              - The number of rows in the data array
            * - height          
              - An alias for nrows
            * - ncols           
              - The number of columns in the data array
            * - width           
              - An alias for ncols
            * -
              -
            * - **Data Array**
              -
            * - dtype           
              - The numpy dtype of the data array
            * - nodata          
              - The NoData value
            * - name            
              - An identifying name for the raster dataset
            * - nbytes          
              - Total number of bytes required by the data array
            * -
              -
            * - **CRS**
              -
            * - crs             
              - The coordinate reference system
            * - crs_units       
              - The unit systems used along the CRS's X and Y axes
            * - crs_units_per_m 
              - The number of CRS units per meter along the X and Y axes
            * - utm_zone        
              - The CRS of the best UTM zone for the raster's center
            * -
              -
            * - **Transform**
              -
            * - transform       
              - A Transform object for the raster
            * - affine          
              - An affine.Affine object for the raster
            * -
              -
            * - **Bounding Box**
              -
            * - bounds          
              - A BoundingBox object for the raster
            * - left            
              - The spatial coordinate of the raster's left edge
            * - right           
              - The spatial coordinate of the raster's right edge
            * - top             
              - The spatial coordinate of the raster's top edge
            * - bottom          
              - The spatial coordinate of the raster's bottom edge
            * - center          
              - The X, Y coordinate of the raster's center
            * - center_x        
              - The X coordinate of the raster's center
            * - center_y        
              - The Y coordinate of the raster's center
            * - orientation     
              - The Cartesian quadrant containing the raster's bounding box

    .. dropdown:: Methods
        
        .. list-table::
            :header-rows: 1

            * - Method
              - Description
            * -
              -
            * - **Object Creation**
              - 
            * - :ref:`__init__ <pfdf.raster.RasterMetadata.__init__>`
              - Creates a RasterMetadata object for input values
            * - :ref:`from_file <pfdf.raster.RasterMetadata.from_file>`
              - Returns a RasterMetadata object for a file-based raster dataset
            * - :ref:`from_url <pfdf.raster.RasterMetadata.from_url>`
              - Returns a RasterMetadata object for the raster at the indicated URL
            * - :ref:`from_rasterio <pfdf.raster.RasterMetadata.from_rasterio>`
              - Returns a RasterMetadata object for a rasterio.DatasetReader
            * - :ref:`from_pysheds <pfdf.raster.RasterMetadata.from_pysheds>`
              - Returns a RasterMetadata object for a pysheds.sgrid.Raster object
            * - :ref:`from_array <pfdf.raster.RasterMetadata.from_array>`
              - Returns a RasterMetadata object for a numpy array
            * -
              -
            * - **Vector Features**
              - 
            * - :ref:`from_points <pfdf.raster.RasterMetadata.from_points>`
              - Creates a RasterMetadata object for a Point or MultiPoint feature file
            * - :ref:`from_polygons <pfdf.raster.RasterMetadata.from_polygons>`
              - Creates a RasterMetadata object for a Polygon or MultiPolygon feature file
            * -
              -
            * - **Pixel Geometries**
              - 
            * - :ref:`dx <pfdf.raster.RasterMetadata.dx>`
              - Returns the change in X coordinate when moving one pixel right
            * - :ref:`dy <pfdf.raster.RasterMetadata.dy>`
              - Returns the change in Y coordinate when moving one pixel down
            * - :ref:`resolution <pfdf.raster.RasterMetadata.resolution>`
              - Returns pixel resolution along the X and Y axes
            * - :ref:`pixel_area <pfdf.raster.RasterMetadata.pixel_area>`
              - Returns the area of a pixel
            * - :ref:`pixel_diagonal <pfdf.raster.RasterMetadata.pixel_diagonal>`
              - Returns the length of a pixel diagonal
            * -
              -
            * - **Comparisons**
              - 
            * - :ref:`__eq__ <pfdf.raster.RasterMetadata.__eq__>`
              - True if another input is a RasterMetadata object with the same metadata
            * - :ref:`isclose <pfdf.raster.RasterMetadata.isclose>`
              - True if another input is a RasterMetadata object with similar metadata
            * -
              -
            * - **IO**
              - 
            * - :ref:`__repr__ <pfdf.raster.RasterMetadata.__repr__>`
              - Returns a string representing the metadata
            * - :ref:`todict <pfdf.raster.RasterMetadata.todict>`
              - Returns a dict representing the metadata
            * - :ref:`copy <pfdf.raster.RasterMetadata.copy>`
              - Returns a copy of the current metadata object
            * -
              -
            * - **Updated Metadata**
              - 
            * - :ref:`update <pfdf.raster.RasterMetadata.update>`
              - Returns a copy of the current metadata with updated fields
            * - :ref:`as_bool <pfdf.raster.RasterMetadata.as_bool>`
              - Returns updated metadata suitable for a boolean data array
            * - :ref:`ensure_nodata <pfdf.raster.RasterMetadata.ensure_nodata>`
              - Returns updated metadata guaranteed to have a NoData value
            * -
              -
            * - **Preprocessing**
              - 
            * - :ref:`__getitem__ <pfdf.raster.RasterMetadata.__getitem__>`
              - Returns a copy of the current metadata for the indexed portion of a data array
            * - :ref:`fill <pfdf.raster.RasterMetadata.fill>`
              - Returns metadata without a NoData value
            * - :ref:`buffer <pfdf.raster.RasterMetadata.buffer>`
              - Returns updated metadata for a buffered raster
            * - :ref:`clip <pfdf.raster.RasterMetadata.clip>`
              - Returns updated metadata for a clipped raster
            * - :ref:`reproject <pfdf.raster.RasterMetadata.reproject>`
              - Returns updated metadata for a reprojected raster

----

Properties
----------

Shape
+++++

.. py:property:: RasterMetadata.shape
    
    The shape of the data array

.. py:property:: RasterMetadata.nrows
    
    The number of rows in the data array

.. py:property:: RasterMetadata.height
    
    An alias for nrows

.. py:property:: RasterMetadata.ncols
    
    The number of columns in the data array

.. py:property:: RasterMetadata.width
    
    An alias for ncols


Data Array
++++++++++

.. py:property:: RasterMetadata.dtype
    
    The numpy dtype of the data array

.. py:property:: RasterMetadata.nodata
    
    The NoData value

.. py:property:: RasterMetadata.name
    
    An identifying name for the raster dataset

.. py:property:: RasterMetadata.nbytes
    
    Total number of bytes required by the data array


CRS
+++

.. py:property:: RasterMetadata.crs
    
    The coordinate reference system

.. py:property:: RasterMetadata.crs_units
    
    The unit systems used along the CRS's X and Y axes

.. py:property:: RasterMetadata.crs_units_per_m
    
    The number of CRS units per meter along the X and Y axes

.. py:property:: RasterMetadata.utm_zone
    
    The CRS of the best UTM zone for the raster's center


Transform
+++++++++

.. py:property:: RasterMetadata.transform
    
    A Transform object for the raster

.. py:property:: RasterMetadata.affine
    
    An affine.Affine object for the raster


Bounding Box
++++++++++++

.. py:property:: RasterMetadata.bounds
    
    A BoundingBox object for the raster

.. py:property:: RasterMetadata.left
    
    The spatial coordinate of the raster's left edge

.. py:property:: RasterMetadata.right
    
    The spatial coordinate of the raster's right edge

.. py:property:: RasterMetadata.top
    
    The spatial coordinate of the raster's top edge

.. py:property:: RasterMetadata.bottom
    
    The spatial coordinate of the raster's bottom edge

.. py:property:: RasterMetadata.center
    
    The X, Y coordinate of the raster's center

.. py:property:: RasterMetadata.center_x
    
    The X coordinate of the raster's center

.. py:property:: RasterMetadata.center_y
    
    The Y coordinate of the raster's center

.. py:property:: RasterMetadata.orientation
    
    The Cartesian quadrant containing the raster's bounding box

----

Object Creation
---------------

.. _pfdf.raster.RasterMetadata.__init__:

.. py:method:: RasterMetadata.__init__(self, shape = None, *, dtype = None, nodata = None, casting = "safe", crs = None, transform = None, bounds = None, name = None)

    Creates a new RasterMetadata object

    .. dropdown:: Shape

        ::

            RasterMetadata(shape)

        Creates a new RasterMetadata object. The shape should be the shape of a raster's data array. This must be a vector of two positive integers. Defaults to (0, 0) if not provided.

    .. dropdown:: Array Metadata

        ::

            RasterMetadata(..., *, dtype)
            RasterMetadata(..., *, nodata)
            RasterMetadata(..., *, dtype, nodata, casting)

        Specifies metadata fields that describe a raster's data array. The dtype input should be convertible to a real-valued numpy dtype, and the NoData value should be a scalar value. If you only provide a nodata value, then the dtype will be inherited from that value. If you provide both the dtype and nodata inputs, then the nodata value will be cast to the indicated dtype. By default, requires safe casting, but see the "casting" input to use other casting rules.

    .. dropdown:: Spatial Metadata

        ::

            RasterMetadata(..., *, crs)
            RasterMetadata(..., *, transform)
            RasterMetadata(..., *, bounds)

        Specifies CRS, affine transform, and/or bounding box metadata. You may only provide one of the "transform" and "bounds" options - these two inputs are mutually exclusive. You also cannot provide "bounds" metadata when the array shape includes 0 values. This is because the resulting Transform would require infinite resolution, which is invalid.

        If a transform/bounds has a CRS that differs from the "crs" input, then the transform/bounds will be reprojected. If you do not provide a crs, then the metadata will inherit any CRS from the transform/bounds. Note that the various preprocessing methods all require the RasterMetadata object to have a transform or bounding box. The "buffer" method also require a CRS when using metric or imperial units.

    .. dropdown:: Name

        ::

            RasterMetadata(..., *, name)

        A string specifying an identifying name. Defaults to "raster".

    :Inputs:
        * **shape** (*(int, int)*) -- The shape of the raster's data array. A vector of 2 positive integers. Defaults to (0,0) if not set
        * **dtype** (*type*) -- The dtype of a raster data array
        * **nodata** (*scalar*) -- A NoData value. Will be cast to the dtype if a dtype is provided
        * **casting** (*str*) -- The casting rule to use when casting the NoData value to the dtype. Options are "safe" (default), "same_kind", "no", "equiv", and "unsafe"
        * **crs** (*CRS-like*) -- A coordinate reference system
        * **transform** (*Transform-like*) -- An affine transform
        * **bounds** (*BoundingBox-like*) -- A bounding box
        * **name** (*str*) -- A string identifying the dataset. Defaults to "raster"

    :Outputs:
        *RasterMetadata* -- The new RasterMetadata object




.. _pfdf.raster.RasterMetadata.from_url:

.. py:method:: RasterMetadata.from_url(url, name = None, *, check_status = True, timeout = 10, bounds = None, require_overlap = True, band = 1, isbool = False, ensure_nodata = True, default_nodata = None, casting = "safe", driver = None)

    Returns a RasterMetadata object for the raster at the indicated URL

    .. dropdown:: Build from URL

        ::

            RasterMetadata.from_url(url)

        Builds a RasterMetadata object for the file at the given URL. Ultimately, this method uses rasterio (and thereby GDAL) to open URLs. As such, many common URL schemes are supported, including: http(s), ftp, s3, (g)zip, tar, etc. Note that although the local "file" URL scheme is theoretically supported, we recommend instead using :ref:`RasterMetadata.from_file <pfdf.raster.RasterMetadata.from_file>` to build metadata from local file paths.

        If a URL follows an http(s) scheme, uses the "requests" library to check the URL before loading metadata. This check is optional (see below to disable), but typically provides more informative error messages when connection problems occur. Note that the check assumes the URL supports HEAD requests, as is the case for most http(s) URLs. All other URL schemes are passed directly to rasterio.

        After loading the URL, this method behaves nearly identically to the :ref:`RasterMetadata.from_file <pfdf.raster.RasterMetadata.from_file>` command. Please see that command's documentation for details on the following options: name, bounds, band, isbool, ensure_nodata, default_nodata, casting, and driver.

    .. dropdown:: HTTP(S) Options

        ::

            RasterMetadata.from_url(..., *, timeout)
            RasterMetadata.from_url(..., *, check_status=False)

        Options that affect the checking of http(s) URLs. Ignored if the URL does not have an http(s) scheme. The "timeout" option specifies a maximum time in seconds for connecting to the remote server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case the URL check will never timeout. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

        You can disable the http(s) URL check by setting  check_status=False. In this case, the URL is passed directly to rasterio, as like all other URL schemes. This can be useful if the URL does not support HEAD requests, or to limit server queries when you are certain the URL and connection are valid.

    :Inputs:
        * **url** (*str*) -- The URL for a file-based raster dataset
        * **name** (*str*) -- An optional name for the metadata. Defaults to "raster"
        * **timeout** (*scalar | vector*) -- A maximum time in seconds to establish a connection with an http(s) server
        * **check_status** (*bool*) -- True (default) to use "requests.head" to validate http(s) URLs. False to disable this check.
        * **bounds** (*BoundingBox-like*) -- A BoundingBox-like object indicating a subset of the saved raster whose metadata should be determined
        * **require_overlap** (*bool*) -- True (default) to raise an error if the bounds do not overlap the raster by at least one pixel. False to not raise an error.
        * **band** (*int*) -- The raster band from which to read the dtype. Uses 1-indexing and defaults to 1
        * **isbool** (*bool*) -- True to set dtype to bool and NoData to False. If False (default), preserves the original dtype and NoData.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.
        * **driver** (*str*) -- A file format to use to read the raster, regardless of extension

    :Outputs:
        *RasterMetadata* -- The metadata object for the raster



.. _pfdf.raster.RasterMetadata.from_file:

.. py:method:: RasterMetadata.from_file(path, name = None, *, bounds = None, require_overlap = True, band = 1, isbool = False, ensure_nodata = True, default_nodata = None, casting = "safe", driver = None)

    Returns the RasterMetadata object for a file-based raster

    .. dropdown:: Load from file

        ::

            RasterMetadata.from_file(path)
            RasterMetadata.from_file(path, name)

        Returns the RasterMetadata object for the raster in the indicated file. Raises a FileNotFoundError if the file cannot be located. By default, records the dtype of band 1, but see below for additional options. The "name" input can be used to provide an optional name for the metadata, defaults to "raster" if unset. By default, if the file does not have a NoData value, then selects a default value based on the dtype. See below for other NoData options.

        Also, by default the method will attempt to use the file extension to detect the file format driver used to read data from the file. Raises an Exception if the driver cannot be determined, but see below for options to explicitly set the driver. You can also use::

            >>> pfdf.utils.driver.extensions('raster')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: Bounding Box

        ::

            RasterMetadata.from_file(..., *, bounds)
            RasterMetadata.from_file(..., *, bounds, require_overlap=False)

        Returns the RasterMetadata object for a bounded subset of the saved dataset. The "bounds" input indicates a rectangular portion of the saved dataset whose metadata should be determined. If the window extends beyond the bounds of the dataset, then the dataset will be windowed to the relevant bound, but no further. The window may be a BoundingBox, Raster, RasterMetadata, or a list/tuple/dict convertible to a BoundingBox object.

        By default, raises a ValueError if the bounds do not overlap the dataset for at least one pixel. Set require_overlap=False to disable this error. In this case, the shape metadata for non-overlapping bounds will contain zeros. We caution that the Transform and BoundingBox are ill-defined when this occurs.

    .. dropdown:: Band

        ::

            RasterMetadata.from_file(..., *, band)

        Specify the raster band to use to determine the dtype. Raster bands use 1-indexing (and not the 0-indexing common to Python). Raises an error if the band does not exist.

    .. dropdown:: Boolean Raster

        :: 

            RasterMetadata.from_file(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The output metadata object will have a bool dtype, and its NoData value will be set to False.

    .. dropdown:: Default NoData

        ::

            RasterMetadata.from_file(..., *, default_nodata)
            RasterMetadata.from_file(..., *, default_nodata, casting)
            RasterMetadata.from_file(..., *, ensure_nodata=False)

        Specifies additional options for NoData values. By default, if the raster file does not have a NoData value, then this routine will set a default NoData value based on the dtype of the raster. Set ensure_nodata=False to disable this behavior. Alternatively, you can use the "default_nodata" option to specify a different default NoData value. The default nodata value should be safely castable to the raster dtype, or use the "casting" option to specify other casting rules.

    .. dropdown:: Specify File Format

        ::

            RasterMetadata.from_file(..., *, driver)

        Specify the file format driver to use for reading the file. Uses this driver regardless of the file extension. You can also call::

            >>> pfdf.utils.driver.rasters()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on rasterio (which in turn uses GDAL/OGR) to read raster files, and so additional drivers may work if their associated build requirements are met. A complete list of driver build requirements is available here: `Raster Drivers <https://gdal.org/drivers/raster/index.html>`_

    :Inputs:
        * **path** (*str | Path*) -- A path to a file-based raster dataset
        * **name** (*str*) -- An optional name for the metadata. Defaults to "raster"
        * **bounds** (*BoundingBox-like*) -- A BoundingBox-like object indicating a subset of the saved raster whose metadata should be determined
        * **require_overlap** (*bool*) -- True (default) to raise an error if the bounds do not overlap the raster by at least one pixel. False to not raise an error.
        * **band** (*int*) -- The raster band from which to read the dtype. Uses 1-indexing and defaults to 1
        * **isbool** (*bool*) -- True to set dtype to bool and NoData to False. If False (default), preserves the original dtype and NoData.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.
        * **driver** (*str*) -- A file format to use to read the raster, regardless of extension

    :Outputs:
        *RasterMetadata* -- The metadata object for the raster





.. _pfdf.raster.RasterMetadata.from_rasterio:

.. py:method:: RasterMetadata.from_rasterio(reader, name = None, *, band = 1, isbool = False, bounds = None, ensure_nodata = True, default_nodata = None, casting = "safe")

    Builds a new RasterMetadata object from a rasterio.DatasetReader

    .. dropdown:: Create Raster

        ::

            RasterMetadata.from_rasterio(reader)
            RasterMetadata.from_rasterio(reader, name)

        Creates a new RasterMetadata object from a rasterio.DatasetReader. Raises a FileNotFoundError if the associated file no longer exists. Uses the file format driver associated with the object to read the raster from file. By default, records the dtype for band 1. The "name" input specifies an optional name for the new metadata. Defaults to "raster" if unset.

    .. dropdown:: Bounding Box

        ::

            RasterMetadata.from_rasterio(..., *, bounds)

        Returns the RasterMetadata object for a bounded subset of the saved dataset. The "bounds" input indicates a rectangular portion of the saved dataset whose metadata should be determined. If the window extends beyond the bounds of the dataset, then the dataset will be windowed to the relevant bound, but no further. The window may be a BoundingBox, Raster, RasterMetadata, or a list/tuple/dict convertible to a BoundingBox object.

    .. dropdown:: Band

        ::

            RasterMetadata.from_rasterio(..., band)

        Specify the raster band to use to determine the dtype. Raster bands use 1-indexing (and not the 0-indexing common to Python). Raises an error if the band does not exist.

    .. dropdown:: Boolean Raster

        ::

            RasterMetadata.from_rasterio(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The output metadata object will have a bool dtype, and its NoData value will be set to False.

    .. dropdown:: Default NoData

        ::

            RasterMetadata.from_rasterio(..., *, default_nodata)
            RasterMetadata.from_rasterio(..., *, default_nodata, casting)
            RasterMetadata.from_rasterio(..., *, ensure_nodata=False)

        Specifies additional options for NoData values. By default, if the raster file does not have a NoData value, then this routine will set a default NoData value based on the dtype of the raster. Set ensure_nodata=False to disable this behavior. Alternatively, you can use the "default_nodata" option to specify a different default NoData value. The default nodata value should be safely castable to the raster dtype, or use the "casting" option to specify other casting rules.

    :Inputs:
        * **reader** (*rasterio.DatasetReader*) -- A rasterio.DatasetReader associated with a raster dataset
        * **name** (*str*) -- An optional name for the metadata. Defaults to "raster"
        * **bounds** (*BoundingBox-liker*) -- A BoundingBox-like object indicating a subset of the saved raster whose metadata should be determined
        * **band** (*int*) -- The raster band from which to read the dtype. Uses 1-indexing and defaults to 1
        * **isbool** (*bool*) -- True to set dtype to bool and NoData to False. If False (default), preserves the original dtype and NoData.
        * **ensure_nodata** (*bool*) -- True (default) to assign a default NoData value based on the raster dtype if the file does not record a NoData value. False to leave missing NoData as None.
        * **default_nodata** (*scalar*) -- The default NoData value to use if the raster file is missing one. Overrides any default determined from the raster's dtype.
        * **casting** (*str*) -- The casting rule to use when converting the default NoData value to the raster's dtype.

    :Outputs:
        *RasterMetadata* -- The metadata object for the raster



.. _pfdf.raster.RasterMetadata.from_pysheds:

.. py:method:: RasterMetadata.from_pysheds(sraster, name = None, isbool = False)

    Creates a RasterMetadata from a pysheds.sview.Raster object

    .. dropdown:: Create Raster

        ::

            RasterMetadata.from_pysheds(sraster)
            RasterMetadata.from_pysheds(sraster, name)

        Creates a new RasterMetadata object from a pysheds.sview.Raster object. Inherits the nodata values, CRS, and transform of the pysheds Raster. The "name" input specifies an optional name for the metadata. Defaults to "raster" if unset.

    .. dropdown:: Boolean Raster

        ::

            RasterMetadata.from_pysheds(..., *, isbool=True)

        Indicates that the raster represents a boolean array, regardless of the dtype of the file data values. The metadata object will have a bool dtype, and its NoData value will be set to False.

    :Inputs:
        * **sraster** (*pysheds.sview.Raster*) -- The pysheds.sview.Raster object used to create the RasterMetadata
        * **name** (*str*) -- An optional name for the metadata. Defaults to "raster"
        * **isbool** (*bool*) -- True to set dtype to bool and NoData to False. If False (default), preserves the original dtype and NoData.

    :Outputs:
        *RasterMetadata* -- The new metadata object




.. _pfdf.raster.RasterMetadata.from_array:

.. py:method:: RasterMetadata.from_array(array, name = None, *, nodata = None, casting = "safe", crs = None, transform = None, bounds = None, spatial = None, isbool = False, ensure_nodata = True)

    Create a RasterMetadata object from a numpy array

    .. dropdown:: Create Raster

        ::

            RasterMetadata.from_array(array, name)

        Creates a RasterMetadata object from a numpy array. Infers a NoData value from the dtype of the array. The Transform and CRS will both be None. The "name" input specifies an optional name for the metadata. Defaults to "raster" if unset.

    .. dropdown:: NoData

        ::

            RasterMetadata.from_array(..., *, nodata)
            RasterMetadata.from_array(..., *, nodata, casting)

        Specifies a NoData value for the metadata. The NoData value will be cast to the same dtype as the array. Raises a TypeError if the NoData value cannot be safely cast to this dtype. Use the casting option to change this behavior. Casting options are as follows:

        * 'no': The data type should not be cast at all
        * 'equiv': Only byte-order changes are allowed
        * 'safe': Only casts which can preserve values are allowed
        * 'same_kind': Only safe casts or casts within a kind (like float64 to float32)
        * 'unsafe': Any data conversions may be done

    .. dropdown:: Spatial Template

        ::

            RasterMetadata.from_array(..., *, spatial)

        Specifies a Raster or RasterMetadata object to use as a default spatial metadata template. By default, transform and crs properties from the template will be copied to the new raster. However, see below for a syntax to override this behavior.

    .. dropdown:: Spatial Keywords

        ::

            RasterMetadata.from_array(..., *, crs)
            RasterMetadata.from_array(..., *, transform)
            RasterMetadata.from_array(..., *, bounds)

        Specifies the crs, transform, and/or bounding box for the metadata. If used in conjunction with the "spatial" option, then any keyword options will take precedence over the metadata in the spatial template. You may only provide one of the transform/bounds inputs - raises an error if both are provided. If the CRS of a Transform or BoundingBox differs from the template/keyword CRS, then the Transform or BoundingBox is reprojected to match the other CRS.

    .. dropdown:: Boolean Raster

        ::

            RasterMetadata.from_array(..., *, isbool=True)

        Indicates that the metadata represents a boolean array, regardless of the dtype of the array. The newly created metadata will have a bool dtype and values, and its NoData value will be set to False.

    .. dropdown:: Default NoData

        ::

            RasterMetadata.from_array(..., *, ensure_nodata=False)

        Disables the use of default NoData values. The new metadata's nodata value will be None unless the "nodata" option is specified.

    :Inputs:
        * **array** (*np.ndarray*) -- A 2D numpy array whose data values represent a raster
        * **name** (*str*) -- An optional name for the metadata. Defaults to "raster"
        * **nodata** (*scalar*) -- A NoData value for the raster metadata
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **spatial** (*Raster | RasterMetadata*) -- A Raster or RasterMetadata object to use as a default spatial metadata template
        * **crs** (*CRS-like*) -- A coordinate reference system
        * **transform** (*Transform-like*) -- An affine transformation for the raster. Mutually exclusive with the "bounds" input
        * **bounds** (*BoundingBox-like*) -- A BoundingBox for the raster. Mutually exclusive with the "transform" input
        * **isbool** (*bool*) -- True to set dtype to bool and NoData to False. If False (default), preserves the original dtype and NoData.
        * **ensure_nodata** (*bool*) -- True (default) to infer a default NoData value from the array's dtype when a NoData value is not provided. False to disable this behavior.

    :Outputs:
        *RasterMetadata* -- A metadata object for the array-based raster dataset





----

From Vector Features
--------------------

.. _pfdf.raster.RasterMetadata.from_points:

.. py:method:: RasterMetadata.from_points(path, field = None, *, dtype = None, field_casting = "safe", nodata = None, casting = "safe", operation = None, bounds = None, resolution = 10, units = "meters", layer = None, driver = None, encoding = None)

    Creates a RasterMetadata from a set of point/multi-point features

    .. dropdown:: From Point Features

        ::

            RasterMetadata.from_points(path)

        Returns metadata derived from the input point features. The contents of the inpu MultiPoint geometries (and see below if the file contains multiple layers). The CRS of the output metadata is inherited from the input feature file. The default resolution of the output metadata is 10 meters, although see below to specify other resolutions. The bounds of the metadata will be the minimal bounds required to contain all input points at the indicated resolution.

        If you do not specify an attribute field, then the metadata will have a boolean dtype. See below to build the metadata from an data property field instead.

        By default, this method will attempt to guess the intended file format and encoding based on the path extension. Raises an error if the format or encoding cannot be determined. However, see below for syntax to specify the driver and encoding, regardless of extension. You can also use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: From Data Field

        ::

            RasterMetadata.from_points(path, field)
            RasterMetadata.from_points(..., *, dtype)
            RasterMetadata.from_points(..., *, dtype, field_casting)

        Builds the metadata using one of the data property fields for the point features. The indicated data field must exist in the data properties, and must have an int or float type. By default, the dtype of the output raster will be int32 or float64, as appropriate for the data field type. Use the "dtype" option to specify a different dtype instead. In this case, the data field values will be cast to the indicated dtype before being used to build the metadata. By default, field values must be safely castable to the indicated dtype. Use the "field_casting" option to select different casting rules. The "dtype" and "field_casting" options are ignored if you do not specify a field.

    .. dropdown:: NoData

        ::

            RasterMetadata.from_points(..., field, *, nodata)
            RasterMetadata.from_points(..., field, *, nodata, casting)

        Specifies the NoData value to use when building the metadata from a data attribute field. By default, the NoData value must be safely castable to the dtype of the output raster. Use the "casting" option to select other casting rules. NoData options are ignored if you do not specify a field.

    .. dropdown:: Field Operation

        ::

            RasterMetadata.from_points(..., field, *, operation)

        Applies the indicated function to the data field values. The input function should accept one numeric input, and return one real-valued numeric output. Useful when data field values require a conversion. For example, you could use the following to scale Point values by a factor of 100::

            def times_100(value):
                return value * 100

            RasterMetadata.from_points(..., field, operation=times_100)

        Values are converted before they are validated against the "dtype" and "field_casting" options, so you can also use an operation to implement a custom conversion from data values to the output raster dtype. The operation input is ignored if you do not specify a field.

    .. dropdown:: Windowed Reading

        ::

            RasterMetadata.from_points(..., *, bounds)

        Only uses point features contained within the indicated bounds. The returned metadata is also clipped to these bounds. This option can be useful when you only need data from a subset of a much larger Point dataset.

    .. dropdown:: Resolution

        ::

            RasterMetadata.from_points(path, *, resolution)
            RasterMetadata.from_points(path, *, resolution, units)

        Specifies the resolution of the output raster. The resolution may be a scalar positive number, a 2-tuple of such numbers, a Transform, a Raster, or a RasterMetadata object. If a scalar, indicates the resolution of the output raster for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution and the second element is the Y-axis. If a Raster/RasterMetadata/Transform, uses the associated resolution. Raises an error if a Raster/RasterMetadata does not have a Transform.

        If the resolution input does not have an associated CRS, then the resolution values are interpreted as meters. Use the "units" option to interpret resolution values in different units instead. Supported units include: "base" (CRS/Transform base unit), "kilometers", "feet", and "miles". Note that this option is ignored if the input resolution has a CRS.

    .. dropdown:: Multiple Layers

        ::

            RasterMetadata.from_points(..., *, layer)

        Use this option when the input feature file contains multiple layers. The "layer" input indicates the layer holding the relevant Point geometries. This may be either an integer index, or the (string) name of a layer in the input file.

    .. dropdown:: File Format Driver

        ::

            RasterMetadata.from_points(..., *, driver)
            RasterMetadata.from_points(..., *, encoding)

        Specifies the file format driver and encoding used to read the Points feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to read vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_

    :Inputs:
        * **path** (*str | Path*) -- The path to a Point or MultiPoint feature file
        * **field** (*str*) -- The name of a data property field used to set pixel values. The data field must have an int or float type.
        * **dtype** (*type*) -- The dtype of the output metadata when building from a data field. Defaults to int32 or float64, as appropriate.
        * **field_casting** (*str*) -- The type of data casting allowed to occur when converting data field values to a specified output dtype. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **nodata** (*scalar*) -- The NoData value for the metadataa
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **operation** (*Callable*) -- A function that should be applied to data field values before they are used to build the metadata. Should accept one numeric input and return one real-valued numeric input.
        * **bounds** (*BoundingBox-like*) -- A bounding box indicating the subset of point features that should be used to create the metadata.
        * **resolution** (*scalar | vector | Transform | Raster*) -- The desired resolution of the output metadata
        * **units** (*str*) -- Specifies the units of the resolution when the resolution input does not have a CRS. Options include** (**) -- "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet", and "miles"
        * **layer** (*int | str*) -- The layer of the input file from which to load the point geometries
        * **driver** (*str*) -- The file-format driver to use to read the Point feature file
        * **encoding** (*str*) -- The encoding of the Point feature file

    :Outputs:
        *RasterMetadata* -- The point-derived metadata



.. _pfdf.raster.RasterMetadata.from_polygons:

.. py:method:: RasterMetadata.from_polygons(path, field = None, *, dtype = None, field_casting = "safe", nodata = None, casting = "safe", operation = None, bounds = None, resolution = 10, units = "meters", layer = None, driver = None, encoding = None)

    Creates RasterMetadata from a set of polygon/multi-polygon features

    .. dropdown:: From Polygon Features

        ::

            RasterMetadata.from_polygons(path)

        Returns metadata derived from the input polygon features. The contents of the input file should resolve to a FeatureCollection of Polygon and/or MultiPolygon geometries (and see below if the file contains multiple layers). The CRS of the metadata is inherited from the input feature file. The default resolution of the metadata is 10 meters, although see below to specify other resolutions. The bounds will be the minimal bounds required to contain all input polygons at the indicated resolution.

        If you do not specify an attribute field, then the returned metadata will have a boolean dtype. See below to build the raster from an data property field instead.

        By default, this method will attempt to guess the intended file format and encoding based on the path extension. Raises an error if the format or encoding cannot be determined. However, see below for syntax to specify the driver and encoding, regardless of extension. You can also use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: From Data Field

        ::

            RasterMetadata.from_polygons(path, field)
            RasterMetadata.from_polygons(..., *, dtype)
            RasterMetadata.from_polygons(..., *, dtype, field_casting)

        Builds the metadata using one of the data property fields for the polygon features. The indicated data field must exist in the data properties, and must have an int or float type. By default, the dtype of the metadata will be int32 or float64, as appropriate. Use the "dtype" option to specify the metadata dtype instead. In this case, the data field values will be cast to the indicated dtype before being used to build the metadata. Note that only some numpy dtypes are supported for building metadata from polygons. Supported dtypes are: bool, int16, int32, uint8, uint16, uint32, float32, and float64. Raises an error if you select a different dtype.

        By default, field values must be safely castable to the indicated dtype. Use the "field_casting" option to select different casting rules. The "dtype" and "field_casting" options are ignored if you do not specify a field.

    .. dropdown:: NoData

        ::

            RasterMetadata.from_polygons(..., field, *, nodata)
            RasterMetadata.from_polygons(..., field, *, nodata, casting)

        Specifies the NoData value to use when building the metadata from a data attribute field. By default, the NoData value must be safely castable to the dtype of the output raster. Use the "casting" option to select other casting rules. NoData options are ignored if you do not specify a field.

    .. dropdown:: Field Operation

        ::

            RasterMetadata.from_polygons(..., field, *, operation)

        Applies the indicated function to the data field values and uses the output values to build the metadata. The input function should accept one numeric input, and return one real-valued numeric output. Useful when data field values require a conversion. For example, you could use the following to scale Polygon values by a factor of 100::

            def times_100(value):
                return value * 100

            RasterMetadata.from_polygons(..., field, operation=times_100)

        Values are converted before they are validated against the "dtype" and "field_casting" options, so you can also use an operation to implement a custom conversion from data values to the output raster dtype. The operation input is ignored if you do not specify a field.

    .. dropdown:: Windowed Reading

        ::

            RasterMetadata.from_polygons(..., *, bounds)

        Only uses polygon features that intersect the indicated bounds. The returned metadata is also clipped to these bounds. This option can be useful when you only need data from a subset of a much larger Polygon dataset.

    .. dropdown:: Resolution

        ::

            RasterMetadata.from_polygons(..., *, resolution)
            RasterMetadata.from_polygons(..., *, resolution, units)

        Specifies the resolution of the metadata. The resolution may be a scalar positive number, a 2-tuple of such numbers, a Transform, a Raster, or a RasterMetadata object. If a scalar, indicates the resolution of the output raster for both the X and Y axes. If a 2-tuple, the first element is the X-axis resolution and the second element is the Y-axis. If a Raster/RasterMetadata/Transform, uses the associated resolution. Raises an error if a Raster/RasterMetadata does not have a Transform.

        If the resolution input does not have an associated CRS, then the resolution values are interpreted as meters. Use the "units" option to interpret resolution values in different units instead. Supported units include: "base" (CRS/Transform base unit), "kilometers", "feet", and "miles". Note that this option is ignored if the input resolution has a CRS.

    .. dropdown:: Multiple Layers

        ::

            RasterMetadata.from_polygons(..., *, layer)

        Use this option when the input feature file contains multiple layers. The "layer" input indicates the layer holding the relevant Polygon geometries. This may be either an integer index, or the (string) name of a layer in the input file.

    .. dropdown:: File Format Driver

        ::

            RasterMetadata.from_polygons(..., *, driver)
            RasterMetadata.from_polygons(..., *, encoding)

        Specifies the file format driver and encoding used to read the polygon feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to read vector files, and so additional drivers may work if their associated build requirements are met. You can call::
    
            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Driver <https://gdal.org/drivers/vector/index.html>`_

    :Inputs:
        * **path** (*str | Path*) -- The path to a Polygon or MultiPolygon feature file
        * **field** (*str*) -- The name of a data property field used to set pixel values. The data field must have an int or float type.
        * **dtype** (*type*) -- The dtype of the output raster when building from a data field. Defaults to int32 or float64, as appropriate. Supported dtypes are** (**) -- bool, int16, int32, uint8, uint16, uint32, float32, and float64
        * **field_casting** (*str*) -- The type of data casting allowed to occur when converting data field values to a specified output dtype. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **nodata** (*scalar*) -- The NoData value for the metadata
        * **casting** (*str*) -- The type of data casting allowed to occur when converting a NoData value to the dtype of the raster. Options are "no", "equiv", "safe" (default), "same_kind", and "unsafe".
        * **operation** (*Callable*) -- A function that should be applied to data field values before they are used to build the raster. Should accept one numeric input and return one real-valued numeric input.
        * **bounds** (*BoundingBox-like*) -- A bounding box indicating the subset of polygon features that should be used to create the raster.
        * **resolution** (*scalar | vector | Transform | Raster*) -- The desired resolution of the metadata
        * **units** (*str*) -- Specifies the units of the resolution when the resolution input does not have a CRS. Options include** (**) -- "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet", and "miles"
        * **layer** (*int | str*) -- The layer of the input file from which to load the polygon geometries
        * **driver** (*str*) -- The file-format driver to use to read the Polygon feature file
        * **encoding** (*str*) -- The encoding of the Polygon feature file

    :Outputs:
        *RasterMetadata* -- The polygon-derived metadata




----

Pixel Geometries
----------------

.. _pfdf.raster.RasterMetadata.dx:

.. py:method:: RasterMetadata.dx(self, unit = "meters")

    Returns the change in the X-axis spatial coordinate when moving one pixel right

    ::

        self.dx()
        self.dx(units)

    Returns the change in X-axis spatial coordinate when moving one pixel to the right. By default, returns dx in meters. Use the "units" option to return dx in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return dx in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The change in X coordinate when moving one pixel right



.. _pfdf.raster.RasterMetadata.dy:

.. py:method:: RasterMetadata.dy(self, units = "meters")

    Returns the change in the Y-axis spatial coordinate when moving one pixel down

    ::

        self.dy()
        self.dy(units)

    Returns the change in Y-axis spatial coordinate when moving one pixel down. By default, returns dy in meters. Use the "units" option to return dy in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return dy in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The change in Y coordinate when moving one pixel down



.. _pfdf.raster.RasterMetadata.resolution:

.. py:method:: RasterMetadata.resolution(self, units = "meters")

    Returns the raster resolution

    ::

        self.resolution()
        self.resolution(units)

    Returns the raster resolution as a tuple with two elements. The first element is the X resolution, and the second element is Y resolution. Note that resolution is strictly positive. By default, returns resolution in meters. Use the "units" option to return resolution in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return resolution in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles"

    :Outputs:
        *float, float* -- The X and Y axis pixel resolution



.. _pfdf.raster.RasterMetadata.pixel_area:

.. py:method:: RasterMetadata.pixel_area(self, units = "meters")

    Returns the area of one pixel

    ::

        self.pixel_area()
        self.pixel_area(units)

    Returns the area of a raster pixel. By default, returns area in meters^2. Use the "units" option to return area in a different unit (squared). Supported units include: "base" (CRS/Transform base unit), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units to return resolution in. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The area of a raster pixel



.. _pfdf.raster.RasterMetadata.pixel_diagonal:

.. py:method:: RasterMetadata.pixel_diagonal(self, units = "meters")

    Returns the length of a pixel diagonal

    ::

        self.pixel_diagonal()
        self.pixel_diagonal(units)

    Returns the length of a pixel diagonal. By default, returns length in meters. Use the "units" option to return length in other units. Supported units include: "base" (base unit of the CRS/Transform), "kilometers", "feet", and "miles".

    :Inputs:
        * **units** (*str*) -- The units in which to return the length of a pixel diagonal. Options include: "base" (CRS/Transform base units), "meters" (default), "kilometers", "feet", and "miles"

    :Outputs:
        *float* -- The area of a raster pixel




----

Comparisons
-----------

.. _pfdf.raster.RasterMetadata.__eq__:

.. py:method:: RasterMetadata.__eq__(self, other)

    True if another object is a RasterMetadata object with matching metadata

    ::

        self == other

    True if the other input is a RasterMetadata with the same shape, dtype, nodata, crs, transform, and bounding box. Note that NaN NoData values are interpreted as equal. Also note that the metadata objects do not require the same name to test as equal.

    :Inputs:
        * **other** (*Any*) -- A second input being compared to the RasterMetadata object

    :Outputs:
        *bool* -- True if the second input is a RasterMetadata object with matching metadata. Otherwise False



.. _pfdf.raster.RasterMetadata.isclose:

.. py:method:: RasterMetadata.isclose(self, other, rtol = 1e-5, atol = 1e-8)

    True if two RasterMetadata objects are similar

    .. dropdown:: Check Similarity

        ::

            self.isclose(other)

        Tests if another RasterMetadata object has similar values to the current object. Tests the shape, dtype, nodata, crs, and transform. To test as True, the two objects must meet the following conditions:

        * shape, dtype, and nodata must be equal,
        * CRSs are compatible, and
        * Transform objects are similar

        To have compatible CRSs, the objects must have the same CRS or at least one CRS must be None. The Transform objects are tested by using ``numpy.allclose`` to compare dx, dy, left, and top values. The transforms are considered similar if ``numpy.allclose`` passes.

    .. dropdown:: Set Tolerance

        ::

            self.isclose(..., rtol, atol)

        Specify the relative and absolute tolerance for the numpy.allclose check. By default, uses a relative tolerance of 1E-5, and an absolute tolerance of 1E-8.

    :Inputs:
        * **other** (*RasterMetadata*) -- Another RasterMetadata object
        * **rtol** (*scalar*) -- The relative tolerance for transform field comparison. Defaults to 1E-5
        * **atol** (*scalar*) -- The absolute tolerance for transform field comparison. Defaults to 1E-8

    :Outputs:
        *bool* -- True if the other object is similar to the current object




----

IO
--

.. _pfdf.raster.RasterMetadata.__repr__:

.. py:method:: RasterMetadata.__repr__(self)

    Returns a string summarizing the raster metadata

    ::

        repr(self)
        str(self)

    Returns a string summarizing key information about the raster metadata.

    :Outputs:
        *str* -- A string summary of the raster metadata



.. _pfdf.raster.RasterMetadata.todict:

.. py:method:: RasterMetadata.todict(self)

    Returns a dict representation of the metadata object

    ::

        self.todict()

    Returns a dict representing the metadata object. The dict will have the following keys: "shape", "dtype", "nodata", "crs", "transform", "bounds", and "name".

    :Outputs:
        *dict* -- A dict representation of the metadata object




.. _pfdf.raster.RasterMetadata.copy:

.. py:method:: RasterMetadata.copy(self)

    Returns a copy of the current metadata object

    ::
        
        self.copy()

    :Outputs:
        *RasterMetadata* -- A copy of the current RasterMetadata object





----

Updated Metadata
----------------

.. _pfdf.raster.RasterMetadata.update:

.. py:method:: RasterMetadata.update(self, *, dtype = None, nodata = None, casting = "safe", crs = None, transform = None, bounds = None, shape = None, keep_bounds = False, name = None)

    Returns a RasterMetadata object with updated fields

    .. dropdown:: Array Metadata

        ::

            self.update(*, dtype)
            self.update(*, nodata)
            self.update(*, nodata, casting)

        Returns a new RasterMetadata object with updated data array metadata. If the updated object does not have a dtype and you provide a NoData value, then the updated object will inherit the dtype of that value. Otherwise, a new NoData value will be cast to the dtype of the updated raster. By default, requires safe casting, but see the "casting" options to use other casting rules.

    .. dropdown:: Spatial Metadata

        ::

            self.update(*, crs)
            self.update(*, transform)
            self.update(*, bounds)

        Returns an object with updated spatial metadata. Note that you may only provide one of the "transform" and "bounds" options - these two inputs are mutually exclusive. If the updated object has a CRS that differs from the transform/bounds, then the transform/bounds will be reprojected. If the updated object does not have a crs, then it will inherit any CRS from the transform/bounds.

    .. dropdown:: Update Shape

        ::

            self.update(*, shape)
            self.update(*, shape, keep_bounds=True)

        Returns a new RasterMetadata object with a different shape. If you do not also update the transform or bounds, then the method will need to compute a new Transform or BoundingBox. By default, keeps the original transform and computes a new BoundingBox for the shape. Set keep_bounds=True to instead keep the original BoundingBox and compute a new Transform. Note that this option is ignored if you provide a new transform or bounds.

    .. dropdown:: Name

        ::

            self.update(*, name)

        Returns an object with an updated name.

    :Inputs:
        * **dtype** (*type*) -- A new data dtype
        * **nodata** (*scalar*) -- A new NoData value
        * **casting** (*str*) -- The casting rule when casting a NoData value to the dtype. Options are "safe" (default), "same_kind", "no", "equiv", and "unsafe"
        * **crs** (*CRS-like*) -- A new coordinate reference system
        * **transform** (*Transform-like*) -- A new affine transform
        * **bounds** (*BoundingBox-like*) -- A new bounding box
        * **shape** (*(int, int)*) -- A new data array shape
        * **keep_bounds** (*bool*) -- True to keep the original BoundingBox when the shape is updated. False (default) to keep the original transform. Ignored if a new transform or bounds is provided
        * **name** (*str*) -- A new identifying name

    :Outputs:
        *RasterMetadata* -- A new RasterMetadata object with updated metadata fields.



.. _pfdf.raster.RasterMetadata.as_bool:

.. py:method:: RasterMetadata.as_bool(self):

    Sets dtype to bool and NoData to False

    ::

        self.as_bool()

    Returns a copy of the current object suitable for a boolean data array. The dtype of the new object is set to bool, and the NoData value is set to False.

    :Outputs:
        *RasterMetadata* -- A copy of the current object with dtype=bool and nodata=False



.. _pfdf.raster.RasterMetadata.ensure_nodata:

.. py:method:: RasterMetadata.ensure_nodata(self, default = None, casting = "safe")

    Returns a RasterMetadata object guaranteed to have a NoData value

    .. dropdown:: Ensure NoData Exists

        ::

            self.ensure_nodata()

        Checks if the current object has a metadata object. If so, returns a copy of the current object. If not, returns a metadata object with a default NoData value for the dtype. Raises a ValueError if the object has neither a NoData value nor a dtype.

    .. dropdown:: Set Default Value

        ::

            self.ensure_nodata(default)
            self.ensure_nodata(default, casting)

        Specifies the default NoData value to use if the metadata does not already have a NoData value. If the metadata object does not have a dtype, then the new object will also inherit the dtype of the NoData value. Otherwise, the NoData value is cast to the metadata's dtype. By default, requires safe casting, but see the "casting" option to select other casting rules.

    :Inputs:
        * **default** (*scalar*) -- The NoData value to use if the metadata does not already have a NoData value
        * **casting** (*str*) -- The casting rule used to convert "default" to the metadata dtype. Options are "safe" (default), "same_kind", "equiv", "no", and "unsafe"

    :Outputs:
        *RasterMetadata* -- A new RasterMetadata object guaranteed to have a NoData value



----

Preprocessing
-------------

.. _pfdf.raster.RasterMetadata.__getitem__:

.. py:method:: RasterMetadata.__getitem__(self, indices, return_slices = False)

    Returns the metadata object for the selected portion of the abstracted data array

    .. dropdown:: Basic Indexing

        ::
    
            self[rows, cols]

        Returns a copy of the metadata for the selected portion of the metadata's abstracted data array. The "rows" input should be an index or slice as would be applied to the first dimension of a 2D numpy array with the same shape as the metadata. The "cols" input is an index or slice as would be applied to the second dimension. Returns an object with an updated shape. Also updates the Transform and BoundingBox as appropriate.

        Note that this syntax has several limitations compared to numpy array indexing. As follows:

        1. Indexing is not supported when the metadata shape includes a 0,
        2. Indices must select at least 1 pixel - empty selections are not supported,
        3. Slices must have a step size of 1 or None,
        4. You must provide indices for exactly 2 dimensions, and
        5. This syntax is limited to the int and slice indices available to Python lists. More advanced numpy indexing methods (such as boolean indices and ellipses) are not supported.

    .. dropdown:: Return Slices

        ::

            self.__getitem__((rows, cols), return_slices=True)

        Returns the standardized row and column slices for the new array in addition to the new metadata object. The two extra outputs are the slices of the data array corresponding to the new metadata object. Start and stop indices will always be positive, and the step size will always be 1.

    :Inputs:
        * **rows** (*int | slice*) -- An index or slice for the first dimension of a numpy array with the same shape as the metadata
        * **cols** (*int | slice*) -- An index or slice for the second dimension of a numpy array with the same shape as the metadata

    :Outputs:
        * *RasterMetadata* -- The metadata object for the indexed portion of the abstracted data array
        * *slice* (optional) -- The row slice corresponding to the new metadata
        * *slice* (optional) -- The column slice corresponding to the new metadata



.. _pfdf.raster.RasterMetadata.fill:

.. py:method:: RasterMetadata.fill(self)

    Returns a metadata object without a NoData value

    ::

        self.fill()

    Returns a copy of the current RasterMetadata that does not have a NoData value.

    :Outputs:
        *RasterMetadata* -- A metadata object without a NoData value



.. _pfdf.raster.RasterMetadata.buffer:

.. py:method:: RasterMetadata.buffer(self, distance = None, units = "meters", *, left = None, bottom = None, right = None, top = None, return_buffers = False)

    Returns the metadata object for a buffered raster

    .. dropdown:: Buffer

        ::

            self.buffer(distance, units)

        Returns a new RasterMetadata object for the raster that would occur if the current metadata object's raster were buffered by the specified distance. The input distance must be positive and is interpreted as meters by default. Use the "units" option to provide the buffering distance in different units instead. Supported units include: "pixels" (the number of pixels to buffer along each edge), "base" (CRS/Transform base units), "meters", "kilometers", "feet", and "miles".

        Note that all units excepts "base" and "pixels" require the metadata object to have a CRS. Additionally, all units except "pixels" require the metadata object to have a transform.

    .. dropdown:: Specific Edges

        ::

            self.buffer(*, left)
            self.buffer(*, right)
            self.buffer(*, bottom)
            self.buffer(*, top)

        Specify the buffering distance for a particular direction. The "distance" input is optional (but still permitted) if any of these options are specified. If both the "distance" input and one of these options are specified, then the direction-specific option takes priority. If a direction does not have a distance and the "distance" input is not provided, then no buffering is applied to that direction.

    .. dropdown:: Return Buffers

        ::

            self.buffer(*, return_buffers=True)

        Returns the pixel_buffers dict in addition to the new metadata object. The new metadata object will be the first output, and the pixel dict will be the second output. The pixel_buffers dict contains the following keys: "left", "bottom", "right", and "top". The value for each key is the number of buffering pixels that would be applied to each side of the data array.

    :Inputs:
        * **distance** (*scalar*) -- A default buffer for all sides
        * **units** (*str*) -- Specifies the units of the input buffers. Options include** (**) -- "pixels", "base", "meters" (default), "kilometers", "feet", and "miles"
        * **left** (*scalar*) -- A buffer for the left side of the raster
        * **right** (*scalar*) -- A buffer for the right side of the raster
        * **top** (*scalar*) -- A buffer for the top of the raster
        * **bottom** (*scalar*) -- A buffer for the bottom of the raster
        * **return_buffers** (*bool*) -- True to also return a pixel buffers dict. False (default) to only return the updated metadata

    :Outputs:
        * *RasterMetadata* -- The metadata object for the buffered raster
        * *dict[str, float]* (Optional) -- A dict with the following keys: "left", "bottom", "right", and "top". The value for each key is the number of buffering pixels that  would be applied to each side of the data array. Only returned if return_buffers=True



.. _pfdf.raster.RasterMetadata.clip:

.. py:method:: RasterMetadata.clip(self, bounds, return_limits = False)

    Returns the RasterMetadata object for a clipped raster

    .. dropdown:: Clip

        ::

            self.clip(bounds)

        Returns the RasterMetadata object for the raster that would occur if the current metadata object's raster were clipped to the indicated bounds. The bounds may be a Raster, RasterMetadata, BoundingBox, dict, list, or tuple representing a bounding box. Note that the output metadata will inherit the bounding box CRS if the current metadata object does not already have a CRS.

    .. dropdown:: Return Limits

        ::

            self.clip(..., return_limits = True)

        Also return the pixel index limits for the clipping operation. The limits indicate the first and last indices of the clipped array, relative to the current array. Limits will be negative or larger than the current array shape if the metadata is clipped outside its current bounds. Returns the new metadata object as the first output, the row index limits, and then the column index limits.

    :Inputs:
        * **bounds** (*BoundingBox-like*) -- The bounds of the clipped raster
        * **return_limits** (*bool*) -- True to also return pixel index limits. False (default) to only return the updated array

    :Outputs:
        * *RasterMetadata* -- The RasterMetadata object for the raster that would occur if the current metadata's raster were clipped to the bounds
        * *(int, int)* (Optional) -- The index limits of the clipped array's rows. Only returned if return_limits=True
        * *(int, int)* (Optional) -- The index limits of the clipped array's columns. Only returned if return_limits=True



.. _pfdf.raster.RasterMetadata.reproject:

.. py:method:: RasterMetadata.reproject(self, template = None, *, crs = None, transform = None)

    Returns the RasterMetadata object for a reprojected raster

    .. dropdown:: Reproject by Template

        ::

            self.reproject(template)

        Returns the RasterMetadata object for the raster that would occur if the current metadata object's raster were reprojected to match a template raster. The new metadata object will have the same CRS, resolution, and grid alignment as the template. The template may be a Raster or RasterMetadata object.

    .. dropdown:: Reproject by Keyword

        ::
            
            self.reproject(..., *, crs)
            self.reproject(..., *, transform)

        Specify the CRS and/or transform of the reprojected raster. If you provide one of these keyword options in addition to a template, then the keyword value will take priority.

    :Inputs:
        * **template** (*Raster | RasterMetadata*) -- A Raster or RasterMetadata object that defines the CRS, resolution and grid alignment of the reprojected raster
        * **crs** (*CRS-like*) -- The CRS for the reprojection. Overrides the template CRS
        * **transform** (*Transform-like*) -- The transform used to determine resolution and grid alignment. Overrides the template transform

    :Outputs:
        *RasterMetadata* -- The RasterMetadata object for the reprojected raster