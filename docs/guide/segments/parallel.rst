Parallelizing Basins
====================

.. highlight:: python

locate_basins
-------------

Locating outlet basins is a computationally difficult task, so the :doc:`raster <rasters>`, :ref:`isnested <pfdf.segments.Segments.isnested>`, :ref:`geojson <pfdf.segments.Segments.geojson>`, and :ref:`save <pfdf.segments.Segments.save>` commands may take a long time to run when working with basins::
    
    # May take a long time to run
    segments.raster(..., basins=True)
    segments.isnested()
    segments.geojson(..., type="basins")
    segments.save(..., type="basins")
    
    
When this is the case, you may be able to use parallelization to hasten this computation. The key command for parallelization is :ref:`locate_basins <pfdf.segments.Segments.locate_basins>`. This command locates terminal outlet basins, and stores the locations internally for later use::
    
    # This will still take a while
    segments.locate_basins()

    # But now these commands are fast,
    # because the basins were pre-located
    segments.raster(..., basins=True)
    segments.isnested()
    segments.geojson(..., type="basins")
    segments.save(..., type="basins")

Setting the ``parallel`` option to True will cause the command to use multiple CPUs to locate the basins, which can potentially speed up this process::

    # Potentially much faster
    segments.locate_basins(parallel=True)

By default, the method will use the number of available CPUs - 1 (one CPU is reserved for the current process), but you can use the ``nprocess`` option to specify the number of parallel processes that should be used::

    # Explicit number of processes
    segments.locate_basins(parallel=True, nprocess=11)

.. note::

    Speed improvements will scale with the number of CPUs and the size of the watershed. Small watersheds will benefit minimally, and may even run slower due to parallelization overhead.

.. tip::

    Filtering the network may delete internally saved basin locations. As such, we recommend calling ``locate_basins`` *after* any filtering.


Requirements
------------

The use of the ``parallel`` option adds two requirements. First, the parallel option cannot be used in an interactive Python session (it will cause the terminal to crash). Instead, you must use the option in a script called from the command line. For example:


.. code:: bash

    python -m my_parallel_script

----

Second, the code in the parallelized script must be protected by a ``if __name__ == "__main__"`` block. So for example::

    from pfdf.segments import Segments
    from pfdf.raster import Raster

    if __name__ == "__main__":
        flow = Raster('flow.tif')
        mask = Raster('mask.tif')
        segments = Segments(flow, mask)

        segments.locate_basins(parallel=True)
        segments.save('my-basins.shp', type="basins")

Neglecting this step will cause the routine to attempt to create an infinite number of parallel processes, crashing the terminal.

.. tip:: See also the :doc:`parallel basins tutorial </tutorials/parallel>` for a detailed example of basin parallelization.

