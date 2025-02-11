Useful Datasets
===============

This page provides links to datasets that may prove useful for running pfdf. Note that you are not required to use these datasets for your own analyses. Instead, they are intended to provide a starting point for US-based hazard assessments and research.


Digital Elevation Models
------------------------
You can download DEMs from the USGS's The National Map (TNM) using the :ref:`dem module <pfdf.data.usgs.tnm.dem.read>`. Alternatively, you can download TNM datasets here: `TNM Data Portal <https://apps.nationalmap.gov/downloader/#/>`_


Existing Vegetation Type
------------------------
You can download `LANDFIRE <https://www.landfire.gov/>`_ existing vegetation type (EVT) rasters using the :ref:`landfire module <pfdf.data.landfire.read>`. Alternatively, you can find EVT datasets here: `LANDFIRE Data Portal <https://www.landfire.gov/viewer/>`_


Soil Characteristics
--------------------
You can download soil characteristic data (including KF-factors and soil thickness) from the `STATSGO archive <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_, using the :ref:`statsgo module <pfdf.data.usgs.statsgo.read>`. Alternatively, you can find this data in the ScienceBase items for the `STATSGO COG Collection <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_, and `STATSGO source archive <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_. The COG collection holds select fields from the source archive that have been reformatted as cloud-optimized GeoTiffs (COGs).


Precipitation Frequencies
-------------------------
You can download precipitation frequency estimates (PFEs) from NOAA Atlas 14 using the :ref:`atlas14 module <pfdf.data.noaa.atlas14.download>`. Alternatively, you can find NOAA Atlas 14 data here: `NOAA Atlas 14 <https://hdsc.nws.noaa.gov/pfds/>`_


Hydrologic Units
----------------
You can download hydrologic unit (HU) data from the USGS's National Hydrologic Dataset using the :ref:`nhd module <pfdf.data.usgs.tnm.nhd>`. Alternatively, you can find HU datasets here: `TNM Data Portal <https://apps.nationalmap.gov/downloader/#/>`_


Soil Burn Severity
------------------
Use this link to download soil burn severity (SBS) datasets from the `BAER <https://burnseverity.cr.usgs.gov/baer/>`_ data portal: `BAER SBS Portal <https://burnseverity.cr.usgs.gov/baer/baer-imagery-support-data-download>`_


Historical Fires
----------------
This link provides access to historical fire datasets from MTBS: `MTBS Historical Fires <https://mtbs.gov/direct-download>`_

These datasets include:

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

