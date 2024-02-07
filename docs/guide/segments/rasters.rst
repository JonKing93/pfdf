Raster Representations
======================

It's often useful to represent the network as a raster, and these representations are used internally when :doc:`computing values <values>` for the individual stream segments. This section introduces the most common representations, and describes commands that return these rasters. Although these commands aren't strictly necessary for many hazard assessment workflows, they can help visualize how the class computes physical and statistical summaries.


.. _segments-raster-properties:

Spatial Metadata
----------------

Raster respresentations of the network will always match the spatial metadata of the flow direction raster used to derive the network. You can use the ``flow`` property to return this raster directly, or alternatively the ``raster_shape``, ``transform``, ``crs``, ``resolution``, and ``pixel_area`` properties to return specific characteristics. When relevant, the units of these properties will match the base units of the coordinate reference system for the network. (In practice, these are often units of meters). As an example::

    >>> segments = Segments(flow, mask)
    >>> segments.raster_shape
    (3378, 2591)
    >>> print(segments.transform)
    |10,   0, 100|
    | 0, -10,   5|
    | 0,   0,   1|
    >>> print(segments.crs)
    EPSG:26911
    >>> segments.resolution
    (10.0, 10.0)
    >>> segments.pixel_area
    100.0


.. _stream-raster:

Segments
--------
The **stream raster** is a commonly used raster representation of the stream network. This raster consists of a 0 background, with stream segments indicated by non-zero values. The value of each non-zero pixel will match of the ID of the associated stream segment. Confluence pixels are always assigned to the most downstream segment. You can use the :ref:`raster method <pfdf.segments.Segments.raster>` to return this raster::
    
    >>> raster = segments.raster()

.. _segment-indices:

Relatedly, the ``indices`` property returns the indices of each segment's pixels within the stream raster. The property returns a list with one element per stream segment. Each element holds two numpy arrays with the row and column indices of the segment's pixels within the stream raster::

    >>> segments.indices
    [
        (
            [298, 298, 298, 298, 298, 298, 298, 298, 298, 298, 298, 298, 298, 298, 298],
            [670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684]
        ),
        ...
        (
           [1168, 1169, ..., 1192, 1192],
           [384, 384, ..., 356, 355]
        )
    ]


.. _outlets:

Outlets
-------

It's often useful to locate outlet pixels within the stream raster. You can use the :ref:`outlet method <pfdf.segments.Segments.outlet>` to return the row and column index of a queried segment's outlet or terminal outlet pixel. Alternatively, use the :ref:`outlets <pfdf.segments.Segments.outlets>` (plural) method to return a list of all outlet or terminal outlet pixel indices. Two other methods further support working with terminal outlets. The :ref:`terminus <pfdf.segments.Segments.terminus>` method returns the ID of a queried segment's terminal segment, and the :ref:`termini <pfdf.segments.Segments.termini>` method returns a numpy array with the IDs of all terminal segments::

    >>> segments.outlet(5)
    (299, 684)
    >>> segments.outlets()
    [(298, 684), (329, 597), ..., (1167, 384), (1192, 355)]
    >>> segments.terminus(5)
    63
    >>> segments.termini()
    [63, 73, 77, ..., 625, 634, 658]


.. _basins:

Terminal Basins
---------------

It can also be useful to represent segment basins as a raster. The **terminal outlet basins raster** is one such representation. This raster consists of a 0 background, with terminal outlet basins indicated by non-zero pixels. The value of each pixel is the ID of the terminal segment associated with the outlet basin. If a pixel belongs to multiple terminal outlet basins, then its value will match the ID of the terminal segment that is farthest downstream. You can return this raster by calling the :ref:`raster <pfdf.segments.Segments.raster>` method with ``basins`` option::

    >>> basins = segments.raster(basins=True)

.. tip:: 
    
    Locating outlet basins is computationally difficult. See the :doc:`parallelization guide <parallel>` for options that can sometimes speed up this process.


.. _basin-mask:

Basin Mask
----------

Sometimes it can be useful to return the **catchment basin mask** for a specific segment. For example, to locate the pixels used to compute a statistical summary over a segment's catchment basin. Here, a basin mask is a boolean raster. True elements indicate pixels that belong to the segment's catchment basin. You can return basin masks using the :ref:`basin_mask <pfdf.segments.Segments.basin_mask>` method:: 

    >>> catchment = segments.basin_mask(id=5)
    
Note that you can also use the ``npixels`` property to return a numpy array with the number of pixels in the catchment basin of each segment::

    >>> segments.npixels
    [2996, 1239, 3088, ..., 164093, 165903, 167035]
