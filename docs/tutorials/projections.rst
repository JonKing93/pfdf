Spatial Projection Tutorial
===========================

This tutorial demonstrates advanced usage of the :ref:`Transform <pfdf.projection.transform.Transform>` and :ref:`BoundingBox <pfdf.projection.bbox.BoundingBox>` classes. Most users will not need these classes, as the :doc:`raster preprocessing routines </guide/rasters/preprocess>` should be sufficient for most common use cases. However, advanced developers may be interested in using these classes to develop custom geospatial routines.


.. admonition:: Download

    The following list provides download links for the tutorial resources:

    * :doc:`Tutorial Datasets <download>`
    * :download:`BoundingBox Script <scripts/bounds.py>`
    * :download:`Transform Script <scripts/transform.py>`


Introduction
------------

The Transform and BoundingBox classes provide information used to spatially locate a raster dataset. In addition to spatial locations, the classes also provide various routines to help facilitate geospatial processing and reprojections. The BoundingBox class is often more useful for geospatial processing, as it provides information on the latitude of a dataset, whereas the Transform class does not. This latitude information is useful when working with angular (geographic) coordinate reference systesms, as the absolute width of longitude units will vary with the latitude of the dataset.

That said, Transform objects provide useful information on pixel resolution and geometries not available from BoundingBox objects. Furthermore, many open-source geospatial libraries rely on affine Transforms to manage raster datasets, so geospatial developers will likely want to use both classes.

Conceptually, Transform and BoundingBox objects both rely on 4 values relating to spatial coordinates. Each also supports an optional CRS, which locates the spatial coordinates on the Earth's surface. The two classes include options to convert distances between CRS units (referred to as "base" units) and explicit metric or imperial units. If you do not provide a CRS, then the object's base units are ambiguous, and the class cannot convert to metric or imperial units. As such, we recommend including CRS information whenever possible.

----

BoundingBox
-----------

