Preprocessing Tutorial
======================

This tutorial shows how to use pfdf to prepare input datasets for an assessment. In general, pfdf requires input datasets to be rasters with the same coordinate reference system (CRS), shape, resolution, and alignment. The library also requires some rasters to fall within a valid data range. However, real datasets aren't usually this clean, and so pfdf provides commands to help achieve these requirements. In this tutorial, we'll demonstrate these commands for a variety of common use cases.

.. admonition:: Download

  You can download the datasets and scripts used in this tutorial here: :doc:`Download Files <download>`. This tutorial follows the ``preprocess`` script. See also ``preprocess_plots`` to reproduce the figures.




Datasets
--------

In this tutorial, we'll start with the following input datasets:

.. _tutorial-datasets:

.. list-table::

    * - **Input Dataset**
      - **Description**
      - **Type**
      - **Resolution**
      - **Shape**
      - **CRS**
    * - perimeter.shp
      - Burn-perimeter polygon features
      - MultiPolygon
      - N/A
      - N/A
      - EPSG: 26911
    * - dem.tif
      - 10 meter digital elevation model
      - Raster
      - 10 meters
      - 2015 x 1957
      - EPSG: 26911
    * - dnbr.tif
      - Differenced normalized burn ratio
      - Raster
      - 10 meters
      - 1280 x 1587
      - EPSG: 26911
    * - kf-factor.shp
      - Soil KF-factor polygon features
      - Polygon
      - N/A
      - N/A
      - EPSG: 26911
    * - retainments.shp
      - Debris-retention features
      - MultiPoint
      - N/A
      - N/A
      - EPSG: 26911
    * - evt.tif
      - Existing vegetation type
      - Raster
      - 30 meters
      - 962 x 1036
      - EPSG: 5070

And we will produce following preprocessed rasters:

.. list-table::

    * - **Raster**
      - **Description**
    * - perimeter
      - Mask of the burned area. Defines the domain of the assessment.
    * - dem
      - Digital elevation model. Used to compute flow directions.
    * - dnbr
      - Provides a measure of burn severity and is used by hazard assessment models.
    * - severity
      - Divides burn severity into 4 classes. Used to delineate a network and run models.
    * - kf-factor
      - Soil KF-factors. Used to implement the :doc:`models of Staley et al., 2017 </guide/models/s17>`.
    * - retainments
      - A mask of features designed to stop debris-flows. Used to design the initial network.
    * - iswater
      - A mask of water bodies. Used to design the initial network.
    * - isdeveloped
      - A mask of human-developed terrain. Used to design the initial network.

The preprocessed rasters will all have the following characteristics:

==============  =====
Characteristic  Value 
==============  =====
Resolution      10 meters
Shape           1280 x 1587
CRS             EPSG: 26911
==============  =====
  

    
Getting Started
---------------
We'll start by importing the :doc:`Raster </guide/rasters/intro>` class, which contains most preprocessing routines. We'll also import the :doc:`severity </guide/misc/severity>` module, which can estimate burn severity from dNBR:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 2
  :end-line: 4

Next, we'll create a *Raster* object for each of the datasets that are already rasters. (And see the :doc:`Rasters tutorial <rasters>` for more practice on these objects):

.. include:: download/code/preprocess.py
  :code:
  :start-line: 6
  :end-line: 9

Inspecting the latitude and longitude labels, we can see that these three rasters have different spatial bounds. We can also see that the EVT raster uses a different CRS than the DEM and dNBR rasters. As we progress through the tutorial, we will modify these rasters to have the same CRS and bounds. 

.. tab-set::

    .. tab-item:: DEM

        .. image:: /images/preprocess/dem.png
          :alt: A DEM raster shows topography over an area.

    .. tab-item:: dNBR

        .. image:: /images/preprocess/dnbr.png
          :alt: A dNBR raster shows burn ratios over an area.

    .. tab-item:: EVT

        .. image:: /images/preprocess/evt.png
          :alt: An EVT raster shows vegetation/terrain types over an area.






Vector Features
---------------

.. note:: 
  
  This tutorial uses GeoJSON to represent vector features, but pfdf will accept most vector feature file formats. See the :ref:`vector driver guide <vector-drivers>` for a complete list of supported formats.

The burn perimeter is a polygon GeoJSON file, so we'll first use the :ref:`Raster.from_polygons <pfdf.raster.Raster.from_polygons>` command to convert it to a raster. Specifically, we'll convert the polygons to a boolean mask with the same resolution as the DEM.

The burn perimeter raster is often used to define the domain of a hazard assessment. However, we'll usually want to include areas outside the perimeter in our assessment, because unburned areas below the perimeter are still at risk of debris-flow runout. To accommodate this, we'll also :ref:`buffer <pfdf.raster.Raster.buffer>` the perimeter raster by 3 kilometers:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 11
  :end-line: 13

Inspecting the raster, we can see that 3 kilometers of NoData have been appended to each edge of the perimeter.

.. tab-set::

    .. tab-item:: Buffered perimeter

      .. image:: /images/preprocess/buffered-perimeter.png
        :alt: A mask of pixels within the burn perimeter.



We'll also use the :ref:`from_polygons <pfdf.raster.Raster.from_polygons>` command to convert the soil KF-factor shapefile to a raster. However, the KF-factor raster should be a raster of data values, rather than a boolean mask. The KF-factor for each polygon is stored in the ``KFFACT`` field, so we'll use the ``field`` option to set the raster's pixels to these values:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 13
  :end-line: 14

Inspecting the raster, we can see that the KF-factor dataset consisted of several large polygons, which are now represented as raster pixels. Note that the raster contains an area of negative values (dark blue region in the middle right), even though pfdf requires positive KF-factors. We will correct for this in a :ref:`later step <constrain-kf>`.

