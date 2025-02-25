models.staley2017 module
========================

.. _Staley et al., 2017: https://doi.org/10.1016/j.geomorph.2016.10.019

.. _pfdf.models.staley2017:

.. py:module:: pfdf.models.staley2017

    Implements the logistic regression models presented in `Staley et al., 2017`_.

    .. list-table::
        :header-rows: 1

        * - Content
          - Description
        * -
          -
        * - **Solver Functions**
          -
        * - :ref:`likelihood <pfdf.models.staley2017.likelihood>`
          - Solves for debris-flow likelihoods given rainfall accumulations
        * - :ref:`accumulation <pfdf.models.staley2017.accumulation>`
          - Solves for the rainfall accumulations needed to achieve given probability levels
        * -
          -
        * - **Model Classes**
          -
        * - :ref:`M1 <pfdf.models.staley2017.M1>`
          - Implements the M1 model
        * - :ref:`M2 <pfdf.models.staley2017.M2>`
          - Implements the M2 model
        * - :ref:`M3 <pfdf.models.staley2017.M3>`
          - Implements the M3 model
        * - :ref:`M4 <pfdf.models.staley2017.M4>`
          - Implements the M4 model
        * -
          -
        * - **Model Methods**
          -
        * - parameters
          - Returns the B, Ct, Cf, and Cs parameters for a model
        * - variables
          - Returns the T, F, and S variables for a model
        * - terrain
          - Returns the terrain variable (T) for a model
        * - fire
          - Returns the fire variable (F) for a model
        * - soil
          - Returns the soil variable (S) for a model


    This module solves the logistic regression models presented in `Staley et al., 2017`_. These models describe debris-flow likelihood as a function of terrain (T), fire burn severity (F), soil (S), and rainfall accumulation (R), such that:

    .. math::

        p = \mathrm{\frac{e^X}{1 + e^X}}


    .. math::

        \mathrm{X = B + C_t\ T\ R + C_f\ F\ R + C_s\ S\ R}

    where:

    .. list-table::

        * - **Variable**
          - **Description**
        * - p
          - Debris-flow likelihood (0 to 1)
        * - T
          - A terrain variable
        * - F
          - A fire severity variable
        * - S
          - A soil variable
        * - R
          - Rainfall accumulation in mm
        * - B
          - Model intercept
        * - Ct, Cf, Cs
          - Variable coefficients

    This module provides two functions to solve models of this form. The :ref:`likelihood function <pfdf.models.staley2017.likelihood>` solves the model in the forward direction, and the :ref:`accumulation function <pfdf.models.staley2017.accumulation>` inverts the model to compute the rainfall accumulations needed to cause debris flows at the specified probability levels.

    .. note:: 
        
        The :ref:`likelihood <pfdf.models.staley2017.likelihood>` and :ref:`accumulation <pfdf.models.staley2017.accumulation>` functions are generalized, so are suitable for *any* model following the form of the above equation.

    In addition to the generic solvers, this module provides the M1, M2, M3, and M4  model classes, which help implement the 4 specific models described in the paper. Each class provides a ``parameters`` method, which returns the corresponding B, Ct, Cf, and Cs values published in the paper. Each class also provides a ``variables`` method, which returns the appropriate T, F, and S variables for a given set of stream segments. These parameters and variables can then be used to run the :ref:`likelihood <pfdf.models.staley2017.likelihood>` and/or :ref:`accumulation <pfdf.models.staley2017.accumulation>` functions.


Solver Functions
----------------

.. _pfdf.models.staley2017.likelihood:

.. py:function:: likelihood(R, B, Ct, T, Cf, F, Cs, S, *, keepdims = False)
    :module: pfdf.models.staley2017

    Computes debris-flow likelihood for the specified rainfall durations

    ::

        likelihood(R, B, Ct, T, Cf, F, Cs, S)
        likelihood(..., keepdims=True)

    Solves the debris-flow likelihoods for the specified rainfall accumulations. This function is agnostic to the actual model being run, and thus can implement all 4 of the models presented in the paper (as well as any other model following the form of Equation 1).

    All of the inputs to this function should be real-valued numpy arrays. The R values are the rainfall accumulations for which the model should be solved. For example, R = 6 solves for debris-flow likelihood when rainfall accumulation is 6 mm/duration. R should be a 1D array listing all the accumulations that should be solved for.

    The three variables - T, F, and S - represent the terrain steepness, wildfire severity, and surface properties variables for the model. In most cases, these are 1D arrays with one element per stream segment being assessed. Variables can also be scalar (in which the same value is used for every segment), or 2D arrays (refer below for details of this less common use case).

    The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic model link equation. B is the intercept, and each C parameter is the coefficient of the associated variable. Parameters can be used to implement multiple runs of the assessment model. Here, we define a "run" as an implementation of the hazard model using a unique set of logistic model parameters. Each parameter should be either a scalar, or vector of parameter values. If a vector, the input should have one element per run. If a scalar, then the same value is used for every run of the model. A common use case is solving the model for multiple rainfall durations (for example: 15, 30, and 60 minute intervals). In the example with 3 durations, each parameter should have 3 elements - each element corresponds to parameter value for the corresponding rainfall duration. Another use case for multiple runs is implementing a parameter sweep to validate model parameters.

    This function solves the debris-flow likelihoods for all stream segments, rainfall accumulations, and parameter runs provided. Note that rainfall accumulations should be relative to the rainfall durations associated with each set of parameters. For example, if using parameters for 15-minute and 30-minute rainfall durations, then the input rainfall accumulations should be for 15-minute and 30-minute intervals, respectively. Accumulation units are the units of the rainfall values used to calibrate the model's parameters. For the 4 models described in the paper, accumulations are millimeters of accumulations per rainfall duration.

    The returned output will be a numpy array with up to 3 dimensions. The first dimension is stream segments, second dimension is rainfall accumulations, and third dimension is parameter runs. By default, this command will remove singleton dimensions from the output array. The first dimension is always retained, but the second is removed if there is a single rainfall accumulation, and the third is removed if there is a single parameter run. Alternatively, set keepdims=True to always return a 3D array.

    As mentioned, one or more variables can also be a 2D array. In this case each row is a stream segment, and each column is a parameter run. Each column will be used to solve the model for (only) the associated parameter run. This allows use of different values for a variable. An example use case could be testing the model using different datasets to derive one or more variables.


    :Inputs: 
        * **R** (*vector (R values)*) -- The rainfall accumulations for which to solve the model
        * **B** (*scalar | vector (Runs)*) -- The intercepts of the link equation
        * **Ct** (*scalar | vector (Runs)*) -- The coefficients for the terrain steepness variable
        * **T** (*vector (Segments) | matrix (Segments x Runs)*) -- The terrain steepness variable
        * **Cf** (*scalar | vector (Runs)*) -- The coefficients for the wildfire severity variable
        * **F** (*vector (Segments) | matrix (Segments x Runs)*) -- The wildfire severity variable
        * **Cs** (*scalar | vector (Runs)*) -- The coefficients for the surface properties variable
        * **S** (*vector (Segments) | matrix (Segments x Runs)*) -- The surface properties variable
        * **keepdims** (*bool*) -- True to always return a 3D numpy array. If False (default), returns a 2D array when there is 1 R value, and a 1D array if there is 1 R value and 1 parameter run.

    :Outputs: 
        *ndarray (Segments x R values x Parameter Runs)* -- The computed likelihoods


.. _pfdf.models.staley2017.accumulation:

.. py:function:: accumulation(p, B, Ct, T, Cf, F, Cs, S, *, keepdims = False, screen = True)
    :module: pfdf.models.staley2017

    Computes rainfall accumulations needed for specified debris-flow probability levels

    .. dropdown:: Solve Rainfall Accumulation

        ::

            accumulation(p, B, Ct, T, Cf, F, Cs, S)

        Returns the rainfall accumulations required to achieve the specified p-values. This function is agnostic to the actual model being run, and thus can implement all 4 of the models presented in the paper (as well as any other model following the form of Equation 1).

        All of the inputs to this function should be real-valued numpy arrays. The p-values - p - are the design probabilities for which the model should be solved. For example, p=0.5 estimates the rainfall accumulation that would result in a 50% probability of a debris flow event. Here, `p` should be a 1D array listing all the design probabilities that should be solved for.

        The three variables - T, F, and S - represent the terrain steepness, wildfire severity, and surface properties variables for the model. In most cases, these are 1D arrays with one element per stream segment being assessed. Variables can also be scalar (in which the same value is used for every segment), or 2D arrays (refer below for details of this less common use case).

        The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic model link equation. B is the intercept, and each C parameter is the coefficient of the associated variable. Parameters can be used to implement multiple runs of the assessment model. Here, we define a "run" as an implementation of the hazard model using a unique set of logistic model parameters. Each parameter should be either a scalar, or vector of parameter values. If a vector, the input should have one element per run. If a scalar, then the same value is used for every run of the model. A common use case is solving the model for multiple rainfall durations (for example: 15, 30, and 60 minute intervals). In the example with 3 durations, each parameter should have 3 elements - each element corresponds to parameter value for the corresponding rainfall duration. Another use case for multiple runs is implementing a parameter sweep to validate model parameters.

        This function solves the rainfall accumulations for all stream segments, p-values, and parameter runs provided. Each accumulation describes the total rainfall required within the rainfall duration associated with its parameters. For example, if using parameters for a 15-minute rainfall duration, the accumulation describes the total rainfall required within a 15-minute window. Accumulation units are the units of the rainfall values used to calibrate the model's parameters. For the 4 models described in the paper, accumulations are in mm.

        The returned output will be a numpy array with up to 3 dimensions. The first dimension is stream segments, second dimension is p-values, and third dimension is parameter runs. By default, this command will remove singleton dimensions from the output array. The first dimension is always retained, but the second is removed if there is a single design probability, and the third is removed if there is a single parameter run. Alternatively, set keepdims=True to always return a 3D array.

        As mentioned, one or more variable can also be a 2D array. In this case each row is a stream segment, and each column is a parameter run. Each column will be used to solve the model for (only) the associated parameter run. This allows use of different values for a variable. An example use case could be testing the model using different datasets to derive one or more variables.

    .. dropdown:: 3D Output

        ::

            accumulation(..., *, keepdims = True)

        Always returns the output as a 3D numpy array, regardless of the number of p-values and parameter runs.

    .. dropdown:: Disable Screening

        ::

            accumulation(..., *, screen = False)

        Disables the screening of negative accumulations. When screening is disabled, negative accumulations are retained in the output, instead of being replaced by nan.

    :Inputs: 
        * **p** (*vector (p values)*) -- The probability levels for which to solve the model
        * **B** (*scalar | vector (Runs)*) -- The intercepts of the link equation
        * **Ct** (*scalar | vector (Runs)*) -- The coefficients for the terrain steepness variable
        * **T** (*vector (Segments) | matrix (Segments x Runs)*) -- The terrain steepness variable
        * **Cf** (*scalar | vector (Runs)*) -- The coefficients for the wildfire severity variable
        * **F** (*vector (Segments) | matrix (Segments x Runs)*) -- The wildfire severity variable
        * **Cs** (*scalar | vector (Runs)*) -- The coefficients for the surface properties variable
        * **S** (*vector (Segments) | matrix (Segments x Runs)*) -- The surface properties variable
        * **keepdims** (*bool*) -- True to always return a 3D numpy array. If false (default), returns a 2D array when there is 1 p-value, and a 1D array if there is 1 p-value and 1 parameter run.
        * **screen** (*bool*) -- True (default) to replace negative accumulations with NaN. False to disable this screening.

    :Outputs: 
        *ndarray (Segments x P-values x Parameter Runs)* -- The computed rainfall accumulations


Model Classes
-------------

.. _pfdf.models.staley2017.M1:

.. py:class:: M1
    :module: pfdf.models.staley2017

    Facilitates the M1 model.

    Terrain (T)
        Proportion of catchment area with both (1) moderate or high burn severity, and (2) slope angle >= 23 degrees.

    Fire (F)
        Mean catchment dNBR / 1000

    Soil (S)
        Mean catchment KF-factor

    ----


    .. _pfdf.models.staley2017.M1.parameters:

    .. py:method:: parameters(cls, durations = [15, 30, 60])
        :classmethod:

        Return model parameters for the queried durations.

        .. dropdown:: All Parameters

            ::

                M1.parameters()

            Returns the logistic model intercepts (B), terrain coefficients (Ct), fire coefficients (Cf), and soil coefficients (Cs) for the M1 model (in that order). Each output value is a numpy 1D array with 3 elements. The three elements are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).


        .. dropdown:: Specific Durations

            ::

                M1.parameters(durations)

            Returns values for the queried rainfall durations. Each output value is a numpy 1D array with one element per queried duration. Valid durations to query are 15, 30, and 60.

        :Inputs: * **durations** (*vector*) -- A list of rainfall durations for which to return model parameters

        :Outputs: * *ndarray* -- Logistic model intercepts (B)
                  * *ndarray* -- Terrain coefficients (Ct)
                  * *ndarray* -- Fire coefficients (Cf)
                  * *ndarray* -- Soil coefficients (Cs)


    .. _pfdf.models.staley2017.M1.variables:

    .. py:method:: variables(segments, moderate_high, slopes, dnbr, kf_factor, omitnan = False)
        :staticmethod:

        Computes the T, F, and S variables for the M1 model

        .. dropdown:: Compute Variables

            ::

                M1.variables(segments, moderate_high, slopes, dnbr, kf_factor)

            Computes the (T)errain, (F)ire, and (S)oil variables from the M1 model for each stream segment in a network. T is the proportion of catchment area that has both (1) moderate or high burn severity, and (2) a slope angle >= 23 degrees. F is mean catchment dNBR divided by 1000. S is mean catchment KF-factor. Returns these outputs as numpy 1D arrays with one element per stream segment. Note that input slopes should be slope gradients, and not slope angles.

        .. dropdown:: Omit NaN Values

            ::

                M1.variables(..., omitnan)

            Specifies how to treat NaN and NoData values in the dnbr and kf_factor rasters. The omitnan option may either be a boolean or a dict. In the default setting (omitnan=False), when a raster contains a NaN or Nodata value in a catchment basin, then the associated variable for the basin will be NaN. For example, if the dnbr raster contains NaN in a segment's catchment, then the F variable will be NaN for that segment. If omitnan=True, NaN and NoData values are ignored. Note that if a raster only contains NaN and NoData values in a catchment, then the variable will still be NaN for the catchment.

            If omitnan is a dict, then it may have the keys "dnbr", and/or "kf_factor". The value of each key should be a boolean indicating whether to omit NaN and NoData values for that raster. If a key is not included, then the omitnan setting for the raster is set to False. Raises a ValueError if the dict includes other keys.

        :Inputs: * **segments** (*Segments*) -- A Segments object defining a stream segment network
                 * **moderate_high** (*Raster*) -- A raster mask indicating watershed pixels with moderate or high burn severity. True pixels indicate moderate or high severity. False pixels are not burned at these levels.
                 * **slopes** (*Raster*) -- A raster with the slope gradients (not angles) for the watershed. NoData pixels are interpreted as locations with slope angles less than 23 degrees.
                 * **dnbr** (*Raster*) -- A dNBR raster for the watershed
                 * **kf_factor** (*Raster*) -- A KF-factor raster for the watershed
                 * **omitnan** (*bool*) -- A boolean or dict indicating whether to ignore NaN and NoData values in the dnbr and kf_factor rasters

        :Outputs: * *ndarray* -- The terrain variable (T) for each stream segment
                  * *ndarray* -- The fire variable (F) for each stream segment
                  * *ndarray* -- The soil variable (S) for each stream segment


    .. _pfdf.models.staley2017.M1.terrain:

    .. py:method:: terrain(segments, moderate_high, slopes)
        :staticmethod:

        Computes the M1 terrain variable

        ::

            M1.terrain(segments, moderate_high, slopes)

        Returns the M1 terrain variable for the network.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **moderate_high** (*Raster*) -- The moderate-high burn severity mask
                 * **slopes** (*Raster*) -- Slope raster

        :Outputs: *ndarray* -- The M1 terrain variable (T)


    .. _pfdf.models.staley2017.M1.fire:

    .. py:method:: fire(segments, dnbr, omitnan = False)
        :staticmethod:

        Computes the M2 fire variable

        ::

            M1.fire(segments, dnbr)
            M1.fire(segments, dnbr, omitnan=True)
        
        Returns the M1 fire variable for the network. Use ``omitnan`` to ignore NaN and NoData values in the dNBR raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **dnbr** (*Raster*) -- A dNBR raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the dNBR raster. Default is False.

        :Outputs: *ndarray* -- The M1 fire variable (F)

    
    .. _pfdf.models.staley2017.M1.soil:

    .. py:method:: soil(segments, kf_factor, omitnan = False)
        :staticmethod:

        Computes the M1 soil variable

        ::

            M1.soil(segments, kf_factor)
            M1.soil(segments, kf_factor, omitnan=True)

        Returns the M1 soil variable for the network. Use ``omitnan`` to ignore NaN and NoData values in the KF-factor raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **kf_factor** (*Raster*) -- A KF-factor raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the KF-factor raster. Default is False

        :Outputs: *ndarray* -- The M1 soil variable (S)