You can use :ref:`BoundingBox objects <pfdf.projection.bbox.BoundingBox>` to locate the spatial coordinates of a raster's edges. These objects include a number of methods useful for geospatial manipulations including: :ref:`locating a raster's center <pfdf.projection.bbox.BoundingBox.center>`, :ref:`reprojection <pfdf.projection.bbox.BoundingBox.reproject>`, :ref:`buffering <pfdf.projection.bbox.BoundingBox.buffer>`, and :ref:`identifying UTM zones <pfdf.projection.bbox.BoundingBox.utm_zone>`. You can also convert a BoundingBox to a :ref:`Transform object <pfdf.projection.transform.Transform>` when combined with a raster shape.

::

    from pfdf.projection import BoundingBox

A BoundingBox relies on the following 4 properties:

* ``left``: The X coordinate of the box's left edge,
* ``bottom``: The Y coordinate of the box's bottom edge
* ``right``: The X coordinate of the box's right edge, and
* ``top``: The Y coordinate of the box's top edge

and an optional ``crs`` property determines the location of the X and Y coordinates on the Earth's surface.


Create BoundingBox
++++++++++++++++++

You can use the :ref:`BoundingBox constructor <pfdf.projection.bbox.BoundingBox.__init__>` to create a new BoundingBox object. The constructor has four required arguments: ``left``, ``bottom``, ``right``, and ``top``. It also accepts an optional ``crs`` argument::

    # With / without a CRS
    >>> BoundingBox(left=50, bottom=0, right=2000, top=4000)
    >>> BoundingBox(left=50, bottom=0, right=2000, top=4000, crs=26911)

Alternatively, you can use the :ref:`from_dict <pfdf.projection.bbox.BoundingBox.from_dict>` or :ref:`from_list <pfdf.projection.bbox.BoundingBox.from_list>` methods to create a BoundingBox from a dict or list/tuple::

    # From a dict. CRS key is optional
    >>> input = {'left': 50, 'bottom': 0, 'right': 2000, 'top': 4000, 'crs': 26911}
    >>> BoundingBox.from_dict(input)

    # From a list or tuple. With/without CRS
    >>> BoundingBox.from_list([50, 0, 2000, 4000])
    >>> BoundingBox.from_list([50, 0, 2000, 4000, 26911])

Conversely, you can convert a BoundingBox to a dict or list using the ``tolist`` and ``todict`` methods::

    >>> bounds = BoundingBox(50, 0, 2000, 4000)
    >>> bounds.todict()
    {'left': 50, 'bottom': 0, 'right': 2000, 'top': 4000, 'crs': None}
    >>> bounds.tolist()
    [50, 0, 2000, 4000, None]


Properties
++++++++++

You can return the spatial coordinates of the left, bottom, right, and top edges using properties of the same name::

    >>> bounds.left
    50
    >>> bounds.bottom
    0
    >>> bounds.right
    2000
    >>> bounds.top
    4000

Alternatively, you can return the X or Y coordinates using the ``xs`` or ``ys`` properties::

    >>> bounds.xs
    (50, 2000)
    >>> bounds.ys
    (0, 4000)

You can also return the (X, Y) coordinate of the box's center using the ``center`` property::

    >>> bounds.center
    (1025.0, 2000.0)

The ``crs`` property returns the box's CRS as a `pyproj.CRS object <https://pyproj4.github.io/pyproj/stable/index.html>`_, and ``units`` returns the units of the CRS along the X and Y axes::

    # CRS
    >>> bounds = BoundingBox(-121, 30, -119, 40, crs=4326)
    >>> bounds.crs
    <Geographic 2D CRS: EPSG:4326>
    Name: WGS 84
    Axis Info [ellipsoidal]:
    - Lat[north]: Geodetic latitude (degree)
    - Lon[east]: Geodetic longitude (degree)
    Area of Use:
    - name: World.
    - bounds: (-180.0, -90.0, 180.0, 90.0)
    Datum: World Geodetic System 1984 ensemble
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

    # CRS Units
    >>> bounds.units
    ('degree', 'degree')

And you can use ``units_per_m`` to convert these units to meters::

    >>> bounds.units_per_m
    (1.097868963629726e-05, 8.993216059187306e-06)

For angular (geographic) coordinate systems, the number of X units per meter will depend on the latitude of the dataset because longitude units become shorter at higher latitudes. Here, the reported X units per meter is specifically the value at the center of the BoundingBox.

Finally, the ``orientation`` property returns the Cartesian quadrant that would contain the box if the origin point were defined as the box's minimum (X, Y) coordinate. Equivalently, the orientation indicates whether left <= right, and whether bottom <= top. For example::

    >>> BoundingBox(0, 2, 10, 5).orientation
    1
    >>> BoundingBox(10, 2, 0, 5).orientation
    2
    >>> BoundingBox(10, 5, 0, 2).orientation
    3
    >>> BoundingBox(0, 5, 10, 2).orientation
    4


Height and Width
++++++++++++++++

Use the ``height`` method to return the distance between the top and bottom edges of the BoundingBox. Similarly, use ``width`` to return the distance between left and right. By default, these methods return values in CRS base units, but you can use the ``units`` option to return values in other units instead::

    # CRS base units (degrees in this case)
    >>> bounds = BoundingBox(-121, 30, -119, 35, crs=4326)
    >>> bounds.height()
    5
    >>> bounds.width()
    2

    # In kilometers
    >>> bounds.height("kilometers")
    555.9746332227937
    >>> bounds.width("kilometers")
    187.55895063575267


