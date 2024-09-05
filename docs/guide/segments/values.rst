Computing Values
================

You'll often need to compute a physical or statistical value for each segment in the network. Uses for these values include: 

* :doc:`Filtering the network <filter>` to model-worthy segments, and
* Inputs to :doc:`hazard assessment models </guide/models/index>`

This section examines commands that compute such values. We note that *Segments* objects only compute these values for stream segments in the network, so these commands are typically faster than computing variables over an entire watershed.

.. _earth-system-variables:

Physical Variables
------------------
The *Segments* class includes methods to calculate commonly used physical variables for each segment in the network. The following table summarizes these methods:

.. list-table::
    :header-rows: 1

    * - Method
      - Description
    * - :ref:`area <pfdf.segments.Segments.area>`
      - Total catchment area
    * - :ref:`burn_ratio <pfdf.segments.Segments.burn_ratio>`
      - The proportion of catchment area that is burned.   
    * - :ref:`burned_area <pfdf.segments.Segments.burned_area>`
      - Burned catchment area
    * - :ref:`catchment_ratio <pfdf.segments.Segments.catchment_ratio>`
      - The proportion of catchment area within a mask
    * - :ref:`developed_area <pfdf.segments.Segments.developed_area>`
      - Developed catchment area
    * - :ref:`confinement <pfdf.segments.Segments.confinement>`
      - Confinement angle in degrees
    * - :ref:`in_mask <pfdf.segments.Segments.in_mask>`
      - Whether each segment has pixels within a mask
    * - :ref:`in_perimeter <pfdf.segments.Segments.in_perimeter>`
      - Whether each segment has pixels in a fire perimeter
    * - :ref:`kf_factor <pfdf.segments.Segments.kf_factor>`
      - Mean catchment KF-factor
    * - :ref:`length <pfdf.segments.Segments.length>`
      - The length of each segment along its stream bed
    * - :ref:`scaled_dnbr <pfdf.segments.Segments.scaled_dnbr>`
      - Mean catchment dNBR / 1000
    * - :ref:`scaled_thickness <pfdf.segments.Segments.scaled_thickness>`
      - Mean catchment soil thickness / 100
    * - :ref:`sine_theta <pfdf.segments.Segments.sine_theta>`
      - Mean catchment sin(θ)
    * - :ref:`slope <pfdf.segments.Segments.slope>`
      - Mean segment slope
    * - :ref:`relief <pfdf.segments.Segments.relief>`
      - Vertical relief to the highest ridge cell
    * - :ref:`ruggedness <pfdf.segments.Segments.ruggedness>`
      - Relief / sqrt(area)


All of these methods return a 1D numpy array with one element per segment. Most require a raster as input, and some require additional inputs::

    >>> area = segments.area()
    >>> burn_ratio = segments.burn_ratio(isburned)
    >>> scaled_dnbr = segments.scaled_dnbr(dnbr)
    >>> confinement = segments.confinement(dem, neighborhood)

Ignoring Pixels
+++++++++++++++

Many methods have an optional ``omitnan`` option. Set this value to True to ignore raster pixels equal to NaN. For example::

    # Will ignore NaN pixels when computing summaries
    >>> scaled_dnbr = segments.scaled_dnbr(dnbr, omitnan=True)
    >>> kf_factor = segments.kf_factor(kf, omitnan=True)

.. _mask-option:

In some cases, the omitnan option may not be sufficient. In this case, all catchment summaries support a ``mask`` option, which accepts a boolean *Raster* mask. False elements of the mask are ignored when computing catchment summaries. For example::
    
    # Will ignore False elements when computing summaries
    >>> scaled_dnbr = segments.scaled_dnbr(dnbr, mask)
    >>> kf_factor = segments.kf_factor(kf, mask)


Additional Options
++++++++++++++++++

The :ref:`area <pfdf.segments.Segments.area>`, :ref:`burned_area <pfdf.segments.Segments.burned_area>`, and :ref:`developed_area <pfdf.segments.Segments.developed_area>` methods all return areas in square kilometers (km²) by default. Analogously, the :ref:`length method <pfdf.segments.Segments.length>` uses meters by default. You can use the ``units`` option to return values in other units instead::

    # Return values in other units
    >>> self.area(units="miles")  # Square miles
    >>> self.area(units="meters") # Square meters
    >>> self.length(units="kilometers")


.. _terminal-option:

Separately, you can also configure any catchment summary to only return values for terminal basins by setting the ``terminal`` option to True::

    # Only returns values for terminal basins
    >>> area = segments.area(terminal=True)
    >>> burn_ratio = segments.burn_ratio(isburned, terminal=True)
    >>> scaled_dnbr = segments.scaled_dnbr(dnbr, terminal=True)




Generic Summaries
-----------------

Some users may want to compute statistical or physical variables not built-in to the class. To support this, the *Segments* class provides two methods for calculating generic statistical summaries from a raster of data values. The :ref:`summary <pfdf.segments.Segments.summary>` method computes a statistical summary over the pixels in each segment (roughly, the pixels in the river bed). Analogously, the :ref:`catchment_summary <pfdf.segments.Segments.catchment_summary>` method computes statistical summaries over the pixels in each segment's catchment basin. Both methods support the following statistics:

.. list-table::
    :header-rows: 1

    * - Key
      - Description
    * - outlet
      - The value of the pixel at each segment's outlet
    * - min
      - Minimum value
    * - max
      - Maximum value
    * - mean
      - Mean
    * - median
      - Median
    * - std
      - Standard deviation
    * - sum
      - Sum of summarized pixels
    * - var
      - Variance
    * - nanmin
      - Minimum, ignoring NaN pixels
    * - nanmax
      - Maximum, ignoring NaN pixels
    * - nanmean
      - Mean, ignoring NaN pixels
    * - nanmedian
      - Median, ignoring NaN pixels
    * - nanstd
      - Standard deviation, ignoring NaN pixels
    * - nansum
      - Sum, ignoring NaN pixels
    * - nanvar
      - Variance, ignoring NaN pixels


Some examples::

    # Summarize the pixels in the segment
    mins = segments.summary("min", raster)
    means = segments.summary("mean", raster)
    vars = segments.summary("var", raster)

    # Summarize the pixels in the catchment
    outlets = segments.catchment_summary("outlet", raster)
    sums = segments.catchment_summary("sum", raster)
    nanmeans = segments.catchment_summary("nanmean", raster)

The :ref:`catchment_summary <pfdf.segments.Segments.catchment_summary>` method also supports the :ref:`mask <mask-option>` and :ref:`terminal <terminal-option>` options described above::

    # Only computes values for outlet basins
    sums = segments.catchment_summary("sum", raster, terminal=True)
    nanmeans = segments.catchment_summary("nanmean", raster, terminal=True)

    # Ignores False pixels
    sums = segments.catchment_summary("sum", raster, mask)
    nanmeans = segments.catchment_summary("nanmean", raster, mask)


.. tip::

    When computing basin summaries, we recommend using the ``outlet``, ``sum``, ``mean``, ``nansum``, or ``nanmean`` options whenever possible. The other statistics require a less efficient algorithm, so may take a while to compute. When other statistics *are* required, then limiting the summary to terminal basins can help improve runtime.


Value Rasters
-------------

As demonstrated, many of the summary methods require a raster of data values as input. When providing one of these rasters, the raster must match the shape, crs, and affine transformation of the flow directions raster used to derive the stream segment network. :ref:`As previously described <segments-raster-properties>`, you can return these values using the ``raster_shape``, ``crs``, and ``transform`` properties. You can also return the full flow directions raster using the ``flow`` property. If an input raster does not have a crs or transform, then it is assumed to have the same crs or transform as the flow directions raster.

You can also use various methods to visualize the pixels being used in different summaries. There are four common cases for computing segment summaries:

1. Computing values over the pixels in each stream segment, 
2. Computing values over all pixels in the catchment basin of each stream segement, 
3. Computing values over the pixels in each terminal outlet basin, and 
4. Returning the values at the outlet or terminal outlet pixels.

For case 1, recall that stream segment pixels can be returned using the :ref:`indices <segment-indices>` property, and visualized using the :ref:`raster method <stream-raster>` method. For case 2, a stream segment catchment basin consists of all pixels that flow into the segment's outlet pixel, and this can be visualized using the :ref:`catchment_mask method <catchment-mask>`. For case 3, recall that you can return the IDs of the terminal segments using the :ref:`terminal_ids property <pfdf.segments.Segments.terminal_ids>`. You can also visualize terminal outlet basins calling the :ref:`catchment_mask method <catchment-mask>` on terminal IDs. Finally for case 4, note that the :ref:`outlets method <outlets>` returns the indices of stream segment outlet pixels.


