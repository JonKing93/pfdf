Installation
============

.. note:: These instructions are for pfdf users. If you plan to develop pfdf, you should do a :ref:`developer installation <dev-install>` instead.

.. admonition:: Prerequisites

    pfdf requires Python 3.11+

Easy Install
------------

This will install the latest release:

.. parsed-literal::
    :class: highlight

    pip install git+https://code.usgs.gov/ghsc/lhp/pfdf@\ |release|\


.. _tutorial-install:

Tutorials
---------
If you want to recreate the plots shown in the :doc:`tutorials </tutorials/index>`, use:

.. parsed-literal::
    :class: highlight

    pip install git+https://code.usgs.gov/ghsc/lhp/pfdf@\ |release|\[tutorials]

This will include `cartopy <https://scitools.org.uk/cartopy/docs/latest/>`_ and `matplotlib <https://matplotlib.org/>`_ with your installation.




Advanced Installation
---------------------

.. highlight:: none

You can install a generic release using::

    pip install git+https://code.usgs.gov/ghsc/lhp/pfdf@X.Y.Z

where ``X.Y.Z`` is the release tag.

You can also install the most recent devlopment from the main branch using::

    pip install git+https://code.usgs.gov/ghsc/lhp/pfdf@main

However, be warned that active development is not stable, so may change at any time without warning.