.. _pfdf.models.staley2017.M2:

.. py:class:: M2
    :module: pfdf.models.staley2017

    Facilitates the M2 model.

    Terrain (T)
        Mean sin(θ) of catchment area burned at moderate or high severity

    Fire (F)
        Mean catchment dNBR / 1000

    Soil (S)
        Mean catchment KF-factor

    ----


    .. _pfdf.models.staley2017.M2.parameters:

    .. py:method:: parameters(cls, durations = [15, 30, 60])
        :classmethod:

        Return model parameters for the queried durations.

        .. dropdown:: All Parameters

            ::

                M2.parameters()

            Returns the logistic model intercepts (B), terrain coefficients (Ct), fire coefficients (Cf), and soil coefficients (Cs) for the M2 model (in that order). Each output value is a numpy 1D array with 3 elements. The three elements are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).


        .. dropdown:: Specific Durations

            ::

                M2.parameters(durations)

            Returns values for the queried rainfall durations. Each output value is a numpy 1D array with one element per queried duration. Valid durations to query are 15, 30, and 60.

        :Inputs: * **durations** (*vector*) -- A list of rainfall durations for which to return model parameters

        :Outputs: * *ndarray* -- Logistic model intercepts (B)
                  * *ndarray* -- Terrain coefficients (Ct)
                  * *ndarray* -- Fire coefficients (Cf)
                  * *ndarray* -- Soil coefficients (Cs)


    .. _pfdf.models.staley2017.M2.variables:

    .. py:method:: variables(segments, moderate_high, slopes, dnbr, kf_factor, omitnan = False)
        :staticmethod:

        Computes the T, F, and S variables for the M2 model

        .. dropdown:: Compute Variables

            ::

                M2.variables(segments, moderate_high, slopes, dnbr, kf_factor)

            Computes the (T)errain, (F)ire, and (S)oil variables from the M2 model for each stream segment in a network. T is the mean sin(θ) of catchment area burned at moderate or high severity, where θ is the slope angle. F is mean catchment dNBR divided by 1000, and S is mean catchment KF-factor. Returns these outputs as numpy 1D arrays with one element per stream segment. Note that input slopes should be slopes gradients, and not angles.

        .. dropdown:: Omit NaN Values

            ::

                M2.variables(..., omitnan)

            Specifies how to treat NaN and NoData values in the slopes, dnbr and kf_factor rasters. The omitnan option may either be a boolean or a dict. In the default setting (omitnan=False), when a raster contains a NaN or Nodata value in a catchment basin, then the associated variable for the basin will be NaN. For example, if the dnbr raster contains NaN in a segment's catchment, then the F variable will be NaN for that segment. If omitnan=True, NaN and NoData values are ignored. Note that if a raster only contains NaN and NoData values in a catchment, then the variable will still be NaN for the catchment.

            If omitnan is a dict, then it may have the keys "slopes", "dnbr", and/or "kf_factor". The value of each key should be a boolean indicating whether to omit NaN and NoData values for that raster. If a key is not included, then the omitnan setting for the raster is set to False. Raises a ValueError if the dict includes other keys.

        :Inputs: * **segments** (*Segments*) -- A Segments object defining a stream segment network
                 * **moderate_high** (*Raster*) -- A raster mask indicating watershed pixels with moderate or high burn severity. True pixels indicate moderate or high severity. False pixels are not burned at these levels.
                 * **slopes** (*Raster*) --- A raster with the slope gradients (not angles) for the watershed
                 * **dnbr** (*Raster*) -- A dNBR raster for the watershed
                 * **kf_factor** (*Raster*) -- A KF-factor raster for the watershed
                 * **omitnan** (*bool*) -- A boolean or dict indicating whether to ignore NaN and NoData values in the slopes, dnbr, and kf_factor rasters

        :Outputs: * *ndarray* -- The terrain variable (T) for each stream segment
                  * *ndarray* -- The fire variable (F) for each stream segment
                  * *ndarray* -- The soil variable (S) for each stream segment


    .. _pfdf.models.staley2017.M2.terrain:

    .. py:method:: terrain(segments, slopes, moderate_high, omitnan = False)
        :staticmethod:

        Computes the M2 terrain variable

        ::

            M2.terrain(segments, slopes, moderate_high)
            M2.terrain(..., omitnan=True)

        Computes the M2 terrain variable. Set omitnan=True to ignore NaN and NoData values in the slopes raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **slope** (*Raster*) -- A slope raster
                 * **moderate_high** (*Raster*) -- Moderate-high burn severity raster mask
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the slopes raster. Default is False

        :Outputs: *ndarray* -- The M2 terrain variable (T)


    .. _pfdf.models.staley2017.M2.fire:

    .. py:method:: fire(segments, dnbr, omitnan = False)
        :staticmethod:

        Computes the M2 fire variable

        ::

            M2.fire(segments, dnbr)
            M2.fire(segments, dnbr, omitnan=True)

        Computes the M2 fire variable. Set omitnan=True to ignore NaN and NoData values in the dNBR raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **dnbr** (*Raster*) -- A dNBR raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the dNBR raster. Default is False.

        :Outputs: *ndarray* -- The M2 fire variable (F)
        

    .. _pfdf.models.staley2017.M2.soil:

    .. py:method:: soil(segments, kf_factor, omitnan = False)
        :staticmethod:

        Computes the M2 soil variable

        ::

            M2.soil(segments, kf_factor)
            M2.soil(..., omitnan=True)
        
        Computes the M2 soil variable. Set omitnan=True to ignore NaN and NoData values in the KF-factor raster.

        :Inputs: * **segments** (*Segments*) --: A stream segment network
                 * **kf_factor** (*Raster*) -- A KF-factor raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the KF-factor raster. Default is False.

        :Outputs: *ndarray* -- The M2 soil variable (S)



