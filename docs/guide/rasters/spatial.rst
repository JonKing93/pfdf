Spatial Metadata
================

As stated, a raster's spatial metadata consists of a coordinate reference system (CRS), and an affine transformation matrix. The transform converts pixel indices to spatial coordinates, and the CRS specifies the location of these coordinates on the Earth's surface. Another commonly used piece of spatial metadata is the raster's bounding box. The bounding box is the rectangle that bounds the raster, and it reports the spatial coodinates of the edges of the raster's data grid.

When the shape of a raster's data grid is known (as is the case for all *Raster* objects), you can implement a complete spatial reference system using either (1) a CRS and a transform, or (2) a CRS and a bounding box. The transform and bounding box provide the same information, albeit formatted for different purposes. The transform is typically more useful for examining pixel resolution and locations, whereas a bounding box is more useful for locating the edges or center of the overall raster dataset. 

The remainder of this page describes some common commands for examining a *Raster* object's :ref:`CRS <guide-crs>`, :ref:`transform <guide-transform>`, and :ref:`bounding box <guide-bbox>` metadata. Note that this page is only an introduction; you can find additional commands and more advanced use cases in the :doc:`spatial metadata tutorial </tutorials/notebooks/08_Spatial_Metadata>`.

----

.. _guide-crs:

CRS
---
You can use the ``crs`` property to return a *Raster* object's CRS. This will return a `pyproj.CRS object <https://pyproj4.github.io/pyproj/latest/examples.html>`_ with detailed information about the CRS. For example:

.. code:: pycon

    >>> raster.crs
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


Missing CRS
+++++++++++

If a *Raster* does not have a CRS, then the ``crs`` property will return ``None``. 

.. code:: pycon

    >>> # Raster lacking a CRS
    >>> print(raster.crs)
    None

When this is the case, you can use the property to specify a CRS for the raster. You can use any input accepted by pyproj to initialize the CRS, or alternatively another *Raster* object. Some common options include:

* An EPSG code, 
* A CRS name, 
* A *Raster* with the desired CRS, or 
* A PROJ4 string

::

    # Common options to initialize a CRS
    raster.crs = 4326                    # An EPSG code
    raster.crs = "NAD83 / UTM zone 11N"  # By name
    raster.crs = other_raster            # Another Raster object
    raster.crs = "+proj=latlon"          # A PROJ4 string

.. note::

    You cannot set the ``crs`` property if a *Raster* already has a CRS. However, see the :ref:`reproject method <guide-reproject>` to reproject a *Raster* to a different CRS.

----

.. _guide-transform:

Transform
---------

You can use the ``transform`` property to return a :ref:`Transform object <pfdf.projection.Transform>` for a *Raster*. A *Transform* object includes information on a raster's resolution, as well as the locations of the left and top edges:

.. code:: pycon

    >>> raster.transform
    Transform(dx=8.9e-05, dy=-9e-05, left=-121, top=0, crs="WGS 84")

Here, ``dx`` is the change in spatial coordinate when moving one pixel right, and ``dy`` is the change in spatial coordinate when moving one pixel down. Alternatively, you can use the ``affine`` property to return the transform as an `affine.Affine object <https://pypi.org/project/affine/>`_, which can be used for coordinate mathematics:

.. code:: pycon

    >>> raster.affine
    Affine(8.9e-05, 0.0, -121.0,
       0.0, -9e-05, 0.0)

You can also use the ``resolution`` method to return the raster's resolution. By default, resolution is reported in meters, but you can use the ``units`` option to report resolution in a different unit instead:

.. code:: pycon

    >>> # Default is meters
    >>> raster.resolution()
    (9.896348471216168, 10.007543398010286)

    >>> # But you can use other units
    >>> raster.resolution("feet")
    (32.46833488, 32.83314763)

    >>> # Report in the base units of the CRS
    >>> # (in this case, units are degrees)
    >>> raster.resolution(units="base")
    (8.9e-05, 9e-05)

Note that resolution is strictly positive. Equivalently, resolution is the absolute value of ``dx`` and ``dy``.

