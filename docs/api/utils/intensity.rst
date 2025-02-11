utils.intensity module
======================

.. _pfdf.utils.intensity:

.. py:module:: pfdf.utils.intensity

    Functions to convert between rainfall accumulations (mm of accumulation over a duration) and rainfall intensities (mm per hour).

    .. list-table::
        :header-rows: 1

        * - Function
          - Description
        * - :ref:`to_accumulation <pfdf.utils.intensity.to_accumulation>`
          - Converts rainfall intensities to accumulations
        * - :ref:`from_accumulation <pfdf.utils.intensity.from_accumulation>`
          - Converts rainfall accumulations to intensities



.. _pfdf.utils.intensity.to_accumulation:

.. py:function:: to_accumulation(I, durations)

    Converts rainfall intensities to accumulations

    ::

        to_accumulation(I, durations)

    Converts the input rainfall intensities (in mm/hour) to rainfall accumulations (mm accumulated over a duration). The input intensities should be a vector in mm/hour. The input durations should be in minutes. The durations may either be scalar, or a vector with one element per intensity.

    :Inputs:
        * **I** (*vector | ndarray*) -- Rainfall intensities (mm/hour)
        * **durations** (*vector*) -- Number of minutes per duration

    :Outputs:
        *numpy array* -- The converted rainfall accumulations




.. _pfdf.utils.intensity.from_accumulation:

.. py:function:: from_accumulation(R, durations, *, dim = None)

    Converts rainfall accumulations to intensities

    .. dropdown:: Convert to Intensity

        ::

            from_accumulation(R, durations)

        Converts the input rainfall accumulations from mm over a duration to rainfall intensities in mm/hour. R should be an array of values representing millimeters of accumulation over one or more durations. The input durations should be in minutes. By default, the durations are broadcast across the final dimension of R, so the length of `durations` should either be 1, or the final value in ``R.shape``.

    .. dropdown:: Broadcasting Dimension

        ::

            from_accumulation(..., *, dim)

        Specifies the dimension of R that durations should be broadcast over. Here, `dim` is the *index* of a dimension of R. So for example, use 0 to broadcast durations over the first dimension, 1 to broadcast along the second dimension, etc. The `dim` input must be a scalar positive index. If None, broadcasts along the final dimension. When using the `dim` option, the length of the durations vector should either be 1, or ``R.shape[dim]``.


    :Inputs:
        * **R** (*ndarray*) -- An array of rainfall accumulations in millimeters over durations
        * **durations** (*vector*) -- Rainfall durations in minutes
        * **dim** (*scalar*) -- The index of the dimension of R over which to broadcast durations

    :Outputs:
        *numpy array* -- The converted rainfall intensities (mm/hour)

