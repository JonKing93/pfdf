pfdf.segments module
====================

.. _pfdf.segments:

.. py:module:: pfdf.segments

.. _pfdf.segments.Segments:

.. py:class:: Segments
    :module: pfdf.segments

    Build and manage a stream segment network


    .. dropdown:: Properties

        ===============  ===========
        Property         Description
        ===============  ===========
        ..
        Network
        ----------------------------          
        length           The number of segments in the network
        nlocal           The number of local drainage networks in the network
        crs              The coordinate reference system associated with the network
        ..
        Segments
        ----------------------------          
        segments         A list of ``shapely.LineString`` objects representing the stream segments
        lengths          The length of each segment
        ids              A unique integer ID associated with each stream segment
        parents          The IDs of the upstream parents of each stream segment
        child            The ID of the downstream child of each stream segment
        isterminus       Whether each segment is a terminal segment
        indices          The indices of each segment's pixels in the stream segment raster
        npixels          The number of pixels in the catchment basin of each stream segment
        ..
        Raster Metadata
        ----------------------------          
        flow             The flow direction raster used to build the network
        raster_shape     The shape of the flow direction raster
        transform        The affine transformation associated with the flow raster
        resolution       The resolution of the flow raster pixels
        pixel_area       The area of a raster pixel
        ===============  ===========

    .. dropdown:: Methods

        ===================================================================  ===========
        Method                                                               Description
        ===================================================================  ===========
        :ref:`__init__ <pfdf.segments.Segments.__init__>`                    Create a stream segment network
        ..
        **Dunders**
        :ref:`__len__ <pfdf.segments.Segments.__len__>`                      The number of segments in the network
        :ref:`__str__ <pfdf.segments.Segments.__str__>`                      A string representing the network
        :ref:`__geo_interface__ <pfdf.segments.Segments.__geo_interface__>`  A geojson-like dict of the network
        ..
        **Rasters**
        :ref:`raster <pfdf.segments.Segments.raster>`                        Returns a raster representation of the stream segment network
        :ref:`basin_mask <pfdf.segments.Segments.basin_mask>`                Returns the catchment or terminal outlet basin mask for the queried stream segment
        :ref:`locate_basins <pfdf.segments.Segments.locate_basins>`          Builds and saves the basin raster, optionally in parallel
        ..
        **Outlets**
        :ref:`terminus <pfdf.segments.Segments.terminus>`                    Return the ID of the queried segment's terminal segment
        :ref:`termini <pfdf.segments.Segments.termini>`                      Return the IDs of all terminal segments
        :ref:`outlet <pfdf.segments.Segments.outlet>`                        Return the indices of the queried segment's outlet or terminal outlet pixel
        :ref:`outlets <pfdf.segments.Segments.outlets>`                      Return the indices of all outlet or terminal outlet pixels
        ..
        **Earth-system Variables**
        :ref:`area <pfdf.segments.Segments.area>`                            Computes the total basin areas
        :ref:`burn_ratio <pfdf.segments.Segments.burn_ratio>`                Computes the burned proportion of basins
        :ref:`burned_area <pfdf.segments.Segments.burned_area>`              Computes the burned area of basins
        :ref:`developed_area <pfdf.segments.Segments.developed_area>`        Computes the developed area of basins
        :ref:`confinement <pfdf.segments.Segments.confinement>`              Computes the confinement angle for each segment
        :ref:`in_mask <pfdf.segments.Segments.in_mask>`                      Checks whether each segment is within a mask
        :ref:`in_perimeter <pfdf.segments.Segments.in_perimeter>`            Checks whether each segment is within a fire perimeter
        :ref:`kf_factor <pfdf.segments.Segments.kf_factor>`                  Computes mean basin KF-factors
        :ref:`scaled_dnbr <pfdf.segments.Segments.scaled_dnbr>`              Computes mean basin dNBR / 1000
        :ref:`scaled_thickness <pfdf.segments.Segments.scaled_thickness>`    Computes mean basin soil thickness / 100
        :ref:`sine_theta <pfdf.segments.Segments.sine_theta>`                Computes mean basin sin(θ)
        :ref:`slope <pfdf.segments.Segments.slope>`                          Computes the mean slope of each segment
        :ref:`relief <pfdf.segments.Segments.relief>`                        Computes the vertical relief to highest ridge cell for each segment
        :ref:`ruggedness <pfdf.segments.Segments.ruggedness>`                Computes topographic ruggedness (relief / sqrt(area)) for each segment
        :ref:`upslope_ratio <pfdf.segments.Segments.upslope_ratio>`          Computes the proportion of basin pixels that meet a criteria
        ..
        **Generic Statistics**
        :ref:`statistics <pfdf.segments.Segments.statistics>`                Print or return info about supported statistics
        :ref:`summary <pfdf.segments.Segments.summary>`                      Compute summary statistics over the pixels for each segment
        :ref:`basin_summary <pfdf.segments.Segments.basin_summary>`          Compute summary statistics over the catchment basins or terminal outlet basins
        ..
        **Filtering**
        :ref:`remove <pfdf.segments.Segments.remove>`                        Removes segments from the network while optionally preserving continuity
        :ref:`keep <pfdf.segments.Segments.keep>`                            Restricts the network to the indicated segments while optionally preserving continuity
        :ref:`copy <pfdf.segments.Segments.copy>`                            Returns a deep copy of the *Segments* object
        ..
        **Export**
        :ref:`geojson <pfdf.segments.Segments.geojson>`                      Returns the network as a ``geojson.FeatureCollection``
        :ref:`save <pfdf.segments.Segments.save>`                            Saves the network to file
        ===================================================================  ===========


    The *Segments* class is used to build and manage a stream segment network. A common workflow is as follows:
    
    1. Use :ref:`the constructor <pfdf.segments.Segments.__init__>` to delineate an initial network
    2. Compute :ref:`earth-system variables <api-segments-variables>` needed for filtering
    3. :ref:`Filter the network <api-filtering>` to a set of model-worthy segments
    4. Compute :ref:`hazard assessment inputs <api-segments-variables>`
    5. :ref:`Export <api-export>` results to file and/or GeoJSON

    .. tip:: See the :doc:`/guide/glossary` for descriptions of many terms used throughout this documentation.

