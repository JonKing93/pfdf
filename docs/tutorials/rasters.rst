Raster Tutorial
===============

This tutorial examines raster factories, properties, and saving to file. See also the :doc:`preprocessing tutorial <preprocess>` for examples of raster preprocessing commands.


.. admonition:: Download

    The following list provides download links for the tutorial resources:

    * :doc:`Tutorial Datasets <download>`
    * :download:`Python Script <scripts/rasters.py>`



Creating Rasters
----------------

Constructor
+++++++++++

The :ref:`Raster constructor <pfdf.raster.Raster.__init__>` is usually the simplest way to create a *Raster* object. The constructor works for a variety of formats, including file-based rasters:

.. code:: pycon

    >>> from pfdf.raster import Raster
    >>> dem = Raster('dem.tif')
    >>> print(dem)
    Raster:
        Name: raster
        Shape: (1979, 2296)
        Dtype: float32
        NoData: nan
        CRS("NAD83")
        Transform(dx=9.26e-05, dy=-9.26-05, left=-118.007, top=34.27, crs="NAD83")  
        BoundingBox(left=-118.00, bottom=34.09, right=-117.7879629630723, top=34.27, crs="NAD83")

as well as numpy arrays:

.. code:: pycon

    >>> import numpy as np
    >>> araster = np.arange(200).reshape(20,10)
    >>> Raster(araster)
    Raster:
        Name: raster
        Shape: (20, 10)
        Dtype: int32
        NoData: -2147483648
        CRS: None
        Transform: None
        BoundingBox: None


Boolean Rasters
+++++++++++++++

You can use the ``isbool`` option to indicate that a raster represents a boolean array. This is often useful for file-based rasters -- many raster-file formats will save boolean raster masks as an ``int`` dtype, but this will cause errors when attempting to use the mask for `boolean indexing <https://numpy.org/doc/stable/user/basics.indexing.html#boolean-array-indexing>`_. The ``isbool`` option resolves this by converting the new raster's data array to bool, regardless of the original dtype.

For example, if we naively load the water mask:

.. code:: pycon

    >>> mask = Raster('mask.tif')
    >>> print(mask.dtype)
    int8
    >>> print(mask.nodata)
    -128

we can see the "mask" raster has an integer dtype, which could cause indexing problems. By contrast, if we use the ``isbool`` option:

.. code:: pycon

    >>> mask = Raster('mask.tif', isbool=True)
    >>> print(mask.dtype)
    bool
    >>> print(mask.nodata)
    False

we can see the raster is correctly converted to a boolean array.



Raster Factories
++++++++++++++++

You can also use *Raster* factories to create a *Raster* object from specific types of inputs. These factories provide additional creation options, and follow the naming convention ``from_<format>``. For example, the :ref:`from_file factory <pfdf.raster.Raster.from_file>` includes a ``band`` option, which you can use to specify a specific band in a multi-band raster:

.. code:: pycon

    >>> dem = Raster.from_file('dem.tif', band=1)
    >>> print(dem.shape)
    (1979, 2296)
    

You can also use the ``bounds`` option to only load a subset of a saved dataset. This can be useful when you only need a small portion of a very large raster, or if a raster is larger than your computer's memory. The bounds may be another Raster, or any BoundingBox-like object:

.. code:: pycon

    >>> dnbr = Raster('dnbr.tif')
    >>> dem = Raster.from_file('dem.tif', bounds=dnbr)
    >>> dem.shape
    (1260, 1873)


The :ref:`from_array factory <pfdf.raster.Raster.from_array>` allows you to add raster metadata (NoData, CRS, and transform) to a *Raster* derived from a numpy array. For example, if we use the *Raster* constructor on a numpy array:

.. code:: pycon

    >>> araster = np.arange(200).reshape(20,10)
    >>> Raster(araster)
    Raster:
        Name: raster
        Shape: (20, 10)
        Dtype: int32
        NoData: -2147483648
        CRS: None
        Transform: None
        BoundingBox: None

we can see the created raster lacks spatial metadata and uses a default NoData value. By contrast, we could use:

.. code:: pycon

    >>> Raster.from_array(araster, nodata=0, crs="EPSG:4326", transform=(1,1,0,0))
    Raster:
        Name: raster
        Shape: (20, 10)
        Dtype: int32
        NoData: 0
        CRS("NAD83 / UTM zone 11N")
        Transform(dx=10, dy=-10, left=0, top=0, crs="NAD83 / UTM zone 11N")
        BoundingBox(left=0, bottom=-200, right=100, top=0, crs="NAD83 / UTM zone 11N")

which adds metadata to the new *Raster*. You can also use the ``spatial`` option to match the CRS and transform of another raster:

.. code:: pycon

    >>> raster = Raster.from_array(araster, nodata=0, spatial=dem)
    Raster:
        Name: raster
        Shape: (20, 10)
        Dtype: int32
        NoData: 0
        CRS("NAD83")
        Transform(dx=9.26e-05, dy=-9.26e-05, left=-117.999, top=34.240, crs="NAD83")
        BoundingBox(left=-117.999, bottom=34.238, right=-117.998, top=34.240, crs="NAD83")
    

Properties
----------

Rasters include a number of data properties with information about the associated data grid and spatial metadata.

Data Grid
+++++++++

Each *Raster* object uses a 2D numpy array to represent its data grid, and you can use  ``.values`` to return this entire array:

.. code:: pycon

    >>> dem = Raster('dem.tif')
    >>> dem.values
    array([[nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan],
       ...,
       [nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan]])

