"""
staley2017  Implements the logistic regression models presented in Staley et al., 2017
----------
BACKGROUND:
This module solves the logistic regression models presented in Staley et al., 2017 
(see citation below). These models describe debris-flow probability as a function 
of terrain (T), fire burn severity (F), soil (S), and rainfall accumulation (R),
such that:

    p = e^X / (1 + e^X)                  Equation 1
    
    X = B + Ct*T*R + Cf*F*R + Cs*S*R

where:
    p is the probability of a debris flow
    T is a terrain variable
    F is a fire severity variable
    S is a soil variable
    R is rainfall accumulation in mm/hour
    B is a model intercept, and
    Ct, Cf, Cs are variable coefficients

The paper details 4 specific probability models, each of which uses a different 
combination of earth-system variables as T, F, and S.

MODULE OVERVIEW:
This module provides two functions that solve models of this form in the forward
and reverse directions. The "probability" function solves the model in the forward
direction - this computes debris-flow probability as a function of rainfall
accumulation using Equation 1.

By contrast, the "accumulation" function determines the rainfall accumulation
needed to cause a debris flow at the specified probability levels. This function
inverts Equation 1, such that:

    R = [ln(p / (1-p)) - B] / (Ct*T + Cf*F + Cs*S)

Both functions can solve for multiple stream segments, parameter values, probability
thresholds, and rainfall accumulations simultaneously. Note that these functions
are generic solvers - as such, they are suitable for any of the 4 models described
in the paper, as well as for any custom models following the form of Equation 1.

In addition to the generic solvers, this module provides the M1, M2, M3, and M4 
model classes, which provide additional support for implementing the 4 specific
models described in the paper. Each class provides a "parameters" method, which 
returns the corresponding B, Ct, Cf, and Cs values published in the paper. Each 
class also provides a "variables" method, which returns the appropriate T, F, 
and S variables for a given set of stream segments. These parameters and variables
can then be used to run the "probability" and/or "accumulation" functions.

EXAMPLE:
This example demonstrates how to use the M1 model to solve for debris-flow
probability and rainfall accumulation. First, use the M1 class to obtain the
parameters and variables needed to implement this model:

    >>> from pfdf.models import staley2017 as s17
    >>> B, Ct, Cf, Cs = s17.M1.parameters()
    >>> T, F, S = s17.M1.variables(segments, <other args>)

Note that the first input to any model's "variables" method is always a 
pfdf.segments.Segments describing a particular stream segment network. The subsequent
inputs will vary, as each model is calibrated to a different set of earth
system variables.
    
Then, to solve for probability given rainfall accumulations:

    >>> R = [0.1, 0.2, 0.3]
    >>> p = s17.probability(R, B, Ct, T, Cf, F, Cs, S)

Or to solve for accumulation given probabilities:

    >>> p = [0.5, 0.75]
    >>> R = s17.accumulation(p, B, Cr, T, Cf, F, Cs, S)

NOTE ON RASTER SHAPES:
Each model's "variables" method uses a pfdf.segments.Segments object to
calculate values from various input rasters. As such, the associated input rasters
must always match the raster shape, crs, and (affine) transform associated with the
stream segment raster.

DESIGNING NEW MODELS:
Advanced users may be interested in implementing new models that follow the form
of Equation 1. Because the "probability" and "accumulation" functions are generalized,
you can them to implement these model variants - to do so, provide the custom
coefficients and variables to a function, and run as usual.

CITATION:
Staley, D. M., Negri, J. A., Kean, J. W., Laber, J. L., Tillery, A. C., & 
Youberg, A. M. (2017). Prediction of spatially explicit rainfall intensity–duration
thresholds for post-fire debris-flow generation in the western United States. 
Geomorphology, 278, 149-162.
https://doi.org/10.1016/j.geomorph.2016.10.019
----------
*FOR USERS*

Key Functions:
    probability         - Solves for debris-flow probabilities given rainfall accumulations
    accumulation        - Solves for the rainfall accumulations needed to achieve given probability levels

Model Classes:
    M1, M2, M3, M4      - Classes that implement the 4 models described in Staley et al., 2017
    .parameters(...)    - Return a model's B, Ct, Cf, and Cs parameters for queried rainfall durations
    .variables(...)     - Calculate the T, F, and S variables for a model
    Model               - Abstract base class implementing common functionality for the M1-4 models

Internal:
    _validate           - Validates parameters/variables and reshapes for broadcasting
    _clean_dimensions   - Optionally removes trailing singleton dimensions
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from pfdf._utils import nodata_, real, validate
from pfdf.errors import DurationsError, ShapeError
from pfdf.raster import Raster, RasterInput
from pfdf.segments import Segments
from pfdf.typing import (
    Accumulations,
    BooleanMask,
    Durations,
    Parameters,
    Pvalues,
    S17ModelParameters,
    S17ModelVariables,
    SegmentAccumulations,
    SegmentPvalues,
    Variables,
)
from pfdf.utils import slope

#####
# Generic solvers
#####


def accumulation(
    p: Pvalues,
    B: Parameters,
    Ct: Parameters,
    T: Variables,
    Cf: Parameters,
    F: Variables,
    Cs: Parameters,
    S: Variables,
    *,
    always_3d: bool = False,
) -> SegmentAccumulations:
    """
    accumulation  Computes rainfall accumulations needed for specified debris-flow probability levels
    ----------
    accumulation(p, B, Ct, T, Cf, F, Cs, S)
    Returns the rainfall accumulations required to achieve the specified p-values.
    This function is agnostic to the actual model being run, and thus can
    implement all 4 of the models presented in the paper (as well as any other
    model following the form of Equation 1).

    All of the inputs to this function should be real-valued numpy arrays.
    The three variables - T, F, and S - represent the terrain steepness,
    wildfire severity, and surface properties variables for the model. In
    most cases, these are 1D arrays with one element per stream segment
    being assessed. Variables can also be 2D arrays - see below for details
    for this less common use case.

    The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic
    model link equation. B is the intercept, and each C parameter
    is the coefficient of the associated variable. The parameters should be
    numpy 1D arrays with one element per run of the hazard assessment model.
    Here, we define a "run" as an implementation of the hazard model using a
    unique set of logistic model parameters. A common use case is solving the
    model for multiple rainfall durations (for example, 15, 30, and 60 minute
    intervals). In the example with 3 durations, each parameter should have
    3 elements - each element corresponds to the parameter value appropriate
    for a particular rainfall duration. Another use case for multiple runs
    is for Monte Carlo validation of one or more model parameters.

    The p-values - p - are the probabilities for which the model should be solved.
    For example, p=0.5 solves for the rainfall intensities that cause a 50%
    likelihood of a debris-flow. p should be a 1D array listing all the
    probabilities that should be solved for.

    This function solves the rainfall accumulations for all stream segments,
    parameter runs, and p-values provided. Each accumulation describes the total
    rainfall required within the rainfall duration associated with its parameters.
    For example, if using parameters for a 15-minute rainfall duration, the accumulation
    describes the total rainfall required within a 15-minute window. Accumulation
    units are the units of the rainfall values used to calibrate the model's parameters.
    For the 4 models described in the paper, accumulations are in mm.

    The returned output will be a 3D numpy array. The first dimension is
    stream segments, second dimension is parameter runs, and third dimension is
    p-values. If only a single p-value is provided, the output is returned as a
    2D array. If there is a single parameter run and a single p-value, then output
    is returned as a 1D array. (Or see below for an option that always returns a 3D array).

    As mentioned, one or more variable can also be a 2D array. In this case
    each row is a stream segment, and each column is a parameter run. Each
    column will be used to solve the model for (only) the associated parameter
    run. This allows use of different values for a variable. An example use
    case could be testing the model using different datasets to derive one or
    more variables.

    accumulation(..., *, always_3d = True)
    Always returns the output as a 3D numpy array, regardless of the number
    of p-values and parameter runs.
    ----------
    Inputs:
        p: The probabilities for which to solve the model
        B: The intercepts of the link equation
        Ct: The coefficients for the terrain steepness variable
        T: The terrain steepness variable
        Cf: The coefficients for the wildfire severity variable
        F: The wildfire severity variable
        Cs: The coefficients for the surface properties variable
        S: The surface properties variable
        always_3d: True to always return a 3D numpy array. If false (default),
            returns a 2D array when there is 1 p-value, and a 1D array if there
            is 1 p-value and 1 parameter run.

    Outputs:
        numpy 3D array (Segments x Parameter Runs x P-values): The rainfall
            accumulations required to achieve the specified p-values.
    """

    # Validate and reshape for broadcasting.
    p, B, Ct, Cf, Cs, T, F, S = _validate(p, "p", B, Ct, Cf, Cs, T, F, S)
    validate.inrange(p, "p", min=0, max=1, nodata=np.nan)

    # Solve the model
    numerator = np.log(p / (1 - p)) - B
    denominator = Ct * T + Cf * F + Cs * S
    accumulation = numerator / denominator

    # Optionally remove trailing singletons
    accumulation = _clean_dimensions(accumulation, always_3d)
    return accumulation


def probability(
    R: Accumulations,
    B: Parameters,
    Ct: Parameters,
    T: Variables,
    Cf: Parameters,
    F: Variables,
    Cs: Parameters,
    S: Variables,
    *,
    always_3d: bool = False,
) -> SegmentPvalues:
    """
    probability  Computes debris-flow probability for the specified rainfall durations
    ----------
    probability(R, B, Ct, T, Cf, F, Cs, S)
    Solves the debris-flow probabilities for the specified rainfall accumulations.
    This function is agnostic to the actual model being run, and thus can
    implement all 4 of the models presented in the paper (as well as any other
    model following the form of Equation 1).

    All of the inputs to this function should be real-valued numpy arrays.
    The three variables - T, F, and S - represent the terrain steepness,
    wildfire severity, and surface properties variables for the model. In
    most cases, these are 1D arrays with one element per stream segment
    being assessed. Variables can also be 2D arrays - see below for details
    for this less common use case.

    The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic
    model link equation. B is the intercept, and each C parameter
    is the coefficient of the associated variable. The parameters should be
    numpy 1D arrays with one element per run of the hazard assessment model.
    Here, we define a "run" as an implementation of the hazard model using a
    unique set of logistic model parameters. A common use case is solving the
    model for multiple rainfall durations (for example, 15, 30, and 60 minute
    intervals). In the example with 3 durations, each parameter should have
    3 elements - each element corresponds to the parameter value appropriate
    for a particular rainfall duration. Another use case for multiple runs
    is for Monte Carlo validation of one or more model parameters.

    The p-values - p - are the probabilities for which the model should be solved.
    For example, p=0.5 solves for the rainfall intensities that cause a 50%
    likelihood of a debris-flow. p should be a 1D array listing all the
    probabilities that should be solved for.

    This function solves the rainfall accumulations for all stream segments,
    parameter runs, and rainfall accumulations provided. Note that rainfall
    accumulations should be relative to the rainfall durations associated with
    each set of parameters. For example, if using parameters for 15-minute and
    30-minute rainfall durations, then input accumulations should be for 15-minute
    and 30-minute intervals, respectively. Accumulation units are the units of the
    rainfall values used to calibrate the model's parameters. For the 4 models
    described in the paoer, accumulations are in mm.

    The returned output will be a 3D numpy array. The first dimension is
    stream segments, second dimension is parameter runs, and third dimension is
    queried rainfall accumulations. If only a single accumulation is provided,
    the output is returned as a 2D array. If there is a single parameter run and
    a single rainfall accumulation, then output is returned as a 1D array. (Or
    see below for an option that always returns a 3D array).

    As mentioned, one or more variable can also be a 2D array. In this case
    each row is a stream segment, and each column is a parameter run. Each
    column will be used to solve the model for (only) the associated parameter
    run. This allows use of different values for a variable. An example use
    case could be testing the model using different datasets to derive one or
    more variables.

    accumulation(..., *, always_3d = True)
    Always returns the output as a 3D numpy array, regardless of the number
    of p-values and parameter runs.
    ----------
    Inputs:
        R: The rainfall accumulations for which to solve the model
        B: The intercepts of the link equation
        Ct: The coefficients for the terrain steepness variable
        T: The terrain steepness variable
        Cf: The coefficients for the wildfire severity variable
        F: The wildfire severity variable
        Cs: The coefficients for the surface properties variable
        S: The surface properties variable
        always_3d: True to always return a 3D numpy array. If false (default),
            returns a 2D array when there is 1 p-value, and a 1D array if there
            is 1 p-value and 1 parameter run.

    Outputs:
        numpy 3D array (Segments x Parameter Runs x P-values): The rainfall
            accumulations required to achieve the specified p-values.
    """

    # Validate and reshape for broadcasting.
    R, B, Ct, Cf, Cs, T, F, S = _validate(R, "R", B, Ct, Cf, Cs, T, F, S)
    validate.positive(R, "R", allow_zero=True, nodata=np.nan)

    # Solve the model
    eX = np.exp(B + Ct * T * R + Cf * F * R + Cs * S * R)
    probability = eX / (1 + eX)

    # Optionally remove trailing singletons
    probability = _clean_dimensions(probability, always_3d)
    return probability


def _validate(PR, PRname, B, Ct, Cf, Cs, T, F, S):
    "Validates parameters and variables and reshapes for broadcasting"

    # Validate parameter vectors
    vectors = {PRname: PR, "B": B, "Ct": Ct, "Cf": Cf, "Cs": Cs}
    for name, value in vectors.items():
        vectors[name] = validate.vector(value, name, dtype=real)

    # Validate variable matrices
    variables = {"T": T, "F": F, "S": S}
    for name, value in variables.items():
        variables[name] = validate.matrix(value, name, dtype=real)

    # Get sizes
    nQueries = vectors[PRname].size
    nRuns = vectors["B"].size
    nSegments = variables["T"].shape[0]

    # Process vectors. Reshape p for broadcasting....
    for name, value in vectors.items():
        if name == PRname:
            vectors[name] = value.reshape(1, 1, nQueries)

        # Check parameters have the same number of runs
        elif value.size != nRuns:
            raise ShapeError(
                f"Model parameters (B, Ct, Cf, Cs) must have the same number of elements (runs). "
                f"But B has {nRuns} element(s), whereas {name} has {value.size}."
            )

        # Reshape parameters for broadcasting
        else:
            vectors[name] = value.reshape(1, nRuns, 1)

    # Check that variables have the same number of rows, and either 1 or nRuns columns
    for name, value in variables.items():
        nrows, ncols = value.shape
        if nrows != nSegments:
            raise ShapeError(
                f"Variables (T, F, S) must have the same number of rows (stream segments). "
                f"But T has {nSegments} row(s), whereas {name} has {value.shape[0]}."
            )
        elif ncols != 1 and ncols != nRuns:
            raise ShapeError(
                f"Variables (T, F, S) must have either 1 or {nRuns} columns. "
                f"But {name} has {value.shape[1]} column(s)."
            )

        # Reshape variables for broadcasting
        variables[name] = value.reshape(nrows, ncols, 1)

    # Return direct references to values (makes the math look nicer)
    PR, B, Ct, Cf, Cs = vectors.values()
    T, F, S = variables.values()
    return PR, B, Ct, Cf, Cs, T, F, S


def _clean_dimensions(output, always_3d):
    "Optionally removes trailing singleton dimensions"

    if not always_3d:
        output = np.atleast_1d(np.squeeze(output))
    return output


#####
# Model classes
#####


class Model(ABC):
    """
    Model  An abstract base class for the 4 logistic models from Staley et al., 2017
    ----------
    The class provides an interface for some of the common patterns between the
    the 4 logistic models. It defines the rainfall durations used to calibrate
    parameters, and provides a function to query model parameters for a given
    set of durations. The class also requires each concrete model to define a
    "variables" function that calculates the (T)errain, (F)ire, and (S)oil
    variables required to run the model.
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters

    Abstract Properties:
        B               - Logistic Model intercepts
        Ct              - Coefficients for the (t)errain variable
        Cf              - Coefficients for the (f)ire variable
        Cs              - Coefficients for the (s)oil variable

    Class Methods:
        parameters      - Returns the model parameters for a queried set of durations

    Abstract Methods:
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments

    Static Methods:
        _validate       - Validates a Segments object and input raster for calculating variables
        _terrain_mask   - Locates pixels that are sufficiently burned and steep
    """

    # The rainfall durations used to calibrate model parameters
    durations = [15, 30, 60]

    # Model parameters: Each concrete model should define these. Each property
    # should have 3 elements and follow the order of the above durations
    B = None  # Logistic model intercepts
    Ct = None  # Terrain coefficients
    Cf = None  # Fire coefficients
    Cs = None  # Soil coefficients

    @classmethod
    def parameters(cls, durations: Durations = durations) -> S17ModelParameters:
        """
        parameters  Return model parameters for the queried durations.
        ----------
        Model.parameters()
        Returns the logistic model intercepts (B), terrain coefficients (Ct),
        fire coefficients (Cf), and soil coefficients (Cs) for a model (in that order).
        Each output value is a numpy 1D array with 3 elements. The three elements
        are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).

        Model.parameters(durations)
        Returns values for the queried rainfall durations. Each output value is a
        numpy 1D array with one element per queried duration. Valid durations to
        query are 15, 30, and 60.
        ----------
        Inputs:
            durations: A list of rainfall durations for which to return model parameters

        Outputs:
            numpy 1D array: Logistic model intercepts (B)
            numpy 1D array: Terrain coefficients (Ct)
            numpy 1D array: Fire coefficients (Cf)
            numpy 1D array: Soil coefficients (Cs)
        """

        # Validate durations
        durations = validate.vector(durations, "durations", dtype=real)
        valid = np.isin(durations, cls.durations)
        if not all(valid):
            bad = np.argwhere(valid == 0)[0][0]
            allowed = ", ".join([str(value) for value in cls.durations])
            raise DurationsError(
                f"Duration {bad} ({durations[bad]}) is not a supported value. "
                f"Supported values are: {allowed}"
            )

        # Get duration indices
        indices = np.empty(durations.shape, dtype=int)
        for d, duration in enumerate(cls.durations):
            elements = np.argwhere(durations == duration)
            indices[elements] = d

        # Get parameters at the specified duration indices
        parameters = [cls.B, cls.Ct, cls.Cf, cls.Cs]
        return (np.array(values)[indices] for values in parameters)

    @classmethod
    @abstractmethod
    def variables(cls, segments: Segments, *args, **kwargs) -> S17ModelVariables:
        """
        variables  Returns terrain, fire, and soil variables for a model
        ----------
        Model.variables(segments, ...)
        Given a set of stream segments, returns a dict with the terrain (T),
        fire (F), and soil (S) variables needed to run the model. Each value in
        the dict is a numpy 1D array with one element per stream segment.
        ----------
        Inputs:
            segments: A set of stream segments
            *args, **kwargs: These will vary by model.

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

    @staticmethod
    def _validate(segments: Any, rasters: list[Any], names: list[str]) -> list[Raster]:
        "Validates segments object and rasters for calculating variables"

        # Require a Segments object
        if not isinstance(segments, Segments):
            raise TypeError("segments must be a pfdf.segments.Segments object")

        # Rasters must be valid and match the stream segment metadata
        for r, raster, name in zip(range(len(rasters)), rasters, names):
            rasters[r] = segments._validate(raster, name)
        return rasters

    @staticmethod
    def _terrain_mask(
        burned: Raster, slopes: Raster, threshold_degrees: float
    ) -> BooleanMask:
        "Returns a mask of pixels that are sufficiently burned, and that have"
        "slopes steeper than a threshold"

        # Validate burn mask and convert threshold from degrees to gradient
        burned = validate.boolean(burned.values, burned.name, nodata=burned.nodata)
        threshold = slope.from_degrees(threshold_degrees)

        # Build the mask. Preserve NoData
        mask = burned & (slopes.values >= threshold)
        if slopes.nodata is not None:
            nodatas = nodata_.mask(slopes.values, slopes.nodata)
            mask[nodatas] = False
        return mask


