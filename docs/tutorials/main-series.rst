Main Series
===========

The main tutorial series introduces the concepts needed to implement standard hazard assessments. The series consists of the following tutorials:

:doc:`Raster Intro <notebooks/02_Raster_Intro>`
    Introduces the :ref:`Raster class <pfdf.raster.Raster>`, which is used to manage raster datasets.

:doc:`Download Data <notebooks/03_Download_Data>`
    Shows how to use the :ref:`data package <pfdf.data>` to download commonly used assessment datasets from the internet.

:doc:`Preprocessing <notebooks/04_Preprocessing>`
    Shows how to use the :doc:`Raster class </guide/rasters/preprocess>` to clean and reproject datasets prior to an assessment.

:doc:`Hazard Assessment <notebooks/05_Hazard_Assessment>`
    Shows how to use pfdf components to implement a hazard assessment.


.. note::

    The linked pages hold pre-run tutorials that don't require any setup. However, we recommend running the tutorials as Jupyter notebooks when possible, as this will allow you to interact with pfdf code directly. You can find setup instructions here: :doc:`Tutorial Setup <how-to-run>`

.. toctree::
    :hidden:

    Raster Intro <notebooks/02_Raster_Intro>
    Download Data <notebooks/03_Download_Data>
    Preprocessing <notebooks/04_Preprocessing>
    Hazard Assessment <notebooks/05_Hazard_Assessment>