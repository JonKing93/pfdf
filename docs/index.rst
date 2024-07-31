pfdf
====

.. highlight:: none

The pfdf package is a Python library designed to facilitate postfire debris-flow hazard assessments and research. The library provides routines to:

* Analyze watersheds
* Delineate stream segment networks
* Compute earth-system variables for stream segments
* Assess debris-flow probabilities using the models of `Staley and others, 2017 <https://doi.org/10.1016/j.geomorph.2016.10.019>`_
* Assess potential sediment volumes using the models of `Gartner and others, 2014 <https://doi.org/10.1016/j.enggeo.2014.04.008>`_
* Classify relative hazards using the methods of `Cannon and others, 2010 <https://doi.org/10.1130/B26459.1>`_, and
* Export results to common GIS formats (such as Shapefiles and GeoJSON)

All routines are optional, and may be configured for a variety of analyses and assessment styles. We note that some coding experience is required to use the routines in this package. As such, pfdf is primarily intended for researchers and developers of hazard assessment tools.

.. tip::

    If you just want to run a hazard assessment (rather than writing code), we recommend seeing the `wildcat assessment tool <https://code.usgs.gov/ghsc/lhp/wildcat>`_ instead.


Installation
------------

.. admonition:: Prerequisites

    pfdf requires Python 3.11+

You can install the latest release using:

.. parsed-literal::

    pip install git+https://code.usgs.gov/ghsc/lhp/pfdf@\ |release|\

See also the :doc:`installation page <resources/installation>` for additional options, or the :ref:`developer instructions <dev-install>` if you plan on developing pfdf.


Using these docs
----------------
These docs contain a variety of resources for pfdf users. The :doc:`User Guide </guide/index>` provides an overview of pfdf's components, introduces key functionality, and provides suggestions for common workflows. The :doc:`Tutorials </tutorials/index>` provide in-depth examples of specific use cases, and the :doc:`API </api/index>` provides complete documentation of every command in pfdf. You can also find links to the `latest release`_, :doc:`contribution guidelines <resources/contributing>` (including a :doc:`developer guide <resources/dev-guide>`), and :doc:`legal documents <resources/legal>` in the navigation sidebar.


Citation
--------
If you use pfdf for a publication, please consider citing it::

    King, J., 2023, pfdf - Python library for postfire debris-flow hazard assessments 
    and research, version 1.1.0: U.S. Geological Survey software release, 
    https://doi.org/10.5066/P13RSBEE


BibTeX::

    @misc{king_2023,
        title = {pfdf - Python library for postfire debris-flow hazard assessments and research, version 1.1.0},
        author = {King, Jonathan},
        url = {https://code.usgs.gov/ghsc/lhp},
        year = {2023},
        doi = {10.5066/P13RSBEE}
    }




.. toctree::
    :hidden:
    :caption: Docs

    Installation <resources/installation>
    User Guide <guide/index>
    Tutorials <tutorials/index>
    API <api/index>

.. toctree::
    :hidden:
    :caption: Resources
    
    Contributing <resources/contributing>
    Legal <resources/legal>
    Release Notes <resources/release-notes/index>
    Latest Release <https://code.usgs.gov/ghsc/lhp/pfdf/-/releases/permalink/latest>


.. _latest release: https://code.usgs.gov/ghsc/lhp/pfdf/-/releases/permalink/latest
