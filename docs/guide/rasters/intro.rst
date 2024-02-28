Rasters
=======

Rasters are a fundamental input for most pfdf routines. In brief, a raster dataset is a 2D rectangular grid of data values. The individual data values (often called "pixels") are regularly spaced along the X and Y axes, and each axis may use its own spacing interval. A raster is typically associated with some spatial metadata, which is used to locate the raster pixels in space. A raster may also have a NoData value; pixels equal to this value represent missing data.

A raster's spatial metadata consists of a coordinate reference system (CRS), and an affine transformation matrix (also known as the "transform"). The transform is used to convert the data grid's row and column indices to spatial coordinates, and the CRS specifies the location of these coordinates on the Earth's surface. A transform defines a raster's resolution and alignment (the location of pixel edges), and takes the form:

.. _affine:

.. math::

    \begin{vmatrix}
    dx & 0 & \mathrm{left}\\
    0 & dy & \mathrm{top}
    \end{vmatrix}

Here, dx and dy are the change in spatial coordinate when incrementing one column or row, respectively. The "left" and "top" variables indicate the spatial coordinates of the data grid's left and top edges. The two remaining coefficients can be used to implement shear transforms. However, pfdf only supports rectangular pixels, so these will always be 0 for our purposes.


Raster Objects
--------------

As stated, rasters are the fundamental input for pfdf analyses. As such, pfdf provides a custom :ref:`Raster class <pfdf.raster.Raster>` to help manage these datasets::

    >>> from pfdf.raster import Raster

This class includes methods to:

* Load rasters from a variety of formats,
* Access raster data and metadata
* Preprocess rasters prior to assessment, and
* Save rasters to file

.. note:: See also the :doc:`raster </tutorials/rasters>` and :doc:`preprocessing </tutorials/preprocess>` tutorials for detailed examples using *Raster* commands.

In many cases, you can create a *Raster* object by calling :ref:`the constructor <pfdf.raster.Raster.__init__>` on a file or an array-like dataset. For example::

    # File-based dataset
    >>> dem = Raster('dem.tif')

    # From a numpy array
    >>> import numpy as np
    >>> array = np.arange(200).reshape(20,10)
    >>> raster = Raster(array)

And you can save a *Raster* to a file using the :ref:`save method <pfdf.raster.Raster.save>`::

    >>> raster.save('my-raster.tif')

Each *Raster* represents its data grid as a 2D numpy array. You can use the ``values`` property to return this array::

    >>> dem.values
    array([[nan, nan, nan, ..., nan, nan, nan],
           [nan, nan, nan, ..., nan, nan, nan],
           [nan, nan, nan, ..., nan, nan, nan],
           ...,
           [nan, nan, nan, ..., nan, nan, nan],
           [nan, nan, nan, ..., nan, nan, nan],
           [nan, nan, nan, ..., nan, nan, nan]])


Note that *Raster* values are read-only, so you will need to make a copy if you want to alter the array::

    # This is fine (not changing values)
    >>> array = dem.values + 1

    # As is this (copied before changing values)
    >>> values = dem.values.copy()
    >>> values[0,0] = 1

    # But not this (didn't copy, so will raise an error)
    >>> dem.values[0,0] = 1

Some other useful properties include:

.. list-table::

    * - **Property**
      - **Description**
      - **Type**
    * - values
      - Data grid (read-only)
      - 2D numpy array
    * - dtype
      - Data type
      - numpy dtype
    * - shape
      - Shape of the data array
      - tuple[int, int]
    * - nodata
      - NoData value
      - numpy scalar
    * - data_mask
      - True elements indicate data pixels
      - 2D boolean numpy array
    * - nodata_mask
      - True elements indicate NoData pixels
      - 2D boolean numpy array

(and see the :doc:`Raster API </api/raster>` for a complete summary of *Raster* properties). The remainder of this section will outline key *Raster* commands, and see also the :doc:`raster tutorial </tutorials/rasters>` and :doc:`preprocessing tutorial </tutorials/preprocess>` for more detailed examples.



Creating Rasters
----------------

Many pfdf commands require one or more rasters as input, and the library recognizes a variety of formats, including:

* Paths to file-based rasters (``str`` or ``Path``)
* 2D numpy arrays (floating, integer, or boolean)
* ``rasterio.DatasetReader`` objects, and
* ``pysheds.sview.Raster`` objects

You are not required to convert raster datasets to *Raster* objects, as pfdf handles this conversion automatically. However, it's often useful to make this conversion, as *Raster* objects have access to :doc:`preprocessing methods <preprocess>` that are helpful for most use cases. This section will examine some of the commands available for creating these objects. The simplest approach is often the :ref:`Raster constructor <pfdf.raster.Raster.__init__>`, but :ref:`factory functions <api-raster-creation>` provide additional options for specific types of inputs.

.. tip:: 
    
    This guide uses GeoTiff files as examples, but pfdf supports most common raster file formats. See also the :ref:`raster driver guide <raster-drivers>` for more information on supported file formats.

Raster Constructor
++++++++++++++++++
The simplest way to create a *Raster* object is using :ref:`the constructor <pfdf.raster.Raster.__init__>`. This option is sufficient for most file-based rasters, as well as pysheds rasters. For example::

    >>> dem = Raster('dem.tif')

You can use the ``name`` parameter to specify an optional string to identify the raster. For example::

    >>> dem = Raster('dem.tif', name="DEM 10m")
    >>> print(dem.name)
    DEM 10m