----

Properties
----------

Network
+++++++

.. py:property:: Segments.length

    The number of stream segments in the network

.. py:property:: Segments.nlocal

    The number of local drainage networks

.. py:property:: Segments.crs

    The coordinate reference system of the stream segment network


Segments
++++++++

.. py:property:: Segments.segments
    
    A list of shapely LineStrings representing the stream segments

.. py:property:: Segments.lengths

    The length of each stream segment in the units of the CRS

.. py:property:: Segments.ids

    The ID of each stream segment

.. py:property:: Segments.parents

    The IDs of the upstream parents of each stream segment

.. py:property:: Segments.child

    The ID of the downstream child of each stream segment

.. py:property:: Segments.isterminus

    Whether each segment is a terminal segment

.. py:property:: Segments.indices

    The row and column indices of the stream raster pixels for each segment

.. py:property:: Segments.npixels

    The number of pixels in the catchment basin of each stream segment


Raster Metadata
+++++++++++++++

.. py:property:: Segments.flow

    The flow direction raster used to build the network

.. py:property:: Segments.raster_shape

    The shape of the stream segment raster

.. py:property:: Segments.transform

    The (affine) transform of the stream segment raster

.. py:property:: Segments.resolution

    The resolution of the stream segment raster pixels

.. py:property:: Segments.pixel_area

    The area of the stream segment raster pixels in the units of the transform



Dunders
-------

.. _pfdf.segments.Segments.__init__:

.. py:method:: Segments.__init__(self, flow, mask, max_length = inf)

    Creates a new Segments object

    .. dropdown:: Create Network

        ::

            Segments(flow, mask)

        Builds a *Segments* object to manage the stream segments in a drainage network. Note that stream segments approximate the river beds in the catchment basins, rather than the full catchment basins. The returned object records the pixels associated with each segment in the network.

        The stream segment network is determined using a :ref:`TauDEM-style <api-taudem-style>` D8 flow direction raster and a raster mask. The mask is used to indicate the pixels under consideration as stream segments. True pixels may possibly be assigned to a stream segment, False pixels will never be assiged to a stream segment. The mask typically screens out pixels with low flow accumulations, and may include other screenings - for example, to remove pixels in bodies of water.

        .. note:: The flow direction raster must have (affine) transform metadata.

    .. dropdown:: Maximum Length

        ::

            Segments(flow, mask, max_length)

        Also specifies a maximum length for the segments in the network. Any segment longer than this length will be split into multiple pieces. The split pieces will all have the same length, which will be <= max_length. The units of max_length should be the base units of the (affine) transform associated with the flow raster. In practice, this is usually units of meters. The maximum length must be at least as long as the diagonal of the raster pixels.

    :Inputs: * **flow** (*Raster*) -- A TauDEM-style D8 flow direction raster
                * **mask** (*Raster*) -- A raster whose True values indicate the pixels that may potentially belong to a stream segment.
                * **max_length** (*scalar*) -- A maximum allowed length for segments in the network. Units should be the same as the units of the (affine) transform for the flow raster.

    :Outputs: *Segments* -- A *Segments* object recording the stream segments in the network.
        
.. _pfdf.segments.Segments.__len__:

.. py:method:: Segments.__len__(self)

    The number of stream segments in a *Segments* object

    ::

        len(segments)


