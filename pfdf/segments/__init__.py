"""
Build and manage stream segment networks
----------
This subpackage contains modules used to implement the "Segments" class, which
provides methods for managing the stream segments in a drainage network. Common 
operations include:

    * Building a stream segment network
    * Filtering the network to a set of model-worthy segments
    * Calculating values for each segment in the network, and
    * Exporting the network (and associated data value) to file or GeoJSON

Please see the documentation of the Segments class for details on implementing 
these procedures.
----------
Class:
    Segments        - Builds and manages a stream segment network

Internal:
    _geojson        - Subpackage to export Segments to geojson
    _validate       - Subpackage to validate inputs for Segments routines
    _segments       - Module implementing the Segments class
    _basins         - Module to locate basins sequentially or in parallel
    _confinement    - Module to compute confinement angles
"""

from pfdf.segments._segments import Segments
