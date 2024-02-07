Download Tutorial Resources
===========================

You can use the following link to download the datasets and scripts for the tutorials: MISSING


Contents
--------
The downloaded archive contains two folders: ``data`` and ``code``. The ``data`` folder holds the GIS datasets used to implement the tutorials. You can find a summary of these dataset files here: :ref:`Tutorial Datasets <tutorial-datasets>`. The ``code`` folder holds the scripts used to implement the tutorials, as follows:

=================  =========
Tutorial           Script(s)
=================  =========
Rasters            ``rasters.py``
Preprocessing      ``preprocess.py``
Hazard Assessment  ``assessment.py`` and ``export.py``
Parallel Basins    ``parallel.py``
Parameter Sweep    ``sweep.py``
=================  =========

The ``code`` folder also contains several files used to reproduce tutorial figures:

=======================  ===========
File                     Description
=======================  ===========
``preprocess_plots.py``  Reproduces the figures for the preprocessing tutorial
``assessment_plots.py``  Reproduces the figures for the hazard assessment tutorial
``plot.py``              Holds the plotting code
=======================  ===========


Running Tutorial Scripts
------------------------

.. highlight:: none

All tutorial scripts are intended to be run from the ``data`` folder. For example, using something like::

    $ cd path/to/download/data
    $ python ../code/preprocess.py

.. important:: 

    You should :ref:`install pfdf with the tutorial extras <tutorial-install>` if you plan to reproduce the tutorial plots.
