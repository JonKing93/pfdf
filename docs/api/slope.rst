pfdf.utils.slope module
=======================

.. _pfdf.utils.slope:

.. py:module:: pfdf.utils.slope

    Functions that convert slopes to different metrics

    ===================================================  ===========
    Function                                             Description
    ===================================================  ===========
    ..
    **To metric from gradient**
    ----------------------------------------------------------------
    :ref:`to_percent <pfdf.utils.slope.to_percent>`      Converts gradient to slope percent
    :ref:`to_radians <pfdf.utils.slope.to_radians>`      Converts gradient to slope angle in radians
    :ref:`to_degrees <pfdf.utils.slope.to_degrees>`      Converts gradient to slope angle in degrees
    :ref:`to_sine <pfdf.utils.slope.to_sine>`            Converts gradient to sin(θ)
    ..
    **From metric to gradient**
    ----------------------------------------------------------------
    :ref:`from_percent <pfdf.utils.slope.from_percent>`  Converts slope percent to gradient
    :ref:`from_radians <pfdf.utils.slope.from_radians>`  Converts slope angle in radians to gradient
    :ref:`from_degrees <pfdf.utils.slope.from_degrees>`  Converts slope angle in degrees to gradient
    :ref:`from_sine <pfdf.utils.slope.from_sine>`        Convert sin(θ) to gradient
    ===================================================  ===========


    This module contains functions that convert between slope gradients (rise/run), and other common slope metrics: 
    
    * slope percent (slope * 100), 
    * slope angle (θ) in radians or degrees, and
    * sin(θ)

    Each slope metric has "to" and "from" methods which convert to the measure from a slope gradient, or from the measure to a slope gradient, respectively. All functions are designed to work on numpy arrays.

To Metric
---------

.. _pfdf.utils.slope.to_percent:

.. py:function:: to_percent(slope)
    :module: pfdf.utils.slope

    Converts slope gradient (rise/run) to slope percent (slope * 100)

    :Inputs: * **slope** (*ndarray*) -- Array of slope gradients
    :Outputs: *ndarray* -- Array of slope percents



.. _pfdf.utils.slope.to_radians:

.. py:function:: to_radians(slope)
    :module: pfdf.utils.slope

    Converts slope gradient (rise/run) to slope angle (θ) in radians

    :Inputs: * **slope** (*ndarray*) -- Array of slope gradients
    :Outputs: *ndarray* -- Array of slope angles in radians



.. _pfdf.utils.slope.to_degrees:

.. py:function:: to_degrees(slope)
    :module: pfdf.utils.slope

    Converts slope gradient (rise/run) to slope angle (θ) in degrees

    :Inputs: * **slope** (*ndarray*) -- Array of slope gradients
    :Outputs: *ndarray* -- Array of slope angles in degrees



.. _pfdf.utils.slope.to_sine:

.. py:function:: to_sine(slope)
    :module: pfdf.utils.slope

    Converts slope gradient (rise/run) to the sine of the slope angle, sin(θ)

    :Inputs: * **slope** (*ndarray*) -- Array of slope gradients
    :Outputs: *ndarray* -- Array of sin(θ) values


From Metric
-----------

.. _pfdf.utils.slope.from_percent:

.. py:function:: from_percent(slope)
    :module: pfdf.utils.slope

    Converts slope percent (slope * 100) to slope gradient (rise/run)

    :Inputs: * **slope** (*ndarray*) -- Array of slope percents
    :Outputs: *ndarray* -- Array of slope gradients



.. _pfdf.utils.slope.from_radians:

.. py:function:: from_radians(slope)
    :module: pfdf.utils.slope

    Converts slope angle (θ) in radians to slope gradient (rise/run)

    :Inputs: * **slope** (*ndarray*) -- Array of slope angles in radians
    :Outputs: *ndarray* -- Array of slope gradients



.. _pfdf.utils.slope.from_degrees:

.. py:function:: from_degrees(slope)
    :module: pfdf.utils.slope

    Converts slope angle (θ) in degrees to slope gradient (rise/run)

    :Inputs: * **slope** (*ndarray*) -- Array of slope angles in degrees
    :Outputs: *ndarray* -- Array of slope gradients



.. _pfdf.utils.slope.from_sine:

.. py:function:: from_sine(slope)
    :module: pfdf.utils.slope

    Converts the sine of the slope angle, sin(θ), to slope gradient (rise/run)

    :Inputs: * **slope** (*ndarray*) -- Array of sin(θ) values
    :Outputs: *ndarray* -- Array of slope gradients