class M1(Model):
    """
    M1  Implements the M1 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

        T: The proportion of catchment area with both (1) moderate or high burn
           severity, and (2) slope angle >= 23 degrees

        F: Mean catchment dNBR / 1000

        S: Mean catchment KF-factor
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic Model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters (15, 30, 60 minute)
    B = [-3.63, -3.61, -3.21]
    Ct = [0.41, 0.26, 0.17]
    Cf = [0.67, 0.39, 0.20]
    Cs = [0.70, 0.50, 0.220]

    @classmethod
    def variables(
        cls,
        segments: Segments,
        moderate_high: RasterInput,
        slopes: RasterInput,
        dnbr: RasterInput,
        kf_factor: RasterInput,
    ) -> S17ModelVariables:
        """
        variables  Computes the T, F, and S variables for the M1 model
        ----------
        M1.variables(segments, moderate_high, slopes, dnbr, kf_factor)
        Computes the (T)errain, (F)ire, and (S)oil variables from the M1 model
        for each stream segment in a network. T is the proportion of catchment
        area that has both (1) moderate or high burn severity, and (2) a slope
        angle >= 23 degrees. F is mean catchment dNBR divided by 1000. S is
        mean catchment KF-factor. Returns these outputs as numpy 1D arrays with
        one element per stream segment. Note that input slopes should be slope
        gradients, and not slope angles.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            moderate_high: A Raster mask indicating watershed pixels with
                moderate or high burn severity. True pixels indicate moderate or
                high severity. False pixels are not burned at these levels.
            slopes: A Raster with the slope gradients (not angles) for the
                watershed. NoData pixels are interpreted as locations with slope
                angles less than 23 degrees.
            dnbr: A dNBR raster for the watershed
            kf_factor: A KF-factor raster for the watershed

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate segments and rasters
        moderate_high, slopes, dnbr, kf_factor = cls._validate(
            segments,
            [moderate_high, slopes, dnbr, kf_factor],
            ["moderate_high", "slopes", "dnbr", "kf_factor"],
        )

        # Get variables
        mask = cls._terrain_mask(moderate_high, slopes, threshold_degrees=23)
        T = segments.upslope_ratio(mask)
        F = segments.scaled_dnbr(dnbr)
        S = segments.kf_factor(kf_factor)
        return T, F, S