.. note::

    The ``height`` and ``width`` methods always return positive values. If orientation is important, you can alternatively use ``xdisp`` to return (right - left) and ```ydisp`` to return (top - bottom). These two values may be negative, depending on the orientation of the box.

Reprojection
++++++++++++
BoundingBox objects provide several methods to support CRS reprojection. The ``utm_zone`` method returns the CRS of the UTM zone overlapping the box's center::

    >>> bounds = BoundingBox(-121, 30, -119, 35, crs=4326)
    >>> bounds.utm_zone()
    <Projected CRS: EPSG:32610>
    Name: WGS 84 / UTM zone 10N
    Axis Info [cartesian]:
    - E[east]: Easting (metre)
    - N[north]: Northing (metre)
    Area of Use:
    - name: Between 126°W and 120°W, northern hemisphere between equator and 84°N, onshore and offshore. Canada - British Columbia (BC); Northwest Territories (NWT); Nunavut; Yukon. United States (USA) - Alaska (AK).
    - bounds: (-126.0, 0.0, -120.0, 84.0)
    Coordinate Operation:
    - name: UTM zone 10N
    - method: Transverse Mercator
    Datum: World Geodetic System 1984 ensemble
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich

and the ``reproject`` method returns a copy of the box reprojected to the indicated CRS::

    >>> bounds = BoundingBox(-121, 30, -119, 35, crs=4326)
    >>> bounds.reproject(crs=26911)
    BoundingBox(left=114051.41723635053, bottom=3320469.2864025724, right=317483.9063835636, top=3880360.1493709222, crs="NAD83 / UTM zone 11N")

Two convenience methods provide quick reprojection to common CRSs. The ``to_utm`` method reprojects the box to the UTM zone overlapping the center point, and ``to_4326`` reprojects the box to EPSG:4326 (often referred to as WGS 84)::

    >>> bounds = BoundingBox(1.1e5, 3.3e6, 3.1e5, 3.8e6, crs=26911)
    >>> bounds.to_utm()
    BoundingBox(left=662481.0003292296, bottom=3294800.314444784, right=889934.600366077, top=3805086.2702514306, crs="WGS 84 / UTM zone 10N")
    >>> bounds.to_4326()
    BoundingBox(left=-121.23509435567578, bottom=29.76890453615655, right=-118.96616273316769, top=34.32388568922283, crs="WGS 84")


Misc geospatial
+++++++++++++++

You can use the ``orient`` method to return a copy of the BoundingBox in the requested orientation. By default, this method places the box in the first Cartesian quadrant, but you can optionally specify a different quadrant instead::

    # Orient into the first quadrant
    >>> bounds = BoundingBox(100, 8, 50, 1)
    >>> bounds.orient()
    BoundingBox(left=50, bottom=1, right=100, top=8, crs=None)

    # Or other quadrants
    >>> bounds.orient(2)
    BoundingBox(left=100, bottom=1, right=50, top=8, crs=None)
    >>> bounds.orient(3)
    BoundingBox(left=100, bottom=8, right=50, top=1, crs=None)
    >>> bounds.orient(4)
    BoundingBox(left=50, bottom=8, right=100, top=1, crs=None)

Separately, you can use the ``buffer`` method to return a copy of the box that has been buffered by a specified distance::

    # Buffer all edges the same amount
    >>> bounds = BoundingBox(50, 0, 2000, 4000, crs=26911)
    >>> bounds.buffer(2, units='kilometers')
    BoundingBox(left=-1950.0, bottom=-2000.0, right=4000.0, top=6000.0, crs="NAD83 / UTM zone 11N")

    # Buffer edges by specific distances
    >>> bounds.buffer(left=0, right=12, bottom=100, top=50)
    BoundingBox(left=50, bottom=-100, right=2012, top=4050, crs="NAD83 / UTM zone 11N")


Transform Conversion
++++++++++++++++++++

When combined with a raster shape, a BoundingBox can be converted to a Transform object. This can be useful if you need to determine resolution or pixel geometries for the raster. To convert a BoundingBox object, use the ``transform`` method with a raster shape::

    # Get a BoundingBox and raster shape
    >>> bounds = BoundingBox(50, 0, 2000, 4000, crs=26911)
    >>> nrows, ncols = (1000, 200)

    # Convert to Transform
    >>> transform = bounds.transform(nrows, ncols)
    >>> print(transform)
    Transform(dx=9.75, dy=-40.0, left=50, top=4000, crs="NAD83 / UTM zone 11N")

----

Transform
---------

You can use :ref:`Transform objects <pfdf.projection.transform.Transform>` to describe a raster's affine transformation matrix. These objects include a number of methods with information on pixel geometries and resolution. You can also convert a Transform to a :ref:`BoundingBox object <pfdf.projection.bbox.BoundingBox>` when combined with a raster shape.

::

    >>> from pfdf.projection import Transform

A Transform relies on the following 4 values:

* ``dx``: The change in X coordinate when moving one pixel right,
* ``dy``: The change in Y coordinate when moving one pixel down,
* ``left``: The X coordinate of the left edge of the raster, and
* ``top``: The Y coordinate of the top edge of the raster

and an optional ``crs`` property determines the location of X and Y coordinates on the Earth's surface.


Create Transform
++++++++++++++++

You can use the :ref:`Transform constructor <pfdf.projection.transform.Transform.__init__>` to create a new Transform object. The constructor has four required arguments: ``dx``, ``dy``, ``left``, and ``top`` and an optional ``crs`` argument::

    # With / without a CRS
    >>> Transform(dx=10, dy=-10, left=5000, top=19)
    >>> Transform(10, -10, 5000, 19, crs=26911)

Alternatively, you can use the :ref:`from_dict <pfdf.projection.transform.Transform.from_dict>`, :ref:`from_list <pfdf.projection.transform.Transform.from_list>`, and :ref:`from_affine <pfdf.projection.transform.Transform.from_affine>` commands to create a Transform from a dict, list, tuple, or `affine.Affine object <https://pypi.org/project/affine/>`_::

    # From a dict. CRS key is optional
    >>> input = {'dx': 10, 'dy': -10, 'left': 5000, 'top': 19, 'crs': 26911}
    >>> Transform.from_dict(input)

    # From a list or tuple. With/without CRS
    >>> Transform.from_list([10, -10, 5000, 19])
    >>> Transform.from_list([10, -10, 5000, 19, 26911])

    # From an affine.Affine object
    >>> from affine import Affine
    >>> input = Affine(10, 0, 5000, 0, -10, 19)
    >>> Transform.from_affine(input)