.. tip::

    See also the :doc:`spatial metadata tutorial </tutorials/notebooks/08_Spatial_Metadata>` for more advanced use of transform commands.


Missing Transform
+++++++++++++++++

If a *Raster* does not have a transform, then the ``transform`` property will return ``None``:

.. code:: pycon

    >>> # Raster without a transform
    >>> print(raster.transform)
    None

When this is the case, you can use the property to initialize a *Transform* for the raster. You can use a variety of inputs to initialize a transform. Some common options include: 

* A dict,
* A ``(dx, dy, left, top)`` list or tuple
* A *Transform* object,
* An `affine.Affine object <https://pypi.org/project/affine/>`_, or 
* A *Raster* object with the desired transform

::

    # Common options to initialize transform
    raster.transform = (10, -10, -121, 5)  # dx, dy, left, top
    raster.transform = {'dx': 10, 'dy': -10, 'left': -121, 'top': 5}
    raster.transform = other_raster
    raster.transform = Transform(10, -10, -121, 5)
    raster.transform = Affine(10, 0, -121, 0, -10, 5)

Since the transform and bounding box represent the same information, initializing the transform will also initialize the bounding box.

.. note::

    You cannot set the ``transform`` property if a *Raster* already has a transform. However, see the :ref:`reproject method <guide-reproject>` to reproject a *Raster* to a different transform.

----

.. _guide-bbox:

Bounding Box
------------
You can use the ``bounds`` property to return a :ref:`BoundingBox object <pfdf.projection.BoundingBox>` for a *Raster*. This reports the spatial coordinates raster's edges:

.. code:: pycon

    >>> raster.bounds
    BoundingBox(left=736399, bottom=4876354, right=846259, top=4990804, crs="NAD83 / UTM zone 11N")

You can also use the ``center`` property to return the coordinate at the center of the *BoundingBox*:

.. code:: pycon

    >>> raster.center
    (791329.0, 4933579.0)

And the ``utm_zone`` property returns the CRS of the UTM zone that overlaps this center coordinate:

.. code:: pycon

    >>> raster.utm_zone
    <Projected CRS: EPSG:32612>
    Name: WGS 84 / UTM zone 12N
    Axis Info [cartesian]:
    - E[east]: Easting (metre)
    - N[north]: Northing (metre)
    Area of Use:
    - name: Between 114°W and 108°W, northern hemisphere between equator and 84°N, onshore and offshore. Canada - Alberta; Northwest Territories (NWT); Nunavut; Saskatchewan. Mexico. United States (USA).
    - bounds: (-114.0, 0.0, -108.0, 84.0)
    Coordinate Operation:
    - name: UTM zone 12N
    - method: Transverse Mercator
    Datum: World Geodetic System 1984 ensemble
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich
    
.. tip::

    See also the :doc:`spatial metadata tutorial </tutorials/notebooks/08_Spatial_Metadata>` for more advanced use of BoundingBox commands.


Missing Bounding Box
++++++++++++++++++++

If a *Raster* does not have a *BoundingBox*, then the ``bounds`` property will return ``None``:

.. code:: pycon

    >>> # Raster without bounds
    >>> print(raster.bounds)
    None


When this is the case, you can use the property to initialize the bounding box. You can use a variety of inputs to initialize a bounding box. These include: 

* A ``(left, bottom, right, top)`` tuple/list, 
* A dict, 
* A *Raster* with the same bounds, or 
* A *BoundingBox* object

::

    # Common options to initialize bounds
    raster.bounds = (0, 5, 10, 100)  # left, bottom, right, top
    raster.bounds = {'left': 0, 'bottom': 5, 'right': 10, 'top': 100}
    raster.bounds = other_raster
    raster.bounds = BoundingBox(0, 5, 10, 100)

Since the bounding box and transform represent the same information, initializing the bounding box will also initialize the transform.

.. note::

    You cannot set the ``bounds`` property if a *Raster* already has a bounding box. However, see the :ref:`clip method <guide-clip>` to clip a *Raster* to different bounds.