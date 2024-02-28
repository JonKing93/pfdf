Raster Tutorial
===============

This tutorial examines raster factories, properties, and saving to file. See also the :doc:`preprocessing tutorial <preprocess>` for examples of raster preprocessing commands.

.. admonition:: Download

  You can download the datasets and script used in this tutorial here: :doc:`Download Files <download>`. This tutorial follows the ``rasters`` script.



Creating Rasters
----------------

Constructor
+++++++++++

The :ref:`Raster constructor <pfdf.raster.Raster.__init__>` is usually the simplest way to create a *Raster* object. The constructor works for a variety of formats, including file-based rasters::

    >>> dem = Raster('dem.tif')

    >>> print(dem.shape)
    (2015, 1957)
    >>> print(dem.dtype)
    float64
    >>> print(dem.crs)
    EPSG:26911
    >>> print(dem.transform)
    | 10.00,   0.00,  407737.17|
    |  0.00, -10.00, 3792373.98|
    |  0.00,   0.00,       1.00|

as well as numpy arrays::

    >>> import numpy as np
    >>> araster = np.arange(200).reshape(20,10)
    >>> raster = Raster(araster)

    >>> print(raster.shape)
    (20, 10)
    >>> print(raster.dtype)
    int32
    >>> print(raster.crs)
    None
    >>> print(raster.transform)
    None


Boolean Rasters
+++++++++++++++

You can use the ``isbool`` option to indicate that a raster represents a boolean array. This is often useful for file-based rasters -- many raster-file formats will save boolean raster masks as an ``int`` dtype, but this will cause errors when attempting to use the mask for `boolean indexing <https://numpy.org/doc/stable/user/basics.indexing.html#boolean-array-indexing>`_. The ``isbool`` option resolves this by converting the new raster's data array to bool, regardless of the original dtype.

For example, if we naively load the water mask::

    >>> mask = Raster('mask.tif')
    >>> print(mask.dtype)
    int8
    >>> print(mask.nodata)
    0

we can see the "mask" raster has an integer dtype, which could cause indexing problems. By contrast, if we use the ``isbool`` option::

    >>> mask = Raster('mask.tif', isbool=True)
    >>> print(mask.dtype)
    bool
    >>> print(mask.nodata)
    False

we can see the raster is correctly converted to a boolean array.



Raster Factories
++++++++++++++++

You can also use *Raster* factories to create a *Raster* object from specific types of inputs. These factories provide additional creation options, and follow the naming convention ``from_<format>``. For example, the :ref:`from_file factory <pfdf.raster.Raster.from_file>` includes a ``band`` option, which you can use to specify a specific band in a multi-band raster::

    >>> dem = Raster.from_file('dem.tif', band=1)
    >>> dem.shape
    (2015, 1957)
    

You can also use the ``window`` option to only load a subset of a saved dataset. This can be useful when you only need a small portion of a very large raster, or if a raster is larger than your computer's RAM::

    >>> window = Raster('dnbr.tif')
    >>> dem = Raster.from_file('dem.tif', window=window)
    >>> dem.shape
    (1280, 1587)


The :ref:`from_array factory <pfdf.raster.Raster.from_array>` allows you to add raster metadata (NoData, CRS, and transform) to a *Raster* derived from a numpy array. For example, if we use the *Raster* constructor on a numpy array::

    >>> araster = np.arange(200).reshape(20,10)
    >>> raster = Raster(araster)
    >>> print(raster.nodata)
    None
    >>> print(raster.crs)
    None
    >>> print(raster.transform)
    None

we can see the created raster is lacking metadata. By contrast, we could use::

    >>> raster = Raster.from_array(araster, nodata=0, crs="EPSG:4326", transform=(1,0,0,0,1,0))
    >>> print(raster.nodata)
    0
    >>> print(raster.crs)
    EPSG:4326
    >>> print(raster.transform)
    | 1.00, 0.00, 0.00|
    | 0.00, 1.00, 0.00|
    | 0.00, 0.00, 1.00|

which adds metadata to the new *Raster*. You can also use the ``spatial`` option to match the CRS and transform of another raster::

    >>> raster = Raster.from_array(araster, nodata=0, spatial=dem)
    >>> print(raster.nodata)
    0
    >>> print(raster.crs)
    EPSG:26911
    >>> print(raster.transform)
    | 10.00,   0.00,  407737.17|
    |  0.00, -10.00, 3792373.98|
    |  0.00,   0.00,       1.00|
    

Properties
----------

Rasters include a number of data properties with information about the associated data grid and spatial metadata.

Data Grid
+++++++++

Each *Raster* object uses a 2D numpy array to represent its data grid, and you can use  ``.values`` to return this entire array::

    >>> dem = Raster('dem.tif')
    >>> dem.values
    array([[nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan],
       ...,
       [nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan],
       [nan, nan, nan, ..., nan, nan, nan]])

