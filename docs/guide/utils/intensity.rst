Rainfall Intensities
====================

The :doc:`staley2017 (s17) module </guide/models/s17>` module works strictly with rainfall accumulations (mm of accumulation over a duration). However, many users find it useful to work with rainfall intensities (mm/hour) instead, and the :doc:`gartner2014 (g14) module </guide/models/g14>` additionally expects rainfall intensities as input. As such, :ref:`utils.intensity module <pfdf.utils.intensity>` provides functions to convert between these two formats.


To Accumulation
---------------

The :ref:`to_accumulation command <pfdf.utils.intensity.to_accumulation>` converts input rainfall intensities to accumulations, given a rainfall duration (in minutes):

.. code:: pycon

    >>> from pfdf.utils import intensity
    >>> I = [16, 20, 24, 40]  # Rainfall intensity in mm/hour
    >>> R = intensity.to_accumulation(I, duration=15)
    >>> print(R) # mm accumulated over a 15 minute interval
    array([ 4.,  5.,  6., 10.])

You can alternatively provide a specific duration for each input intensity:

.. code:: pycon

    >>> I = [16, 20, 24, 40]
    >>> durations = [15, 30, 60, 60]  # in minutes
    >>> R = intensity.to_accumulation(I, durations)
    >>> print(R) # mm accumulated over the relevant interval
    array([ 4., 10., 24., 40.])


From Accumulation
-----------------

The :ref:`from_accumulation command <pfdf.utils.intensity.from_accumulation>` converts from rainfall accumulations to intensities, again given the relevant durations (in minutes). By default, this command is intended for output from the :ref:`s17.accumulation command <pfdf.models.staley2017.accumulation>`, so the input durations are broadcast along the final dimension of the input accumulations array:

.. code:: pycon

    >>> from pfdf.utils import intensity
    >>> import numpy as np

    >>> # Mimic s17 output, 5 segments x 3 durations
    >>> R = np.array([
        [10, 21, 43],
        [5, 11, 22],
        [11, 22, 45], 
        [1, 3, 7],
        [7, 14, 29],
    ])

    >>> # Durations (in minutes) are broadcast over the columns
    >>> durations = [15, 30, 60]
    >>> I = intensity.from_accumulation(R, durations)
    >>> print(I) # mm/hour
    array([[40., 42., 43.],
           [20., 22., 22.],
           [44., 44., 45.],
           [ 4.,  6.,  7.],
           [28., 28., 29.]])

Alternatively, you can use the ``dim`` option to specify the index of the dimension over which to broadcast durations. For example:

    >>> R = np.array([
        [1, 2],
        [2, 4],
        [4, 8], 
    ])
    >>> durations = [15, 30, 60]
    >>> I = intensity.from_accumulation(R, durations, dim=0),
    >>> print(I)
    array([[4., 8.],
           [4., 8.],
           [4., 8.]]),