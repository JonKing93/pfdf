Segments
========

The :ref:`Segments class <pfdf.segments.Segments>` is the core of pfdf, and allows users to build and manage a stream segment network. 

::

    >>> from pfdf.segments import Segments

Typical workflow is as follows:

1. Build an initial stream segment network by :ref:`initializing a Segments object <initial-network>`
2. :doc:`Compute earth-system variables <values>` for the segments
3. :doc:`Filter the network <filter>` to a final set of model-worthy segments
4. Use the object to :doc:`calculate inputs <values>` for hazard assessment models
5. :doc:`Save assessment results <export>` to file or GeoJSON

.. tip:: 
  
    The :doc:`hazard assessment tutorial </tutorials/assessment>` demonstrates many of the commands discussed in this section.


Terminology
-----------
Before continuing this guide, we recommend reading the :doc:`glossary <../glossary>`, which defines key terms used throughout the ``Segments`` documentation. We suggest reading the glossary in order, as most terms build off of previous definitions.


.. _initial-network:

Building a Network
------------------
You can build an initial stream segment network by :ref:`initializing a Segments object <pfdf.segments.Segments.__init__>`. There are two essential inputs for this procedure: 

1. A D8 flow direction raster (see the :doc:`watershed module </guide/watershed/watershed>`), and
2. A raster mask indicating watershed pixels that may potentially be stream segments. 

::

    # Delineate a network
    >>> segments = Segments(flow, mask)

Note that the flow direction raster must have a CRS and a Transform.

In part, the mask is used to limit stream segments to watershed pixels that likely represent a physical stream bed. To do so, the mask will typically limit the stream segments to pixels that exceed some minimum flow accumulation. The mask might also remove certain areas from the hazard modeling process. For example, a mask might screen out pixels in large bodies of water, or below human development in order to prevent hazard modeling in these areas. For example::

    # Create a delineation mask
    >>> from pfdf import watershed
    >>> flow = watershed.flow(conditioned_dem)
    >>> drainage_area = watershed.accumulation(flow) * flow.pixel_area
    >>> mask = drainage_area >= 100

    # Delineate the network
    >>> segments = Segments(flow, mask)

When building a stream segment network, you may also provide an optional maximum length. In this case, any stream segments exceeding the indicated length will be split into multiple pieces in the *Segments* object. By default, ``max_length`` is interpreted in meters, but you can use the ``units`` option to specify other units::

    # Delineate a network and allow any length
    >>> segments = Segments(flow, mask)
    >>> segments.length   # The number of segments
    2422

    # Delineate a network, but limit the maximum length to 500 meters
    >>> segments = Segments(flow, mask, max_length=500)
    >>> segments.length   # More segments because some were split
    2561

    # Other units
    >>> segments = Segments(flow, mask, max_length=0.5, units='kilometers')


Basic Properties
----------------
:ref:`Skip to table <segments-properties>`

A *Segments* object includes a number of properties with information about the stream segment network. The ``size`` property returns the total number of segments in the network, and the ``segments`` property returns a list of ``shapely.LineString`` objects representing the segments. The coordinates in the LineStrings are ordered from upstream to downstream. The ``crs`` property reports the coordinate reference system associated with the LineString coordinates, and can be used to locate the segments spatially.

Each segment in the network is assigned a unique integer ID. These IDs are used to represent segments within rasters, as well as to identify segments for various commands. The ID for a given segment is constant, so will not change if other segments are removed from the network. The ``ids`` property returns a numpy 1D array with the ID of each segment.

A *Segments* object also includes properties to faciliate working with outlets and local drainage basins. The ``nlocal`` property returns the number of local drainage networks in the network, and ``terminal_ids`` returns the IDs of the terminal outlet segments.

The following table summarizes these properties:

.. _segments-properties:

.. list-table::
    :header-rows: 1

    * - Property
      - Description
      - Type
    * - size
      - Number of segments in the network
      - ``int``
    * - segments
      - Segment representations, including coordinates.
      - ``list[shapely.LineString]``
    * - crs
      - Coordinate reference system
      - ``pyproj.CRS``
    * - ids
      - Unique and constant ID for each segment
      - 1D numpy array
    * - terminal_ids
      - The IDs of the terminal outlet segments
      - 1D numpy array
    * - nlocal
      - Number of local drainage basins
      - ``int``