.. _pfdf.segments.Segments.__str__:

.. py:method:: Segments.__str__(self)

    String representation of the object

    ::

        str(segments)


.. _pfdf.segments.Segments.__geo_interface__:

.. py:method:: Segments.__geo_interface__(self)

    A geojson dict-like representation of the *Segments* object

    ::

        segments.__geo_interface__


Rasters
-------

.. _pfdf.segments.Segments.basin_mask:

.. py:method:: Segments.basin_mask(self, id, terminal = False)

    Return a mask of the queried segment's catchment or terminal outlet basin

    .. dropdown:: Catchment Mask

        ::

            self.basin_mask(id)

        Returns the catchment basin mask for the queried segment. The catchment basin consists of all pixels that drain into the segment. The output will be a boolean raster whose True elements indicate pixels that are in the catchment basin.

    .. dropdown:: Terminal Basin Mask

        ::

            self.basin_mask(id, terminal=True)

        Returns the mask of the queried segment's terminal outlet basin. The terminal outlet basin is the catchment basin for the segment's local drainage network. This basin is a superset of the segment's catchment basin. The output will be a boolean raster whose True elements indicate pixels that are in the local drainage basin.

    :Inputs: * **id** (*int*) -- The ID of the stream segment whose basin mask should be determined
             * **terminal** (*bool*) -- True to return the terminal outlet basin mask for the segment. False (default) to return the catchment mask.

    :Outputs: *Raster* -- The boolean raster mask for the basin. True elements indicate pixels that belong to the basin.


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

        First, you cannot use the "parallel" option from an interactive python session. Instead, the pfdf code MUST be called from a script via the command line. For example, something like::
                
                $ python -m my_script

        Second, the code in the script must be within a::

            if __name__ == "__main__":

        block. Otherwise, the parallel processes will attempt to rerun the script, resulting in an infinite loop of CPU process creation.

        By default, setting parallel=True will create a number of parallel processes equal to the number of CPUs - 1. Use the nprocess option to specify a different number of parallel processes. Note that you can obtain the number of available CPUs using os.cpu_count(). Also note that parallelization options are ignored if only 1 CPU is available.

    :Inputs: * **parallel** (*bool*) -- True to build the raster in parallel. False (default) to build sequentially.
             * **nprocess** (*int*) -- The number of parallel processes. Must be a scalar, positive integer. Default is the number of CPUs - 1.


Outlets
-------

.. _pfdf.segments.Segments.terminus:

.. py:method:: Segments.terminus(self, id)

    Returns the ID of a queried segment's terminal segment

    ::

        self.terminus(id)

    Returns the ID of the queried segment's terminal segment. The terminal segment is the final segment in the queried segment's local drainage network. The input should be the ID associated with the queried segment.

    :Inputs: * **id** (*int*) -- The ID of the segment being queried

    :Outputs: *int* -- The ID of the queried segment's terminal segment

    
.. _pfdf.segments.Segments.termini:

.. py:method:: Segments.termini(self)

    Returns the IDs of all terminal segments

    ::

        self.termini()

    Returns a numpy 1D array with the IDs of all terminal segments in the network. A terminal segment is a segment at the bottom of its local drainage network.

    :Outputs: *ndarray* -- The IDs of the terminal segments in the network


.. _pfdf.segments.Segments.outlet:

.. py:method:: Segments.outlet(self, id, terminal = False)

    Return the indices of the queried segment's outlet pixel

    .. dropdown:: Locate Outlet

        ::

            self.outlet(id)

        Returns the indices of the queried segment's outlet pixel in the stream segment raster. The outlet pixel is the segment's most downstream pixel. The first output is the row index, second output is the column index.

    .. dropdown:: Locate Terminal Outlet

        ::

            self.outlet(id, terminal=True)

        Returns the indices of the queried segment's terminal outlet pixel. The terminal outlet is the final pixel in the segment's local drainage network.

    :Inputs: * **id** (*int*) -- The ID of the queried segment
             * **terminal** (*bool*) -- True to return the indices of the terminal outlet pixel. False (default) to return the indices of the outlet pixel.

    :Outputs: * *int* -- The row index of the outlet pixel
              * *int* -- The column index of the outlet pixel


.. _pfdf.segments.Segments.outlets:

.. py:method:: Segments.outlets(self, terminal = False)

    Returns the row and column indices of all outlet or terminal outlet pixels

    .. dropdown:: Locate Outlets

        ::

            self.outlets()

        Returns a list of outlet pixel indices for the network. The output has one element per stream segment. Each element is a tuple with the outlet indices for the associated segment. The first element of the tuple is the row index, and the second element is the column index.

    .. dropdown:: Locate Terminal Outlets

        :: 

            self.outlets(terminal=True)

        Returns the indices of all terminal outlet pixels in the network. Terminal outlets are outlets at the bottom of their local drainage network. The output list will have one element per terminal outlet.

    :Inputs: * **terminal** (*bool*) -- True to return the indices of the terminal outlet pixels. False (default) to return the indices of all output pixels.

    Outputs: *list[tuple[int, int]]* -- A list of outlet pixel indices


