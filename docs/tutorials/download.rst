Download Tutorial Resources
===========================

The Python script(s) for each tutorial can be downloaded at the top of each tutorial's page. Use the following link to download the datasets:  `Download Datasets <https://code.usgs.gov/ghsc/lhp/pfdf/-/raw/tutorial-data/tutorial-resources.zip?ref_type=heads&inline=false>`_

.. note::

    You will need to unzip the downloaded archive before running the tutorials.


Contents
--------
The downloaded archive contains a variety of GeoTiff and GeoJSON datasets used throughout the tutorials. You can find a summary of most of these datasets here: :ref:`Tutorial Datasets <tutorial-datasets>`. The archive also includes the ``mask.tif`` file, which provides an example of a boolean-like dataset for the Raster tutorial.


Running Tutorial Scripts
------------------------

.. highlight:: none

All tutorial scripts are intended to be run from downloaded (and unzipped) data folder. For example, if you want to run the preprocessing tutorial, you could place the ``preprocess.py`` script in an adjacent ``code`` folder, and then run the tutorial using something like::

    $ cd path/to/data
    $ python ../code/preprocess.py

.. important:: 

    You should :ref:`install pfdf with the tutorial extras <tutorial-install>` if you plan to reproduce the tutorial plots.
