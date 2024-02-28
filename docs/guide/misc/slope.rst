Slope Conversions
=================

There are a number of different metrics used to represent topographic slopes, including:

.. list-table::
  :header-rows: 1

  * - Metric
    - Description
  * - Gradient
    - Rise / Run
  * - Slope percent
    - Gradient * 100
  * - Angle
    - Degrees or radians
  * - sin(θ)
    - Sine of the slope angle

The pfdf library works exclusively in slope gradients, and so the :ref:`utils.slope module <pfdf.utils.slope>` provides functions that convert between slope gradients and other metrics::

    >>> from pfdf.utils import slope

Specifically, the module provides functions to convert from slope gradients to the following metrics:

.. list-table::
    
    * - **Name**
      - **Description**
    * - percent
      - slope percent
    * - radians
      - angle in radians
    * - degrees
      - angle in degrees
    * - sine
      - Sine of the slope angle

      
Each metric has a ``from_<name>`` and a ``to_<name>`` method. The "from" method converts from that metric to slope gradient, and the "to" method converts from slope gradient to that metric. All functions are configured to operate on numpy arrays. For example::

    # Convert from degrees to gradient
    >>> import numpy as np
    >>> degrees = np.array([10, 20, 30, 40, 50])
    >>> gradient = slope.from_degrees(degrees)
    >>> print(gradient)
    [0.17632698 0.36397023 0.57735027 0.83909963 1.19175359]

    # Convert back to degrees
    >>> slope.to_degrees(gradient)
    array([10., 20., 30., 40., 50.])

Another example (using slope percents)::

    # Convert from gradient to slope percent
    >>> gradient = np.arange(1,10)
    >>> percent = slope.to_percent(gradient)
    >>> print(percent)
    [100 200 300 400 500 600 700 800 900]

    # Convert back to gradient
    >>> slope.from_percent(percent)
    array([1., 2., 3., 4., 5., 6., 7., 8., 9.])

Note that you can convert between non-gradient metrics by chaining a "from" and a "to" command::

    # Converting from degrees to slope percent
    >>> degrees = np.array([10, 20, 30])
    >>> gradient = slope.from_degrees(degrees)
    >>> percent = slope.to_percent(gradient)
    >>> print(percent)
    [17.63269807 36.39702343 57.73502692]