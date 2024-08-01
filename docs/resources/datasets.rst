Useful Datasets
===============

This page provides links to datasets that may prove useful for running pfdf. Note that you are not required to use these datasets for your own analyses. Instead, they are intended to provide a starting point for US-based hazard assessments and research.

----

`DEM <https://apps.nationalmap.gov/downloader/#/>`_
    This link provides digital elevation model data from the USGS National Map. The 10 meter dataset is most appropriate for pfdf. This is accessed as the "1/3 arcsecond" 3DEP Elevation Product.

----

`EVT <https://www.landfire.gov/viewer/>`_
    This link can be used to download existing vegetation type data released by `LANDFIRE <https://www.landfire.gov/>`_. This dataset is often used to create water masks and development masks for pfdf.

----

`Soil Characteristics <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_
    This link can be used to download STATSGO soils data useful for implementing the :doc:`Staley 2017 models </guide/models/s17>`. The dataset is a collection of zipped Shapefiles, and the most relevant zip archives follow the naming pattern ``ussoils_XYshp.zip``. KF-factors are stored in the ``KFFACT`` field, and soil thicknesses are in the ``THICK`` field.

----

`Historical Fires <https://mtbs.gov/direct-download>`_
    This link provides access to historical fire data from MTBS. These datasets include:

    .. list-table::
        :header-rows: 1

        * - Dataset
          - File Suffix
        * - Fire perimeter
          - ``burn_bndy.shp``
        * - dNBR
          - ``dnbr.tif``
        * - Burn Severity
          - ``dnbr6.tif``

    Downloaded burn severities use the following classification scheme:

    .. list-table::
        :header-rows: 1

        * - Severity Class
          - Description
        * - 1
          - Unburned
        * - 2
          - Low
        * - 3
          - Moderate
        * - 4
          - High
        * - 5
          - Enhanced Greening
        * - 6
          - Non-processing mask (often clouds)

