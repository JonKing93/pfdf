Tutorial Setup
==============

.. highlight:: none

When possible, we recommend running the tutorials as Jupyter notebooks, as this will allow you to interact with pfdf code directly. This page describes the setup steps needed to run the tutorials.

.. note::

    You **are not** required to run the notebooks to use the tutorials. If you are having trouble running the notebooks, you can instead read through :doc:`pre-run notebooks <main-series>` provided in these docs.


Download Workspace
------------------
First, download the tutorial workspace. You can do so here: :download:`Download Tutorial Workspace <tutorials.zip>` or on the previous page of these docs. The download is a zip archive holding the tutorial notebooks, and various other resources. You will need to extract the archive to run the tutorials.

In addition to the tutorial Jupyter notebooks, the workspace will include the following contents:

* ``data``: Small datasets used to run the hazard assessment tutorial
* ``tools``: Utility modules used to run the tutorials. You **do not** need to understand these modules to use the tutorials or pfdf.
* ``check_installation``: Utility script that checks the Jupyter kernel is set up correctly for the tutorials.

Running the tutorials will also add the following folders to the workspace:

* ``examples``: Small example datasets used for illustrative purposes
* ``preprocessed``: Preprocessed datasets produced by the preprocessing tutorials
* ``exports``: Saved assessment results from the hazard assessment tutorial.


Installation
------------
To run the tutorials, you must install pfdf with the additional tutorial dependencies. You can find detailed instructions in the :ref:`Installation Guide <tutorial-install>`, but in brief, the steps are:

1. `Create and activate <install-environment>`_ a clean virtual environment,
2. Install `Python 3.11 or 3.12 <https://www.python.org/downloads/>`_, and then
3. Install :ref:`pfdf with tutorial dependencies <tutorial-install>` using::

    pip install pfdf[tutorials] -i https://code.usgs.gov/api/v4/groups/859/-/packages/pypi/simple


Running the Notebooks
---------------------
Installing pfdf with the tutorial dependencies will include Jupyter Lab with your installation, and you can use this to run the notebooks. After activating the pfdf+tutorials virtual environment, you can open the tutorials using::
    
    jupyter lab --notebook-dir path/to/extracted/tutorials

This will open the tutorial workspace in Jupyter Lab. You can open a tutorial notebook by selecting it in the file browser sidebar. We recommend starting with ``01_Start_Here.ipynb``.

.. important::

    Make sure the Jupyter kernel is set to the environment where you installed pfdf with the tutorial dependencies.

.. tip::

    If you're not familiar with Jupyter notebooks, you can learn more here: `JupyterLab Docs <https://jupyterlab.readthedocs.io/en/stable/>`_

