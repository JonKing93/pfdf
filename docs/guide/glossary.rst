Glossary
========
This section defines key terms used throughout the documentation. We recommend reading this glossary in order, as most terms build off of previous definitions.

* :ref:`Stream Segments <def-segments>`
* :ref:`Local Drainage Network <def-local>`
* :ref:`Upstream Parents <def-parents>`
* :ref:`Downstream Child <def-child>`
* :ref:`Outlets <def-outlet>`
* :ref:`Terminal Outlets <def-terminal-outlet>`
* :ref:`Catchment Basins <def-catchment>`
* :ref:`Terminal Outlet Basins <def-basin>`

----

.. _def-segments:

Stream Segments
    A stream segment approximates a stream bed in a drainage area. Each stream segment consists of a set of points that proceed from upstream to downstream. When multiple segments meet at a confluence point, then the upstream segments
    end just before the confluence, and a new segment begins at the confluence. Stream segments are well-represented as LineString (also known as Polyline) features.

.. _def-local:

Local Drainage Network
    A local drainage network is a subset of stream segments that exhibit flow connectivity. Each segment in a local network flows directly into another local segment and/or has another local segment flow directly into it. It is common for a stream segment network to consist of multiple local drainage networks. Note that the distinguishing characteristic of a local network is connectivity, rather than flow paths. As such, it is possible for a local network to be downstream of another local network. So long as the segments in the two networks do not connect, the networks are considered distinct, even if one network eventually flows into the other.

.. _def-parents:

Upstream Parents
    A segment's upstream parents are the segments that flow immediately into the segment. A segment may have no parents (if it is at the top of its local drainage network), or multiple parents (if the segment begins at a confluence point). The key characteristic of a parent is immediate upstream connectivity. A upstream segment that flows into the current segment via intermediate segments is not a parent of the current segment.

.. _def-child:

Downstream Child
    A segment's downstream child is the segment that it flows immediately into. A segment may have at most one child. A terminal segment (a segment at the bottom of a local drainage network) will not have a child. The key characteristic of a child is immediate downstream connectivity. If the current segment flows into a downstream segment via intermediate segments, then the downstream segment is not a child of the current segment.

.. _def-outlet:

Outlets
    An outlet is the final, most downstream point in a stream segment. All points that eventually flow into the stream segment will eventually flow through the outlet (and the outlet is the most upstream point at which this is the case). When multiple segments join at a confluence, then the upstream outlets are *just before* the confluence point. As such, no two stream segments will share the same outlet point. Outlets are well-represented as point features.

.. _def-terminal-outlet:

Terminal Outlet
    A terminal outlet is the outlet point of a local drainage network. The segment associated with the outlet is sometimes referred to as a "terminal segment". All the stream segments in a local network share the same terminal outlet. As such, the terminal outlets are a subset of the complete set of segment outlets, and the terminal outlet for a segment is not necessarily the same as the segment's outlet. Terminal outlets are well-represented as point features.

.. _def-catchment:

Catchment Basin
    The catchment basin for a stream segment is the complete set of points that eventually drain into the segment's outlet. If a stream segment has upstream parents, then its catchment basin will include the (necessarily) smaller catchment basins of the parents. Catchment basins are well-represented as Polygon features.

.. _def-basin:

Terminal Outlet Basin
    A terminal outlet basin is the catchment basin for a terminal segment. This is the complete set of points that eventually drain into the terminal outlet point of a local drainage network. All the stream segments in a local network are associated with the same terminal outlet basin. As such, the terminal outlet basins are a subset of the complete set of segment catchment basins. Note that a given segment's catchment basin will be a subset of the points in its terminal outlet basin. Terminal outlet basins are well-represented as Polygon features.

