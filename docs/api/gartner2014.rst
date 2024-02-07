pfdf.models.gartner2014 module
==============================

.. _Gartner et al., 2014: https://doi.org/10.1016/j.enggeo.2014.04.008

.. _pfdf.models.gartner2014:

.. py:module:: pfdf.models.gartner2014

    Functions that implement the debris-flow volume models of `Gartner et al., 2014`_.

    ====================================================  ===========
    Functions                                             Description
    ====================================================  ===========
    :ref:`emergency <pfdf.models.gartner2014.emergency>`  Runs the emergency assessment model
    :ref:`longterm <pfdf.models.gartner2014.longterm>`    Runs the long-term assessment model
    ====================================================  ===========

    This module contains functions that solve the two debris-flow volume models presented in `Gartner et al., 2014`_. As follows:

    ----

    .. _api-g14-emergency:

    **Emergency Assessment Model**

    .. math::

        V = \mathrm{exp}[4.22 + 0.39\ \mathrm{sqrt}(i15) + 0.36\ \mathrm{ln}(Bmh) + 0.13\ \mathrm{sqrt}(R)]

    where:

    .. list-table::

        * - **Variable**
          - **Description**
          - **Units**
        * - V
          - Potential sediment volume
          - meters^3
        * - i15
          - Peak 15-minute rainfall intensity
          - mm/hour
        * - Bmh
          - Catchment area burned at moderate or high intensity
          - km^2
        * - R
          - Watershed relief
          - meters

    ----

    .. _api-g14-longterm:

    **Long-Term Model**

    .. math::

        V = \mathrm{exp}[6.07 + 0.71\ \mathrm{ln}(i60) + 0.22\ \mathrm{ln}(B_t) - 0.24\ \mathrm{ln}(T) + 0.49\ \mathrm{ln}(A) + 0.03\ \mathrm{sqrt}(R)]

    where:

    .. list-table::

        * - **Variable**
          - **Description**
          - **Units**
        * - V
          - Potential sediment volume
          - meters^3
        * - i60
          - Peak 60-minute rainfall intensity
          - mm/hour
        * - Bt
          - Total burned catchment area
          - km^2
        * - T
          - Time elapsed since fire
          - years
        * - A
          - Total catchment area
          - km^2
        * - R
          - Watershed relief
          - meters

----

.. _pfdf.models.gartner2014.emergency:

.. py:function:: emergency(i15, Bmh, R, *, B = 4.22, Ci = 0.39, Cb = 0.36, Cr = 0.13, keepdims = False)
    :module: pfdf.models.gartner2014

    Solves the :ref:`emergency assessment model <api-g14-emergency>`.

    .. dropdown:: Default Model

        ::

            emergency(i15, Bmh, R)

        Solves the emergency assessment model given peak 15-minute rainfall intensity in mm/h (i15), the catchment area burned at moderate-or-high intensity in km^2 (Bmh), and the watershed relief in meter (R). Returns the potential volume of debris-flow sediment in m^3 (V).

        The model solves the equation:

        .. math:: 

            V = \mathrm{exp}[4.22 + 0.39\ \mathrm{sqrt}(i15) + 0.36\ \mathrm{ln}(Bmh) + 0.13\ \mathrm{sqrt}(R)]

        Each of the three input variables may either be a scalar, vector, or matrix of data values. If a variable is scalar, then the same value is used to assess potential sediment volume for each segment in the network. 

        If Bmh or R are a 1D array, then they should have one element per segment in the network. By contrast, if i15 is a 1D array, then each element is interpreted as a parameter for a distinct run of the model. Essentially, the model is run over the stream network for each value of i15.

        If a variable has more than 1 dimension, then it is parsed as a matrix. Rows are interpreted as values for segments, and columns are runs of the model. A variable may have either 1 row or one row per segment. If it has 1 row, then the same value is used for every segment per run. The matrix may have either 1 column or one column per run. If it has 1 column, then the same values are used for each run.

        The output volumes will either be a 1D array (for a single run), or a 2D array (for multiple runs). Each row holds the values for one stream segment, and each column is a run. (And see below for an option to always return 2D output).


    .. dropdown:: Custom Parameters

        ::

            emergency(..., *, B, Ci, Cb, Cr)

        
        Also specifies the parameters to use in the model. These are the intercept (B), rainfall intensity coefficient (Ci), burned area coefficient (Cb), and relief coefficient (Cr). By default, each coefficient is set to the value presented in `Gartner et al., 2014`_. This syntax allows you to run the model using different parameter values - for example, for an updated model calibration.

        In this case, the model solves the generalized equation:

        .. math::

            V = \mathrm{exp}[B + C_i\ \mathrm{sqrt}(i15) + C_b\ \mathrm{ln}(Bmh) + C_r\ \mathrm{sqrt}(R)]

        In many cases, input parameters will be scalar. However, this syntax also allows parameters to be vectors, in which each value is used for a distinct model run. All parameters with more than one value must have the same number of runs. Parameters with a single value will use the same value for each run. This setup can be useful for comparing results for different parameters - for example, using a Monte Carlo process to calibrate model parameters.


    .. dropdown:: 2D Output

        ::

            emergency(..., *, keepdims = True)

        Always returns output as a 2D array, regardless of the number of parameter runs.

    :Inputs: * **i15** (*ndarray*) -- Peak 15-minute rainfall intensities in mm/hour.
             * **Bmh** (*ndarray*) -- Catchment area burned at moderate or high intensity in km^2
             * **R** -- Watershed relief in meters
             * **B** (*vector*) -- The model intercept
             * **Ci** (*vector*) -- The coefficient of the i15 rainfall intensity term
             * **Cb** (*vector*) -- The coefficient of the Bmh burned area term
             * **Cr** (*vector*) -- The coefficient of the R watershed relief term
             * **keepdims** (*bool*) -- True to always return a 2D numpy array. If False (default), returns a 1D array when there is a single parameter run.

    :Outputs: *ndarray (Segments x Parameter Runs)* -- The predicted debris-flow sediment volumes in m^3



