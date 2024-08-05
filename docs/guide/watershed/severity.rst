Burn Severities
===============

The :ref:`severity module <pfdf.severity>` provides two utilities for working with 4-class burned area reflectance rasters. These datasets are typically referred as `BARC4 burn severities <https://burnseverity.cr.usgs.gov/baer/faqs>`_. In brief, these rasters classify each pixel's burn severity using an integer from 1 (unburned) to 4 (highly burned). You can use the :ref:`classification <pfdf.severity.classification>` function to return the scheme used/expected by this module::

    # Import the severity module and examine the classification scheme
    >>> from pfdf import severity
    >>> severity.classification()
    {
      'unburned': 1, 
      'low': 2, 
      'moderate': 3, 
      'high': 4, 
      'burned': [2, 3, 4]
    }


mask
++++
The :ref:`mask <pfdf.severity.mask>` function is used to generate a mask from a BARC4-like burn severity raster. Given a set of burn descriptors, the function returns a boolean *Raster* object. Pixels that match one of the burn descriptors are marked as True, all other pixels are False. For example::

    # Load a BARC4-like raster
    >>> from pfdf.raster import Raster
    >>> barc4 = Raster('barc4.tif')

    # Locate pixels with various burn severity levels
    >>> high = severity.mask(barc4, "high")
    >>> moderate_high = severity.mask(barc4, ["high", "moderate"])
    >>> burned = severity.mask(barc4, "burned")


estimate
++++++++
We recommend using official burn severity classification products when possible. However, these rasters are not always available. When this is the case, you can use the :ref:`estimate <pfdf.severity.estimate>` command to estimate a BARC4-like burn severity from dNBR::

    # Estimate severity from dNBR
    >>> dnbr = Raster('dnbr.tif')
    >>> barc4 = severity.estimate(dnbr)

By default, the function uses the following dNBR thresholds to classify severity:

.. list-table::

    * - **Class**
      - **dNBR Range**
    * - unburned: 1
      - [-Inf, 125]
    * - low: 2
      - (125, 250]
    * - moderate: 3
      - (250, 500]
    * - high: 4
      - (500, Inf]

However, you can use the ``thresholds`` option to select different thresholds::

    # Use custom thresholds to estimate severity from dNBR
    >>> thresholds = [100, 300, 700]
    >>> barc4 = severity.estimate(dnbr, thresholds)

Note that thresholds are always inclusive for the lower class, and exclusive of the higher class.


