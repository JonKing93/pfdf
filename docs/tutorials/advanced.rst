Advanced Topics
===============

These tutorials examine several advanced topics. They include:

:doc:`Raster Properties <notebooks/06_Raster_Properties>`
    Examines :ref:`Raster <pfdf.raster.Raster>` metadata and data properties in greater detail.

:doc:`Raster Factories <notebooks/07_Raster_Factories>`
    Examines methods to :doc:`create Raster objects </guide/rasters/create>` from various data sources.

:doc:`Spatial Metadata <notebooks/08_Spatial_Metadata>`
    Introduces the :ref:`BoundingBox <pfdf.projection.BoundingBox>` and :ref:`Transform <pfdf.projection.Transform>` classes, which are used to manage geospatial raster metadata

:doc:`RasterMetadata Class <notebooks/09_RasterMetadata_Class>`
    Introduces the :ref:`RasterMetadata class <pfdf.raster.RasterMetadata>`, which manages raster metadata without loading data values into memory

:doc:`Parallelizing Basins <notebooks/10_Parallel_Basins>`
    Demonstrates how to locate :ref:`outlet basins <basins>` in parallel using multiple CPUs

:doc:`Parameter Sweeps <notebooks/11_Parameter_Sweep>`
    Demonstrates how to run assessment models using multiple values of model parameters.

.. note::

    The linked pages hold pre-run tutorials that don't require any setup. However, we recommend running the tutorials as Jupyter notebooks when possible, as this will allow you to interact with pfdf code directly. You can find setup instructions here: :doc:`Tutorial Setup <how-to-run>`

.. toctree::
    :hidden:

    Raster Properties <notebooks/06_Raster_Properties>
    Raster Factories <notebooks/07_Raster_Factories>
    Spatial Metadata <notebooks/08_Spatial_Metadata>
    RasterMetadata Class <notebooks/09_RasterMetadata_Class>
    Parallelizing Basins <notebooks/10_Parallel_Basins>
    Parameter Sweep <notebooks/11_Parameter_Sweep>