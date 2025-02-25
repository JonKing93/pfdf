segments package
================

.. _pfdf.segments:

.. py:module:: pfdf.segments

.. _pfdf.segments.Segments:

.. py:class:: Segments
    :module: pfdf.segments

    Build and manage a stream segment network


    .. dropdown:: Properties

        .. list-table::
            :header-rows: 1

            * - Property
              - Description
            * - 
              -
            * - **Network**
              - 
            * - size
              - The number of segments in the network
            * - nlocal
              - The number of local drainage networks
            * - crs
              - The coordinate reference system associated with the network
            * - crs_units
              - The units of the CRS along the X and Y axes
            * - 
              - 
            * - **Segments**
              - 
            * - segments
              - A list of shapely.LineString objects representing the stream segments
            * - ids
              - A unique integer ID associated with each stream segment
            * - terminal_ids
              - The IDs of the terminal segments
            * - indices
              - The indices of each segment's pixels in the stream segment raster
            * - npixels
              - The number of pixels in the catchment basin of each stream segment
            * - 
              -
            * - **Raster Metadata**
              - 
            * - flow
              - The flow direction raster used to build the network
            * - raster_shape
              - The shape of the stream segment raster
            * - transform
              - The affine Transform of the stream segment raster
            * - bounds
              - The BoundingBox of the stream segment raster
            * - located_basins
              - True when the object has pre-located outlet basins



    .. dropdown:: Methods

        .. list-table::
            :header-rows: 1

            * - Method
              - Description
            * - 
              -
            * - **Object Creation**
              - 
            * - :ref:`__init__ <pfdf.segments.Segments.__init__>`
              - Builds an initial stream segment network
            * - 
              - 
            * - **Dunders**
              - 
            * - :ref:`__len__ <pfdf.segments.Segments.__len__>`
              - The number of segments in the network
            * - :ref:`__repr__ <pfdf.segments.Segments.__repr__>`
              - A string representing the network
            * - :ref:`__geo_interface__ <pfdf.segments.Segments.__geo_interface__>`
              - A geojson-like dict of the network
            * - 
              - 
            * - **Outlets**
              - 
            * - :ref:`isterminal <pfdf.segments.Segments.isterminal>`
              - Indicates whether segments are terminal segments
            * - :ref:`termini <pfdf.segments.Segments.termini>`
              - Returns the IDs of terminal segments
            * - :ref:`outlets <pfdf.segments.Segments.outlets>`
              - Returns the row and column indices of outlet pixels
            * - 
              - 
            * - **Local Networks**
              - 
            * - :ref:`parents <pfdf.segments.Segments.parents>`
              - Returns the IDs of segments immediately upstream
            * - :ref:`child <pfdf.segments.Segments.child>`
              - Returns the ID of the segment immediately downstream
            * - :ref:`ancestors <pfdf.segments.Segments.ancestors>`
              - Returns the IDs of upstream segments in a local network
            * - :ref:`descendents <pfdf.segments.Segments.descendents>`
              - Returns the IDs of downstream segments in a local network
            * - :ref:`family <pfdf.segments.Segments.family>`
              - Returns the IDs of segments in a local network
            * - :ref:`isnested <pfdf.segments.Segments.isnested>`
              - Indicates whether segments are in a nested network
            * - 
              - 
            * - **Rasters**
              - 
            * - :ref:`locate_basins <pfdf.segments.Segments.locate_basins>`
              - Builds and saves the basin raster, optionally in parallel
            * - :ref:`raster <pfdf.segments.Segments.raster>`
              - Returns a raster representation of the stream segment network
            * - :ref:`catchment_mask <pfdf.segments.Segments.catchment_mask>`
              - Returns the catchment basin mask for the queried stream segment
            * - 
              - 
            * - **Generic Statistics**
              - 
            * - :ref:`statistics <pfdf.segments.Segments.statistics>`
              - Print or return info about supported statistics
            * - :ref:`summary <pfdf.segments.Segments.summary>`
              - Compute summary statistics over the pixels for each segment
            * - :ref:`catchment_summary <pfdf.segments.Segments.catchment_summary>`
              - Compute summary statistics over catchment basin pixels
            * - 
              - 
            * - **Earth System Variables**
              - 
            * - :ref:`area <pfdf.segments.Segments.area>`
              - Computes the total basin areas
            * - :ref:`burn_ratio <pfdf.segments.Segments.burn_ratio>`
              - Computes the burned proportion of basins
            * - :ref:`burned_area <pfdf.segments.Segments.burned_area>`
              - Computes the burned area of basins
            * - :ref:`catchment_ratio <pfdf.segments.Segments.catchment_ratio>`
              - Computes the proportion of catchment basin pixels within a mask
            * - :ref:`confinement <pfdf.segments.Segments.confinement>`
              - Computes the confinement angle for each segment
            * - :ref:`developed_area <pfdf.segments.Segments.developed_area>`
              - Computes the developed area of basins
            * - :ref:`in_mask <pfdf.segments.Segments.in_mask>`
              - Checks whether each segment is within a mask
            * - :ref:`in_perimeter <pfdf.segments.Segments.in_perimeter>`
              - Checks whether each segment is within a fire perimeter
            * - :ref:`kf_factor <pfdf.segments.Segments.kf_factor>`
              - Computes mean basin KF-factors
            * - :ref:`length <pfdf.segments.Segments.length>`
              - Computes the length of each stream segment
            * - :ref:`scaled_dnbr <pfdf.segments.Segments.scaled_dnbr>`
              - Computes mean basin dNBR / 1000
            * - :ref:`scaled_thickness <pfdf.segments.Segments.scaled_thickness>`
              - Computes mean basin soil thickness / 100
            * - :ref:`sine_theta <pfdf.segments.Segments.sine_theta>`
              - Computes mean basin sin(theta)
            * - :ref:`slope <pfdf.segments.Segments.slope>`
              - Computes the mean slope of each segment
            * - :ref:`relief <pfdf.segments.Segments.relief>`
              - Computes the vertical relief to highest ridge cell for each segment
            * - :ref:`ruggedness <pfdf.segments.Segments.ruggedness>`
              - Computes topographic ruggedness (relief / sqrt(area)) for each segment
            * - 
              -
            * - **Filtering**
              - 
            * - :ref:`continuous <pfdf.segments.Segments.continuous>`
              - Indicates segments that can be filtered while preserving flow continuity
            * - :ref:`keep <pfdf.segments.Segments.keep>`
              - Restricts the network to the indicated segments
            * - :ref:`remove <pfdf.segments.Segments.remove>`
              - Removes the indicated segments from the network
            * - :ref:`copy <pfdf.segments.Segments.copy>`
              - Returns a deep copy of the *Segments* object
            * - 
              -
            * - **Export**
              - 
            * - :ref:`geojson <pfdf.segments.Segments.geojson>`
              - Returns the network as a geojson.FeatureCollection
            * - :ref:`save <pfdf.segments.Segments.save>`
              - Saves the network to file


    The *Segments* class is used to build and manage a stream segment network. A common workflow is as follows:
    
    1. Use :ref:`the constructor <pfdf.segments.Segments.__init__>` to delineate an initial network
    2. Compute :ref:`earth-system variables <api-segments-variables>` needed for filtering
    3. :ref:`Filter the network <api-filtering>` to a set of model-worthy segments
    4. Compute :ref:`hazard assessment inputs <api-segments-variables>`
    5. :ref:`Export <api-export>` results to file and/or GeoJSON

    .. tip:: 
        
        Read the :doc:`/guide/glossary` for descriptions of many terms used throughout this documentation.

