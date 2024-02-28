Raster Preprocessing
====================

Some pfdf routines requires multiple rasters as input. When this is the case, the routine will require each raster to have the same shape, CRS and transform. Other routines require a raster to fall within a valid data range. In reality, most datasets are not this clean, and so *Raster* objects support a number of preprocessing commands to help meet these requirements.

.. note:: The commands in this section usually alter an existing raster in-place, rather than returning a new *Raster* object.

.. tip:: See also the :doc:`preprocessing tutorial </tutorials/preprocess>` for in-depth examples of these commands.


buffer
------
Use the :ref:`buffer <pfdf.raster.Raster.buffer>` command to add NoData pixels to the edges of a raster for a specified distance::

    # Create a Raster from a fire perimeter
    >>> perimeter = Raster.from_polygons('perimeter.shp')
    >>> perimeter.resolution
    (10, 10)
    >>> perimeter.shape
    (3000, 2500)

    # Buffer the perimeter by 1000 units
    >>> perimeter.buffer(distance=1000)
    >>> perimeter.shape
    (3200, 2700)

Note that buffering distance is interpreted in the units of the transform. Use the ``pixels`` option to specify the buffer in pixels instead::

    # Buffer the perimeter by 5 pixels
    >>> perimeter.shape
    (3000, 2500)
    >>> perimeter.buffer(distance=5, pixels=True) 
    >>> perimeter.shape
    (3010, 2510)


reproject
---------
Use the :ref:`reproject <pfdf.raster.Raster.reproject>` method to reproject a *Raster* to the same CRS and transform of another (template) *Raster*::

    # The CRS of the DEM is 26911
    >>> dem = Raster('dem.tif')
    >>> print(dem.CRS)
    EPSG:26911

    # The CRS of the dNBR is 4326
    >>> dnbr = Raster('dnbr.tif')
    >>> print(dnbr.CRS)
    EPSG:4326

    # Reprojects the dNBR to 26911
    >>> dnbr.reproject(template=dem)
    >>> print(dnbr.CRS)
    EPSG:26911

By default, this method will use nearest-neighbor interpolation to reproject the raster. Use the ``resampling`` option to select a different algorithm::

    # Uses bilinear resampling
    >>> dnbr.reproject(template=dem, resampling='bilinear')

See the :ref:`reproject API <pfdf.raster.Raster.reproject>` for a complete list of supported algorithms.


clip
----
Use the :ref:`clip <pfdf.raster.Raster.clip>` command to match a raster's bounds to the bounds of a second raster::

    # The DEM's spatial bounds
    >>> dem = Raster('dem.tif')
    >>> dem.bounds
    BoundingBox(left=0, bottom=0, right=100, top=100)

    # The dNBR has different bounds
    >>> dnbr = Raster('dnbr.tif')
    >>> dnbr.bounds
    BoundingBox(left=20, bottom=20, right=150, top=150)

    # Clip the dNBR to the bounds of the DEM
    >>> dnbr.clip(bounds=dem)
    >>> dnbr.bounds
    BoundingBox(left=0, bottom=0, right=100, top=100)

Note that if a raster is clipped outside its initial bounds, then the exterior pixels will be filled with NoData.
    


set_range
---------
Use the :ref:`set_range <pfdf.raster.Raster.set_range>` method to constrain a dataset to a valid data range::

    # A raw dNBR dataset has a large range of data values
    >>> import numpy as np
    >>> dnbr = Raster('dnbr.tif')
    >>> np.min(dnbr.values)
    -9000
    >>> np.max(dnbr.max)
    3520

    # Constrain the dNBR to an expected data range
    >>> dnbr.set_range(min=-1000, max=1000)
    >>> np.min(dnbr.values)
    -1000
    >>> np.max(dnbr.values)
    1000

By default, out-of-range pixels are set to the value of the nearest bound. Use the ``fill`` option to replace these pixels with NoData instead::

    # Replaces out-of-range pixels with NoData values
    >>> dnbr.set_range(min=-1000, max=1000, fill=True)



find
----

Use the :ref:`find <pfdf.raster.Raster.find>` method to locate raster pixels that match the indicated data values. This command is particularly useful for building terrain masks from existing vegetation type (EVT) datasets::

    # 7292 is sometimes used to classify a pixel as open water
    >>> evt = Raster('evt.tif')
    >>> iswater = evt.find(7292)
    >>> print(iswater.dtype)
    bool

    # These values are used to classify human-developed terrain and roads
    >>> development = [7296, 7297, 7298, 7299, 7300]
    >>> isdeveloped = evt.find(development)
    >>> print(isdeveloped.dtype)
    bool

.. note:: Unlike the other preprocessing routines, this command produces a new *Raster* as output.


