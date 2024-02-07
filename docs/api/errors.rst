pfdf.errors module
==================

.. _pfdf.errors:

.. py:module:: pfdf.errors

    Classes that define custom exceptions

Numpy Arrays
------------

.. py:exception:: pfdf.errors.ArrayError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    Generic class for invalid numpy arrays

.. py:exception:: pfdf.errors.EmptyArrayError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.ArrayError`

    When a numpy array has no elements

.. py:exception:: pfdf.errors.DimensionError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.ArrayError`

    When a numpy array has invalid nonsingleton dimensions

.. py:exception:: pfdf.errors.ShapeError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.ArrayError`

    When a numpy axis has an invalid shape


Spatial Metadata
----------------

.. py:exception:: pfdf.errors.CrsError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When a coordinate reference system is invalid

.. py:exception:: pfdf.errors.TransformError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When an affine transformation is invalid


Rasters
-------

.. py:exception:: pfdf.errors.RasterError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    Generic class for invalid Raster metadata.


.. py:exception:: pfdf.errors.RasterShapeError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.RasterError`

    When a raster array has an invalid shape


.. py:exception:: pfdf.errors.RasterTransformError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.RasterError`

    When a raster has an invalid affine transformation


.. py:exception:: pfdf.errors.RasterCrsError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.RasterError`

    When a raster has an invalid coordinate reference system


Vector Features
---------------

.. py:exception:: pfdf.errors.FeaturesError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When vector features are not valid


.. py:exception:: pfdf.errors.FeatureFileError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.FeaturesError`

    When a vector feature file cannot be read

.. py:exception:: pfdf.errors.GeometryError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.FeaturesError`

    When a feature geometry is not valid


.. py:exception:: pfdf.errors.CoordinatesError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.GeometryError`

    When a feature's coordinates are not valid


.. py:exception:: pfdf.errors.PolygonError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.CoordinatesError`

    When a polygon's coordinates are not valid

.. py:exception:: pfdf.errors.PointError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.CoordinatesError`

    When a point's coordinates are not valid


Models
------

.. py:exception:: pfdf.errors.DurationsError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When queried rainfall durations are not recognized