Like numpy arrays, *Raster* objects also have ``.dtype``, ``.shape``, and ``.size`` properties, which return the data type, array shape, and number of elements, respectively::

    >>> print(dem.dtype)
    float64
    >>> print(dem.shape)
    (2015, 1957)
    >>> print(dem.size)
    3943355

*Raster* objects also have ``.height`` and ``.width`` properties, which are analogous to the equivalent properties in `rasterio <https://rasterio.readthedocs.io/>`_. Here, height is the number of rows, and width is the number of columns::

    >>> dem.height
    2015
    >>> dem.width
    1957

.. note:: ``(height, width)`` is equivalent to ``shape``.


NoData
++++++

Use ``.nodata`` to retrieve the NoData value::

    >>> dem.nodata
    nan

You can also use the ``.data_mask`` and ``.nodata_mask`` properties to return boolean arrays that indicate the locations of data / nodata pixels in the data grid. For ``.data_mask``, True elements indicate the locations of data pixels, whereas for ``.nodata_mask``, True elements indicate the locations of NoData pixels::

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
*Raster* objects also have a number of properties pertaining to spatial metadata. Use ``.crs`` to return the coordinate reference system This will always be an instance of a `rasterio.crs.CRS object <https://rasterio.readthedocs.io/en/latest/api/rasterio.crs.html#rasterio.crs.CRS>`_::

    >>> dem.crs
    EPSG:26911
    >>> type(dem.crs)
    <class 'rasterio.crs.CRS'>

You can also use ``.transform`` to return the :ref:`affine transform <affine>`. This will always be an instance of an `affine.Affine <https://pypi.org/project/affine/>`_ object::

    >>> dem.transform
    | 10.00,   0.00,  407737.17|
    |  0.00, -10.00, 3792373.98|
    |  0.00,   0.00,       1.00|
    >>> type(dem.transform)
    <class 'affine.Affine'>

You can also use ``.dx`` and ``.dy`` to return the relevant coefficients from the affine matrix::

    >>> dem.dx
    10.0
    >>> dem.dy
    -10.0

Use ``.bounds`` to return the spatial coordinates of the raster's edges. This will always be an instance of a `rasterio.coords.BoundingBox object <https://rasterio.readthedocs.io/en/stable/api/rasterio.coords.html#rasterio.coords.BoundingBox>`_::

    >>> dem.bounds
    BoundingBox(left=407737.16646630806, bottom=3772223.9833854814, right=427307.16646630806, top=3792373.9833854814)
    >>> type(dem.bounds)
    <class 'rasterio.coords.BoundingBox'>
    
Alternatively, use ``.left``, ``.right``, ``.top``, or ``.bottom`` to return the coordinate of a specific edge::

    >>> dem.left
    407737.16646630806
    >>> dem.right
    427307.16646630806
    >>> dem.top
    3792373.9833854814
    >>> dem.bottom
    3772223.9833854814

If a *Raster* does not have a transform, then its bounds, dx, and dy will all have NaN values. For example::

    >>> araster = np.arange(200).reshape(20,10)
    >>> raster = Raster(araster)
    >>> print(raster.transform)
    None

    >>> raster.bounds
    BoundingBox(left=nan, bottom=nan, right=nan, top=nan)
    >>> raster.dx
    nan
    >>> raster.dy
    nan



Pixel Properties
++++++++++++++++
Several properties provide information about pixel sizes and areas. Use ``.resolution`` to return the strictly-positive spacing along the X and Y axes::
    
    >>> dem.resolution
    (10.0, 10.0)

Alternatively, use ``.pixel_width`` and ``.pixel_height`` return the spacing for a particular axis::

    >>> dem.pixel_width
    10.0
    >>> dem.pixel_height
    10.0

The ``.pixel_area`` property returns the area of a pixel in the units of the transform, and ``.pixel_diagonal`` returns the length between opposing corners (again in the units of the transform)::

    >>> dem.pixel_area
    100.0
    >>> dem.pixel_diagonal
    14.142

If a raster doesn't have an affine transform, then all pixel properties will be NaN. For example::

    >>> araster = np.arange(200).reshape(20,10)
    >>> raster = Raster(araster)
    >>> print(raster.transform)
    None

    >>> raster.resolution
    (nan, nan)
    >>> raster.pixel_width
    nan
    >>> raster.pixel_height
    nan
    >>> raster.pixel_area
    nan
    >>> raster.pixel_diagonal
    nan


Saving
------

Use the :ref:`save method <pfdf.raster.Raster.save>` to save a *Raster* dataset to a file. For example::

    >>> araster = np.arange(200).reshape(20,10)
    >>> raster = Raster(araster)
    >>> raster.save("example.tif")

By default, the command won't overwrite existing files. Use the ``overwrite`` option to change this::

    >>> raster.save("example.tif")  # Created new file
    >>> raster.save("example.tif")  # Error because attempting to overwrite
    Traceback (most recent call last):
    ...
    FileExistsError: Output file already exists:
    ...
    If you want to replace existing files, set "overwrite=True

    >>> raster.save("example.tif", overwrite=True)  # This works fine
