Raster Representations
======================

It's often useful to represent the network as a raster, and these representations are used internally when :doc:`computing values <values>` for the individual stream segments. This section introduces the most common representations, and describes commands that return these rasters. Although these commands aren't strictly necessary for many hazard assessment workflows, they can help visualize how the class computes physical and statistical summaries.


.. _segments-raster-properties:

Spatial Metadata
----------------

Raster respresentations of the network will always match the spatial metadata of the flow direction raster used to derive the network. You can use the ``flow`` property to return this raster directly, or alternatively the ``raster_shape``, ``crs``, ``transform``, and ``bounds`` properties to return specific characteristics. As an example:

.. code:: pycon

    >>> # Create a network
    >>> segments = Segments(flow, mask)

    >>> # Examine its metadata
    >>> segments.raster_shape
    (3378, 2591)
    >>> segments.crs.name
    'NAD83 / UTM zone 11N'
    >>> print(segments.transform)
    Transform(dx=10, dy=-10, left=0, top=0, crs='NAD83 / UTM zone 11N')
    >>> segments.bounds
    BoundingBox(left=0, bottom=-25910, right=33780, top=0)

You can also use the flow raster to query other raster properties. For example:

.. code:: pycon

    >>> segments.flow.resolution()
    (10, 10)


.. _stream-raster:

Segments
--------
The **stream raster** is a commonly used raster representation of the stream network. This raster consists of a 0 background, with stream segments indicated by non-zero values. The value of each non-zero pixel will match of the ID of the associated stream segment. Confluence pixels are always assigned to the most downstream segment. You can use the :ref:`raster method <pfdf.segments.Segments.raster>` to return this raster::
    
    raster = segments.raster()

.. _segment-indices:

Relatedly, the ``indices`` property returns the indices of each segment's pixels within the stream raster. The property returns a list with one element per stream segment. Each element holds two numpy arrays with the row and column indices of the segment's pixels within the stream raster:

.. code:: pycon

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

It's often useful to locate outlet pixels within the stream raster. You can use the :ref:`outlets method <pfdf.segments.Segments.outlets>` to return the row and column indices of outlet pixels. Additionally, the :ref:`termini method <pfdf.segments.Segments.termini>` returns the IDs of each segment's associated terminal segment, and the :ref:`isterminal method <pfdf.segments.Segments.isterminal>` tests whether given segments are terminal or not:

.. code:: pycon

    >>> segments.outlet(5)
    (299, 684)
    >>> segments.outlets()
    [(298, 684), (329, 597), ..., (1167, 384), (1192, 355)]
    >>> segments.terminus(5)
    63
    >>> segments.termini()
    [63, 77, 77, ..., 625, 625, 625]
    >>> segments.isterminal(62)
    array([False])
    >>> segments.isterminal([62, 63, 77])
    array([False, True, True])


.. _basins:

Terminal Outlet Basins
----------------------

It can also be useful to represent segment basins as a raster. The **terminal outlet basins raster** is one such representation. This raster consists of a 0 background, with terminal outlet basins indicated by non-zero pixels. The value of each pixel is the ID of the terminal segment associated with the outlet basin. If a pixel belongs to multiple terminal outlet basins, then its value will match the ID of the terminal segment that is farthest downstream. You can return this raster by calling the :ref:`raster <pfdf.segments.Segments.raster>` method with ``basins`` option::

    basins = segments.raster(basins=True)

.. tip:: 
    
    Locating outlet basins is computationally difficult. See the :doc:`parallelization guide <parallel>` for options that can sometimes speed up this process.


.. _catchment-mask:

Catchment Mask
--------------

Sometimes it can be useful to return the **catchment basin mask** for a specific segment. For example, to locate the pixels used to compute a statistical summary over a segment's catchment basin. Here, a catchment mask is a boolean raster. True elements indicate pixels that belong to the segment's catchment basin. You can use the :ref:`catchment_mask <pfdf.segments.Segments.catchment_mask>` method to return these masks:: 

    catchment = segments.catchment_mask(id=5)
    
Note that you can also use the ``npixels`` property to return a numpy array with the number of pixels in the catchment basin of each segment:

.. code:: pycon

    >>> segments.npixels
    [2996, 1239, 3088, ..., 164093, 165903, 167035]
