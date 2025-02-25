projection package
==================

.. _pfdf.projection:

.. py:module:: pfdf.projection

Classes that implement raster projections and spatial metadata.

.. list-table::
    :header-rows: 1

    * - Content
      - Description
    * - :ref:`crs module <pfdf.projection.crs>`
      - Utility functions for working with ``pyproj.CRS`` objects
    * - ``CRS`` class
      - CRS class used by pfdf. Currently an alias to ``pyproj.CRS``
    * - :ref:`BoundingBox class <pfdf.projection.BoundingBox>`
      - Class implementing bounding box metadata
    * - :ref:`Transform class <pfdf.projection.Transform>`
      - Class implementing affine transform metadata

----

.. toctree::

    crs module <crs>
    BoundingBox class <bbox>
    Transform class <transform>