----

Properties
----------

Network
+++++++

.. py:property:: Segments.size

    The number of stream segments in the network

.. py:property:: Segments.nlocal

    The number of local drainage networks

.. py:property:: Segments.crs

    The coordinate reference system of the stream segment network

.. py:property:: Segments.crs_units

    The units of the CRS along the X and Y axes


Segments
++++++++

.. py:property:: Segments.segments
    
    A list of shapely LineStrings representing the stream segments

.. py:property:: Segments.ids

    The ID of each stream segment

.. _pfdf.segments.Segments.terminal_ids:

.. py:property:: Segments.terminal_ids

    The IDs of the terminal segments

.. py:property:: Segments.indices

    The indices of each segment's pixels in the stream segment raster

.. py:property:: Segments.npixels

    The number of pixels in the catchment basin of each stream segment


Raster Metadata
+++++++++++++++

.. py:property:: Segments.flow

    The flow direction raster used to build the network

.. py:property:: Segments.raster_shape

    The shape of the stream segment raster

.. py:property:: Segments.transform

    The affine Transform of the stream segment raster

.. py:property:: Segments.bounds
    
    The BoundingBox of the stream segment raster

.. py:property:: Segments.located_basins

    True when the object has pre-located outlet basins


----

Dunders
-------

.. _pfdf.segments.Segments.__init__:

.. py:method:: Segments.__init__(self, flow, mask, max_length = inf, units = "meters")

    Creates a new *Segments* object

    .. dropdown:: Create Network

        ::

            Segments(flow, mask)

        Builds a *Segments* object to manage the stream segments in a drainage network. Note that stream segments approximate the river beds in the catchment basins, rather than the full catchment basins. The returned object records the pixels associated with each segment in the network.

        The stream segment network is determined using a :ref:`TauDEM-style <api-taudem-style>` D8 flow direction raster and a raster mask. The mask is used to indicate the pixels under consideration as stream segments. True pixels may possibly be assigned to a stream segment, False pixels will never be assigned to a stream segment. The mask typically screens out pixels with low flow accumulations, and may include other screenings - for example, to remove pixels in bodies of water.

        .. note:: The flow direction raster must have (affine) transform metadata.

    .. dropdown:: Maximum Length

        ::

            Segments(..., max_length)
            Segments(..., max_length, units)

        Also specifies a maximum length for the segments in the network. Any segment longer than this length will be split into multiple pieces. The split pieces will all have the same length, which will be < max_length. Note that the max_length must be at least as long as the diagonal of the raster pixels. By default, this command interprets max_length in meters. Use the ``units`` option to specify max_length in different units instead. Unit options include: "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet", and "miles".

    :Inputs: 
        * **flow** (*Raster*) -- A TauDEM-style D8 flow direction raster
        * **mask** (*Raster*) -- A raster whose True values indicate the pixels that may potentially belong to a stream segment.
        * **max_length** (*scalar*) -- A maximum allowed length for segments in the network.
        * **units** (*str*) -- Specifies the units of max_length. Options include: "base" (CRS base units), "meters" (default)", "kilometers", "feet", and "miles".

    :Outputs: *Segments* -- A *Segments* object recording the stream segments in the network.
        
.. _pfdf.segments.Segments.__len__:

.. py:method:: Segments.__len__(self)

    The number of stream segments in the network

    ::

        len(self)

    :Outputs:
        *int* -- The number of segments in the network


.. _pfdf.segments.Segments.__repr__:

.. py:method:: Segments.__repr__(self)

    Returns a string summarizing the *Segments* object

    ::

        str(self)

    Returns a string summarizing key info about the Segments object.

    :Outputs:
        *str* -- A string summarizing the *Segments* object


.. _pfdf.segments.Segments.__geo_interface__:

.. py:method:: Segments.__geo_interface__(self)

    A geojson dict-like representation of the *Segments* object

    ::

        segments.__geo_interface__

    :Outputs:
        *geojson.FeatureCollection* -- A geojson-like dict of the *Segments* object

----

Outlets
-------

.. _pfdf.segments.Segments.isterminal:

.. py:method:: Segments.isterminal(self, ids = None)

    Indicates whether segments are terminal segments

    .. dropdown:: All Segments

        ::

            self.isterminal()

        Determines whether each segment is a terminal segment or not. A segment is terminal if it does not have a downstream child. (Note that there may still be other segments furhter downstream if the segment is in a nested drainage network). Returns a boolean 1D numpy array with one element per segment in the network. True elements indicate terminal segments, False elements are segments that are not terminal.

    .. dropdown:: Specific Segments

        ::
        
            self.isterminal(ids)

        Determines whether the queried segments are terminal segments or not. Returns a boolean 1D array with one element per queried segment.

    :Inputs:
        * **ids** (*vector*) -- The IDs of segments being queried. If not set, queries all segments in the network.

    :Outputs:
        *boolean 1D numpy array* -- Whether each segment is terminal.


.. _pfdf.segments.Segments.termini:

.. py:method:: Segments.termini(self, ids = None)

    Returns the IDs of terminal segments

    .. dropdown:: All Segments

        ::

            self.termini()

        Determines the ID of the terminal segment for each stream segment in the network. Returns a numpy 1D array with one element per stream segment. Typically, many segments will drain to the same terminal segment, so this array will usually contain many duplicate IDs.

        .. tip::

            If you instead want the unique IDs of the terminal segments, use the :ref:`terminal_ids property <pfdf.segments.Segments.terminal_ids>` instead.


    .. dropdown:: Specific Segments
        
        ::
            
            self.termini(ids)

        Only returns terminal segment IDs for the queried segments. The output array will have one element per queried segment.

    :Inputs:
        * **ids** (*vector*) -- The IDs of the queried segments. If not set, then queries every segment in the network.

    :Outputs:
        *numpy 1D array* -- The ID of the terminal segment for each queried segment


.. _pfdf.segments.Segments.outlets:

