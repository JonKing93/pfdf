data package
============

.. _pfdf.data:

.. py:module:: pfdf.data

Modules for loading commonly used datasets from the internet.

.. list-table::
    :header-rows: 1

    * - Module
      - Description
    * - :ref:`landfire <pfdf.data.landfire>`
      - Modules to load `LANDFIRE`_ datasets, including EVTs
    * - :ref:`noaa <pfdf.data.noaa>`
      - Modules to load `NOAA`_ datasets, including precipitation frequencies from `NOAA Atlas 14`_
    * - :ref:`retainments <pfdf.data.retainments>`
      - Modules to load locations of debris retainment features
    * - :ref:`usgs <pfdf.data.usgs>`
      - Modules to load `USGS`_ datasets, including DEMs, HUs, and STATSGO soil data

.. _LANDFIRE: https://www.landfire.gov/
.. _NOAA: https://www.noaa.gov
.. _NOAA Atlas 14: https://hdsc.nws.noaa.gov/pfds/
.. _USGS: https://www.usgs.gov

.. admonition:: Backwards Compatibility

    The modules in this package rely on various third-party APIs, and it is possible that these APIs may change in ways that necessitate updating pfdf. Since these APIs are outside of the control of the pfdf project, updates to pfdf that address API changes will not be considered backwards-incompatible updates, even if the updates alter pfdf function signatures or behavior.

----

.. toctree::

    landfire package <landfire/index>
    noaa package <noaa/index>
    retainments package <retainments/index>
    usgs package <usgs/index>
    