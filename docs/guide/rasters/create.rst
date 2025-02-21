Creating Raster Objects
=======================

Many pfdf commands require one or more rasters as input, and the library recognizes a variety of formats, including:

* Paths to file-based rasters (``str`` or ``Path``)
* 2D numpy arrays (floating, integer, or boolean)
* ``rasterio.DatasetReader`` objects, and
* ``pysheds.sview.Raster`` objects

You are not required to convert raster datasets to *Raster* objects, as pfdf handles this conversion automatically. However, it's often useful to make this conversion, as *Raster* objects have access to :doc:`preprocessing methods <preprocess>` that are helpful for most use cases. This section will examine some of the commands available for creating these objects. The simplest approach is often the :ref:`Raster constructor <pfdf.raster.Raster.__init__>`, but :ref:`factory functions <api-raster-creation>` provide additional options for specific types of inputs.

.. tip:: 
    
    This guide uses GeoTiff files as examples, but pfdf supports most common raster file formats. Refer to the :ref:`raster driver guide <raster-drivers>` for more information on supported file formats.

----

Raster Constructor
------------------
The simplest way to create a *Raster* object is using :ref:`the constructor <pfdf.raster.Raster.__init__>`. This option is sufficient for most file-based rasters, as well as pysheds rasters. For example::

    # Create a raster
    dem = Raster('dem.tif')

You can use the ``name`` property to specify an optional string to identify the raster. For example:

.. code:: pycon

    >>> # Create a named raster
    >>> dem = Raster('dem.tif', name="DEM 10m")

    >>> print(dem.name)
    DEM 10m

    >>> print(dem)
    Raster:
        Name: DEM 10m
        Shape: (11445, 10986)
        Dtype: float32
        NoData: -999999.0
        CRS("NAD83 / UTM zone 11N")
        Transform(dx=10, dy=-10, left=736399, top=4990804, crs="NAD83 / UTM zone 11N")
        BoundingBox(left=736399, bottom=4876354, right=846259, top=4990804, crs="NAD83 / UTM zone 11N")


Finally, the ``isbool`` option will convert the data grid to a boolean array, regardless of the input dataset's dtype. NoData pixels are converted to False. This option is often useful when loading file-based datasets, as many raster file formats do not support boolean dtypes. Note that the input dataset's pixels must all be 1s or 0s, excluding NoData values:

.. code:: pycon

    >>> # By default, the file has a "uint8" dtype
    >>> mask = Raster('iswater.tif')
    >>> print(mask.dtype)
    uint8

    >>> # But using "isbool" converts the array to boolean
    >>> mask = Raster('iswater.tif', isbool=True)
    >>> print(mask.dtype)
    bool
    >>> mask.nodata
    False

----

from_file
---------
The :ref:`from_file <pfdf.raster.Raster.from_file>` method provides some additional options for loading a file-based raster dataset. For example, this command adds the ``band`` option, which allows you to load a raster from a particular band of a multi-band raster::

    # Load from band 3
    dem = Raster.from_file('my-raster.tif', band=3)

You can also use the ``driver`` option to specify the file format when a file has a nonstandard extension::

    # Open a GeoTiff with an unusual extension
    dem = Raster.from_file('raster.unusual', driver="GTiff")

The ``bounds`` option allows you to only load a subset of a raster into memory. This is useful when you only need a small portion of a very large dataset, or when a raster dataset is larger than your computer's RAM::

    # Load the subset of a large raster that's in the bounds of a smaller raster
    perimeter = Raster('a-fire-perimeter.tif')
    raster = Raster.from_file('very-large-raster.tif', bounds=perimeter)

    # Load a subset of data from a known bounding box
    bounds = {'left': -124, 'right': -121, 'bottom': 30, 'top': 33, 'crs': 4326}
    raster = Raster.from_file('very-large-raster.tif', bounds=bounds)

----

from_array
----------

Although you can call the *Raster* constructor on numpy arrays, the resulting object will have a default NoData value, and will not have spatial metadata:

.. code:: pycon

    >>> # Use the constructor on a numpy array
    >>> import numpy as np
    >>> araster = np.arange(100).reshape(5,20)
    >>> raster = Raster(araster)

    >>> # The created raster lacks spatial metadata, and has a default NoData value
    >>> print(raster)
    Raster:
        Shape: (5, 20)
        Dtype: int32
        NoData: -2147483648
        CRS: None
        Transform: None
        BoundingBox: None

The :ref:`Raster.from_array <pfdf.raster.Raster.from_array>` command allows you to optionally provide these values:

.. code:: pycon

    >>> # Use Raster.from_array on a numpy array
    >>> import numpy as np
    >>> araster = np.arange(100).reshape(5,20)
    >>> raster = Raster.from_array(araster, nodata=-999, crs=4326, transform=(10, -10, 100, 5))

    >>> # The created Raster has spatial metadata and a custom NoData value
    >>> print(raster)
    Raster:
        Shape: (5, 20)
        Dtype: int32
        NoData: -999
        CRS("WGS 84")
        Transform(dx=10, dy=-10, left=100, top=5, crs="WGS 84")
        BoundingBox(left=100, bottom=-45, right=300, top=5, crs="WGS 84")

You can also use the ``spatial`` parameter to optionally match the CRS and transform of another *Raster*:

.. code:: pycon

    >>> # Using a spatial template
    >>> dem = Raster('dem.tif')
    >>> raster = Raster.from_array(araster, spatial=dem)

    # Created raster has the CRS and transform of the template
    >>> print(raster)
    Raster:
        Shape: (5, 20)
        Dtype: int32
        NoData: -2147483648
        CRS("NAD83 / UTM zone 11N")
        Transform(dx=10, dy=-10, left=736399, top=4990804, crs="NAD83 / UTM zone 11N")
        BoundingBox(left=736399, bottom=4876354, right=846259, top=4990804, crs="NAD83 / UTM zone 11N")