class M2(Model):
    """
    M2  Implements the M2 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

        T: The mean sin(theta) of catchment area burned at moderate or high.
           Note that theta is the slope angle.

        F: Mean catchment dNBR / 1000

        S: Mean catchment KF-factor
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic Model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters (15, 30, 60 minute)
    B = [-3.62, -3.61, -3.22]
    Ct = [0.64, 0.42, 0.27]
    Cf = [0.65, 0.38, 0.19]
    Cs = [0.68, 0.49, 0.22]

    @classmethod
    def variables(
        cls,
        segments: Segments,
        moderate_high: RasterInput,
        slopes: RasterInput,
        dnbr: RasterInput,
        kf_factor: RasterInput,
    ) -> S17ModelVariables:
        """
        variables  Computes the T, F, and S variables for the M2 model
        ----------
        M2.variables(segments, moderate_high, slopes, dnbr, kf_factor)
        Computes the (T)errain, (F)ire, and (S)oil variables from the M2 model
        for each stream segment in a network. T is the mean sin(theta) of catchment
        area burned at moderate or high severity, where theta is the slope angle.
        F is mean catchment dNBR divided by 1000, and S is mean catchment KF-factor.
        Returns these outputs as numpy 1D arrays with one element per stream segment.
        Note that input slopes should be slopes gradients, and not angles.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            moderate_high: A Raster mask indicating watershed pixels with
                moderate or high burn severity. True pixels indicate moderate or
                high severity. False pixels are not burned at these levels.
            slopes: A raster with the slope gradients (not angles) for the watershed
            dnbr: A dNBR raster for the watershed
            kf_factor: A KF-factor raster for the watershed

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate segments and rasters
        moderate_high, slopes, dnbr, kf_factor = cls._validate(
            segments,
            [moderate_high, slopes, dnbr, kf_factor],
            ["moderate_high", "slopes", "dnbr", "kf_factor"],
        )

        # Get variables
        slopes = slope.to_sine(slopes.values)
        T = segments.sine_theta(slopes, mask=moderate_high)
        F = segments.scaled_dnbr(dnbr)
        S = segments.kf_factor(kf_factor)
        return T, F, S