.. _kf-plot:

.. tab-set::

  .. tab-item:: KF-factor

    .. image:: /images/preprocess/kf-factor.png
      :alt: A raster of KF-factor values over an area.



Finally, we'll use the :ref:`from_points command <pfdf.raster.Raster.from_points>` to convert the debris-retention points to a raster. This command converts each point to a single pixel:
  
.. include:: download/code/preprocess.py
  :code:
  :start-line: 14
  :end-line: 15
  
This raster is mostly empty, so the following plot instead illustrates the locations of the features relative to the burn perimeter:

.. tab-set::

  .. tab-item:: Retainment Features

    .. image:: /images/preprocess/retainment-features.png
      :alt: A set of retainment-feature points adjacent to the burn perimeter.



Reprojection
------------

Next, we'll reproject all the rasters to have the same CRS, resolution, and alignment. The DEM is often a good projection template, as the DEM is foundational to a hazard assessment. The fire perimeter can also be a good template, particularly for perimeters in a local projection. Here, we'll use the DEM as our projection template:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 17
  :end-line: 20

Once the rasters are in the same projection, we'll clip them all to the same bounds as the perimeter. This will effectively set the perimeter raster as the domain of the hazard assessment.

.. include:: download/code/preprocess.py
  :code:
  :start-line: 22
  :end-line: 25

.. tab-set::

  .. tab-item:: Perimeter

    .. image:: /images/preprocess/reprojected-perimeter.png

  .. tab-item:: DEM

    .. image:: /images/preprocess/reprojected-dem.png

  .. tab-item:: dNBR

    .. image:: /images/preprocess/reprojected-dnbr.png

  .. tab-item:: EVT

    .. image:: /images/preprocess/reprojected-evt.png

  .. tab-item:: KF-factor

    .. image:: /images/preprocess/reprojected-kf-factor.png



Data Ranges
-----------
It's often useful to constrain a dataset to a valid data range, and you can do this using the :ref:`set_range <pfdf.raster.Raster.set_range>` command. We will use this for the dNBR and KF-factor datasets. Reasonable dNBR values are from about -1000 to 1000, but processing artifacts can result in dNBR values with much larger magnitudes. Here, we'll use :ref:`set_range <pfdf.raster.Raster.set_range>` to constrain the dNBR raster to values within this range. Note that values outside the range will be set to the nearest bound:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 27
  :end-line: 28

.. _constrain-kf:

We'll also constrain the KF-factor raster to positive values, as negative values are unphysical. :ref:`Inspecting the raster <kf-plot>`, we can see a region of negative values over Morrison reservoir. Essentially, the negative values have been used to denote a water body. Here, we'll use the ``fill`` option, which will replace negative pixels with NoData (rather than setting them to the bound at 0):

.. include:: download/code/preprocess.py
  :code:
  :start-line: 28
  :end-line: 29

Inspecting the rasters, we can see that their values have been constrained to the indicated ranges. For the dNBR, values have been clipped to the range from -1000 to 1000. For the KF-factors, the negative values over the water feature have been converted to NoData.

.. tab-set::

  .. tab-item:: dNBR

    .. image:: /images/preprocess/constrained-dnbr.png

  .. tab-item:: KF-factor

    .. image:: /images/preprocess/constrained-kf-factor.png


Estimate Severity
-----------------
A pfdf hazard assessment requires a `BARC4-like <https://burnseverity.cr.usgs.gov/baer/faqs>`_ burn severity raster. We recommend using an official burn severity product when possible, but sometimes these rasters are not available. If this is the case, you can use the :ref:`estimate <pfdf.severity.estimate>` command from the :doc:`severity </api/severity>` module to estimate burn severity from a dNBR raster. We'll do that here:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 31
  :end-line: 32

Inspecting the severity raster, we can see that it has classified the dNBR values into 4 groups.

.. tab-set::

  .. tab-item:: Severity

    .. image:: /images/preprocess/burn-severity.png



Terrain Masks
-------------
In a hazard assessment, it's often useful to locate different types of terrain to help constrain the assessment. For example, debris flows are unlikely to initiate in an open-water feature (such as a lake or ocean), so it's often useful to screen such features out of an assessment.

Here, we'll use the :ref:`find <pfdf.raster.Raster.find>` command to build terrain masks from an EVT (existing vegetation type) raster. EVT data often consists of integer classes, where each class indicates a different type of surface. This tutorial is derived from the `LANDFIRE EVT <https://landfire.gov/evt.php>`_ classification scheme, but you may need a different scheme for your own data. We'll start by generating an open-water mask. In the LANDFIRE classification, open water is denoted by the value 7292:

.. include:: download/code/preprocess.py
  :code:
  :start-line: 34
  :end-line: 35

We'll also create a mask for human-developed surfaces, as these areas can alter the flow and course of debris flows. LANDFIRE has several classifications for such surfaces include:

=========  ===========
Class      Description
=========  ===========
7296-7298  Low / medium / high development
7299       Roads
7300       Developed open space
=========  ===========

.. include:: download/code/preprocess.py
  :code:
  :start-line: 35
  :end-line: 37

Inspecting the rasters, we can see that this assessment has a large developed area to the south, which is part of greater Los Angeles. The assessment also contains several water bodies, including the reservoir with the negative KF-factor values.

.. tab-set::

  .. tab-item:: Development

    .. image:: /images/preprocess/development-mask.png

  .. tab-item:: Water

    .. image:: /images/preprocess/water-mask.png



Putting it all together
-----------------------

.. include:: download/code/preprocess.py
  :code:
  :start-line: 2
