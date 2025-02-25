models.gartner2014 module
=========================

.. _Gartner et al., 2014: https://doi.org/10.1016/j.enggeo.2014.04.008

.. _pfdf.models.gartner2014:

.. py:module:: pfdf.models.gartner2014

    Functions that implement the debris-flow volume models of `Gartner et al., 2014`_.

    .. list-table::
      :header-rows: 1

      * - Function
        - Description
      * - :ref:`emergency <pfdf.models.gartner2014.emergency>`
        - Runs the emergency assessment model
      * - :ref:`longterm <pfdf.models.gartner2014.longterm>`
        - Runs the long-term assessment model

    This module contains functions that solve the two debris-flow volume models presented in `Gartner et al., 2014`_. As follows:

    ----

    .. _api-g14-emergency:

    **Emergency Assessment Model**

    .. math::

        lnV = 4.22 + 0.39\ \mathrm{sqrt}(i15) + 0.36\ \mathrm{ln}(Bmh) + 0.13\ \mathrm{sqrt}(R)

    .. math::

        V = \mathrm{exp}(lnV)

    .. math::

        \mathrm{95\%} \ \mathrm{CI} = \mathrm{exp}[lnV ± (1.96 \times 1.04)]

    where:

    .. list-table::

        * - **Variable**
          - **Description**
          - **Units**
        * - V
          - Potential sediment volume
          - meters^3
        * - lnV
          - Natural log of potential sediment volume
          -
        * - i15
          - Peak 15-minute rainfall intensity
          - mm/hour
        * - Bmh
          - Catchment area burned at moderate or high intensity
          - km^2
        * - R
          - Watershed relief
          - meters
        * - 1.96
          - Normal distribution percentile multiplier for 95% confidence interval
          -
        * - 1.04
          - Residual standard error of the model
          -


    ----

    .. _api-g14-longterm:

    **Long-Term Model**

    .. math::

        lnV = 6.07 + 0.71\ \mathrm{ln}(i60) + 0.22\ \mathrm{ln}(B_t) - 0.24\ \mathrm{ln}(T) + 0.49\ \mathrm{ln}(A) + 0.03\ \mathrm{sqrt}(R)

    .. math::

        V = \mathrm{exp}(lnV)

    .. math::

        \mathrm{95\%} \ \mathrm{CI} = \mathrm{exp}[lnV ± (1.96 \times 1.25)]



    where:

    .. list-table::

        * - **Variable**
          - **Description**
          - **Units**
        * - V
          - Potential sediment volume
          - meters^3
        * - lnV
          - Natural log of potential sediment volume
          -
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
        * - 1.96
          - Normal distribution percentile multiplier for 95% confidence interval
          -
        * - 1.25
          - Residual standard error of the model
          -

----

.. _pfdf.models.gartner2014.emergency:

.. py:function:: emergency(i15, Bmh, R, *, B = 4.22, Ci = 0.39, Cb = 0.36, Cr = 0.13, CI = 0.95, RSE = 1.04, keepdims = False)
    :module: pfdf.models.gartner2014

    Solves the :ref:`emergency assessment model <api-g14-emergency>`.

    .. dropdown:: Default Model

        ::

            emergency(i15, Bmh, R)

        Solves the emergency assessment model given peak 15-minute rainfall intensity in mm/h (i15), the catchment area burned at moderate-or-high intensity in km^2 (Bmh), and the watershed relief in meter (R). Returns the predicted volume of debris-flow sediment in m^3 (V), the lower bounds of the 95% confidence interval (Vmin), and the upper bound of the 95% confidence interval (Vmax).

        The model solves the equation:

        .. math:: 

            lnV = 4.22 + 0.39\ \mathrm{sqrt}(i15) + 0.36\ \mathrm{ln}(Bmh) + 0.13\ \mathrm{sqrt}(R)

        .. math::

            V = \mathrm{exp}(lnV)

        and uses residual standard error (RSE = 1.04) to estimate the bounds of the 95% confidence interval:

        .. math::

            V_{min} = \mathrm{exp}(lnV - 1.96 * 1.04)

        .. math::

            V_{max} = \mathrm{exp}(lnV + 1.96 * 1.04)

        Note that the volume confidence interval is estimated using a normal distribution, hence the 1.96 percentile multiplier for a 95% interval.

        Most commonly, the Bmh and R variables should be vectors or scalars (although refer below for a less common 2D option). If one of these variables is a vector, then it should have one element per segment in the network. If a scalar, then the same value is used to assess potential sediment volume for each segment in the network. The i15 variable should be a vector with one element per rainfall intensity. The model will be run over the entire stream network for each i15 value.

        The output will be a tuple of 3 numpy arrays, in order: V, Vmin, and Vmax. The V array will have up to two dimensions. The first dimension is is stream segments, and the second dimension is rainfall intensities. By default, the second dimension will be removed if there is a single rainfall intensity (and use the keepdims option below to return arrays with constant numbers of dimensions). For this base syntax, the Vmin and Vmax arrays will always match the shape of the V array, but this is not always the case for the more complex syntaxes detailed below.


    .. dropdown:: Custom Parameters

        ::

            emergency(..., *, B, Ci, Cb, Cr)

        Also specifies the parameters to use in the model. These are the intercept (B), rainfall intensity coefficient (Ci), burned area coefficient (Cb), and relief coefficient (Cr). By default, each coefficient is set to the value presented in Gartner et al., 2014. This syntax allows you to run the model using different parameter values - for example, for an updated model calibration.

        In this case, the model solves the generalized equation:

        .. math:: 

            lnV = 4.22 + C_i\ \mathrm{sqrt}(i15) + C_b\ \mathrm{ln}(Bmh) + C_r\ \mathrm{sqrt}(R)

        .. math::

            V = \mathrm{exp}(lnV)

        In many cases, input parameters will be scalar. However, this syntax also allows parameters to be vectors, in which each value is used for a distinct model run. Here, a "run" is defined as a unique set of model parameters. All parameters with more than one value must have the same number of runs. Parameters with a single value will use the same value for each run. This setup can be useful for comparing results for different parameters - for example, using a Monte Carlo process to calibrate model parameters.

        The Bmh and R variables also support values for distinct runs. In this case, Bmh and/or R should be a matrix. Note that whenever Bmh or R have more than one dimension, then the variable is parsed as a matrix. In this case, each row is a stream segment, and each column is a parameter run. Each column will be used to solve the model for (only) the associated parameter run. If B, Ci, Cb, and Cr are all scalar, then this syntax effectively allows you to test multiple values for each Bmh and R variable - for example, to test the model using different datasets to derive input variables.

        When implementing multiple runs, then the output V array will have up to three dimensions (stream segments x rainfall intensities x parameter runs). The Vmax and Vmin arrays will match the shape of the V array. By default, this function removes singleton dimensions from the output arrays. The first dimension is always retained, but the second is removed if there is a single rainfall intensity, and the third is removed if there is a single run. (And use the keepdims option below to return arrays with constant numbers of dimensions).

    .. dropdown:: Confidence Intervals

        ::

            emergency(..., *, CI, RSE)
    
        Also specifies parameters for estimating confidence intervals. CI are the confidence intervals and should be values between 0 and 1. For example, use 0.95 to estimate the 95% confidence interval. RSE is the residual standard error of the model. When using these parameters, the confidence interval is calculated using:

        .. math::

            V_{min} = \mathrm{exp}[lnV - X * RSE]

        .. math::

            V_{max} = \mathrm{exp}[lnV + X * RSE]

        Here, X is a percentile multiplier computed from a normal distribution, such that:

        .. math::

            q = 1 - \frac{1-CI}{2}

        .. math::

            X = \mathrm{norm.ppf}(q)

        The CI input should be a vector with one element per confidence interval that should be calculated. Alternatively, set CI to None or an empty vector to disable the confidence interval calculations. When specifying confidence intervals, the output V array will have up to 3 dimensions (segments x i15 x runs). By contrast, the Vmax and Vmin arrays may have up to 4 dimensions (segments x i15 x runs x CIs). By default, removes singleton dimensions from the output arrays, but use the keepdims option to return arrays with a fixed number of dimensions. If the confidence intervals are disabled, then Vmax and Vmin will be empty arrays, such that the length of their final dimension is 0.

        The RSE input may be a scalar, vector, or matrix. If scalar, uses the same RSE for all confidence interval calculations. If a vector, then each element is interpreted as the RSE for a distinct parameter run. This can be useful when calculating confidence intervals for different model calibrations. If RSE has more than one dimension, then it is interpreted as a matrix. Each row holds the values for a parameter run, and each column is the value for one of the input confidence intervals. This can be useful for calculating the same CI using different RSE values.


    .. dropdown:: Constant Dimensions

        ::

            emergency(..., *, keepdims = True)

        Returns arrays with a fixed number of dimensions. The V array will always have 3 dimensions (segments x i15 x parameter runs), whereas the Vmax and Vmin arrays will always have 4 dimensions (segments x i15 x parameter runs x confidence intervals).

    :Inputs: * **i15** (*ndarray*) -- Peak 15-minute rainfall intensities in mm/hour.
             * **Bmh** (*ndarray*) -- Catchment area burned at moderate or high intensity in km^2
             * **R** -- Watershed relief in meters
             * **B** (*vector*) -- The model intercept
             * **Ci** (*vector*) -- The coefficient of the i15 rainfall intensity term
             * **Cb** (*vector*) -- The coefficient of the Bmh burned area term
             * **Cr** (*vector*) -- The coefficient of the R watershed relief term
             * **CI** (*vector*) -- The confidence interval to calculate. Should be on the interval from 0 to 1.
             * **RSE** (*vector*) -- The residual standard error of the model. Used to compute confidence intervals
             * **keepdims** (*bool*) -- True to return arrays with constant numbers of dimensions. False (default) to remove singleton dimensions.

    :Outputs: 
        * **V** *ndarray (Segments x i15 x Runs)* -- The predicted debris-flow sediment volumes in m^3
        * **Vmin** *ndarray (Segments x i15 x Runs x CIs)* -- The lower bound of the confidence interval
        * **Vmax** *ndarray (Segments x i15 x Runs x CIs)* -- The upper bound of the confidence interval


