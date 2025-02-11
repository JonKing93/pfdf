severity module
===============

.. _pfdf.severity:

.. py:module:: pfdf.severity

    Functions that estimate and locate burn severity

    .. list-table::
        :header-rows: 1

        * - Function
          - Description
        * - :ref:`classification <pfdf.severity.classification>`
          - Returns a dict with the BARC4 classification scheme
        * - :ref:`mask <pfdf.severity.mask>`
          - Returns a mask of the specified burn severities
        * - :ref:`estimate <pfdf.severity.estimate>`
          - Estimates a BARC4-like burn severity raster


    The severity module is used to generate and work with rasters that record `BARC4-like <https://burnseverity.cr.usgs.gov/baer/faqs>`_ burn severity. The BARC4 classification is as follows:

    =====  ===========
    Class  Description
    =====  ===========
    1      Unburned
    2      Low burn severity
    3      Moderate burn severity
    4      High burn severity
    =====  ===========

    This module has two main functions: :ref:`mask <pfdf.severity.mask>` and :ref:`estimate <pfdf.severity.estimate>`.

    Burn severity rasters are typically used to derive data masks used to
    implement various parts of a hazard assessment. For example, a burned pixel mask used to delineate a stream network, or the high-moderate burn mask used to implement the M1, M2, and M3 models in the :ref:`staley2017 module <pfdf.models.staley2017>`. Use the :ref:`mask <pfdf.severity.mask>` function to generate these masks from a BARC4-like burn severity raster. Note that :ref:`mask <pfdf.severity.mask>` searches for burn-severity levels by name, and you can return the supported names using the :ref:`classification <pfdf.severity.classification>` function. 

    We recommend using field-verified BARC4-like burn severity data when possible, but these maps are not always available. If this is the case, users can use the :ref:`estimate <pfdf.severity.estimate>` function to estimate a BARC4-like burn severity raster from dNBR, BARC256, or other burn severity measure.

----


.. _pfdf.severity.classification:

.. py:function:: classification()
    :module: pfdf.severity

    Returns the BARC4 burn severity classification scheme

    ::

        classification()

    Returns a dict reporting the BARC4 burn severity classification scheme used by the module. Keys are the strings "unburned", "low", "moderate", "high", and "burned". Values are the integers associated with each burn severity level.

    :Outputs: *dict* -- Maps burn severity levels to their integers in the classification scheme
 


.. _pfdf.severity.mask:

.. py:function:: mask(severity, descriptions)
    :module: pfdf.severity

    Generates a burn severity mask
    
    ::

        mask(severity, descriptions)

    Given a burn severity raster, locates pixels that match any of the specified burn severity levels. Returns a *Raster* holding the mask of matching pixels. Pixels that match one of the specified burn severities will have a value of 1. All other pixels will be 0.

    Note that the burn severity descriptions are strings describing the appropriate burn severity levels. The supported strings are: "unburned", "burned", "low", "moderate", and "high".

    :Inputs: * **severity** (*Raster-like*) --  A BARC4-like burn severity raster.
             * **descriptions** (*str | list[str]*): A list of strings indicating the burn severity levels that should be set as True in the returned mask

    :Outputs: *Raster* -- The burn severity mask



.. _pfdf.severity.estimate:
    
.. py:function:: estimate(raster, thresholds = [125, 250, 500])
    :module: pfdf.severity

    Estimates a BARC4-like burn severity raster

    .. dropdown:: Estimate severity
        
        ::
            
            estimate(raster)

        Estimates a BARC4 burn severity from a raster assumed to be (raw dNBR * 1000). (See the following syntax if you instead have raw dNBR, BARC256, or another burn-severity measure). This process classifies the burn severity of each raster pixel using an integer from 1 to 4. The classification scheme is as follows:
        
        =====  =========== ===========
        Class  dNBR Range  Level
        =====  =========== ===========
        1      [-∞, 125]   Unburned
        2      (125, 250]  Low
        3      (250, 500]  Moderate
        4      (500, ∞]    High
        =====  =========== ===========

        NoData values are set to 0. Returns a *Raster* object holding the estimated BARC4 burn severity raster.

    .. dropdown:: Custom thresholds
        
        ::
            
            estimate(raster, thresholds)

        Specifies the thresholds to use to distinguish between burn severity classes in the input raster. This syntax should be used whenever the input raster is not (raw dNBR * 1000), and also supports custom thresholds for the (raw dNBR * 1000) case. Note that the function does not check the intervals of raster values when thresholds are specified.

        The "thresholds" input should have 3 elements. In order, these should
        be the thresholds between:
        
        (1) unburned and low severity, 
        (2) low and moderate severity, and 
        (3) moderate and high severity. 
        
        Each threshold defines the upper bound (inclusive) of the less-burned class, and the lower bound (exclusive) of the  more-burned class. The thresholds must be in increasing order.

    :Inputs: * **raster** (*Raster-like*) -- A raster holding the data used to classify burn severity
             * **thresholds** (*vector*) -- The 3 thresholds to use to distinguish between burn severity classes

    :Outputs: *Raster* -- The BARC4 burn severity estimate

