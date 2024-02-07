Segments
========

The :ref:`Segments class <pfdf.segments.Segments>` is the core of pfdf, and allows users to build and manage a stream segment network. 

::

    >>> from pfdf.segments import Segments

Typical workflow is as follows:

1. Build an initial stream segment network by :ref:`initializing a Segments object <initial-network>`
2. :doc:`Compute earth-system variables <values>` for the segments
3. :doc:`Reduce the network <filter>` to a final set of model-worthy segments
4. Use the object to :doc:`calculate inputs <values>` for hazard assessment models
5. :doc:`Save assessment results <export>` to file or GeoJSON

.. tip:: The :doc:`hazard assessment tutorial </tutorials/assessment>` demonstrates many of the commands discussed in this section.


Terminology
-----------
Before continuing this guide, we recommend reading the :doc:`glossary <../glossary>`, which defines key terms used throughout the ``Segments`` documentation. We suggest reading the glossary in order, as most terms build off of previous definitions.


.. _initial-network:

Building a Network
------------------
You can build an initial stream segment network by :ref:`initializing a Segments object <pfdf.segments.Segments.__init__>`. There are two essential inputs for this procedure: 

1. A D8 flow direction raster (see the :doc:`watershed module <../watershed>`), and
2. A raster mask indicating watershed pixels that may potentially be stream segments. 

::

    >>> segments = Segments(flow, mask)

Note that the flow direction raster must have (affine) transform metadata.

In part, the mask is used to limit stream segments to watershed pixels that likely represent a physical stream bed. To do so, the mask will typically limit the stream segments to pixels that exceed some minimum flow accumulation. The mask might also remove certain areas from the hazard modeling process. For example, a mask might screen out pixels in large bodies of water, or below human development in order to prevent hazard modeling in these areas. For example::

    >>> from pfdf import watershed
    >>> flow = watershed.flow(conditioned_dem)
    >>> drainage_area = watershed.accumulation(flow) * flow.pixel_area
    >>> mask = drainage_area >= 100

    >>> segments = Segments(flow, mask)

When building a stream segment network, you may also provide an optional maxmimum length. In this case, any stream segments exceeding the indicated length will be split into multiple pieces in the Segments object::

    >>> segments = Segments(flow, mask)
    >>> segments.length   # The number of segments
    2422

    >>> segments = Segments(flow, mask, max_length=500)
    >>> segments.length   # More segments because some were split
    2561

Basic Properties
----------------
:ref:`Skip to table <segments-properties>`

A Segments object includes a number of properties with information about the stream segment network. The ``length`` property returns the total number of segments in the network, and ``segments`` returns a list of ``shapely.LineString`` objects representing the segments. The coordinates in the LineStrings are ordered from upstream to downstream. The ``crs`` property reports the coordinate reference system associated with the LineString coordinates, and can be used to locate the segments spatially. The ``lengths`` (plural) property returns the lengths of the individual segments as a 1D numpy array. These lengths will be in the base units of the coordinate reference system. (In practice, this is often meters).

Segments objects also include two properties to faciliate working with terminal outlet basins. The ``nlocal`` property returns the number of local drainage networks in the network. This number is equivalent to the number of terminal outlet basins, which is the same as the number of terminal outlets. The ``isterminus`` property returns a boolean 1D numpy array that indicates whether each segment is a terminal segment. True elements indicate a terminal segment, False elements are not terminal segments.

Each segment in the network is assigned a unique integer ID. These IDs are used to represent segments within rasters, as well as to identify segments for various commands. The ID for a given segment is constant, so will not change if other segments are removed from the network. The ``ids`` property returns a numpy 1D array with the ID of each segment.

A Segment object also tracks the connectivity of segments in the network. The ``child`` property returns a numpy 1D array holding the ID of each segment's child. A value of 0 indicates that the segment does not have a child (equivalently, that the segment is a terminal segment). You can also use the ``parents`` property to return the IDs of each segment's parent segments. Parents are represented as a numpy array with one row per segment and multiple columns. Each column represents a parent. Each row will contain some combination of 0 and non-zero elements. Non-zero elements are the IDs of the segment's parents. Zero elements are fill values that accommodate different numbers of parents for different segments.

The following table summarizes these properties:

.. _segments-properties:

.. list-table::
    :header-rows: 1

    * - Property
      - Description
      - Type
    * - length
      - Number of segments in the network
      - ``int``
    * - segments
      - Segment representations, including coordinates.
      - ``list[shapely.LineString]``
    * - crs
      - Coordinate reference system
      - ``rasterio.coords.CRS``
    * - lengths
      - Spatial length of each segment in the network.
      - 1D numpy array
    * - nlocal
      - Number of local drainage basins
      - ``int``
    * - isterminus
      - Whether each segment is a terminal segment
      - Boolean 1D numpy array
    * - ids
      - Unique and constant ID for each segment
      - 1D numpy array
    * - child
      - The ID of each segment's child segment
      - 1D numpy array
    * - parents
      - The IDs of each segment's parent segments
      - 2D numpy array