.. _pfdf.models.gartner2014.longterm:

.. py:function:: longterm(i60, Bt, T, A, R, *, B = 6.07, Ci = 0.71, Cb = 0.22, Ct = -0.24, Ca = 0.49, Cr = 0.03, CI = 0.95, RSE = 1.25, keepdims=False)
    :module: pfdf.models.gartner2014

    Solves the :ref:`long-term model <api-g14-longterm>`.

    .. dropdown:: Default Model

        ::

            longterm(i60, Bt, T, A, R)

        Solves the emergency assessment model given peak 60-minute rainfall intensity in mm/h (i60), the catchment area burned at any severity level in km^2 (Bt), time since the most recent fire in years (T), total watershed area in km^2 (A), and watershed relief in m (R). Returns the predicted volume of debris-flow sediment in m^3 (V), the lower bounds of the 95% confidence interval (Vmin), and the upper bound of the 95% confidence interval (Vmax).

        The model solves the equation:

        .. math::

            lnV = 6.07 + 0.71\ \mathrm{ln}(i60) + 0.22\ \mathrm{ln}(B_t) - 0.24\ \mathrm{ln}(T) + 0.49\ \mathrm{ln}(A) + 0.03\ \mathrm{sqrt}(R)

        .. math::

            V = \mathrm{exp}(lnV)

        and uses residual standard error (RSE = 1.25) to estimate the bounds of the 95% confidence interval:

        .. math::

            V_{min} = \mathrm{exp}(lnV - 1.96 * 1.25)

        .. math::

            V_{max} = \mathrm{exp}(lnV + 1.96 * 1.25)

        Note that the volume confidence interval is estimated using a normal distribution, hence the 1.96 percentile multiplier for a 95% interval.

        Most commonly, the Bt, T, A, and R variables should be vectors or scalars (although refer below for a less common 2D option). If a variable is scalar, then the same value is used to assess potential sediment volume for each segment in the network. T is often a scalar, although refer to the next syntax for its vector case. If Bt, A, or R is a vector, then the variable should have one element per segment in the network. The i60 variable should be a vector with one element per rainfall intensity. The model will be run over the entire stream network for each i60 value.

        The output will be a tuple of 3 numpy arrays, in order: V, Vmin, and Vmax. The V array will have up to two dimensions. The first dimension is is stream segments, and the second dimension is rainfall intensities. By default, the second dimension will be removed if there is a single rainfall intensity (and use the keepdims option below to return arrays with constant numbers of dimensions). For this base syntax, the Vmin and Vmax arrays will always match the shape of the V array, but this is not always the case for the more complex syntaxes detailed below.

    .. dropdown:: Custom Parameters

        ::

            longterm(..., *, B, Ci, Cb, Ct, Ca, Cr)

        Also specifies the parameters to use in the model. These are the intercept (B), rainfall intensitiy coefficient (Ci), burned area coefficient (Cb), elapsed time coefficient (Ct), total area coefficient (Ca), and relief coefficient (Cr). By default, each coefficient is set to the value presented in Gartner et al., 2014. This syntax allows you to run the model using different parameter values. For example, for an updated model calibration.

        In this case, the model solves the generalized equation:

        .. math::

            lnV = 6.07 + C_i\ \mathrm{ln}(i60) + C_b\ \mathrm{ln}(B_t) - C_t\ \mathrm{ln}(T) + C_a\ \mathrm{ln}(A) + C_r\ \mathrm{sqrt}(R)

        .. math::

            V = \mathrm{exp}(lnV)

        In many cases, input parameters will be scalar. However, this syntax also allows parameters to be vectors, in which each value is used for a distinct model run. Here, a "run" is defined as a unique set of model parameters. All parameters with more than one value must have the same number of runs. Parameters with a single value will use the same value for each run. This setup can be useful for comparing results for different parameters - for example, using a Monte Carlo process to calibrate model parameters.

        The Bt, T, A, and R variables also support values for distinct runs. If T is a vector, then it is interpreted as one value per parameter run. Otherwise, a variable should be a matrix to support multiple runs. Note that whenever one of these variables has more than one dimension, then the variable is parsed as a matrix. In this case, each row is a stream segment, and each column is a parameter run. Each column will be used to solve the model for (only) the associated parameter run. If B, Ci, Cb, Ct, Ca, and Cr are all scalar, then this syntax effectively allows you to test multiple values of the Bt, T, A, and/or R variables - for example, to run the model using different numbers of years of recovery.

        When implementing multiple runs, then the output V array will have up to three dimensions (stream segments x rainfall intensities x parameter runs). The Vmax and Vmin arrays will match the shape of the V array. By default, this function removes singleton dimensions from the output arrays. The first dimension is always retained, but the second is removed if there is a single rainfall intensity, and the third is removed if there is a single run. (And use the keepdims option below to return arrays with constant numbers of dimensions).


    .. dropdown:: Confidence Intervals

        ::

            longterm(..., *, CI, RSE)

        Also specifies parameters for estimating confidence intervals. CI are the confidence intervals and should be values between 0 and 1. For example, use CI=0.95 to estimate the 95% confidence interval. RSE is the residual standard error of the model. When using these parameters, the confidence interval is calculated using:

        .. math::

            V_{min} = \mathrm{exp}[lnV - X * RSE]

        .. math::

            V_{max} = \mathrm{exp}[lnV + X * RSE]

        Here, X is a percentile multiplier computed from a normal distribution, such that:

        .. math::

            q = 1 - \frac{1-CI}{2}

        .. math::
          
            X = \mathrm{norm.ppf}(q)

        The CI input should be a vector with one element per confidence interval that should be calculated. Alternatively, set CI to None or an empty vector to disable the confidence interval calculations. When specifying confidence intervals, the output V array will have up to 3 dimensions (segments x i60 x runs). By contrast, the Vmax and Vmin arrays may have up to 4 dimensions (segments x i60 x runs x CIs). By default, removes singleton dimensions from the output arrays, but use the keepdims option to return arrays with a fixed number of dimensions. If the confidence intervals are disabled, then Vmax and Vmin will be empty arrays, such that the length of their final dimension is 0.

        The RSE input may be a scalar, vector, or matrix. If scalar, uses the same RSE for all confidence interval calculations. If a vector, then each element is interpreted as the RSE for a distinct parameter run. This can be useful when calculating confidence intervals for different model calibrations. If RSE has more than one dimension, then it is interpreted as a matrix. Each row holds the values for a parameter run, and each column is the value for one of the input confidence intervals. This can be useful for calculating the same CI using different RSE values.


    .. dropdown:: Constant Dimensions

        ::

            longterm(..., *, keepdims = True)

        Returns arrays with a fixed number of dimensions. The V array will always have 3 dimensions (segments x i60 x parameter runs), whereas the Vmax and Vmin arrays will always have 4 dimensions (segments x i60 x parameter runs x confidence intervals).

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
             * **CI** (*vector*) -- The confidence interval to calculate. Should be on the interval from 0 to 1.
             * **RSE** (*vector*) -- The residual standard error of the model. Used to compute confidence intervals
             * **keepdims** (*bool*) -- True to return arrays with constant numbers of dimensions. False (default) to remove singleton dimensions.

    :Outputs: 
        * **V** *ndarray (Segments x i15 x Runs)* -- The predicted debris-flow sediment volumes in m^3
        * **Vmin** *ndarray (Segments x i15 x Runs x CIs)* -- The lower bound of the confidence interval
        * **Vmax** *ndarray (Segments x i15 x Runs x CIs)* -- The upper bound of the confidence interval
    
    