Conversely, you can convert a Transform to a dict or list using the ``tolist`` and ``todict`` methods::

    >>> transform = Transform(10, -10, 5000, 19)
    >>> transform.todict()
    {'dx': 10, 'dy': -10, 'left': 5000, 'top': 19, 'crs': None}
    >>> transform.tolist()
    [10, -10, 5000, 19, None]

Properties
++++++++++

You can return left, top, and crs using properties of the same name::

    >>> transform.left
    5000
    >>> transform.top
    19
    >>> transform.crs.name
    'NAD83 / UTM zone 11N'

You can also query the base units of the CRS (along the X and Y axes) using the ``units`` property::

    >>> transform.units
    ('metre', 'metre')

The `affine` property returns the Transform as an `affine.Affine object <https://pypi.org/project/affine/>`_ suitable for coordinate mathematics::

    >>> transform.affine
    Affine(10.0, 0.0, 5000.0,
        0.0, -10.0, 19.0)

and ``orientation`` returns the Cartesian quadrant that would contain the raster if the origin point were defined using the raster's minimum X and Y coordinates. Equivalently, the quadrant is determined by the sign of the ``dx`` and ``dy`` values::

    >>> Transform(1,-1,0,0).orientation
    1
    >>> Transform(-1,-1,0,0).orientation
    2
    >>> Transform(-1,1,0,0).orientation
    3
    >>> Transform(1,1,0,0).orientation
    4


Resolution
++++++++++

