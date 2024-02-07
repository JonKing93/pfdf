Parallelizing Basins
====================

This tutorial demonstrates how to locate terminal outlet basins using multiple CPUs. This example uses a simplified hazard assessment for the sake of brevity, but more complex implementations are also suitable.

.. admonition:: Download

  You can download the datasets and script used in this tutorial here: :doc:`Download Files <download>`. This tutorial follows the ``parallel`` script.



Python Script
-------------
To locate basins using multiple CPUs, the assessment must be run as a Python script from the command line. It cannot be run in an interactive session. For example, the following script implements a simplified hazard assessment with parallelized basins:

.. include:: download/code/parallel.py
    :code:
    :start-line: 0

Most of this code will look familiar to readers of the :doc:`assessment tutorial <assessment>`. However, there are two critical changes: a new block on line 5, and the :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` command on line 24.

We begin with the :ref:`locate_basins <pfdf.segments.Segments.locate_basins>` command. This command locates the terminal outlet basins and saves the locations internally for later use with commands such as :ref:`save <pfdf.segments.Segments.save>`, :ref:`geojson <pfdf.segments.Segments.geojson>`, and :ref:`Segments.raster <pfdf.segments.Segments.raster>`. Filtering may delete these locations, so the command is usually run after any filtering steps. Locating basins is computationally difficult, so this command may take some time to run. In the default state, the command locates the basins sequentially, using only a single CPU. However, setting the ``parallel`` option to True allows the use of multiple CPUs. 

.. highlight:: none

The use of multiple CPUs imposes two restrictions. First, the code must be run from the command line as a Python script. For example, you could run the tutorial script using something like::
    
    $ python parallel.py
    
or

::

    $ python -m parallel

Second, the code in the script must be protected by the ``if __name__ == "__main__":`` block seen on line 5 of the example script. This is essential, because the Python interpreter re-imports the script for each activated CPU. If this block is missing, the re-imported script will reach the part of the code that activates multiple CPUs and will attempt to activate even more CPUs. These CPUs will each then re-import the script, resulting in an infinite loop that will eventually crash the terminal. By contrast, code in a ``if __name__ == "__main__":`` block isn't run when the script is re-imported, thereby preventing the infinite loop.


Performance
-----------

Runtime improvements will scale with the number of CPUs and the size of the watershed, so large watersheds will benefit more strongly from parallelization than small watersheds. For very small watersheds, the time spent activating CPUs may exceed the performance boost from parallelization, causing the code to actually run *slower*. Keep this in mind when deciding whether or not to parallelize.

.. admonition:: Rule of Thumb
    
    Parallelization is often appropriate if it takes several minutes (or longer) to locate the basins.