.. _pfdf.models.staley2017.M3:

.. py:class:: M3
    :module: pfdf.models.staley2017

    Facilitates the M3 model.

    .. _pfdf.models.staley2017.M3.parameters:

    .. py:method:: parameters(cls, durations = [15, 30, 60])
        :classmethod:

        Return model parameters for the queried durations.

        Terrain (T)
            Topographic ruggedness (vertical relief / sqrt(catchment area))

        Fire (F)
            Proportion of catchment area burned at moderate or high severity

        Soil (S)
            Mean catchment soil thickness / 100

        ----


        .. dropdown:: All Parameters

            ::

                M3.parameters()

            Returns the logistic model intercepts (B), terrain coefficients (Ct), fire coefficients (Cf), and soil coefficients (Cs) for the M3 model (in that order). Each output value is a numpy 1D array with 3 elements. The three elements are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).


        .. dropdown:: Specific Durations

            ::

                M3.parameters(durations)

            Returns values for the queried rainfall durations. Each output value is a numpy 1D array with one element per queried duration. Valid durations to query are 15, 30, and 60.

        :Inputs: * **durations** (*vector*) -- A list of rainfall durations for which to return model parameters

        :Outputs: * *ndarray* -- Logistic model intercepts (B)
                  * *ndarray* -- Terrain coefficients (Ct)
                  * *ndarray* -- Fire coefficients (Cf)
                  * *ndarray* -- Soil coefficients (Cs)


    .. _pfdf.models.staley2017.M3.variables:

    .. py:method:: variables(segments, moderate_high, relief, soil_thickness, relief_per_m = 1, omitnan = False)
        :staticmethod:

        Computes the T, F, and S variables for the M3 model

        .. dropdown:: Compute Variables

            ::

                M3.variables(segments, moderate_high, relief, soil_thickness)
                M3.variables(..., relief_per_m)

            Computes the (T)errain, (F)ire, and (S)oil variables from the M3 model for each stream segment in a network. T is the topographic ruggedness of each segment. This is defined as a segment's vertical relief, divided by the square root of its catchment area. F is the proportion of catchment area burned at moderate or high severity. S is mean catchment soil thickness divided by 100. Returns these outputs as numpy 1D arrays with one element per stream segment.

            By default, the relief dataset is interpreted in units of meters. If this is not the case, use the "relief_per_m" input to specify a conversion factor (number of relief units per meter).

        .. dropdown:: Omit NaN Values

            ::

                M3.variables(..., omitnan)

            Specifies how to treat NaN and NoData values in the soil_thickness raster. The omitnan option may either be a boolean or a dict. In the default setting (omitnan=False), when the soil_thickness raster contains a NaN or Nodata value in a catchment basin, then the S variable for the basin will be NaN. If omitnan=True, NaN and NoData values are ignored. Note that if the soil_thickness raster only contains NaN and NoData values in a catchment, then S will still be NaN for that catchment.

            Alternatively, omitnan may be a dict with the single key "soil_thickness". The value of the key should be a boolean indicating whether to omit NaN and NoData values for the soil_thickness raster. Raises a ValueError if the dict includes other keys.

        :Inputs: * **segments** (*Segments*) -- A Segments object defining a stream segment network
                 * **moderate_high** (*Raster*) -- A raster mask indicating watershed pixels with moderate or high burn severity. True pixels indicate moderate or high severity. False pixels are not burned at these levels.
                 * **relief** (*Raster*) -- A vertical relief raster for the watershed
                 * **soil_thickness** (*Raster*) -- A soil thickness raster for the watershed
                 * **relief_per_m** (*scalar*) -- A conversion factor between relief units and meters
                 * **omitnan** (*bool*) -- A boolean or dict indicating whether to ignore NaN and NoData values in the soil_thickness raster

        :Outputs: * *ndarray* -- The terrain variable (T) for each stream segment
                  * *ndarray* -- The fire variable (F) for each stream segment
                  * *ndarray* -- The soil variable (S) for each stream segment


    .. _pfdf.models.staley2017.M3.terrain:

    .. py:method:: terrain(segments, relief, relief_per_m = 1)
        :staticmethod:

        Computes the M3 terrain variable

        ::
            
            M3.terrain(segments, relief)
            M3.terrain(..., relief_per_m)

        Computes the M3 terrain variable. By default, the relief values are interpreted as meters. If this is not the case, use the "relief_per_m" input to provide a conversion factor (number of relief units per meter). 

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **relief** (*Raster*) -- A vertical relief raster
                 * **relief_per_m** (*scalar*) -- Conversion factor between relief units and meters

        :Outputs: *ndarray* -- The M3 terrain variable (T)
        

    .. _pfdf.models.staley2017.M3.fire:

    .. py:method:: fire(segments, moderate_high)
        :staticmethod:

        Computes the M3 fire variable

        ::

            M3.fire(segments, moderate_high)

        Computes the M3 fire variable.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **moderate_high** (*Raster*) -- A moderate-high burn severity raster mask

        :Outputs: *ndarray* -- The M3 fire variable (F)


    .. _pfdf.models.staley2017.M3.soil:
    
    .. py:method:: soil(segments, soil_thickness, omitnan = False)
        :staticmethod:

        Computes the M3 soil variable

        ::

            M3.soil(segments, soil_thickness)
            M3.soil(..., omitnan=True)

        Computes the M3 soil variable. Set omitnan=True to ignore NaN and NoData values in the soil_thickness raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **soil_thickness** (*Raster*) -- A soil thickness raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the soil thickness raster. Default is False.

        :Outputs: *ndarray* -- The M3 soil variable (S)



