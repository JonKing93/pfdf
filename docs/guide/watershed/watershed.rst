Watershed Module
================

The :ref:`watershed module <pfdf.watershed>` provides functions that analyze watersheds using output from a digital elevation model (DEM). Most notably, the ``flow`` function is used to compute flow directions, which are required to delineate a stream segment network. Note that the functions in this module process an entire watershed raster. Please read the :doc:`segments module </guide/segments/values>` if you only need values for individual stream segments or stream segment catchment basins.

The typical base workflow for using this module is to use:

1. :ref:`condition` to condition a DEM (fill pits and resolve flats), and then
2. :ref:`flow` to compute D8 flow directions from the conditioned DEM

These flow directions are an essential input to all other watershed functions, as well as the :doc:`Segments class </guide/segments/index>`. From here, many users will use:

3. :ref:`accumulation` to compute flow accumulations of various quantities,
4. :ref:`slopes` to compute flow slopes, and
5. :ref:`relief` to compute vertical relief.


.. admonition:: DEM Resolution

    Many of the hazard assessment models in pfdf were calibrated using data from a 10 meter DEM. As such, we recommend using a 10 meter DEM for standard applications of the models. Read `Smith et al., (2019) <https://doi.org/10.5194/esurf-7-475-2019>`_ for a discussion of the effects of DEM resolution on topographic analysis.


.. admonition:: Georeferencing

    The :ref:`slopes function <pfdf.watershed.slopes>` requires the input DEM to have both a CRS and affine Transform. Most workflows will require flow slopes, so we recommend using a properly georeferenced DEM whenever possible.


.. warning:: 
    
    The functions in this module rely on the pysheds library, which assigns a default NoData of 0 to any raster lacking a NoData value. This can cause unexpected results when a raster has valid 0 values and lacks NoData. Consider using a placeholder NoData when this is the case.


.. _condition:

Condition
---------
The first step for most users is to apply the :ref:`condition <pfdf.watershed.condition>` function to a DEM. This step will:

1. Fill pits (single-pixel low points),
2. Fill depressions (multi-cell low points), and
3. Resolve flats

Note that this function returns a new conditioned *Raster* object as output - it does not modify the input DEM dataset::

    # Condition a DEM
    from pfdf import watershed
    from pfdf.raster import Raster
    dem = Raster('dem.tif')
    conditioned = watershed.condition(dem)

You can also use the ``fill_pits``, ``fill_depressions``, and ``resolve_flats`` options to disable specific conditioning steps::

    # Disable steps of the DEM conditioning algorithm
    output = watershed.condition(dem, fill_pits=False)
    output = watershed.condition(dem, fill_depressions=False)
    output = watershed.condition(dem, resolve_flats=False)


.. _flow:

Flow Directions
---------------
Next, use the :ref:`flow function <pfdf.watershed.flow>` to compute flow directions from the conditioned DEM::

    flow = watershed.flow(conditioned)


.. _taudem-style:

This function produces D8 flow directions in the `TauDEM <https://hydrology.usu.edu/taudem/taudem5/>`_ style:

.. math::

    \begin{matrix}
    4 & 3 & 2\\
    5 & \mathrm{X} & 1\\
    6 & 7 & 8\\
    \end{matrix}  

where X is the current pixel, and integers indicate flow in a particular direction. So for example, if pixel X flows into the next pixel to the left, then X will be marked with a flow direction of 5. But if X flows into the pixel to the right, then its flow direction will be 1.

.. important:: 
    
    All pfdf routines that use flow directions require values in the `TauDEM <https://hydrology.usu.edu/taudem/taudem5/>`_ style. Keep this in mind if you use something other than this function to compute flow directions.


.. _accumulation:

Accumulation
------------
The :ref:`accumulation <pfdf.watershed.accumulation>` function computes flow accumulation for each pixel in the watershed. In the simplest case, the value for each pixel is the number of upstream pixels flowing into it::
    
    npixels = watershed.accumulation(flow)

You can use the ``times`` option to apply a multiplicative constant to these pixel counts. Setting the option equal to the area of a raster pixel will return accumulation in area, rather than pixel counts::

    pixel_area = flow.pixel_area(units="meters")
    area_m2 = watershed.accumulation(flow, times=pixel_area)

You can also compute accumulation using a second raster as pixel weights. For example, you could use::

    barc4 = Raster('barc4.tif')
    isburned = barc4.values > 0
    nburned = watershed.accumulation(flow, weights=isburned)

to compute the number of burned upstream pixels.


.. _slopes:

Slopes
------

D8 flow slopes are often useful for implementing :doc:`hazard assessment models </guide/models/s17>`. You can compute them using the :ref:`slopes function <pfdf.watershed.slopes>`::

    slopes = watershed.slopes(dem, flow)

Note that this function requires the DEM to have both a CRS and an affine Transform. The function also assumes that the DEM is in meters. If this is not the case, use the "dem_per_m" option to specify a conversion factor from DEM units to meters. For example, if your DEM is in units of feet, use::

    slopes = watershed.slopes(dem_in_feet, flow, dem_per_m=3.28084)

.. note:: The input DEM may be a raw DEM; a conditioned DEM is not required for this function. However, you may wish to use a conditioned DEM for consistency across your analyses.


.. _relief:

Relief
------

Vertical relief is often used to implement :doc:`potential sediment volume models </guide/models/g14>`. Use the :ref:`relief function <pfdf.watershed.relief>` to compute it::

    relief = watershed.relief(dem, flow)

.. note:: As with :ref:`slopes`, the DEM input may be a raw DEM; a conditioned DEM is not required for this function. However, you may wish to use a conditioned DEM for consistency across your analyses.