----

from_polygons
-------------

Sometimes, you will have a dataset represented as a set of polygon or multi-polygon features. For example, fire perimeters and soil properties are often represented as polygons. The routines in pfdf require raster datasets, so you will need to convert these polygon datasets to rasters before processing. You can use the :ref:`Raster.from_polygons <pfdf.raster.Raster.from_polygons>` command to do so:

.. code:: pycon

    >>> # Create a Raster from polygon features
    >>> perimeter = Raster.from_polygons("fire-perimeter.shp")
    Raster:
        Shape: (1328, 1677)
        Dtype: bool
        NoData: False
        CRS("NAD83 / UTM zone 12N")
        Transform(dx=10.0, dy=-10.0, left=277924, top=4961656, crs="NAD83 / UTM zone 12N")
        BoundingBox(left=277924, bottom=4948376.0, right=294694.0, top=4961656, crs="NAD83 / UTM zone 12N")


.. tip:: 
    
    This guide uses Shapefiles as examples, but pfdf supports most common vector feature file formats. Refer to the :ref:`vector driver guide <vector-drivers>` for more information on supported file formats.

Building from Data Fields
+++++++++++++++++++++++++

By default, the ``from_polygons`` command will create a boolean raster. Pixels inside a polygon will be marked as True, and all other pixels will be False. This is most suitable for polygons that represent a mask, such as a fire perimeter:

.. code:: pycon

    >>> # By default, creates a boolean raster
    >>> print(perimeter.dtype)
    bool
    >>> print(perimeter.nodata)
    False

However, other datasets (such as soil properties) are better represented by numeric values. When this is the case, you can use the ``field`` option to build the raster from one of the polygon data fields. In this case, the dtype of the output raster will match the dtype of the data field. Pixels inside a polygon will be set to the value of the polygon's data field, and all other pixels are set to a default NoData value:

.. code:: pycon

    >>> # Create a raster from a polygon field
    >>> kf = Raster.from_polygons('kf-factor.shp', field="KFFACT")
    Raster:
        Shape: (3161, 3635)
        Dtype: float64
        NoData: nan
        CRS("NAD_1927_Albers")
        Transform(dx=10, dy=-10, left=-1408681, top=2559888, crs="NAD_1927_Albers")
        BoundingBox(left=-1408681, bottom=2528278, right=-1372331, top=2559888, crs="NAD_1927_Albers")

    >>> # Creates a floating-point raster whose NoData is NaN
    >>> print(kf.dtype)
    float64
    >>> kf.nodata
    nan

You can also use the ``nodata`` option to specify a custom NoData value:

.. code:: pycon

    >>> kf = Raster.from_polygons('kf-factor.shp', field="KFFACT", nodata=-999)
    Raster:
        Shape: (3161, 3635)
        Dtype: float64
        NoData: -999
        CRS("NAD_1927_Albers")
        Transform(dx=10, dy=-10, left=-1408681, top=2559888, crs="NAD_1927_Albers")
        BoundingBox(left=-1408681, bottom=2528278, right=-1372331, top=2559888, crs="NAD_1927_Albers")

Windowed Reading
++++++++++++++++

You can use the ``bounds`` option to only use polygons that intersect a specified bounding box. This can be useful when you only need data from a small subset of a much larger polygon dataset. The ``bounds`` input may be an existing *Raster* object, *BoundingBox* object, or any input convertible to a *BoundingBox*. For example::

    # Only load polygons that intersect an existing raster
    dem = Raster('dem.tif')
    raster = Raster.from_polygons('large-dataset.shp', bounds=dem)

    # Only load polygons that intersect a known bounding box
    bounds = {'left': -124, 'right': -121, 'bottom': 30, 'top': 33, 'crs': 4326}
    raster = Raster.from_polygons('large-dataset.shp', bounds=bounds)

Custom Resolution
+++++++++++++++++

By default, the command will create a raster with 10 meter resolution, but you can use the ``resolution`` option to specify different values::

    Raster.from_polygons('perimeter.shp', resolution=dem)   # Match other raster
    Raster.from_polygons('perimeter.shp', resolution=5)     # 5 meter resolution
    Raster.from_polygons('perimeter.shp', resolution=(5,6)) # Separate X and Y resolutions

If you provide resolution as a number (rather than as a *Transform* or *Raster* object), then the units are interpreted as meters by default. Use the ``units`` option to specify other units::

    Raster.from_polygons('perimeter.shp', resolution=.01, units="kilometers")
    Raster.from_polygons('perimeter.shp', resolution=.01, units="miles")
    Raster.from_polygons('perimeter.shp', resolution=5, units="feet")



----

from_points
-----------

Sometimes, you may need to convert a set of points or multi-points to a raster. This is most common when including debris retainment features in an analysis. You can use the :ref:`Raster.from_points <pfdf.raster.Raster.from_points>` command to do so. The syntax is the same as :ref:`from_polygons <pfdf.raster.Raster.from_polygons>`, except that the file path should be for a point and/or multi-point feature file:

.. code:: pycon

    >>> # Boolean output
    >>> features = Raster.from_points('retainment-features.shp')
    >>> features.dtype
    bool

    >>> # Numeric output
    >>> features = Raster.from_points('retainment-features.shp', field='Volume')
    >>> features.dtype
    float64

    >>> # Subset of large dataset
    >>> features = Raster.from_points('large-dataset.shp', bounds=dem)

