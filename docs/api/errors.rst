errors module
=============

.. _pfdf.errors:

.. py:module:: pfdf.errors

    Classes that define custom exceptions

Numpy Arrays
------------

.. py:exception:: ArrayError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    Generic class for invalid numpy arrays

.. py:exception:: EmptyArrayError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.ArrayError`

    When a numpy array has no elements

.. py:exception:: DimensionError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.ArrayError`

    When a numpy array has invalid nonsingleton dimensions

.. py:exception:: ShapeError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.ArrayError`

    When a numpy axis has an invalid shape

----

Spatial Metadata
----------------

.. py:exception:: CRSError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When a coordinate reference system is invalid


.. py:exception:: MissingCRSError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.CRSError`

    When a required CRS is missing.


.. py:exception:: TransformError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When an affine transformation is invalid


.. py:exception:: MissingTransformError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.TransformError`

    When a required transform is missing


.. py:exception:: MissingNoDataError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When a required NoData value is missing

----

Rasters
-------

.. py:exception:: RasterError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    Generic class for invalid Raster metadata.


.. py:exception:: RasterShapeError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.RasterError`

    When a raster array has an invalid shape


.. py:exception:: RasterTransformError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.RasterError`

    When a raster has an invalid affine transformation


.. py:exception:: RasterCRSError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.RasterError`

    When a raster has an invalid coordinate reference system

----

Vector Features
---------------

.. py:exception:: FeaturesError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When vector features are not valid


.. py:exception:: FeatureFileError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.FeaturesError`

    When a vector feature file cannot be read


.. py:exception:: NoFeaturesError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.FeaturesError`

    When there are no vector features to convert to a raster


.. py:exception:: GeometryError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.FeaturesError`

    When a feature geometry is not valid


.. py:exception:: CoordinateError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.GeometryError`

    When a feature's coordinates are not valid


.. py:exception:: PolygonError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.CoordinateError`

    When a polygon's coordinates are not valid

.. py:exception:: PointError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.CoordinateError`

    When a point's coordinates are not valid


----

.. _overlap-errors:

Overlap
-------

.. py:exception:: NoOverlapError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When a dataset does not overlap a required bounding box.

.. py:exception:: NoOverlappingFeaturesError
    :module: pfdf.errors

    Bases: :py:class:`~pfdf.errors.NoOverlapError`, :py:class:`~pfdf.errors.NoFeaturesError`

    When a vector feature dataset does not overlap a required bounding box.




----

Models
------

.. py:exception:: DurationsError
    :module: pfdf.errors

    Bases: :py:class:`Exception`

    When queried rainfall durations are not recognized


----

.. _data-api-errors:

Data Acquisition
----------------

.. py:exception:: DataAPIError

    Bases: :py:class:`Exception`

    When an API response is not valid


.. py:exception:: InvalidJSONError

    Bases: :py:class:`~pfdf.errors.DataAPIError`

    When API JSON is not valid


.. py:exception:: MissingAPIFieldError

    Bases: :py:class:`~pfdf.errors.DataAPIError`, :py:class:`KeyError`

    When an API JSON response is missing a required field   


.. py:exception:: TNMError

    Bases: :py:class:`~pfdf.errors.DataAPIError`

    Errors unique to the TNM API


.. py:exception:: TooManyTNMProductsError

    Bases: :py:class:`~pfdf.errors.TNMError`

    When a TNM query has too many search results


.. py:exception:: NoTNMProductsError

    Bases: :py:class:`~pfdf.errors.TNMError`

    When there are no TNM products in the search results


.. py:exception:: LFPSError

    Bases: :py:class:`~pfdf.errors.DataAPIError`

    Errors unique to the LANDFIRE LFPS API


.. py:exception:: InvalidLFPSJobError

    Bases: :py:class:`~pfdf.errors.LFPSError`

    When a LANDFIRE LFPS job cannot be used for a data read


.. py:exception:: LFPSJobTimeoutError

    Bases: :py:class:`~pfdf.errors.LFPSError`

    When a LANDFIRE LFPS job takes too long to execute