.. _api-segments-variables:

Earth-system Variables
----------------------

.. _pfdf.segments.Segments.area:

.. py:method:: Segments.area(self, mask = None, terminal = False)

    Returns the areas of basins

    .. dropdown:: Catchment Area

        ::

            self.area()

        Computes the total area of the catchment basin for each stream segment. The returned area will be in the same units as the pixel_area property.

    .. dropdown:: Masked Area

        ::

            self.area(mask)

        Computes masked areas for the basins. True elements in the mask indicate pixels that should be included in the calculation of areas. False pixels are ignored and given an area of 0. Nodata elements are interpreted as False.

    .. dropdown:: Terminal Basin Areas

        ::

            self.area(..., *, terminal=True)

        Only returns values for the terminal outlet basins.

    :Inputs: * **mask** (*Raster*) -- A raster mask whose True elements indicate the pixels that should be used to compute upslope areas.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The catchment area for each stream segment


.. _pfdf.segments.Segments.burn_ratio:

.. py:method:: Segments.burn_ratio(self, isburned, terminal = False)

    Returns the proportion of burned pixels in basins

    .. dropdown:: Burn Ratio

        ::

            self.burn_ratio(isburned)

        Given a mask of burned pixel locations, determines the proportion of burned pixels in the catchment basin of each stream segment. Returns a numpy 1D array with the ratio for each segment. Ratios are on the interval from 0 to 1.

    .. dropdown:: Terminal Basin Ratios

        ::

            self.burn_ratio(isburned, terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **isburned** (*Raster*) -- A raster mask whose True elements indicate the locations of burned pixels in the watershed.
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The proportion of burned pixels in each basin


.. _pfdf.segments.Segments.burned_area:

.. py:method:: Segments.burned_area(self, isburned, terminal = False)

    Returns the total burned area of basins

    .. dropdown:: Burned Area

        ::

            self.burned_area(isburned)

        Given a mask of burned pixel locations, returns the total burned area in the catchment of each stream segment. Returns a numpy 1D array with the burned area for each segment. The returned areas will be in the same units as the "pixel_area" property.

    .. dropdown:: Terminal Basin Area

        ::

            self.burned_area(isburned, terminal=True)

        Only computes areas for the terminal outlet basins.

    :Inputs: * **isburned** (*Raster*) -- A raster mask whose True elements indicate the locations of burned pixels within the watershed
             * **terminal** (*bool*) -- True to only compute values for terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The burned catchment area for the basins


.. _pfdf.segments.Segments.confinement:

.. py:method:: Segments.confinement(self, dem, neighborhood, factor = 1)

    Returns the mean confinement angle of each stream segment

    .. dropdown:: Confinement Angle

        ::

            self.confinement(dem, neighborhood)

        Computes the mean confinement angle for each stream segment. Returns these angles as a numpy 1D array. The order of angles matches the order of segment IDs in the object.

        The confinement angle for a given pixel is calculated using the slopes in the two directions perpendicular to stream flow. A given slope is calculated using the maximum DEM height within N pixels of the processing pixel in the associated direction. Here, the number of pixels searched in each direction (N) is equivalent to the "neighborhood" input. The slope equation is thus::

            slope = max height(N pixels) / (N * length)

        where length is one of the following:

        * X axis resolution (for flow along the Y axis)
        * Y axis resolution (for flow along the X axis)
        * length of a raster cell diagonal (for diagonal flow)

        Recall that slopes are computed perpendicular to the flow direction, hence the use of X axis resolution for Y axis flow and vice versa. The confinment angle is then calculated using:

        .. math::

            θ = 180 - \mathrm{tan}^{-1}(\mathrm{slope}_1) - \mathrm{tan}^{-1}(\mathrm{slope}_2)

        and the mean confinement angle is calculated over all the pixels in the stream segment.

        .. admonition:: Example

            Consider a pixel flowing east with neighborhood=4. (East here indicates that the pixel is flowing to the next pixel on its right - it is not an indication of actual geospatial directions). Confinement angles are then calculated using slopes to the north and south. The north slope is determined using the maximum DEM height in the 4 pixels north of the stream segment pixel, such that::

                slope = max height(4 pixels north) / (4 * Y axis resolution)

            and the south slope is computed similarly. The two slopes are used to compute the confinement angle for the pixel, and this process is then repeated for all pixels in the stream segment. The final value for the stream segment will be the mean of these values.

        .. important::

            This syntax requires that the units of the DEM are the same as the units of the stream segment resolution (which you can return using the ``resolution`` property). Use the following syntax if this is not the case.

    .. dropdown:: Scale Length Units

        ::

            self.confinement(dem, neighborhood, factor)

        Also specifies a multiplicative constant needed to scale the stream segment raster resolution to the same units as the DEM. If the raster resolution uses different units than the DEM data, then confinement slopes will be calculated incorrectly. Use this syntax to correct for this.

    :Inputs: * **dem** (*Raster*) -- A raster of digital elevation model (DEM) data.
             * **neighborhood** (*int*) -- The number of raster pixels to search for maximum heights. Must be a positive integer.
             * **factor** (*scalar*) -- A multiplicative constant used to scale the stream segment raster resolution to the same units as the DEM data.

    :Outputs: *ndarray* -- The mean confinement angle for each stream segment.


.. _pfdf.segments.Segments.developed_area:

.. py:method:: Segments.developed_area(self, isdeveloped, terminal = False)

    Returns the total developed area of basins

    .. dropdown:: Developed Area

        ::

            self.developed_area(isdeveloped)

        Given a mask of developed pixel locations, returns the total developed area in the catchment of each stream segment. Returns a numpy 1D array with the developed area for each segment.

    .. dropdown:: Terminal Basin Area

        ::

            self.developed_area(isdeveloped, terminal)

        Only computes areas for the terminal outlet basins.

    :Inputs: * **isdeveloped** (*Raster*) -- A raster mask whose True elements indicate the locations of developed pixels within the watershed.
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

        Given a raster of slopes (rise/run), returns the mean slope for each segment as a numpy 1D array. If a stream segment's pixels contain NaN or NoData values, then the slope for the segment is set to NaN. If ``terminal=True``, only returns values for the terminal segments.

    .. dropdown:: Ignore NaN Pixels

        ::

            self.slope(slopes, omitnan=True)

        Ignores NaN and NoData values when computing mean slope. However, if a segment only contains NaN and NoData values, then its value will still be NaN.

    :Inputs: * **slopes** (*Raster*) -- A slope (rise/run) raster for the watershed
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

.. py:method:: Segments.ruggedness(self, relief)

    Returns the ruggedness of each stream segment catchment

    ::

        self.ruggedness(relief)
        self.ruggedness(relief, terminal=True)

    Returns the ruggedness of the catchment for each stream segment in the network. Ruggedness is defined as a stream segment's vertical relief, divided by the square root of its catchment area. Returns ruggedness values as a numpy 1D array with one element per stream segment. If ``terminal=True``, only returns values for the terminal segments.

    :Inputs: * **relief** (*Raster*) -- A vertical relief raster for the watershed
             * **terminal** (*bool*) -- True to only return values for terminal segments. False (default) to return values for all segments.

    :Outputs: *ndarray* -- The topographic ruggedness of each stream segment
    

.. _pfdf.segments.Segments.upslope_ratio:

.. py:method:: Segments.upslope_ratio(self, mask, terminal = False)

    Returns the proportion of basin pixels that meet a criteria

    .. dropdown:: Upslope Ratio

        ::

            self.upslope_ratio(mask)

        Given a raster mask, computes the proportion of True pixels in the catchment basin for each stream segment. Returns the ratios as a numpy 1D array with one element per stream segment. Ratios will be on the interval from 0 to 1. Note that NoData pixels in the mask are interpreted as False.

    .. dropdown:: Terminal Basins

        ::

            self.upslope_ratio(mask, terminal=True)

        Only computes values for the terminal outlet basins.

    :Inputs: * **mask** (*Raster*) -- A raster mask for the watershed. The method will compute the proportion of True elements in each catchment
             * **terminal** (*bool*) -- True to only compute values for the terminal outlet basins. False (default) to compute values for all catchment basins.

    :Outputs: *ndarray* -- The proportion of True values in each basin


Generic Statistics
------------------

.. _pfdf.segments.Segments.statistics:

.. py:method:: Segments.statistics(asdict = False)

    Prints or returns info about supported statistics

    .. dropdown:: Print Info

        ::

            Segments.statistics()

        Prints information about supported statistics to the console. The printed text is a table with two columns. The first column holds the names of statistics that can be used with the "summary" and "basin_summary" methods. The second column is a description of each statistic.

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

    :Inputs: * **statistic** (*str*) -- A string naming the requested statistic. See ``Segments.statistics()`` for info on supported statistics
             * **values** (*Raster*) -- A raster of data values over which to compute stream segment summary values.

    :Outputs: *ndarray* -- The summary statistic for each stream segment

    
.. _pfdf.segments.Segments.basin_summary:

.. py:method:: Segments.basin_summary(self, statistic, values, mask = None, terminal = False)

    Computes a summary statistic over each catchment or terminal outlet basin

    .. dropdown:: Catchment Summary

        ::

            self.basin_summary(statistic, values)

        Computes the indicated statistic over the catchment basin pixels for each stream segment. Uses the input values raster as the data value for each pixel. Returns a numpy 1D array with one element per stream segment.

        Note that NoData values are converted to NaN before computing statistics. If using one of the statistics that ignores NaN values (e.g. nanmean), a basin's summary value will still be NaN if every pixel in the basin basin is NaN.

        .. tip::

            We recommend only the "outlet", "mean", "sum", "nanmean", and "nansum" statistics whenever possible. The remaining statistics require a less efficient algorithm, and so are much slower to compute. Alternatively, see below for an option to only compute statistics for terminal outlet basins.


    .. dropdown:: Masked Summary

        ::

            self.basin_summary(statistic, values, mask)

        Computes masked statistics over the catchment basins. True elements in the mask indicate pixels that should be included in statistics. False elements are ignored. If a catchment does not contain any True pixels, then its summary statistic is set to NaN. Note that a mask will have no effect on the "outlet" statistic.

    .. dropdown:: Terminal Basin Summaries

        ::

            self.basin_summary(..., terminal=True)

        Only computes statistics for the terminal outlet basins. The output will have one element per terminal segment. The order of values will match the order of IDs reported by the ``Segments.termini`` method. The number of terminal outlet basins is often much smaller than the total number of segments. As such, this option presents a faster alternative and is particularly suitable when computing statistics other than "outlet", "mean", "sum", "nanmean", or "nansum".

    :Inputs: * **statistic** (*str*) -- A string naming the requested statistic. See ``Segments.statistics()`` for info on supported statistics.
             * **values** (*Raster*) -- A raster of data values over which to compute basin summaries
             * **mask** (*Raster*) -- An optional raster mask for the data values. True elements are used to compute basin statistics. False elements are ignored.
             * **terminal** (*bool*) -- True to only compute statistics for terminal outlet basins. False (default) to compute statistics for every catchment basin.

    :Outputs: *ndarray* -- The summary statistic for each basin


.. _api-filtering:

Filtering
---------

.. _pfdf.segments.Segments.remove:

.. py:method:: Segments.remove(self, *, ids = None, indices = None, continuous = True, upstream = True, downstream = True)

    Removes segments from the network while optionally preserving continuity

    .. dropdown:: Remove Segments

        ::

            self.remove(*, ids)
            self.remove(*, indices)

        Attempts to remove the indicated segments, but prioritizes the continuity of the stream network. An indicated segment will not be removed if it is between two segments being retained. Equivalently, segments are only removed from the upstream and downstream ends of a local network. Conceptually, this algorithm first marches upstream, and removes segments until it reaches a segment that was not indicated as input. The algorithm then marches downstream, and again removes segments until it reaches a segment that was not indicated as input. As such, the total number of removed segments may  be less than the number of input segments. Note that if you remove terminal segments after calling the ``locate_basins`` command, the saved basin
        raster may be deleted.

        If using "ids", the input should be a list or numpy 1D array whose elements are the IDs of the segments that may potentially be removed from the network. If using "indices" the input should be a boolean numpy 1D array with one element per segment in the network. True elements indicate the stream segments that may potentially be removed. False elements will always be retained. If you provide both inputs, segments indicated by either input are potentially removed from the network.

        Returns the indices of the segments that were removed from the network as a boolean numpy 1D array. The output indices will have one element per segment in the original network. True elements indicate segments that were removed. False elements are segments that were retained. These indices are often useful for filtering values computed for the original network.

    .. dropdown:: Disregard flow continuity

        ::

            self.remove(..., *, continuous=False)

        Removes all indicated segments, regardless of the continuity of the stream network.

    .. dropdown:: Customize flow edges

        ::

            self.remove(*, continuous=True, upstream=False)
            self.remove(*, continuous=True, downstream=False)

        Further customizes the removal of segments when prioritizing the continuity of the stream network. When upstream=False, segments will not be removed from the upstream end of a local network. Equivalently, a segment will not be removed if it flows into a segment retained in the network. When downstream=False, segments will not be removed from the downstream end of a local network. So a segment will not be removed if a retained segment flow into it. These options are ignored when continuous=False.

    :Inputs: * **ids** (*list | ndarray*) -- A list or numpy 1D array listing the IDs of segments that may be removed from the network
             * **indices** (*ndarray*) -- A boolean numpy 1D array with one element per stream segment. True elements indicate segments that may be removed from the network.
             * **continuous** (*bool*) -- If True (default), segments will only be removed if they do not break the continuity of the stream network. If False, all indicated segments are removed.
             * **upstream** (*bool*) -- Set to False to prevent segments from being removed from the upstream end of a local network. Ignored if continuous=False.
             * **downstream** (*bool*) -- Set to False to prevent segments from being removed from the downstream end of a local network. Ignored if continuous=False.

    :Outputs: *boolean ndarray* -- The indices of the segments that were removed from the network. Has one element per segment in the initial network. True elements indicate removed segments.

    
.. _pfdf.segments.Segments.keep:

.. py:method:: Segments.keep(self, *, ids = None, indices = None, continuous = True, upstream = True, downstream = True)

    Restricts the network to the indicated segments

    .. dropdown:: Keep Segments

        ::

            self.keep(*, ids)
            self.keep(*, indices)

        Attempts to restrict the network to the indicated segments, but prioritizes the continuity of the stream network. A segment will be retained if it is an indicated input, or if it falls between two segments being retained. Equivalently, segments are only removed from the upstream and downstream ends of a local network. Conceptually, this algorithm first marches upstream and removes segments until it reaches a segment that was indicated as input. The algorithm then marches downstream, and again removes segments until reaching a segment that was indicated as input. As such, the total number of retained segments may be greater than the number of input segments. Note that if you remove terminal segments after calling the ``locate_basins`` command, the saved basin raster may be deleted.

        If using "ids", the input should be a list or numpy 1D array whose elements are the IDs of the segments to definitely retain in the network. If using "indices" the input should be a boolean numpy 1D array with one element per segment in the network. True elements indicate stream segments that should definitely be retained. False elements may potentially be removed. If you provide both inputs, segments indicated by either input are definitely retained in the network.

        Returns the indices of the retained segments as a boolean 1D numpy array. The output indices will have one element per segment in the original network. True elements indicate segments that were retained. False elements are segments that were remove. These indices are often useful for filtering values computed from the original network.

    .. dropdown:: Disregard flow continuity

        ::

            self.keep(..., continuous=False)

        Only keeps the indicated segments, regardless of network continuity. All segments not indicated by the "ids" or "indices" inputs will be removed.

    .. dropdown:: Customize flow edges

        ::

            self.keep(..., continuous=True, upstream=False)
            self.keep(..., continuous=True, downstream=False)

        Further customizes the removal of segments when prioritizing the continuity of the stream network. When upstream=False, segments will not be removed from the upstream end of a local network. Equivalently, a segment will not be removed if it flows into a segment retained in the network. When downstream=False, segments will not be removed from the downstream end of a local network. So a segment will not be removed if a retained segment flow into it. These options are ignored when continuous=False.

    :Inputs: * **ids** (*list | ndarray*) -- A list or numpy 1D array listing the IDs of segments that should always be retained in the network
             * **indices** (*ndarray*) -- A boolean numpy 1D array with one element per stream segment. True elements indicate segments that should always be retained in the network.
             * **continuous** (*bool*) -- If True (default), segments will only be removed if they do not break the continuity of the stream network. If False, all non-indicated segments are removed.
             * **upstream** (*bool*) -- Set to False to prevent segments from being removed from the upstream end of a local network. Ignored if  continuous=False.
             * **downstream** (*bool*) -- Set to False to prevent segments from being removed from the downstream end of a local network. Ignored if continuous=False.

    :Outputs: *boolean ndarray* -- The indices of the segments that remained in the network. Has one element per segment in the initial network. True elements indicate retained segments.


.. _pfdf.segments.Segments.copy:

.. py:method:: Segments.copy(self)

    Returns a copy of a *Segments* object

    ::

        self.copy()

    Returns a copy of the current *Segments* object. Stream segments can be removed from the new/old objects without affecting one another. Note that the flow direction raster and saved basin rasters are not duplicated in memory. Instead, both objects reference the same underlying array.

    :Outputs: *Segments* -- A copy of the current *Segments* object.


.. _api-export:

Export
------

.. _pfdf.segments.Segments.geojson:

.. py:method:: Segments.geojson(self, properties = None, *, type = "segments")

    Exports the network to a ``geojson.FeatureCollection`` object

    .. dropdown:: Segments

        ::

            self.geojson()
            self.geojson(..., *, type='segments')

        Exports the network to a ``geojson.FeatureCollection`` object. The individual Features have LineString geometries whose coordinates proceed from upstream to downstream. Will have one feature per stream segment.

    .. dropdown:: Terminal Basins

        ::

            self.geojson(..., *, type='basins')

        Exports terminal outlet basins as a collection of Polygon features. The number of features will be <= the number of local drainage networks. (The number of features will be less than the number of local networks if a local network flows into another local network).

        .. note::

            You can use :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` to pre-build the raster before calling this command. If not pre-built, then this command will generate the terminal basin raster sequentially, which may take a while. Note that :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` includes options to parallelize this process, which may improve runtime.

    .. dropdown:: Outlets

        ::

            self.geojson(..., *, type='outlets')
            self.geojson(..., *, type='segment outlets')

        Exports outlet points as a collection of Point features. If type="outlets", exports the terminal outlet points, which will have one feature per local drainage network. If type="segment outlets", exports the complete set of outlet points, which will have one feature per segment in the network.

    .. dropdown:: Feature Properties

        ::

            self.geojson(properties, ...)   

        Specifies data properties for the GeoJSON features. The "properties" input should be a dict. Each key should be a string and will be interpreted as the name of the associated property field. Each value should be a numpy 1D array with an integer, floating, or boolean dtype. All properties in the output GeoJSON features will have a floating dtype, regardless of the input type. If exporting segments or segment outlets, then each array should have one element per segment in the network. If exporting basins or outlets, then each array should have one element per local drainage network.

    :Inputs: * **properties** (*dict[str, ndarray]*) -- A dict whose keys are the (string) names of the property fields. Each value should be a numpy 1D array with an integer, floating-point, or boolean dtype. Each array should have one element per segment (for segments or segment outlets), or one element per local drainage network (for outlets or basins).
             * **type** (*"segments" | "basins" | "outlets" | "segment outlets"*) -- A string indicating the type of feature to export.

    :Outputs: *geojson.FeatureCollection* -- The collection of stream network features


.. _pfdf.segments.Segments.save:

.. py:method:: Segments.save(self, path, properties = None, *, type = "segments", driver = None, overwrite = False)

    Saves the network to a vector feature file

    .. dropdown:: Save Segments

        ::

            save(path)
            save(path, *, type='segments')
            save(..., overwrite=True)

        Saves the network to the indicated path. Each segment is saved as a vector feature with a LineString geometry whose coordinates proceed from upstream to downstream. The vector features will not have any data properties. In the default state, the method will raise a FileExistsError if the file already exists. Set overwrite=True to enable the replacement of existing files.

        By default, the method will attempt to guess the intended file format based on the path extensions, and will raise an Exception if the file format cannot be guessed. However, see below for a syntax to specify the driver, regardless of extension. You can use::

            >>> pfdf.utils.driver.extensions('vector')

        to return a summary of supported file format drivers, and their associated extensions.

    .. dropdown:: Basins

        ::

            self.save(..., *, type='basins')

        Saves the terminal outlet basins as a collection of Polygon features. The number of features will be <= the number of local drainage networks. (The number of features will be less than the number of local networks if a local network flows into another local network).

        .. note::

            You can use :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` to pre-build the raster before calling this command. If not pre-built, then this command will generate the terminal basin raster sequentially, which may take a while. Note that :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` includes options to parallelize this process, which may improve runtime.

    .. dropdown:: Outlets

        ::

            self.save(..., *, type='outlets')
            self.save(..., *, type='segment outlets')

        Saves outlet points as a collection of Point features. If type="outlets", saves the terminal outlet points, which will have one feature per local drainage network. If type="segment outlets", saves the complete set of outlet points, which will have one feature per segment in the network.

    .. dropdown:: Feature Properties

        ::

            self.save(path, properties, ...)

        Specifies data properties for the saved features. The "properties" input should be a dict. Each key should be a string and will be interpreted as the name of the associated property field. Each value should be a numpy 1D array with an integer, floating, or boolean dtype. All properties in the saved features will have a floating dtype, regardless of the input type. If saving segments or segment outlets, then each array should have one element per segment in the network. If saving basins or outlets, then each array should have one element per local drainage network.

    .. dropdown:: Specify File Format

        ::

            save(..., *, driver)

        Specifies the file format driver to used to write the vector feature file. Uses this format regardless of the file extension. You can call::

            >>> pfdf.utils.driver.vectors()

        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR) to write vector files, and so additional drivers may work if their associated build requirements are met. You can call::

            >>> fiona.drvsupport.vector_driver_extensions()

        to summarize the drivers currently supported by fiona, and a complete list of driver build requirements is available here: `Vector Drivers <https://gdal.org/drivers/vector/index.html>`_

    :Inputs: * **path** (*Path | str*) -- The path to the output file
             * **properties** (*dict[str, ndarray]*) -- A dict whose keys are the (string) names of the property fields. Each value should be a numpy 1D array with an integer, floating-point, or boolean dtype. Each array should have one element per segment (for segments or segment outlets), or one element per local drainage network (for outlets or basins).
             * **type** (*"segments" | "basins" | "outlets" | "segment outlets"*) -- A string indicating the type of feature to export.
             * **overwrite** (*bool*) -- True to allow replacement of existing files. False (default) to prevent overwriting.
             * **driver** (*str*) -- The name of the file-format driver to use when writing the vector feature file. Uses this driver regardless of file extension.

             