.. _pfdf.models.staley2017.M4:

.. py:class:: M4
    :module: pfdf.models.staley2017

    Facilitates the M4 model.

    Terrain (T)
        Proportion of catchment area that both (1) was burned, and (2) has a slope angle >= 30 degrees

    Fire (F)
        Mean catchment dNBR / 1000

    Soil (S)
        Mean catchment soil thickness / 100

    ----


    .. _pfdf.models.staley2017.M4.parameters:

    .. py:method:: parameters(cls, durations = [15, 30, 60])
        :classmethod:

        Return model parameters for the queried durations.

        .. dropdown:: All Parameters

            ::

                M4.parameters()

            Returns the logistic model intercepts (B), terrain coefficients (Ct), fire coefficients (Cf), and soil coefficients (Cs) for the M4 model (in that order). Each output value is a numpy 1D array with 3 elements. The three elements are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).


        .. dropdown:: Specific Durations

            ::

                M4.parameters(durations)

            Returns values for the queried rainfall durations. Each output value is a numpy 1D array with one element per queried duration. Valid durations to query are 15, 30, and 60.

        :Inputs: * **durations** (*vector*) -- A list of rainfall durations for which to return model parameters

        :Outputs: * *ndarray* -- Logistic model intercepts (B)
                  * *ndarray* -- Terrain coefficients (Ct)
                  * *ndarray* -- Fire coefficients (Cf)
                  * *ndarray* -- Soil coefficients (Cs)


    .. _pfdf.models.staley2017.M4.variables:

    .. py:method:: variables(segments, isburned, slopes, dnbr, soil_thickness, omitnan = False)
        :staticmethod:

        Computes the T, F, and S variables for the M4 model

        .. dropdown:: Compute Variables
            
            ::

                M4.variables(segments, isburned, slopes, dnbr, soil_thickness)

            
            Computes the (T)errain, (F)ire, and (S)oil variables from the M4 model for each stream segment in a network. T is the proportion of catchment area that both (1) was burned, and (2) has a slope angle >= 30 degrees. F is mean catchment dNBR / 1000, and S is mean catchment soil thickness divided by 100. Returns these outputs as numpy 1D arrays with one element per stream segment. Note that input slopes should be slope gradients, and not angles.

        .. dropdown:: Omit NaN Values

            ::

                M4.variables(..., omitnan)

            Specifies how to treat NaN and NoData values in the dnbr and soil_thickness rasters. The omitnan option may either be a boolean or a dict. In the default setting (omitnan=False), when a raster contains a NaN or Nodata value in a catchment basin, then the associated variable for the basin will be NaN. For example, if the dnbr raster contains NaN in a segment's catchment, then the F variable will be NaN for that segment. If omitnan=True, NaN and NoData values are ignored. Note that if a raster only contains NaN and NoData values in a catchment, then the variable will still be NaN for the catchment.

            If omitnan is a dict, then it may have the keys "dnbr" and/or "soil_thickness". The value of each key should be a boolean indicating whether to omit NaN and NoData values for that raster. If a key is not included, then the omitnan setting for the raster is set to False. Raises a ValueError if the dict includes other keys.

        :Inputs: * **segments** (*Segments*) -- A Segments object defining a stream segment network
                 * **isburned** (*Raster*) -- A raster mask indicating watershed pixels that were burned (low, moderate or high severity). True elements indicate burned pixels, False elements are not burned.
                 * **slopes** (*Raster*) -- A raster of slope gradients (not angles) for the watershed
                 * **dnbr** (*Raster*) -- A dNBR raster for the watershed
                 * **soil_thickness** (*Raster*) -- A soil thickness raster for the watershed
                 * **omitnan** (*Raster*) -- A boolean or dict indicating whether to ignore NaN and NoData values in the dnbr and soil_thickness rasters

        :Outputs: * *ndarray* -- The terrain variable (T) for each stream segment
                  * *ndarray* -- The fire variable (F) for each stream segment
                  * *ndarray* -- The soil variable (S) for each stream segment

    .. _pfdf.models.staley2017.M4.terrain:

    .. py:method:: terrain(segments, isburned, slopes)
        :staticmethod:

        Computes the M4 terrain variable

        ::

            M4.terrain(segments, isburned, slopes)

        Computes the M4 terrain variable.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **isburned** (*Raster*) -- A burned pixel raster mask
                 * **slopes** (*Raster*) -- A slope raster

        :Outputs: *ndarray* -- The M4 terrain variable (T)


    .. _pfdf.models.staley2017.M4.fire:

    .. py:method:: fire(segments, dnbr, omitnan = False)
        :staticmethod:

        Computes the M4 fire variable

        ::

            M4.fire(segments, dnbr)
            M4.fire(segments, dnbr, omitnan=True)
        
        Computes the M4 fire variable. Set omitnan=True to ignore NaN and NoData values in the dNBR raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **dnbr** (*Raster*) -- A dNBR raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the dNBR raster. Default is False.

        :Outputs: *ndarray* -- The M4 fire variable (F)

    
    .. _pfdf.models.staley2017.M4.soil:

    .. py:method:: soil(segments, soil_thickness, omitnan = False)
        :staticmethod:

        Computes the M4 soil variable

        ::

            M4.soil(segments, soil_thickness)
            M4.soil(..., omitnan=True)

        Computes the M4 soil variable. Set omitnan=True to ignore NaN and NoData values in the soil_thickness raster.

        :Inputs: * **segments** (*Segments*) -- A stream segment network
                 * **soil_thickness** (*Raster*) -- A soil thickness raster
                 * **omitnan** (*bool*) -- True to ignore NaN and NoData values in the soil thickness raster. Default is False.

        :Outputs: *ndarray* -- The M4 soil variable (S)