Finally, the ``isbool`` option will convert the data grid to a boolean array, regardless of the input dataset's dtype. NoData pixels are converted to False. This option is often useful when loading file-based datasets, as many raster file formats do not support boolean dtypes. Note that the input dataset's pixels must all be 1s or 0s, excluding NoData values::

    # By default, the file has a "uint8" dtype
    >>> mask = Raster('iswater.tif')
    >>> print(mask.dtype)
    uint8

    # But using "isbool" converts the array to boolean
    >>> mask = Raster('iswater.tif', isbool=True)
    >>> print(mask.dtype)
    bool
    >>> mask.nodata
    False


from_file
+++++++++
The :ref:`from_file <pfdf.raster.Raster.from_file>` method provides some additional options for loading a file-based raster dataset. For example,this command adds the ``band`` option, which allows you to load a raster from a particular band of a multi-band raster::

    >>> dem = Raster.from_file('my-raster.tif', band=3)

You can also use the ``driver`` option to specify the file format when a file has a nonstandard extension::

    >>> dem = Raster.from_file('raster.unusual', driver="GTiff")

The ``window`` option allows you to only load a subset of a raster into memory. This is useful when you only need a small portion of a very large dataset, or when a raster dataset is larger than your computer's RAM::

    >>> window = Raster('small-raster.tif')
    >>> raster = Raster.from_file('very-large-raster.tif', window=window)


from_array
++++++++++

Although you can call the *Raster* constructor on numpy arrays, the resulting object will not have spatial metadata or a NoData value::

    >>> import numpy as np
    >>> araster = np.arange(100).reshape(5,20)
    >>> raster = Raster(araster)

    >>> raster.nodata
    None
    >>> raster.crs
    None
    >>> raster.transform
    None

The :ref:`Raster.from_array <pfdf.raster.Raster.from_array>` command allows you to optionally provide these values::

    >>> from affine import Affine
    >>> transform = Affine(10, 0, 100,0,-10,5)
    >>> raster = Raster.from_array(araster, nodata=-999, crs="epsg:4326", transform=transform)

    >>> raster.nodata
    -999
    >>> print(raster.crs)
    EPSG:4326
    >>> print(raster.transform)
    |10,   0, 100|
    | 0, -10,   5|
    | 0,   0,   1|

You can also use the ``spatial`` parameter to optionally match the CRS and transform of another *Raster*::

    >>> dem = Raster('dem.tif')
    >>> raster = Raster.from_array(araster, nodata=-999, spatial=dem)

    >>> raster.nodata
    -999
    >>> print(raster.crs)
    EPSG:4326
    >>> print(raster.transform)
    |10,   0, 100|
    | 0, -10,   5|
    | 0,   0,   1|



from_polygons
+++++++++++++

Sometimes, you'll have a dataset represented as a set of polygon or multi-polygon features. For example, fire perimeters and soil properties are often represented as polygons. The routines in pfdf require raster datasets, so you will need to convert these polygon datasets to rasters before processing. You can use the :ref:`Raster.from_polygons <pfdf.raster.Raster.from_polygons>` command to do so. The command requires the path to a vector feature file, and we recommend also using the ``resolution`` option to match the resolution of the new raster to an existing raster::

    >>> dem = Raster('dem.tif')
    >>> perimeter = Raster.from_polygons("fire-perimeter.shp", resolution=dem)
    >>> print(perimeter.resolution)
    (10.0, 10.0)

By default, this command will create a boolean raster. Pixels inside a polygon will be marked as True, and all other pixels will be False. This is most suitable for polygons that represent a mask, such as a fire perimeter::

    >>> print(perimeter.dtype)
    bool
    >>> print(perimeter.nodata)
    False

However, other datasets (such as soil properties) are better represented by numeric values. When this is the case, you can use the ``field`` option to build the raster from one of the polygon data fields. In this case, pixels inside a polygon will be set to the value of the polygon's data field, and all other pixels will be NaN::

    >>> kf = Raster.from_polygons('kf-factor.shp', resolution=dem, field="KFFACT")

    >>> print(kf.dtype)
    float64
    >>> kf.nodata
    nan

You can also use the ``fill`` option to replace non-polygon pixels with a data value, rather than NaN::

    >>> kf = Raster.from_polygons("kf-factor.shp", resolution=dem, field="KFFACT", fill=-1 )


from_points
+++++++++++

Sometimes, you'll also need to convert a set of points or multi-points to a raster. This is most common when including debris-flow retainment features in an analysis. You can use the :ref:`Raster.from_points <pfdf.raster.Raster.from_points>` command to do so. The syntax is the same as :ref:`from_polygons <pfdf.raster.Raster.from_polygons>`, except that the file path should be for a point and/or multi-point feature file::

    # Boolean output
    >>> dem = Raster('dem.tif')
    >>> features = Raster.from_points('retainment-features.shp', resolution=dem)
    >>> features.dtype
    bool

    # Numeric output
    >>> features = Raster.from_points('retainment-features.shp', resolution=dem, field='Volume')
    >>> features.dtype
    float64



Saving Rasters
--------------

All pfdf commands that produce a raster will return a *Raster* object as output. You can use the ``values`` property to retrieve the raster's data grid, but it's often useful to use the :ref:`save method <pfdf.raster.Raster.save>` to save the raster to the indicated filepath::

    >>> araster.save('my-file.tif')

By default, this method will not overwrite existing files, but you can use the ``overwrite`` option to change this::

    >>> araster.save('my-file.tif', overwrite=True)

You can also use the ``driver`` option to specify the file format for filepaths with non-standard extensions::

    >>> araster.save('my-file.unusual', driver='GTiff')



