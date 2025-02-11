User Guide
==========

Welcome to the pfdf user guide. This guide is intended for users who have read the :doc:`main series tutorials </tutorials/main-series>` and are ready for a more detailed discussion of pfdf. Specifically, the guide provides more in-depth discussions of pfdf components and concepts, with some practical suggestions for implementing common workflows. Although the guide is more detailed than the tutorials, it is not exhausted, and users should see the :doc:`API </api/index>` for a complete reference guide to pfdf.

----

:doc:`Arrays <arrays>`
    Tips for working with numeric inputs.

:doc:`Rasters <rasters/index>`
    A class to manage raster datasets.

:doc:`Download Data <data>`
    Routines to download commonly used datasets from the internet.

:doc:`Watershed Analyses <watershed/index>`
    Modules that analyze watershed datasets, including: 
    
    * :doc:`Soil burn-severity (SBS) <watershed/severity>`, 
    * :doc:`Digital elevation models (DEMs) <watershed/watershed>`, and 
    * :doc:`Flow directions <watershed/watershed>`.

:doc:`Segments <segments/index>`
    A class to build and manage stream segment networks.

:doc:`Models <models/index>`
    Hazard assessment models, including:
    
    * :doc:`Probability and rainfall accumulation <models/s17>`, 
    * :doc:`Potential sediment volume <models/g14>`, and 
    * :doc:`Hazard classification <models/c10>`.

:doc:`Utilities <utils/index>`
    Miscellaneous utilities to facilitate working with pfdf: 
    
    * :doc:`Rainfall intensities and accumulations <utils/intensity>`,
    * :doc:`Slope unit conversions <utils/slope>`,
    * :doc:`Distance unit conversions <utils/units>`,
    * :doc:`File format drivers <utils/driver>`, and
    * :doc:`NoData values <utils/nodata>`

.. toctree::
    :hidden:

    Working with arrays <arrays>
    Rasters <rasters/index>
    Download Data <data>
    Watershed Analyses <watershed/index>
    Segments <segments/index>
    Models <models/index>
    Misc Utilities <utils/index>
    Glossary <glossary>