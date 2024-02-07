Parameter Sweep
===============

This tutorial demonstrates how to run the :doc:`M1 probability model </guide/models/s17>` using multiple values of the model's parameters. This type of analysis can be useful for calibrating model parameters. We recommend reading the :doc:`hazard assessment tutorial <assessment>` before this.

.. admonition:: Download

  You can download the datasets and script used in this tutorial here: :doc:`Download Files <download>`. This tutorial follows the ``sweep`` script.


Getting Started
---------------
We'll start by importing `numpy <https://numpy.org/>`_, the :doc:`staley2017 module </guide/models/s17>`, and the script used to run the :doc:`hazard assessment tutorial <assessment>`:

.. include:: download/code/sweep.py
    :code:
    :start-line: 2
    :end-line: 5

We'll then load the stream segment network and the M1 variables from the hazard assessment:

.. include:: download/code/sweep.py
    :code:
    :start-line: 7
    :end-line: 11

Finally, we'll define the rainfall parameters we'll use to run the model. Here, we'll run the model for 6 mm of rainfall over a 15 minute duration:

.. include:: download/code/sweep.py
    :code:
    :start-line: 13
    :end-line: 15



One parameter
-------------
Let's say that we'd like to calibrate the model's ``Ct`` parameter. One approach could be to run the model using multiple values of ``Ct``. If we have a database of known-debris flow events, we could compare the database to the model results to try and determine an optimal ``Ct`` value.

Here we will demonstrate how to run the model using multiple ``Ct`` values. (Comparing results to a database is beyond the scope of this tutorial). We'll start by getting the standard M1 parameters for the ``B``, ``Cf``, and ``Cs`` variables: 

.. include:: download/code/sweep.py
    :code:
    :start-line: 17
    :end-line: 18

Next, we'll sample every ``Ct`` value from 0.01 to 1 in steps of 0.01:

.. include:: download/code/sweep.py
    :code:
    :start-line: 18
    :end-line: 19

Finally, we'll run the probability model:

.. include:: download/code/sweep.py
    :code:
    :start-line: 19
    :end-line: 20

The output probabilities will be a matrix with one row per stream segment. Each column holds the probabilities for one of the 100 tested ``Ct`` values::

    >>> p1.shape
    (470, 100)
    >>> p1.shape == (segments.length, Ct.size)
    True



Multiple Parameters
-------------------
We could instead choose to test multiple values of multiple parameters simultaneously. When this is the case, the parameters with multiple values should be vectors with the same numbers of elements. Each iterative set of parameters values will then be used for a model run.

For this example, let's say we've decided to sample the ``Ct`` and ``Cf`` parameters simultaneously. We'll generate 1000 random values of ``Ct`` with a mean of 0.4 and standard deviation of 0.25. We'll also generate 1000 values of ``Cf`` with a mean of 0.67 and standard deviation of 0.3:

.. include:: download/code/sweep.py
    :code:
    :start-line: 22
    :end-line: 24

We can then run the model as normal:

.. include:: download/code/sweep.py
    :code:
    :start-line: 24
    :end-line: 25

Once again, the output probabilities will be a matrix with one row per segment. Each column holds the probabilities for one of the 1000 tested (``Ct``, ``Cf``) pairs. For example, column 0 holds the values for (``Ct[0]``, ``Cf[0]``), column 1 holds the values for (``Ct[1]``, ``Cf[1]``), etc:

    >>> p2.shape
    (470, 1000)
    >>> p1.shape == (segments.length, Cf.size)
    True


.. note::

    This tutorial uses random sampling for the sake of brevity, but this method can result in undersampled regions of a parameter space. When testing multiple parameters, we recommend sampling methods like a `Latin hypercube <https://en.wikipedia.org/wiki/Latin_hypercube_sampling>`_ instead.


Putting it all together
-----------------------

.. include:: download/code/sweep.py
    :code:
    :start-line: 2
    :end-line: 25