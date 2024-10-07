Rasters
=======

Rasters are fundamental inputs for most pfdf routines. In brief, a raster dataset is a 2D rectangular grid of data values. The individual data values (often called "pixels") are regularly spaced along the X and Y axes, and each axis may use its own spacing interval. A raster is typically associated with some spatial metadata, which is used to locate the raster pixels in space. A raster may also have a NoData value; pixels equal to this value represent missing data.

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

    # Import the Raster class
    from pfdf.raster import Raster

This class includes methods to:

* Load rasters from a variety of formats,
* Access raster data and metadata
* Preprocess rasters prior to assessment, and
* Save rasters to file

.. note:: See also the :doc:`raster </tutorials/rasters>` and :doc:`preprocessing </tutorials/preprocess>` tutorials for detailed examples using *Raster* commands.

In many cases, you can create a *Raster* object by calling :ref:`the constructor <pfdf.raster.Raster.__init__>` on a file or an array-like dataset. For example, from a file:

.. code:: pycon

    >>> # File-based dataset
    >>> dem = Raster('dem.tif')
    Raster:
        Name: raster
        Shape: (11445, 10986)
        Dtype: float32
        NoData: -999999.0
        CRS("NAD83 / UTM zone 11N")
        Transform(dx=10, dy=-10, left=736399, top=4990804, crs="NAD83 / UTM zone 11N")
        BoundingBox(left=736399, bottom=4876354, right=846259, top=4990804, crs="NAD83 / UTM zone 11N")

or from a numpy array:

.. code:: pycon

    >>> # From a numpy array
    >>> import numpy as np
    >>> array = np.arange(200).reshape(20,10)
    >>> raster = Raster(array)
    Raster:
        Name: raster
        Shape: (20, 10)
        Dtype: int32
        NoData: -2147483648
        CRS: None
        Transform: None
        BoundingBox: None

Once you have a *Raster* object, you can save the raster to file using the :ref:`save method <pfdf.raster.Raster.save>`::

    # Save to file
    raster.save('my-raster.tif')


Data Properties
----------------

Each *Raster* represents its data grid as a 2D numpy array. You can use the ``values`` property to return this array:

.. code:: pycon

    >>> # Return Raster data values
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
    array = dem.values + 1

    # As is this (copied before changing values)
    values = dem.values.copy()
    values[0,0] = 1

    # But not this (didn't copy, so will raise an error)
    dem.values[0,0] = 1

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

(and see the :doc:`Raster API </api/raster>` for a complete summary of *Raster* properties). The remainder of this section will outline key *Raster* commands, and see also the :doc:`raster </tutorials/rasters>`, :doc:`preprocessing </tutorials/preprocess>`, and :doc:`projection </tutorials/projections>` tutorials for more detailed examples.