Like numpy arrays, *Raster* objects also have ``.dtype``, ``.shape``, and ``.size`` properties, which return the data type, array shape, and number of elements, respectively:

.. code:: pycon

    >>> print(dem.dtype)
    float32
    >>> print(dem.shape)
    (1260, 1873)
    >>> print(dem.size)
    2359980

*Raster* objects also have ``.height`` and ``.width`` properties, which are analogous to the equivalent properties in `rasterio <https://rasterio.readthedocs.io/>`_. Here, height is the number of rows, and width is the number of columns:

.. code:: pycon

    >>> dem.height
    1260
    >>> dem.width
    1873

.. note:: 
    
    ``(height, width)`` is equivalent to ``shape``.


NoData
++++++

Use ``.nodata`` to retrieve the NoData value:

.. code:: pycon

    >>> dem.nodata
    nan

You can also use the ``.data_mask`` and ``.nodata_mask`` properties to return boolean arrays that indicate the locations of data / nodata pixels in the data grid. For ``.data_mask``, True elements indicate the locations of data pixels, whereas for ``.nodata_mask``, True elements indicate the locations of NoData pixels:

.. code:: pycon

    >>> print(dem.values)
    array([[nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        ...,
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan],
        [nan, nan, nan, ..., nan, nan, nan]])

    >>> print(dem.data_mask)
    array([[False, False, False, ..., False, False, False],
        [False, False, False, ..., False, False, False],
        [False, False, False, ..., False, False, False],
        ...,
        [False, False, False, ..., False, False, False],
        [False, False, False, ..., False, False, False],
        [False, False, False, ..., False, False, False]])

    >>> print(dem.nodata_mask)
    array([[ True,  True,  True, ...,  True,  True,  True],
        [ True,  True,  True, ...,  True,  True,  True],
        [ True,  True,  True, ...,  True,  True,  True],
        ...,
        [ True,  True,  True, ...,  True,  True,  True],
        [ True,  True,  True, ...,  True,  True,  True],
        [ True,  True,  True, ...,  True,  True,  True]])


Spatial Metadata
++++++++++++++++
*Raster* objects also have a number of properties pertaining to spatial metadata. Use ``.crs`` to return the coordinate reference system. This will return a `pyproj.CRS object <https://pyproj4.github.io/pyproj/stable/index.html>`_:

.. code:: pycon

    >>> dem.crs
    <Geographic 2D CRS: EPSG:4269>
    Name: NAD83
    Axis Info [ellipsoidal]:
    - Lat[north]: Geodetic latitude (degree)
    - Lon[east]: Geodetic longitude (degree)
    Area of Use:
    - undefined
    Datum: North American Datum 1983
    - Ellipsoid: GRS 1980
    - Prime Meridian: Greenwich

    >>> type(dem.crs)
    <class 'pyproj.crs.crs.CRS'>

You can also use ``.transform`` to return the :ref:`affine transform <affine>`. This will always be a :ref:`Transform object <pfdf.projection.transform.Transform>`:

.. code:: pycon

    >>> dem.transform
    Transform(dx=9.26e-05, dy=-9.26e-05, left=-118.00, top=34.24, crs="NAD83")

    >>> type(dem.transform)
    <class 'pfdf.projection.transform.Transform'>

Use ``.bounds`` to return the raster's bounding box as a :ref:`BoundingBox object <pfdf.projection.bbox.BoundingBox>`:

.. code:: pycon

    >>> dem.bounds
    BoundingBox(left=-118.00, bottom=34.12, right=-117.83, top=34.24, crs="NAD83")

    >>> type(dem.bounds)
    <class 'pfdf.projection.bbox.BoundingBox'>



Pixel Characteristics
+++++++++++++++++++++
Several methods provide information about resolution and pixel geometries. By default, these methods return values in units of meters, but you can use the ``units`` option to return values in :doc:`other units </guide/utils/units>` instead. Use the ``resolution`` method to return the (strictly positive) spacing along the X and Y axes:

.. code:: pycon
    
    >>> dem.resolution()
    (8.517348140404517, 10.295826561487834)

    >>> dem.resolution(units="feet")
    (27.944055578754977, 33.77895853506507)

Alternatively, use ``dx`` to return the change in the X-axis spatial coordinate when moving one pixel right, and ``dy`` to return the change in the Y-axis spatial coordinate when moving one pixel down. Note that these values may not be positive:

.. code:: pycon

    >>> dem.dx()
    8.517348140404517

    >>> dem.dy()
    -10.295826561487834

The ``pixel_area`` method returns the area of a single pixel, and ``pixel_diagonal`` returns the length between a pixel's opposing corners:

.. code:: pycon

    >>> dem.pixel_area()
    87.69313921741583

    >>> dem.pixel_diagonal()
    13.362232744907965


Saving
------

Use the :ref:`save method <pfdf.raster.Raster.save>` to save a *Raster* dataset to a file. For example::

    araster = np.arange(200).reshape(20,10)
    raster = Raster(araster)
    raster.save("example.tif")

By default, the command won't overwrite existing files: 

.. code:: pycon

    >>> raster.save("example.tif")  # Created new file
    >>> raster.save("example.tif")  # Error because attempting to overwrite
    Traceback (most recent call last):
    ...
    FileExistsError: Output file already exists:
    ...
    If you want to replace existing files, set "overwrite=True"

Use the ``overwrite`` option to change this::

    raster.save("example.tif", overwrite=True)  # This works fine
