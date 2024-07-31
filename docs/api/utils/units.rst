pfdf.utils.units module
=======================

.. _pfdf.utils.units:

.. py:module:: pfdf.utils.units

    Functions to convert distances between different units

    .. list-table::
        :header-rows: 1

        * - Function
          - Description
        * - :ref:`supported <pfdf.utils.units.supported>`
          - Returns a list of units supported by pfdf
        * - :ref:`convert <pfdf.utils.units.convert>`
          - Converts distances from one unit to another
        * - :ref:`units_per_meter <pfdf.utils.units.units_per_meter>`
          - Returns the conversion factors from supported units to meters

Functions
---------

.. _pfdf.utils.units.supported:

.. py:function:: supported()
    :module: pfdf.utils.units

    Returns a list of unit options supported by pfdf

    ::

        supported()

    Returns a list of supported unit options.

    :Outputs:
        *list* -- The unit options supported by pfdf


.. _pfdf.utils.units.convert:

.. py:function:: convert(distance, from_units, to_units)
    :module: pfdf.utils.units

    Converts distances from one unit to another

    ::

        convert(distance, from_units, to_units)

    Converts the input distances from one unit to another. Distances  may be a scalar or array-like dataset. Always returns converted distances as a numpy array. Note that you cannot convert between "base" units, as these units are ambiguous and depend on the selection of CRS.

    :Inputs:
        * **distance** (*int | float | np.ndarray*) -- The distances that should be converted
        * **from_units** (*str*) -- The current units of distances
        * **to_units** (*str*) -- The units that the distances should be converted to

    :Outputs:
        *np.ndarray* -- The converted distances


.. _pfdf.utils.units.units_per_meter:

.. py:function:: units_per_meter()
    :module: pfdf.utils.units

    Returns conversion factors between supported units and meters

    ::

        units_per_meter()

    Returns a dict whose keys are the (string) names of unit options supported by pfdf. Values are the multiplicative conversion factors used to convert from meters to the associated unit. Note that the "base" unit refers to the base units of a CRS. The base conversion factor is nan because these units are variable and depend on the selection of CRS.

    :Outputs:
        *dict* -- Multiplicative conversion factors from meters to each unit
        