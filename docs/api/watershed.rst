pfdf.watershed module
=====================

.. _pfdf.watershed:

.. py:module:: pfdf.watershed

    Functions that implement raster watershed analyses

    =================================================  ===========
    Function                                           Description
    =================================================  ===========
    :ref:`condition <pfdf.watershed.condition>`        Conditions a DEM by filling pits and depressions, and resolving flats
    :ref:`flow <pfdf.watershed.flow>`                  Computes D8 flow directions from a conditioned DEM
    :ref:`slopes <pfdf.watershed.slopes>`              Computes D8 flow slopes
    :ref:`relief <pfdf.watershed.relief>`              Computes vertical relief to the nearest ridge cell
    :ref:`accumulation <pfdf.watershed.accumulation>`  Computes basic, weighted, or masked flow accumulation
    :ref:`catchment <pfdf.watershed.catchment>`        Returns the catchment mask for a watershed pixel
    :ref:`network <pfdf.watershed.network>`            Returns the stream segments as a list of shapely.LineString objects
    =================================================  ===========

    .. note:: 

        The functions in this module are for raster-wide analyses. Please see the :ref:`Segments class <pfdf.segments.Segments>` if you instead want to compute values for individual stream segments and basins.

    .. tip:: 

        Most users will not need the :ref:`catchment <pfdf.watershed.catchment>` or :ref:`network <pfdf.watershed.network>` functions, as these are implemented internally by the :ref:`Segments class <pfdf.segments.Segments>`.

    .. warning:: The functions in this module rely on the pysheds library, which assigns a default NoData of 0 to any raster lacking a NoData value. This can cause unexpected results when a raster has valid 0 values and lacks NoData. Consider using a placeholder NoData when this is the case.


    Workflow
    --------

    Typical workflow is to first use the :ref:`condition <pfdf.watershed.condition>` function to condition a DEM (i.e. filling pits and resolving flats). Then, use the :ref:`flow <pfdf.watershed.flow>` function to compute D8 flow directions from a DEM. These flow directions are an essential input to all other watershed functions, as well as the :ref:`Segments class <pfdf.segments.Segments>`. With the flow directions, users can compute flow accumulation (also referred to as upslope area), D8 flow slopes, and the vertical relief of watershed pixels.


    .. _api-taudem-style:

    Flow direction style
    --------------------

    This module produces flow directions in the TauDEM style:
    
    .. math::

        \begin{matrix}
        4 & 3 & 2\\
        5 & \mathrm{X} & 1\\
        6 & 7 & 8\\
        \end{matrix}    
    
    where X is the current pixel, and integers indicate flow in a particular direction. So for example, if pixel X flows into the next pixel to the left, then X will be marked with a flow direction of 5. But if X flows into the pixel to the right, then its flow direction will be 1.    

    .. note:: All pfdf routines that use flow directions expect values in the TauDEM style.
    
----


.. _pfdf.watershed.condition:

.. py:function:: condition(dem, *, fill_pits = True, fill_depressions = True, resolve_flats = True)
    :module: pfdf.watershed

    Conditions a DEM to resolve pits, depressions, and/or flats

    .. dropdown:: Conditioning a DEM

        ::

            condition(dem)

        Conditions a DEM by filling pits, filling depressions, and then resolving flats. A pit is defined as a single cell lower than all its surrounding neighbors. When a pit is filled, its elevation is raised to match that of its lowest neighbor. A depression consists of multiple cells surrounded by higher terrain. When a depression is filled, the elevations of all depressed cells are raised to match the elevation of the lowest pixel on the border of the depression. Flats are sets of adjacent cells with the same elevation, and often result from filling pits and depressions (although they may also occur naturally). When a flat is resolved the elevations of the associated cells are minutely adjusted so that their elevations no longer match.

    .. dropdown:: Skipping steps

        ::

            condition(dem, *, fill_pits=False)
            condition(dem, *, fill_depressions=False)
            condition(dem, *, resolve_flats=False)

        Allows you to skip specific steps of the conditioning algorithm. Setting an option to False will disable the associated conditioning step. Raises a ValueError if you attempt to skip all three steps.

    :Inputs: * **dem** (*Raster-like*) -- A digital elevation model raster
             * **fill_pits** (*bool*) -- True (default) to fill pits. False to disable this step
             * **fill_depressions** (*bool*) -- True (default) to fill depressions. False to disable this step
             * **resolve_flats** (*bool*) -- True (default) to resolve flats. False to disable this step

    :Outputs: *Raster* --  A conditioned DEM raster



.. _pfdf.watershed.flow:

.. py:function:: flow(dem)
    :module: pfdf.watershed

    Compute D8 flow directions from a conditioned DEM

    ::

        flow(dem)

    Computes D8 flow directions for a conditioned DEM. Flow direction numbers follow the :ref:`TauDEM style <taudem-style>`. Values of 0 indicate NoData - these may result from NoData values in the original DEM, as well as any unresolved pits, depressions, or flats.

    :Inputs: * **dem** (*Raster-like*) -- A conditioned digital elevation model raster

    :Outputs: *Raster* -- The D8 flow directions for the DEM



.. _pfdf.watershed.slopes:

.. py:function:: slopes(dem, flow, check_flow = True)
    :module: pfdf.watershed

    Computes D8 flow slopes for a watershed

    .. dropdown:: Computing slopes

        ::

            slopes(dem, flow)

        Returns D8 flow slopes for a watershed. Computes these slopes using a DEM raster, and TauDEM-style D8 flow directions. 
        


    .. dropdown:: Disable flow validation
        
        ::
            
            slopes(..., check_flow=False)

        Disables validation checking of the flow directions raster. Validation is not necessary for flow directions directly output by the "watershed.flow" function, and disabling the validation can improve runtimes for large rasters. 
        
        .. warning:: This option may produce unexpected results if the flow directions raster contains invalid values.

    :Inputs: * **dem** (*Raster-like*) -- A digital elevation model raster
             * **flow** (*Raster-like*) -- A raster with TauDEM-style D8 flow directions
             * **check_flow** (*bool*) -- True (default) to validate the flow directions raster. False to disable validation checks.

    :Outputs: *Raster* -- The computed D8 flow slopes for the watershed
   


.. _pfdf.watershed.relief:

.. py:function:: relief(dem, flow, check_flow = True)

    Computes vertical relief to the highest ridge cell

    .. dropdown:: Computing Relief

        ::

            relief(dem, flow)

        Computes the vertical relief for each watershed pixel. Here, vertical relief is defined as the change in elevation between each pixel and its nearest ridge cell. (A ridge cell is an upslope cell with no contributing flow from other pixels). Computes these slopes using a DEM raster, and :ref:`TauDEM-style <taudem-style>` D8 flow directions. 
        
        .. note:: The DEM can be a raw DEM (as opposed to a conditioned DEM). It does not need to resolve pits and flats.

    .. dropdown:: Disable flow validation
        
        ::
            
            relief(..., check_flow=False)

        Disables validation checking of the flow directions raster. Validation is not necessary for flow directions directly output by the :ref:`flow <pfdf.watershed.flow>` function,    and disabling the validation can improve runtimes for large rasters.

        .. warning:: This option may produce unexpected results if the flow directions raster contains invalid values.

    :Inputs: * **dem** (*Raster-like*) -- A digital elevation model raster
             * **flow** (*Raster-like*) -- A TauDEM-style D8 flow direction raster
             * **check_flow** (*bool*) -- True (default) to validate the flow directions raster. False to disable validation checks.

    :Outputs: *Raster* -- The vertical relief of the nearest ridge cell.



.. _pfdf.watershed.accumulation:

.. py:function:: accumulation(flow, weights = None, mask = None, *, omitnan = False, check_flow = True)
    :module: pfdf.watershed

    Computes basic, weighted, or masked flow accumulation

    .. dropdown:: Computing Accumulation
        
        ::
            
            accumulation(flow)

        Uses D8 flow directions to compute basic flow accumulation. In this setup, each pixel is given a value of 1, so the accumulation for each pixel indicates the number of upslope pixels. Note that each pixel is included in its own accumulation, so the minimum valid accumulation is 1. NoData values are indicated by NaN. Flow directions should follow the :ref:`TauDEM style <taudem-style>`.

    .. dropdown:: Weighted Accumulation

        ::

            accumulation(flow, weights)
            accumulation(flow, weights, *, omitnan=True)

        
        Computes weighted accumulations. Here, the value of each pixel is set by the input "weights" raster, so the accumulation for each pixel is a sum over itself and all upslope pixels. The weights raster must have the same shape, transform, and crs as the flow raster.

        In the default case, NaN and NoData values in the weights raster are set to propagate through the accumulation. So any pixel that is downstream of a NaN or a NoData weight will have its accumulation set to NaN. Setting omitnan=True will change this behavior to instead ignore NaN and NoData values. Effectively, NaN and NoData pixels will be given weights of 0.

    .. dropdown:: Masking
        
        ::
            
            accumulation(..., mask)


        Computes a masked accumulation. In this syntax, only the True elements of the mask are included in accumulations. All False elements are given a weight of 0. NoData elements in the mask are interpreted as False. The accumulation for each pixel is thus the sum over all catchment pixels included in the mask.  If weights are not specified, then all included pixels are given a weight of 1. Note that the mask raster must have the same shape, transform, and crs as the flow raster.

    .. dropdown:: Disable flow validation

        ::

            accumulation(..., *, check_flow=False)

        Disables validation checking of the flow directions raster. Validation is not necessary for flow directions directly output by the :ref:`watershed.flow <pfdf.watershed.flow>` function, and disabling the validation can improve runtimes for large rasters. 
        
        .. warning:: This option may produce unexpected results if the flow directions raster contains invalid values.

    :Inputs: * **flow** (*Raster-like*) -- A D8 flow direction raster in the TauDEM style
             * **weights** (*Raster-like*) -- A raster indicating the value of each pixel
             * **mask** (*Raster-like*) -- A raster whose True elements indicate pixels that should be included in the accumulation.
             * **omitnan** (*bool*) --  True to ignore NaN and NoData values in the weights raster. False (default) propagates these values as NaN to all downstream pixels.
             * **check_flow** (*bool*) -- True (default) to validate the flow directions raster. False to disable validation checks.

    :Outputs: *Raster* -- The computed flow accumulation