You can return ``dx``, ``dy``, and a tuple of (X axis, Y axis) resolution using the methods of the same name::

    >>> transform = Transform(10, -10, 0, 0, 26911)
    >>> transform.dx()
    10
    >>> transform.dy()
    -10
    >>> transform.resolution()
    (10, 10)

.. note:: 
    
        Resolution is the absolute value of dx and dy, so is strictly positive. 
    
By default, these methods will return values in the base unit of the CRS, and you can use the ``units`` option to return the values in explicit metric or imperial units::

    # Default is CRS base units
    >>> transform = Transform(9e-5, 9e-5, -121, 0, 4326)
    >>> transform.dx()
    9e-5
    >>> transform.dy()
    -9e-5
    
    # Other units
    >>> transform.dx(units="meters")
    10.007543398010286 
    >>> transform.dy("feet") 
    -32.833147631267344

The values for ``dy`` are always constant. However, ``dx`` values are variable when using an angular (geographic) CRS, due to the changing width of longitude units at different latitudes. By default, ``dx`` and ``resolution`` return values as measured at the equator. However, you can use the ``y`` input to obtain more accurate results at other latitudes. This input should be the latitude of the raster's center in the base units of the angular CRS. In practice, this is typically units of decimal degrees::

    # Transform with an angular CRS
    >>> transform = Transform(9e-5, -9e-5, -121, 30, crs=4326)

    # Values as measured at the equator
    >>> transform.dx("meters")
    10.007543398010286
    >>> transform.resolution("meters")
    (10.007543398010286, 10.007543398010286)

    # dx is smaller at higher latitudes
    >>> transform.dx("meters", y=35)
    8.197699632790652
    >>> transform.resolution("meters", y=35)
    (8.197699632790652, 10.007543398010286)


Pixel Geometries
++++++++++++++++

You can use the ``pixel_area`` method to return the area of a single pixel, and ``pixel_diagonal`` to return the length of a pixel diagonal. Both of these commands support the ``units`` and ``y`` options discussed in the previous section::

    >>> transform = Transform(9e-5, -9e-5, -121, 30, 4326)

    # Pixel area at equator and higher latitude
    >>> transform.pixel_area("meters")
    100.15092486305926
    >>> transform.pixel_area("meters", y=35)
    82.03883483900543

    # Pixel diagonal at equator and higher latitude
    >>> transform.pixel_diagonal("meters")
    14.152803599503475
    >>> transform.pixel_diagonal("meters", y=35)
    12.93650664331431


BoundingBox Conversion
++++++++++++++++++++++

When combined with a raster shape, a Transform can be converted to a BoundingBox object. This can be useful, as BoundingBox objects include methods not supported by Transform objects. For example, you can use a BoundingBox to return the raster's center, determine the best UTM projection, or determine the bounds of a buffered raster.

To convert a Transform object, use the ``bounds`` method with a raster shape::

    # Get a Transform object and raster shape
    >>> transform = Transform(10, -10, 0, , 26911)
    >>> nrows, ncols = (1000, 2000)

    # Convert to BoundingBox
    >>> bounds = transform.bounds(nrows, ncols)
    >>> print(bounds)
    BoundingBox(left=0, bottom=-10000, right=20000, top=0, crs="NAD83 / UTM zone 11N")


Reprojection
++++++++++++

Transform objects include a ``reproject`` method, which will convert the Transform to a different CRS::

    >>> transform = Transform(10, -10, 0, 0, 26911)
    >>> transform.reproject(crs=4326)
    Transform(dx=8.958996677677078e-05, dy=-9.019376924314101e-05, left=-121.48874388438703, top=0.0, crs="WGS 84")

However, BoundingBox objects provide more accurate reprojections than Transform objects. As such, the preferred reprojection workflow for Transforms is as follows:
    
1. Convert the Transform to a BoundingBox object,
2. Reproject the BoundingBox,
3. Convert the reprojected BoundingBox back to a Transform