class M3(Model):
    """
    M3  Implements the M3 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

        T: Topographic ruggedness (vertical relief divided by the square root
           of catchment area)

        F: The proportion of catchment area burned at moderate or high severity

        S: Mean catchment soil thickness / 100
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic Model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters (15, 30, 60 minute)
    B = [-3.71, -3.79, -3.46]
    Ct = [0.32, 0.21, 0.14]
    Cf = [0.33, 0.19, 0.10]
    Cs = [0.47, 0.36, 0.18]

    @classmethod
    def variables(
        cls,
        segments: Segments,
        moderate_high: RasterInput,
        relief: RasterInput,
        soil_thickness: RasterInput,
    ) -> S17ModelVariables:
        """
        variables  Computes the T, F, and S variables for the M3 model
        ----------
        M3.variables(segments, moderate_high, relief, soil_thickness)
        Computes the (T)errain, (F)ire, and (S)oil variables from the M3 model
        for each stream segment in a network. T is the topographic ruggedness of
        each segment. This is defined as a segment's vertical relief, divided by
        the square root of its catchment area. F is the proportion of catchment
        area burned at moderate or high severity. S is mean catchment soil thickness
        divided by 100. Returns these outputs as numpy 1D arrays with one element
        per stream segment.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            moderate_high: A Raster mask indicating watershed pixels with
                moderate or high burn severity. True pixels indicate moderate or
                high severity. False pixels are not burned at these levels.
            relief: A vertical relief raster for the watershed
            soil_thickness: A soil thickness raster for the watershed

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate segments and rasters
        moderate_high, relief, soil_thickness = cls._validate(
            segments,
            [moderate_high, relief, soil_thickness],
            ["moderate_high", "relief", "soil_thickness"],
        )

        # Get variables
        T = segments.ruggedness(relief)
        F = segments.upslope_ratio(moderate_high)
        S = segments.scaled_thickness(soil_thickness)
        return T, F, S


