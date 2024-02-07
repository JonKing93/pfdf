Burn Severities
===============

The :ref:`severity module <pfdf.severity>` provides two utilities for working with `BARC4-like burn severity <https://burnseverity.cr.usgs.gov/baer/faqs>`_ rasters. In brief, these rasters classify pixel burn severity using integers from 1 (unburned) to 4 (highly burned). You can use the :ref:`classification <pfdf.severity.classification>` function to return the scheme used/expected by this module::

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
The :ref:`mask <pfdf.severity.mask>` function is used to generate a mask from a BARC4-like burn severity raster. Given a set of burn descriptors, the function returns a boolean Raster. Pixels that match one of the burn descriptors are marked as True, all other pixels are False. For example::

    >>> from pfdf.raster import Raster
    >>> barc4 = Raster('barc4.tif')

    >>> high = severity.mask(barc4, "high")
    >>> moderate_high = severity.mask(barc4, ["high", "moderate"])
    >>> burned = severity.mask(barc4, "burned")


estimate
++++++++
We recommend using official burn severity classification products when possible. However, these rasters are not always available. When this is the case, you can use the :ref:`estimate <pfdf.severity.estimate>` command to estimate a BARC4-like burn severity from dNBR::

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

    >>> thresholds = [100, 300, 700]
    >>> barc4 = severity.estimate(dnbr, thresholds)

Note that thresholds are always inclusive for the lower class, and exclusive of the higher class.


