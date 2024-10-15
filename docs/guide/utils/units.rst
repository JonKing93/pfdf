Distance Unit Conversions
=========================

The :ref:`utils.units module <pfdf.utils.units>` module provides information on the unit systems supported by pfdf. It also provides a function to convert values between different units::

    from pfdf.utils import units


Supported Units
---------------

You can use the ``supported`` function to return a list of unit options supported by pfdf:

.. code:: pycon

    >>> units.supported()
    ['base', 'meters', 'metres', 'kilometers', 'kilometres', 'feet', 'miles']


Convert Units
-------------

Use the ``convert`` function to convert a value from one set of units to another. For example:

.. code:: pycon

    >>> units.convert(5, from_units="meters", to_units="feet")
    array([16.40419948])

The function accepts values from any array-like collection of real-valued numbers. Converted values are always returned as an ``np.ndarray``.