.. _pfdf.watershed.catchment:

.. py:function:: catchment(flow, row, column, check_flow = True) 
    :module: pfdf.watershed

    Returns the catchment mask for a DEM pixel

    .. dropdown:: Locate a catchment
        
        ::
            
            catchment(flow, row, column)

        Determines the extent of the catchment upstream of the DEM pixel at the indicated row and column. Returns a mask for this catchment extent. The mask will have the same shape as the input flow directions raster - True values indicate pixels that are in the upstream catchment extent, False values are outside of the catchment. Any NoData values in the flow directions will become False values in the catchment mask.

    .. dropdown:: Disable flow validation
        
        ::
            
            catchment(..., check_flow=False)

        Disables validation checking of the flow directions raster. Validation is not necessary for flow directions directly output by the :ref:`watershed.flow <pfdf.watershed.flow>` function, and disabling the validation can improve runtimes for large rasters. 
        
        .. warning:: This option may produce unexpected results if the flow directions raster contains invalid values.

    :Inputs: * **flow** (*Raster-like*) -- D8 flow directions for the DEM (in the TauDEM style)
            * **row** (*int*) -- The row index of the queried pixel in the DEM
            * **column** (*int*) -- The column index of the queried pixel in the DEM
            * **check_flow** (*bool*) -- True (default) to validate the flow directions raster. False to disable validation checks.

    :Outputs: *Raster* -- The upstream catchment mask for the queried pixel



.. _pfdf.watershed.network:

.. py:function:: network(flow, mask, max_length = None, check_flow = True)
    :module: pfdf.watershed

    Returns a list of stream segment LineStrings

    .. dropdown:: Delineate a network
        
        ::
            
            network(flow, mask)

        Calculates a stream segment network and returns the segments as a list of ``shapely.LineString``'' objects. These stream segments approximate the river beds in a drainage basin - they are not the full catchment basin.

        The stream segment network is determined using a :ref:`TauDEM-style <taudem-style>` D8 flow direction raster and a raster mask. The mask is used to indicate the pixels under consideration as stream segments. True pixels may possibly be assigned to a stream segment, False pixels will never be assigned to a stream segment. The mask typically screens out pixels with low flow accumulations, and may include
        other screenings - for example, to remove pixels in large bodies of water, or pixels below developed areas.

    .. dropdown:: Maximum length
        
        ::
            
            network(..., max_length)

        Also specifies a maximum length for the segments in the network. Any segment longer than this length will be split into multiple pieces. The split pieces will all have the same length, which will be <= max_length. The units of max_length should be the base units of the coordinate reference system associated with the flow raster. In practice, this is often units of meters.

    .. dropdown:: Disable flow validation
        
        ::
            
            network(..., check_flow=False)

        Disables validation checking of the flow directions raster. Validation is not necessary for flow directions directly output by the :ref:`watershed.flow <pfdf.watershed.flow>` function, and disabling the validation can improve runtimes for large rasters.

        .. warning:: This option may produce unexpected results if the flow directions raster contains invalid values.

    :Inputs: * **flow** (*Raster-like*) -- A TauDEM-style D8 flow direction raster
             * **mask** (*Raster-like*) -- A raster whose True values indicate the pixels that may potentially belong to a stream segment.
             * **max_length** (*scalar*) -- A maximum allowed length for segments in the network. Units should be the same as the base units of the flow raster CRS
             * **check_flow** (*bool*) -- True (default) to validate the flow directions raster. False to disable validation checks.

    :Outputs: *list[shapely.LineString]* -- The stream segments in the network, represented by ``shapely.LineString`` objects. The coordinates of each LineString proceed from upstream to downstream. Coordinates are relative to the flow raster CRS (rather than raster pixel indices).

    