.. _pfdf.models.gartner2014.longterm:

.. py:function:: longterm(i60, Bt, T, A, R, *, B = 6.07, Ci = 0.71, Cb = 0.22, Ct = -0.24, Ca = 0.49, Cr = 0.03, keepdims=False)
    :module: pfdf.models.gartner2014

    Solves the :ref:`long-term model <api-g14-longterm>`.

    .. dropdown:: Default Model

        ::

            longterm(i60, Bt, T, A, R)

        Solves the emergency assessment model given peak 60-minute rainfall intensity in mm/h (i60), the catchment area burned at any severity level in km^2 (Bt), time since the most recent fire in years (T), total watershed area in km^2 (A), and watershed relief in m (R). Returns the predicted volume of debris-flow sediment in m^3 (V).

        The model solves the equation:

        .. math::
            
            V = \mathrm{exp}[6.07 + 0.71\ \mathrm{ln}(i60) + 0.22\ \mathrm{ln}(B_t) - 0.24\ \mathrm{ln}(T) + 0.49\ \mathrm{ln}(A) + 0.03\ \mathrm{sqrt}(R)]

        Each of the input variables may either be a scalar, vector, or matrix of data values. If a variable is scalar, then the same value is used to compute potential sediment volume for each segment in the network.

        If Bt, A, or R are a 1D array, then they should have one element per segment in the network. By contrast, if i60 or T are a 1D array, then each element is interpreted as a parameter for a distinct run of the model. Essentially, the model is run over the stream network for each pair of i15 and T values.

        If a variable has more than 1 dimension, then it is parsed as a matrix. Rows are interpreted as values for segments, and columns are runs of the model. A variable may have either 1 row or one row per segment. If it has 1 row, then the same value is used for every segment per run. The matrix may have either 1 column or one column per run. If it has 1 column, then the same values are used for each run.

        The output volumes will either be a 1D array (for a single run), or a 2D array (for multiple runs). Each row holds the values for one stream segment, and each column is a run. (And see below for an option to always return 2D output).


    .. dropdown:: Custom Parameters

        ::

            longterm(..., *, B, Ci, Cb, Ct, Ca, Cr)

        Also specifies the parameters to use in the model. These are the intercept (B), rainfall intensitiy coefficient (Ci), burned area coefficient (Cb), elapsed time coefficient (Ct), total area coefficient (Ca), and relief coefficient (Cr). By default, each coefficient is set to the value presented in `Gartner et al., 2014`_. This syntax allows you to run the model using different parameter values - for example, for an updated model calibration.

        In this case, the model solves the generalized equation:

        .. math::

            V = \mathrm{exp}[B + C_i\ \mathrm{ln}(i60) + C_b\ \mathrm{ln}(B_t) - C_t\ \mathrm{ln}(T) + C_a\ \mathrm{ln}(A) + C_r\ \mathrm{sqrt}(R)]

        In many cases, input parameters will be scalar. However, this syntax also allows parameters to be vectors, in which each value is used for a distinct model run. All parameters with more than one value must have the same number of runs. Parameters with a single value will use the same value for each run. This setup can be useful for comparing results for different parameters - for example, using a Monte Carlo process to calibrate model parameters.


    .. dropdown:: 2D Output

        ::

            longterm(..., *, keepdims = True)

        Always returns output as a 2D array, regardless of the number of parameter runs.

    :Inputs: * **i60** (*ndarray*) -- Peak 60-minute rainfall intensities in mm/hour
             * **Bt** (*ndarray*) -- Total burned catchment area in km^2
             * **T** (*ndarray*) -- Time elapsed since fire in years
             * **A** (*ndarray*) -- Total catchment area in km^2
             * **R** (*ndarray*) -- Watershed relief in meters
             * **B** (*vector*) -- The model intercept
             * **Ci** (*vector*) -- The coefficient of the i60 rainfall intensity term
             * **Cb** (*vector*) -- The coefficient of the Bt burned area term
             * **Ct** (*vector*) -- The coefficient of the T elapsed time term
             * **Ca** (*vector*) -- The coefficient of the A total area term
             * **Cr** (*vector*) -- The coefficient of the R watershed relief term
             * **keepdims** (*bool*) -- True to always return a 2D numpy array. If False (default), returns a 1D array when there is a single parameter run.

    :Outputs: *ndarray (Segments x Parameter Runs)* -- The predicted debris-flow sediment volumes in m^3
    
    