.. py:method:: Segments.outlets(self, ids = None, *, segment_outlets = False, as_array = False)

    Returns the row and column indices of outlet pixels

    .. dropdown:: All Segments

        ::
            
            self.outlets()

        Returns the row and column index of the terminal outlet pixel for each segment in the network. Returns a list with one element per segment in the network. Each element is a tuple of two integers. The first element is the row index of the outlet pixel in the stream network raster, and the second element is the column index.

    .. dropdown:: Specific Segments

        ::

            self.outlets(ids)

        Only returns outlet pixel indices for the queried segments. The output list will have one element per queried segment.

    .. dropdown:: Non-terminal Outlets

        ::

            self.outlets(..., *, segment_outlets=True)

        Returns the indices of each segment's immediate outlet pixel, rather than the indices of the terminal outlet pixels. Each segment outlet is the final pixel in the stream segment itself. (Compare with a terminal outlet, which is the final pour point in the segment's local drainage network).

    .. dropdown:: As Array

        ::

            self.outlets(..., *, as_array=True)

        Returns the outlet pixel indices as a numpy array, rather than as a list. The output array will have one row per queried stream segment, and two columns. The first column is the row indices, and the second column is the column indices.

    :Inputs:
        * **ids** (*vector*) -- The IDs of the queried stream segments. If not set, queries all segments in the network.
        * **segment_outlets** (*bool*) -- True to return the indices of each stream segment's outlet pixel. False (default) to return the indices of terminal outlet pixels
        * **as_array** (*bool*) -- True to return the pixel indices as an Nx2 numpy array. False (default) to return indices as a list of 2-tuples.

    :Outputs:
        *list[tuple[int, int]] | numpy array* -- The outlet pixel indices of the
            queried stream segments


----

Local Networks
--------------

.. _pfdf.segments.Segments.parents:

.. py:method:: Segments.parents(self, id)

    Returns the IDs of the queried segment's parent segments

    ::

        self.parents(id)

    Given a stream segment ID, returns the IDs of the segment's parents. If the segment has parents, returns a list of IDs. If the segment does not have parents, returns None.

    :Inputs:
        * **id** (*scalar*) -- The queried stream segment

    :Outputs:
        *list[int] | None* -- The IDs of the parent segments


.. _pfdf.segments.Segments.child:

.. py:method:: Segments.child(self, id)

    Returns the ID of the queried segment's child segment

    ::

        self.child(id)

    Given a stream segment ID, returns the ID of the segment's child segment as an int. If the segment does not have a child, returns None.

    :Inputs:
        * **id** (*scalar*) -- The ID of the queried segment

    :Outputs:
        *int | None* -- The ID of the segment's child


.. _pfdf.segments.Segments.ancestors:

.. py:method:: Segments.ancestors(self, id)

    Returns the IDs of all upstream segments in a local drainage network

    ::

        self.ancestors(id)

    For a queried stream segment ID, returns the IDs of all upstream segments in the local drainage network. These are the IDs of the queried segment's parents, the IDs of the parents parents, etc. If the queried segment does not have any parent segments, returns an empty array.

    :Inputs:
        * **id** (*scalar*) -- The ID of a stream segment in the network

    :Outputs:
        *numpy 1D array* -- The IDs of all segments upstream of the queried segment within the local drainage network.


.. _pfdf.segments.Segments.descendents:

.. py:method:: Segments.descendents(self, id)

    Returns the IDs of all downstream segments in a local drainage network

    ::

        self.descendents(id)

    For a queried stream segment, returns the IDs of all downstream segments in the queried segment's local drainage network. This is the ID of any child segment, the child of that child, etc. If the queried segment does not have any descendents, then the returned array will be empty.

    :Inputs:
        * **id** (*scalar*) -- The ID of the queried stream segment

    :Outputs:
        *numpy 1D array* -- The IDs of all downstream segments in the local drainage network.


.. _pfdf.segments.Segments.family:

.. py:method:: Segments.family(self, id)

    Return the IDs of stream segments in a local drainage network

    ::

        self.family(id)

    Returns the IDs of all stream segments in the queried segment's local drainage network. This includes all segments in the local network that flow to the queried segment's outlet, including the queried segment itself. Note that the returned IDs may include segments that are neither ancestors nor descendents of the queried segment, as the network may contain multiple branches draining to the same outlet.

    :Inputs:
        * **id** (*scalar*) -- The ID of the queried stream segment

    :Outputs:
        *numpy 1D array* -- The IDs of all segments in the local drainage network.


.. _pfdf.segments.Segments.isnested:

.. py:method:: Segments.isnested(self, ids = None)

    Determines which segments are in nested drainage basins

    .. dropdown:: All Segments

        ::

            self.isnested()

        Identifies segments in nested drainage basins. A nested drainage basin is a local drainage network that flows into another local drainage network further downstream. Nesting is an indication of flow discontinuity. Returns a 1D boolean numpy array with one element per stream segment. True elements indicate segments in nested networks. False elements are segments not in a nested network.

    .. dropdown:: Specific Segments

        ::
            
            self.isnested(ids)

        Determines whether the queried segments are in nested drainage basins. The output array will have one element per queried segment.

    :Inputs:
        **ids** (*vector*) -- The IDs of the segments being queried. If unset, queries all segments in the network.

    :Outputs:
        *boolean 1D numpy array* -- Whether each segment is in a nested drainage network



----

Rasters
-------

.. _pfdf.segments.Segments.catchment_mask:

.. py:method:: Segments.catchment_mask(self, id)

    Return a mask of the queried segment's catchment basin

    ::

        self.catchment_mask(id)

    Returns the catchment basin mask for the queried segment. The catchment basin consists of all pixels that drain into the segment. The output will be a boolean raster whose True elements indicate pixels that are in the catchment basin.

    :Inputs: * **id** (*int*) -- The ID of the stream segment whose catchment mask should be determined

    :Outputs: *Raster* -- The boolean raster mask for the catchment basin. True elements indicate pixels that are in the catchment.


.. _pfdf.segments.Segments.raster:

.. py:method:: Segments.raster(self, basins=False)

    Return a raster representation of the stream network

    .. dropdown:: Stream Segment Raster

        ::

            self.raster()
            
        Returns the stream segment raster for the network. This raster has a 0 background. Non-zero pixels indicate stream segment pixels. The value of each pixel is the ID of the associated stream segment.

    .. dropdown:: Terminal Basin Raster

        ::

            self.raster(basins=True)

        Returns the terminal outlet basin raster for the network. This raster has a 0 background. Non-zero pixels indicate terminal outlet basin pixels. The value of each pixel is the ID of the terminal segment associated with the basin. If a pixel is in multiple basins, then its value to assigned to the ID of the terminal segment that is farthest downstream.

        .. note::

            You can use :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` to pre-build the raster before calling this command. If not pre-built, then this command will generate the terminal basin raster sequentially, which may take a while. Note that :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` includes options to parallelize this process, which may improve runtime.

    :Inputs: * **basins** (*bool*) -- False (default) to return the stream segment raster. True to return a terminal basin raster

    :Outputs: *Raster* --  A stream segment raster, or terminal outlet basin raster.


.. _pfdf.segments.Segments.locate_basins:

.. py:method:: Segments.locate_basins(self, parallel = False, nprocess = None)

    Builds and saves a terminal basin raster, optionally in parallel

    .. dropdown:: Pre-locate Basins

        ::

            self.locate_basins()

        
        Builds the terminal basin raster and saves it internally. The saved raster will be used to quickly implement other commands that require it. (For example, :ref:`raster <pfdf.segments.Segments.raster>`, :ref:`geojson <pfdf.segments.Segments.geojson>`, and :ref:`save <pfdf.segments.Segments.save>`). Note that the saved raster is deleted if any of the terminal outlets are removed from the *Segments* object, so it is usually best to call this command *after* filtering the network.

    .. dropdown:: Parallelization

        ::

            self.locate_basins(parallel=True)
            self.locate_basins(parallel=True, nprocess)

        
        Building a basin raster is computationally difficult and can take a while to run. Setting parallel=True allows this process to run on multiple CPUs, which can improve runtime. However, the use of this option imposes two restrictions.

        First, you cannot use the "parallel" option from an interactive python session. Instead, the pfdf code MUST be called from a script via the command line. For example, something like:

        .. code:: bash
                
                python -m my_script

        Second, the code in the script must be within a::

            if __name__ == "__main__":

        block. Otherwise, the parallel processes will attempt to rerun the script, resulting in an infinite loop of CPU process creation.

        By default, setting parallel=True will create a number of parallel processes equal to the number of CPUs - 1. Use the nprocess option to specify a different number of parallel processes. Note that you can obtain the number of available CPUs using os.cpu_count(). Also note that parallelization options are ignored if only 1 CPU is available.

    :Inputs: * **parallel** (*bool*) -- True to build the raster in parallel. False (default) to build sequentially.
             * **nprocess** (*int*) -- The number of parallel processes. Must be a scalar, positive integer. Default is the number of CPUs - 1.

----

.. _api-segments-variables:

Earth-system Variables
----------------------

.. _pfdf.segments.Segments.area:

.. py:method:: Segments.area(self, mask = None, *, units = "kilometers",  terminal = False)

    Returns catchment areas

    .. dropdown:: Catchment Area

        ::

            self.area()
            self.area(..., *, units)
            self.area(..., *, terminal=True)

        Computes the total area of the catchment basin for each stream segment. By default, returns areas in kilometers^2. Use the ``units`` option to return areas in other units (squared) instead. Supported units include: "base" (CRS base units), "meters", "kilometers", "feet", and "miles". By default, returns an area for each segment in the network. Set ``terminal=True`` to only return values for the terminal outlet basins.

    .. dropdown:: Masked Area

        ::

            self.area(mask)

        Computes masked areas for the basins. True elements in the mask indicate pixels that should be included in the calculation of areas. False pixels are ignored and given an area of 0. Nodata elements are interpreted as False.

    :Inputs: 
        * **mask** (*Raster*) -- A raster mask whose True elements indicate the pixels that should be used to compute upslope areas.
        * **units** (*str*) -- The units (squared) in which to return areas. Options include: "base" (CRS base units), "meters", "kilometers" (default), "feet", and "miles".
        * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *numpy 1D array* -- The catchment area for each stream segment


.. _pfdf.segments.Segments.burn_ratio:

.. py:method:: Segments.burn_ratio(self, isburned, terminal = False)

    Returns the proportion of burned pixels in basins

    ::

        self.burn_ratio(isburned)
        self.burn_ratio(..., terminal=True)

    Given a mask of burned pixel locations, determines the proportion of burned pixels in the catchment basin of each stream segment. Ratios are on the interval from 0 to 1. By default, returns a numpy 1D array with the ratio for each segment. Set ``terminal=True`` to only return values for the terminal outlet basins.

    :Inputs: * **isburned** (*Raster*) -- A raster mask whose True elements indicate the locations of burned pixels in the watershed.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The proportion of burned pixels in each basin


.. _pfdf.segments.Segments.burned_area:

.. py:method:: Segments.burned_area(self, isburned, *, units = "kilometers", terminal = False)

    Returns the total burned area of basins

    ::

        self.burned_area(isburned)
        self.burned_area(..., *, units)
        self.burned_area(..., *, terminal=True)

    Given a mask of burned pixel locations, returns the total burned area in the catchment of each stream segment. By default, returns areas in kilometers^2. Use the ``units`` option to return areas in other units (squared) instead. Supported units include: "base" (CRS base units), "meters", "kilometers", "feet", and "miles". By default, returns the burned catchment area for each segment in the network. Set ``terminal=True`` to only return values for the terminal outlet basins.

    :Inputs: 
        * **isburned** (*Raster*) -- A raster mask whose True elements indicate the locations of burned pixels within the watershed
        * **units** (*str*) -- The units (squared) in which to return areas. Options include: "base" (CRS base units), "meters", "kilometers" (default), "feet", and "miles".
        * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The burned catchment area for the basins


.. _pfdf.segments.Segments.catchment_ratio:

.. py:method:: Segments.catchment_ratio(self, mask, terminal = False)

    Returns the proportion of catchment basin pixels within a mask

    .. dropdown:: Catchment Ratio

        ::

            self.catchment_ratio(mask)

        Given a raster mask, computes the proportion of True pixels in the catchment basin for each stream segment. Returns the ratios as a numpy 1D array with one element per stream segment. Ratios will be on the interval from 0 to 1. Note that NoData pixels in the mask are interpreted as False.

    .. dropdown:: Terminal Basins

        ::

            self.catchment_ratio(mask, terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **mask** (*Raster*) -- A raster mask for the watershed. The method will compute the proportion of True elements in each catchment
             * **terminal** (*bool*) -- True to only compute values for the terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The proportion of True values in each basin


.. _pfdf.segments.Segments.confinement:

.. py:method:: Segments.confinement(self, dem, neighborhood, dem_per_m = 1)

    Returns the mean confinement angle of each stream segment

    ::

        self.confinement(dem, neighborhood)
        self.confinement(..., dem_per_m)

    Computes the mean confinement angle for each stream segment. Returns these angles as a numpy 1D array. The order of angles matches the order of segment IDs in the object.

    The confinement angle for a given pixel is calculated using the slopes in the two directions perpendicular to stream flow. A given slope is calculated using the maximum DEM height within N pixels of the processing pixel in the associated direction. Here, the number of pixels searched in each direction (N) is equivalent to the "neighborhood" input. The slope equation is thus::

        slope = max height(N pixels) / (N * length)

    where length is one of the following:

    * X axis resolution (for flow along the Y axis)
    * Y axis resolution (for flow along the X axis)
    * length of a raster cell diagonal (for diagonal flow)

    Recall that slopes are computed perpendicular to the flow direction, hence the use X axis resolution for Y axis flow and vice versa.

    The confinment angle is then calculated using:

    .. math::

        θ = 180 - \mathrm{tan}^{-1}(\mathrm{slope}_1) - \mathrm{tan}^{-1}(\mathrm{slope}_2)

    and the mean confinement angle is calculated over all the pixels in the stream segment.

    .. admonition:: Example

        Consider a pixel flowing east with neighborhood=4. (East here indicates that the pixel is flowing to the next pixel on its right - it is not an indication of actual geospatial directions). Confinement angles are then calculated using slopes to the north and south. The north slope is determined using the maximum DEM height in the 4 pixels north of the stream segment pixel, such that::

                slope = max height(4 pixels north) / (4 * Y axis resolution)

        and the south slope is computed similarly. The two slopes are used to compute the confinement angle for the pixel, and this process is then repeated for all pixels in the stream segment. The final value for the stream segment will be the mean of these values.

    .. important::

        By default, this routine assumes that the DEM units are meters. If this is not the case, then use the "dem_per_m" to specify a conversion factor (number of DEM units per meter).

    :Inputs:
        * **dem** (*Raster-like*) -- A raster of digital elevation model (DEM) data.
        * **neighborhood** (*int*) -- The number of raster pixels to search for maximum heights. Must be a positive integer.
        * **dem_per_m** (*scalar*) -- A conversion factor from DEM units to meters

    :Outputs:
        *numpy 1D array* -- The mean confinement angle for each stream segment.



.. _pfdf.segments.Segments.developed_area:

.. py:method:: Segments.developed_area(self, isdeveloped, *, units = "kilometers", terminal = False)

    Returns the total developed area of basins

    ::

        self.developed_area(isdeveloped)
        self.developed_area(..., *, units)
        self.developed_area(..., *, terminal=True)

    Given a mask of developed pixel locations, returns the total developed area in the catchment of each stream segment. By default, returns areas in kilometers^2. Use the ``units`` option to return areas in other units (squared) instead. Supported units include: "base" (CRS base units), "meters", "kilometers", "feet", and "miles". By default, returns the burned catchment area for each segment in the network. Set ``terminal=True`` to only return values for the terminal outlet basins.

    :Inputs: 
        * **isdeveloped** (*Raster*) -- A raster mask whose True elements indicate the locations of developed pixels within the watershed.
        * **units** (*str*) -- The units (squared) in which to return areas. Options include: "base" (CRS base units), "meters", "kilometers" (default), "feet", and "miles".
        * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The developed catchment area for each basin


.. _pfdf.segments.Segments.in_mask:

.. py:method:: Segments.in_mask(self, mask, terminal = False)

    Determines whether segments have pixels within a mask

    ::
    
        self.in_mask(mask)
        self.in_mask(mask, terminal=True)

    Given a raster mask, returns a boolean 1D numpy array with one element per segment. True elements indicate segments that have at least one pixel
    within the mask. False elements have no pixels within the mask. If terminal=True, only returns values for the terminal segments.

    :Inputs: * **mask** (*Raster*) -- A raster mask for the watershed.
             * **terminal** (*bool*) -- True to only return values for terminal segments. False (default) to return values for all segments.

    :Outputs: *boolean ndarray* -- Whether each segment has at least one pixel within the mask.


.. _pfdf.segments.Segments.in_perimeter:

.. py:method:: Segments.in_perimeter(self, perimeter, terminal=False)

    Determines whether segments have pixels within a fire perimeter

    ::

        self.in_perimeter(perimeter)
        self.in_perimeter(perimeter, terminal=True)

    Given a fire perimeter mask, returns a boolean 1D numpy array with one element per segment. True elements indicate segments that have at least one pixel within the fire perimeter. False elements have no pixels within the mask. If terminal=True, only returns values for the terminal segments.

    :Inputs: * **perimeter** (*Raster*) -- A fire perimeter raster mask
             * **terminal** (*bool*) -- True to only return values for terminal segments. False (default) to return values for all segments.

    :Outputs: *boolean ndarray* -- Whether each segment has at least one pixel within the fire perimeter.


.. _pfdf.segments.Segments.kf_factor:

.. py:method:: Segments.kf_factor(self, kf_factor, mask = None, *, terminal = False, omitnan = False)

    Computes mean soil KF-factor for basins

    .. dropdown:: Catchment KF-Factor

        ::

            self.kf_factor(kf_factor)

        Computes the mean catchment KF-factor for each stream segment in the network. Note that the KF-Factor raster must have all positive values. If a catchment basin contains NaN or NoData values, then its mean KF-Factor is set to NaN.

    .. dropdown:: Masked KF-Factor

        ::

            self.kf_factor(kf_factor, mask)

        Also specifies a data mask for the watershed. True elements of the mask are used to compute mean KF-Factors. False elements are ignored. If a basin only contains False elements, then its mean Kf-factor is set to NaN.

    .. dropdown:: Ignore NaN Pixels

        ::

            self.kf_factor(..., *, omitnan=True)

        Ignores NaN and NoData values when computing mean KF-factors. If a basin only contains NaN and/or NoData values, then its mean KF-factor will still be NaN.

    .. dropdown:: Terminal Basins

        ::

            self.kf_factor(..., *, terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **kf_factor** (*Raster*) -- A raster of soil KF-factor values. Cannot contain negative elements.
             * **mask** (*Raster*) -- A raster mask whose True elements indicate the pixels that should be used to compute mean KF-factors
             * **omitnan** (*bool*) -- True to ignore NaN and NoData values. If False (default), any basin with (unmasked) NaN or NoData values will have its mean Kf-factor set to NaN.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The mean catchment KF-Factor for each basin


.. _pfdf.segments.Segments.length:

.. py:method:: Segments.length(self, *, units = "meters", terminal = False)

    Returns the length of each stream segment

    ::

        self.length()
        self.length(*, units)
        self.length(*, terminal=True)

    Returns the length of each stream segment in the network. By default, returns lengths in meters. Use the ``units`` option to return lengths in other units. Supported units include: "base" (CRS base units), "meters", "kilometers", "feet", and "miles". By default, returns a numpy 1D array with one element per segment. Set ``terminal=True`` to only return values for the terminal outlet segments.

    :Inputs:
        * **units** (*str*) -- Indicates the units in which to return segment lengths. Options include: "base" (CRS base units), "meters" (default), "kilometers", "feet", and "miles".
        * **terminal** (*bool*) -- True to only return the lengths of terminal outlet segments. False (default) to return the length of every segment in the network

    :Outputs:
        *numpy 1D array* -- The lengths of the segments in the network


.. _pfdf.segments.Segments.scaled_dnbr:

.. py:method:: Segments.scaled_dnbr(self, dnbr, mask = None, *, terminal = False, omitnan = False)

    Computes mean catchment dNBR / 1000 for basins

    .. dropdown:: Scaled dNBR

        ::

            self.scaled_dnbr(dnbr)

        Computes mean catchment dNBR for each stream segment in the network. These mean dNBR values are then divided by 1000 to place dNBR values roughly on the interval from 0 to 1. Returns the scaled dNBR values as a numpy 1D array. If a basin contains NaN or NoData values, then its dNBR value is set to NaN.

    .. dropdown:: Masked dNBR

        ::

            self.scaled_dnbr(dnbr, mask)

        Also specifies a data mask for the watershed. True elements of the mask are used to compute scaled dNBR values. False elements are ignored. If a catchment only contains False elements, then its scaled dNBR value is set to NaN.

    .. dropdown:: Ignore NaN Pixels

        ::

            self.scaled_dnbr(..., *, omitnan=True)

        Ignores NaN and NoData values when computing scaled dNBR values. However, if a basin only contains these values, then its scaled dNBR value will still be NaN.

    .. dropdown:: Terminal Basins

        ::

            self.scaled_dnbr(..., *, terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **dnbr** (*Raster*) -- A dNBR raster for the watershed
             * **mask** (*Raster*) -- A raster mask whose True elements indicate the pixels that should be used to compute scaled dNBR
             * **omitnan** (*bool*) -- True to ignore NaN and NoData values. If False (default), any basin with (unmasked) NaN or NoData values will have its value set to NaN.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The mean catchment dNBR/1000 for the basins


.. _pfdf.segments.Segments.scaled_thickness:

.. py:method:: Segments.scaled_thickness(self, soil_thickness, mask = None, *, omitnan = False, terminal = False)

    Computes mean catchment soil thickness / 100 for basins

    .. dropdown:: Scaled Soil Thickness

        ::

            self.scaled_thickness(soil_thickness)

        Computes mean catchment soil-thickness for each segment in the network. Then divides these values by 100 to place soil thicknesses approximately on the interval from 0 to 1. Returns a numpy 1D array with the scaled soil thickness values for each segment. Note that the soil thickness raster must have all positive values.

    .. dropdown:: Masked Thickness

        ::

            self.scaled_thickness(soil_thickness, mask)

        Also specifies a data mask for the watershed. True elements of the mask are used to compute mean soil thicknesses. False elements are ignored. If a catchment only contains False elements, then its scaled soil thickness is set to NaN.

    .. dropdown:: Ignore NaN Pixels

        ::

            self.scaled_thickness(..., *, omitnan=True)

        Ignores NaN and NoData values when computing scaled soil thickness values. However, if a basin only contains NaN and NoData, then its scaled soil thickness will still be NaN.

    .. dropdown:: Terminal Basins

        ::

            self.scaled_thickness(..., *, terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **soil_thickess** (*Raster*) -- A raster with soil thickness values for the watershed. Cannot contain negative values.
             * **mask** (*Raster*) -- A raster mask whose True elements indicate the pixels that should be used to compute scaled soil thicknesses
             * **omitnan** (*bool*) -- True to ignore NaN and NoData values. If False (default), any basin with (unmasked) NaN or NoData values will have its value set to NaN.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* --  The mean catchment soil thickness / 100 for each basin


.. _pfdf.segments.Segments.sine_theta:

.. py:method:: Segments.sine_theta(self, sine_thetas, mask = None, *, omitnan = False, terminal = False)

    Computes the mean sin(θ) value for each segment's catchment

    .. dropdown:: Catchment sin(θ)

        ::

            self.sine_theta(sine_thetas)

        Given a raster of watershed sin(θ) values, computes the mean sin(θ) value for each stream segment catchment. Here, θ is the slope angle. Note that the pfdf.utils.slope module provides utilities for converting from slope gradients (rise/run) to other slope measurements, including sin(θ) values. All sin(θ) values should be on the interval from 0 to 1. Returns a numpy 1D array with the sin(θ) values for each segment.

    .. dropdown:: Masked sin(θ)

        ::

            self.sine_theta(sine_thetas, mask)

        Also specifies a data mask for the watershed. True elements of the mask are used to compute mean sin(θ) values. False elements are ignored. If a catchment only contains False elements, then its sin(θ) value is set to NaN.

    .. dropdown:: Ignore NaN Pixels

        ::
            
            self.sine_theta(..., *, omitnan=True)

        Ignores NaN and NoData values when computing mean sin(θ) values. However, if a basin only contains NaN and NoData, then its sin(θ) value will still be NaN.

    .. dropdown:: Terminal Basins

        ::

            self.sine_theta(..., terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **sine_thetas** (*Raster*) -- A raster of sin(θ) values for the watershed
             * **mask** (*Raster*) -- A raster mask whose True elements indicate the pixels that should be used to compute sin(θ) values
             * **omitnan** (*bool*) -- True to ignore NaN and NoData values. If False (default), any basin with (unmasked) NaN or NoData values will have its value set to NaN.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The mean sin(θ) value for each basin
    

.. _pfdf.segments.Segments.slope:

.. py:method:: Segments.slope(self, slopes, *, terminal = False, omitnan = False)

    Returns the mean slope (rise/run) for each segment

    .. dropdown:: Mean Slope

        ::

            self.slope(slopes)
            self.slope(..., *, terminal=True)

        Given a raster of slope gradients (rise/run), returns the mean slope for each segment as a numpy 1D array. If a stream segment's pixels contain NaN or NoData values, then the slope for the segment is set to NaN. If ``terminal=True``, only returns values for the terminal segments.

    .. dropdown:: Ignore NaN Pixels

        ::

            self.slope(slopes, omitnan=True)

        Ignores NaN and NoData values when computing mean slope. However, if a segment only contains NaN and NoData values, then its value will still be NaN.

    :Inputs: * **slopes** (*Raster*) -- A slope gradient (rise/run) raster for the watershed
             * **terminal** (*bool*) -- True to only return values for terminal segments. False (default) to return values for all segments.

    :Outputs: *ndarray* -- The mean slope for each stream segment.


.. _pfdf.segments.Segments.relief:

.. py:method:: Segments.relief(self, relief)

    Returns the vertical relief for each segment

    ::

        self.relief(relief)
        self.relief(relief, terminal=True)

    Returns the vertical relief between each stream segment's outlet and the nearest ridge cell as a numpy 1D array. If ``terminal=True``, only returns values for the terminal segments.

    :Inputs: * **relief** (*Raster*) -- A vertical relief raster for the watershed
             * **terminal** (*bool*) -- True to only return values for terminal segments. False (default) to return values for all segments.

    :Outputs: *ndarray* -- The vertical relief for each segment


.. _pfdf.segments.Segments.ruggedness:

.. py:method:: Segments.ruggedness(self, relief, relief_per_m = 1, *, terminal = False)

    Returns the ruggedness of each stream segment catchment

    .. dropdown:: Topographic Ruggedness

        ::

            self.ruggedness(relief)
            self.ruggedness(relief, relief_per_m)

        Returns the ruggedness of the catchment for each stream segment in the network in units of meters^-1. Ruggedness is defined as a stream segment's vertical relief, divided by the square root of its catchment area. By default, interprets relief values as meters. If this is not the case, use the "relief_per_m" option to provide a conversion factor between relief units and meters. This ensures that ruggedness values are scaled correctly.

    .. dropdown:: Terminal Segments

        ::

            self.ruggedness(..., terminal=True)

        Only returns values for the terminal segments.

    :Inputs:
        * **relief** (*Raster-like*) -- A vertical relief raster for the watershed
        * **relief_per_m** (*scalar*) -- A conversion factor between relief units and meters
        * **terminal** (*bool*) -- True to only return values for terminal segments. False (default) to return values for all segments.

    :Outputs:
        *numpy 1D array* -- The topographic ruggedness of each stream segment


----

Generic Statistics
------------------

.. _pfdf.segments.Segments.statistics:

.. py:method:: Segments.statistics(asdict = False)

    Prints or returns info about supported statistics

    .. dropdown:: Print Info

        ::

            Segments.statistics()

        Prints information about supported statistics to the console. The printed text is a table with two columns. The first column holds the names of statistics that can be used with the "summary" and "catchment_summary" methods. The second column is a description of each statistic.

    .. dropdown:: Return Info as Dict

        ::

            Segments.statistics(asdict=True)

        Returns info as a dict, rather than printing to console. The keys of the dict are the names of the statistics. The values are the descriptions.

    :Inputs: * **asdict** (*bool*) -- True to return info as a dict. False (default) to print info to the console.

    :Outputs: *None | dict* -- None if printing to console. Otherwise a dict whose keys are statistic names, and values are descriptions.


.. _pfdf.segments.Segments.summary:

.. py:method:: Segments.summary(self, statistic, values)

    Computes a summary value for each stream segment

    ::

        self.summary(statistic, values)

    Computes a summary statistic for each stream segment. Each summary value is computed over the associated stream segment pixels. Returns the statistical summaries as a numpy 1D array with one element per segment.

    Note that NoData values are converted to NaN before computing statistics.
    If using one of the statistics that ignores NaN values (e.g. nanmean),
    a segment's summary value will still be NaN if every pixel in the stream
    segment is NaN.

    :Inputs: * **statistic** (*str*) -- A string naming the requested statistic. Use ``Segments.statistics()`` for info on supported statistics
             * **values** (*Raster*) -- A raster of data values over which to compute stream segment summary values.

    :Outputs: *ndarray* -- The summary statistic for each stream segment

    
.. _pfdf.segments.Segments.catchment_summary:

.. py:method:: Segments.catchment_summary(self, statistic, values, mask = None, terminal = False)

    Computes a summary statistic over each catchment basin's pixel

    .. dropdown:: Catchment Summary

        ::

            self.catchment_summary(statistic, values)

        Computes the indicated statistic over the catchment basin pixels for each stream segment. Uses the input values raster as the data value for each pixel. Returns a numpy 1D array with one element per stream segment.

        Note that NoData values are converted to NaN before computing statistics. If using one of the statistics that ignores NaN values (e.g. nanmean), a basin's summary value will still be NaN if every pixel in the basin basin is NaN.

        .. tip::

            We recommend only the "outlet", "mean", "sum", "nanmean", and "nansum" statistics whenever possible. The remaining statistics require a less efficient algorithm, and so are much slower to compute. Alternatively, refer below for an option to only compute statistics for terminal outlet basins.


    .. dropdown:: Masked Summary

        ::

            self.catchment_summary(statistic, values, mask)

        Computes masked statistics over the catchment basins. True elements in the mask indicate pixels that should be included in statistics. False elements are ignored. If a catchment does not contain any True pixels, then its summary statistic is set to NaN. Note that a mask will have no effect on the "outlet" statistic.

    .. dropdown:: Terminal Basin Summaries

        ::

            self.catchment_summary(..., terminal=True)

        Only computes statistics for the terminal outlet basins. The output will have one element per terminal segment. The order of values will match the order of IDs reported by the ``Segments.termini`` method. The number of terminal outlet basins is often much smaller than the total number of segments. As such, this option presents a faster alternative and is particularly suitable when computing statistics other than "outlet", "mean", "sum", "nanmean", or "nansum".

    :Inputs: * **statistic** (*str*) -- A string naming the requested statistic. Use ``Segments.statistics()`` for info on supported statistics.
             * **values** (*Raster*) -- A raster of data values over which to compute basin summaries
             * **mask** (*Raster*) -- An optional raster mask for the data values. True elements are used to compute basin statistics. False elements are ignored.
             * **terminal** (*bool*) -- True to only compute statistics for terminal outlet basins. False (default) to compute statistics for every catchment basin.

    :Outputs: *ndarray* -- The summary statistic for each basin

----

.. _api-filtering:

Filtering
---------

.. _pfdf.segments.Segments.continuous:

.. py:method:: Segments.continuous(self, selected, type = "indices", *, remove = False, keep_upstream = False, keep_downstream = False)
    
    Indicates segments that can be filtered while preserving flow continuity

    .. dropdown:: Flow Continuous Filtering

        ::

            self.continuous(selected)
            self.continuous(..., *, remove=True)
            self.continuous(..., type="ids")

        Given a selection of segments that will be filtered using the :ref:`keep <pfdf.segments.Segments.keep>` or  :ref:`remove <pfdf.segments.Segments.remove>` commands, returns the boolean indices of segments that can be filtered while preserving flow continuity. By default, assumes that the selected segments are for use with the "keep" command. Set ``remove=True`` to indicate that selected segments are for use with the :ref:`remove command <pfdf.segments.Segments.remove>` instead.

        By default, expects the selected segments to be a boolean numpy 1D array with one element per segment in the network. True/False elements should indicate segments for the keep/remove commands, as appropriate. Set ``type="ids"`` to select segments using segment IDs instead. In this case, the selected segments should be a list or numpy 1D array whose elements are the IDs of the segments selected for filtering.

    .. dropdown:: Network Edges

        ::

            self.continuous(..., *, keep_upstream=True)
            self.continuous(..., *, keep_downstream=True)

        Further customizes the flow continuity algorithm. Set ``keep_upstream=True`` to always retain segments on the upstream end of a local drainage network. Set ``keep_downstream=True`` to always retain segments on the downstream end of a local drainage network.

    :Inputs:
        * **selected** (*boolean vector | ID vector*) -- The segments being selected for filtering
        * **type** (*str*) -- "indices" (default) to select segments using a boolean vector. "ids" to select segments using segments IDs
        * **remove** (*bool*) -- True to indicate that segments are selected for removal. False (default) to indicate that selected segments should be kept.
        * **keep_upstream** (*bool*) -- True to always retain segments on the upstream end of a local drainage network. False (default) to treat as usual.
        * **keep_downstream** (*bool*) -- True to always retain segments on the downstream end of a local drainage network. False (default) to treat as usual.

    :Outputs:
        *boolean 1D numpy array* -- The boolean indices of segments that can be filtered while preserving flow continuity. If ``remove=False`` (default), then True elements indicate segments that should be retained in the network. If ``remove=True``, then True elements indicate segments that should be removed from the network.


.. _pfdf.segments.Segments.remove:

.. py:method:: Segments.remove(self, selected, type = "indices")

    Remove segments from the network

    ::

        self.remove(selected)
        self.remove(selected, type="ids")

    Removes the indicated segments from the network. By default, expects a boolean numpy 1D array with one element per segment in the network. True elements indicate segments that should be removed, and False elements are segments that should be retained.

    Set ``type="ids"`` to select segments using IDs, rather than a boolean vector. In this case, the input should be a list or numpy 1D array whose elements are the IDs of the segments that should be removed from the network.

    .. note::

        Removing terminal outlet segments can cause any previously located basins to be deleted. As such we recommend calling the :ref:`locate_basins command <pfdf.segments.Segments.locate_basins>` after this command.

    :Inputs:
        * **selected** (*boolean vector | ID vector*) -- The segments that should be removed from the network
        * **type** (*str*) -- "indices" (default) to select segments using a boolean vector. "ids" to select segments using segments IDs

    
.. _pfdf.segments.Segments.keep:

.. py:method:: Segments.keep(self, selected, type = "indices")

    Restricts the network to the indicated segments

    ::

        self.keep(selected)
        self.keep(selected, type="ids")

    Restricts the network to the indicated segments, discarding all other segments. By default, expects a boolean numpy 1D array with one element per segment in the network. True elements indicate segments that should be retained, and False elements are segments that should be discarded.

    Set ``type="ids"`` to select segments using IDs, rather than a boolean vector. In this case, the input should be a list or numpy 1D array whose elements are the IDs of the segments that should be retained in the network.

    .. note::

        Removing terminal outlet segments can cause any previously located basins to be deleted. As such we recommend calling the :ref:`locate_basins command <pfdf.segments.Segments.locate_basins>` after this command.

    :Inputs:
        * **selected** (*boolean vector | ID vector*) -- The segments that should be retained in the network
        * **type** (*str*) -- "indices" (default) to select segments using a boolean vector. "ids" to select segments using segments IDs


.. _pfdf.segments.Segments.copy:

.. py:method:: Segments.copy(self)

    Returns a copy of a *Segments* object

    ::

        self.copy()

    Returns a copy of the current *Segments* object. Stream segments can be removed from the new/old objects without affecting one another. Note that the flow direction raster and saved basin rasters are not duplicated in memory. Instead, both objects reference the same underlying array.

    :Outputs: *Segments* -- A copy of the current *Segments* object.

----

.. _api-export:

Export
------

.. _pfdf.segments.Segments.geojson:

.. py:method:: Segments.geojson(self, type = "segments", properties = None, *, crs=None)

    Exports the network to a ``geojson.FeatureCollection`` object

    .. dropdown:: Segments

        ::

            self.geojson()
            self.geojson(type='segments')

        Exports the network to a ``geojson.FeatureCollection`` object. The individual Features have LineString geometries whose coordinates proceed from upstream to downstream. Will have one feature per stream segment.

    .. dropdown:: Terminal Basins

        ::

            self.geojson(type='basins')

        Exports terminal outlet basins as a collection of Polygon features. The number of features will be <= the number of local drainage networks. (The number of features will be less than the number of local networks if a local network flows into another local network).

        .. note::

            You can use :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` to pre-build the raster before calling this command. If not pre-built, then this command will generate the terminal basin raster sequentially, which may take a while. Note that :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` includes options to parallelize this process, which may improve runtime.

    .. dropdown:: Outlets

        ::

            self.geojson(type='outlets')
            self.geojson(type='segment outlets')

        Exports outlet points as a collection of Point features. If type="outlets", exports the terminal outlet points, which will have one feature per local drainage network. If type="segment outlets", exports the complete set of outlet points, which will have one feature per segment in the network.

    .. dropdown:: Feature Properties

        ::

            self.geojson(..., properties)

        Specifies data properties for the GeoJSON features. The "properties" input should be a dict. Each key should be a string and will be interpreted as the name of the associated property field. Each value should be a numpy 1D array with a boolean, integer, floating, or string dtype. Boolean values are converted to integers in the output GeoJSON object. 
        
        If exporting segments or segment outlets, then each array should have one  element per segment in the network. If exporting outlets or basins, each array may have either (1) one element per segment in the network, or (2) one outlet per terminal segment in the network. If using one element per segment, extracts the values for the terminal segments prior to GeoJSON export.

    .. dropdown:: Specify CRS

        ::

            self.geojson(..., *, crs)

        Specifies the CRS of the output geometries. By default, returns geometries in the CRS of the flow direction raster used to derive the network. Use this option to return geometries in a different CRS instead.
 
    :Inputs: 
        * **type** (*"segments" | "basins" | "outlets" | "segment outlets"*) -- A string indicating the type of feature to export.
        * **properties** (*dict[str, ndarray]*) -- A dict whose keys are the (string) names of the property fields. Each value should be a numpy 1D array with a boolean,  integer, floating, or string dtype. Each array may have one element per segment (any type of export), or one element per local drainage network (basins and outlets only).
        * **crs** (*CRS-like*) -- The CRS of the output geometries. Defaults to the CRS of the flow-direction raster used to derive the network.


    :Outputs: *geojson.FeatureCollection* -- The collection of stream network features


.. _pfdf.segments.Segments.save:

.. py:method:: Segments.save(self, path, type = "segments", properties = None, *, crs = None, driver = None, overwrite = False)

    Saves the network to a vector feature file

    .. dropdown:: Save Segments

        ::

            self.save(path)
            self.save(path, type='segments')
            self.save(..., *, overwrite=True)

        Saves the network to the indicated path. Each segment is saved as a vector feature with a LineString geometry whose coordinates proceed from upstream to downstream. The vector features will not have any data properties. In the default state, the method will raise a FileExistsError if the file already exists. Set overwrite=True to enable the replacement of existing files. Returns the absolute path to the saved file as output.

        By default, the method will attempt to guess the intended file format based on the path extensions, and will raise an Exception if the file format cannot be guessed. However, refer below for a syntax to specify the driver, regardless of extension. You can use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: Basins

        ::

            self.save(path, type='basins', ...)

        Saves the terminal outlet basins as a collection of Polygon features. The number of features will be <= the number of local drainage networks. (The number of features will be less than the number of local networks if a local network flows into another local network).

        .. note::

            You can use :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` to pre-build the raster before calling this command. If not pre-built, then this command will generate the terminal basin raster sequentially, which may take a while. Note that :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` includes options to parallelize this process, which may improve runtime.

    .. dropdown:: Outlets

        ::

            self.save(path, type='outlets', ...)
            self.save(path, type='segment outlets', ...)

        Saves outlet points as a collection of Point features. If type="outlets", saves the terminal outlet points, which will have one feature per local drainage network. If type="segment outlets", saves the complete set of outlet points, which will have one feature per segment in the network.

    .. dropdown:: Feature Properties

        ::

            self.save(..., properties)

        Specifies data properties for the saved features. The "properties" input should be a dict. Each key should be a string and will be interpreted as the name of the associated property field. Each value should be a numpy 1D array with a boolean, integer, floating, or string dtype. Boolean values are converted to integers in the output GeoJSON object.

        If exporting segments or segment outlets, then each array should have one element per segment in the network. If exporting outlets or basins, each array may have either (1) one element per segment in the network, or (2) one outlet per terminal segment in the network. If using one element per segment, extracts the values for the terminal segments prior to saving.

    .. dropdown:: Specify CRS

        ::

            self.save(..., *, crs)

        Specifies the CRS of the output file. By default, uses the CRS of the flow direction raster used to derive the network. Use this option to export results in a different CRS instead.

    .. dropdown:: Specify File Format

        ::

            save(..., *, driver)

        Specifies the file format driver to used to write the vector feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to write vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_

    :Inputs: 
        * **path** (*Path | str*) -- The path to the output file
        * **type** (*"segments" | "basins" | "outlets" | "segment outlets"*) -- A string indicating the type of feature to export.
        * **properties** (*dict[str, ndarray]*) -- A dict whose keys are the (string) names of the property fields. Each value should be a numpy 1D array with a boolean, integer, floating, or string dtype. Each array may have one element per segment (any type of export), or one element per local drainage network (basins and outlets only).
        * **crs** (*CRS-like*) -- The CRS of the output file. Defaults to the CRS of the flow-direction raster used to derive the network.
        * **overwrite** (*bool*) -- True to allow replacement of existing files. False (default) to prevent overwriting.
        * **driver** (*str*) -- The name of the file-format driver to use when writing the vector feature file. Uses this driver regardless of file extension.

    :Outputs:
        *Path* -- The path to the saved file
             