pfdf
====

.. highlight:: none

The pfdf package is a Python library designed to facilitate postfire debris-flow hazard assessments and research. The library provides routines to:

* Download assessment datasets
* Analyze watersheds
* Delineate stream segment networks
* Compute stream segment characteristics
* Run the debris-flow likelihood models of `Staley and others, 2017 <https://doi.org/10.1016/j.geomorph.2016.10.019>`_
* Run the potential sediment volume models of `Gartner and others, 2014 <https://doi.org/10.1016/j.enggeo.2014.04.008>`_
* Classify hazards following `Cannon and others, 2010 <https://doi.org/10.1130/B26459.1>`_, and
* Export results to common GIS formats (such as Shapefiles and GeoJSON)

All routines are optional, and may be configured for a variety of analyses and assessment styles. We note that some coding experience is required to use the routines in this package. As such, pfdf is primarily intended for researchers and developers of hazard assessment tools.

.. tip::

    If you just want to run a hazard assessment, then you may want the `wildcat package <https://ghsc.code-pages.usgs.gov/lhp/wildcat/>`_ instead of pfdf. The pfdf library is intended for users who want to build and modify assessment frameworks, whereas wildcat is intended to quickly produce assessments.


Using these docs
----------------
These docs contain a variety of resources for pfdf users. We recommend most users begin with the :doc:`Tutorials </tutorials/index>`. The tutorials are a collection of `Jupyter notebooks <https://docs.jupyter.org/en/latest/>`_ designed to introduce users to pfdf. The :doc:`main series </tutorials/main-series>` introduces the components needed to run hazard assessments, and there are :doc:`advanced tutorials </tutorials/advanced>` on more specialized topics.

The tutorials are only intended as an introduction, so do not discuss every component of pfdf. After completing the tutorials, users may find the :doc:`User Guide </guide/index>` a useful resource. The guide discusses every module and class in pfdf, with more detailed discussions of the components introduced in the tutorials. Finally, the :doc:`API </api/index>` is the complete reference guide to pfdf, and describes every command and option in full detail.

This documentation also provides various resources for the pfdf community. These include links to :doc:`commonly used datasets <resources/datasets>`, :doc:`contribution guidelines <resources/contributing>` (including a :doc:`developer guide <resources/dev-guide>`), :doc:`legal documents <resources/legal>`, :doc:`release notes <resources/release-notes/index>`, and the `latest release`_. You can find links to these resources in the navigation sidebar.

.. _latest release: https://code.usgs.gov/ghsc/lhp/pfdf/-/releases/permalink/latest

Citation
--------
If you use pfdf for a publication, please consider citing it. Please see the :doc:`Citation Page </resources/citation>` for more details.


.. toctree::
    :hidden:
    :caption: Documentation

    Introduction <self>
    Installation <resources/installation>
    Tutorials <tutorials/index>
    User Guide <guide/index>
    API <api/index>

.. toctree::
    :hidden:
    :caption: Resources
    
    FAQs / Troubleshooting <resources/faqs>
    Datasets <resources/datasets>
    Citation <resources/citation>
    Contributing <resources/contributing>
    Legal <resources/legal>

.. toctree::
    :hidden:
    :caption: Releases

    Latest Release <https://code.usgs.gov/ghsc/lhp/pfdf/-/releases/permalink/latest>
    Release Notes <resources/release-notes/index>