class M4(Model):
    """
    M4  Implements the M4 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

        T: The proportion of catchment area that both (1) was burned and (2) has
           a slope angle >= 30 degrees

        F: Mean catchment dNBR / 1000

        S: Mean catchment soil thickness / 100
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic Model intercepts
        Ct              - Terrain coefficients
        Cf              - Fire coefficients
        Cs              - Soil coefficients

    Methods:
        parameters      - Returns model parameters for the queried rainfall durations
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments
    """

    # Model parameters (15, 30, 60 minute)
    B = [-3.60, -3.64, -3.30]
    Ct = [0.51, 0.33, 0.20]
    Cf = [0.82, 0.46, 0.24]
    Cs = [0.27, 0.26, 0.13]

    @classmethod
    def variables(
        cls,
        segments: Segments,
        isburned: RasterInput,
        slopes: RasterInput,
        dnbr: RasterInput,
        soil_thickness: RasterInput,
    ) -> S17ModelVariables:
        """
        variables  Computes the T, F, and S variables for the M4 model
        ----------
        M4.variables(segments, isburned, slopes, dnbr, soil_thickness)
        Computes the (T)errain, (F)ire, and (S)oil variables from the M4 model
        for each stream segment in a network. T is the proportion of catchment
        area that both (1) was burned, and (2) has a slope angle >= 30 degrees.
        F is mean catchment dNBR / 1000, and S is mean catchment soil thickness
        divided by 100. Returns these outputs as numpy 1D arrays with one element
        per stream segment. Note that input slopes should be slope gradients, and
        not angles.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            isburend: A Raster mask indicating watershed pixels that were burned
                (low, moderate or high severity). True elements indicate burned
                pixels, False elements are not burned.
            slopes: A raster of slope gradients (not angles) for the watershed
            dnbr: A dNBR raster for the watershed
            soil_thickness: A soil thickness raster for the watershed

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate segments and rasters
        isburned, slopes, dnbr, soil_thickness = cls._validate(
            segments,
            [isburned, slopes, dnbr, soil_thickness],
            ["isburned", "slopes", "dnbr", "soil_thickness"],
        )

        # Get variables
        mask = cls._terrain_mask(isburned, slopes, threshold_degrees=30)
        T = segments.upslope_ratio(mask)
        F = segments.scaled_dnbr(dnbr)
        S = segments.scaled_thickness(soil_thickness)
        return T, F, S
