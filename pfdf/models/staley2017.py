"""
staley2017  Implements the logistic regression models presented in Staley et al., 2017
----------
This module solves the logistic regression models presented in Staley et al., 2017 
(see citation below) - specifically, these are logistic models of form:

    R = [ln(p / (1-p)) - B] / (Ct*T + Cf*F + Cs*S)          Equation 1

where:
  p is the probability of an event
  B is the model intercept
  T is a terrain variable
  F is a wildfire variable
  S is a soil variable, and
  Ct, Cf, Cs are variable coefficients

The solution of the model (R) is the rainfall accumulation needed to cause a debris-flow
at the specified probability level. The "solve" function provides a generalized
solution to logistic models of this form, and can solve for multiple stream segments,
parameter values, and probability thresholds simultaneously.

The M1, M2, M3, and M4 model classes provide additional support for implementing
the four specific models described in the paper. Each class provides a "parameters"
method, which returns the appropriate B, Ct, Cf, and Cs values published in the paper. 
Each class also provides a "variables" method, which returns the T, F, and S
variables for a given set of stream segments. For example, to obtain the terms for
the M1 model, use:

    >>> from pfdf.models import staley2017 as s17
    >>> parameters = s17.M1.parameters()
    >>> variables = s17.M1.variables(...)

Note that the outputs of the "parameters" and "variables" methods are dicts whose
keys are the corresponding terms of the model. Continuing the example:

    >>> B, Ct, Cf, Cs = parameters.values()
    >>> T, F, S = variables.values()

We re-emphasize that the "solve" function provides a general solutiofn to Equation
1, so users are not required to use any of the M1-4 models. Rather, they are
a convenience for common use cases. We recommend users read a model's documentation
for additional details on its implementation and use.

NOTE ON RASTER SHAPES:
Many commands in this module compute values for a set of stream segments using
various input rasters. When this is the case, the shape of the input rasters
should match the shape of the stream raster used to define the segments.

DESIGNING NEW MODELS:
Advanced users may be interested in implementing new models that follow the form
of Equation 1. Because the "solve" function is generalized, you can use it to
implement these model variants - to do so, provide the updated coefficients
and/or variables to the function, and run as usual.

Such users may also be interested in the "burn_gradient", "kf_factor", "ruggedness", 
"scaled_dnbr", "scaled_thickness", and "upslope_ratio" functions. These lower-level
functions are used to calculate the individual variables for the M1-4 models, and
may faciliate the calculation of variables for model variants. We note that
"upslope_ratio" is generalizable to a number of variables, including M1-T, M2-F,
and M4-T. Also note that each of these functions computes values over a set of
stream segments.

CITATION:
Staley, D. M., Negri, J. A., Kean, J. W., Laber, J. L., Tillery, A. C., & 
Youberg, A. M. (2017). Prediction of spatially explicit rainfall intensity–duration
thresholds for post-fire debris-flow generation in the western United States. 
Geomorphology, 278, 149-162.
https://doi.org/10.1016/j.geomorph.2016.10.019
----------
*FOR USERS*

Key Functions:
    solve               - Solves a debris-flow logistic model for a set of stream segments

Model Classes:
    M1, M2, M3, M4      - Classes that implement the 4 models described in Staley et al., 2017
    .parameters()       - Return the associated parameters for a model
    .variables()        - Return the associated variables for a model

Individual Variables:
    burn_gradient       - Returns the mean gradient of catchment pixels burned at a given severity level
    kf_factor           - Returns the mean catchment KF-factor
    ruggedness          - Returns topographic ruggedness
    scaled_dnbr         - Returns mean catchment dNBR / 1000
    scaled_thickness    - Returns mean catchment soil thickness / 100
    upslope_ratio       - Returns the proportion of upslope pixels that meet some criteria

*INTERNAL*

Abstract Base Class:
    Model               - Provides common functionality for the M1-4 model classes

Aliases:
    _kf_factor          - An alias for the kf_factor function
"""

from abc import ABC, abstractmethod
from typing import Dict

import numpy as np

from pfdf import _validate as validate
from pfdf._utils import real
from pfdf.errors import DurationsError
from pfdf.rasters import Raster
from pfdf.segments import Segments
from pfdf.typing import (
    Accumulations,
    Durations,
    DurationValues,
    Parameters,
    Pvalues,
    SegmentValues,
    Variables,
)

# Type aliases
ParameterDict = Dict[str, DurationValues]
VariableDict = Dict[str, SegmentValues]


#####
# Logistic model solver
#####


def solve(
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
) -> Accumulations:
    """
    solve  Computes rainfall accumulations by solving the logistic model from Staley et al., 2017
    ----------
    solve(p, B, Ct, T, Cf, F, Cs, S)
    Solves the logistic model from Staley et al., 2017 (Equation 5). Returns
    the rainfall accumulations required to achieve the specified p-values.
    This function is agnostic to the actual model being run, and thus can
    implement all 4 of the models presented in the paper (as well as any other
    model following the form of Equation 5).

    All of the inputs to this function should be real-valued numpy arrays.
    The three variables - T, F, and S - represent the terrain steepness,
    wildfire severity, and surface properties variables for the model. In
    most cases, these are 1D arrays with one element per stream segment
    being assessed. Variables can also be 2D arrays - see below for details
    for this less common use case.

    The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic
    model link equation (Equation 4). B is the intercept, and each C parameter
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
    is returned as a 1D array. (And see below for an option that always returns a 3D array).

    As mentioned, one or more variable can also be a 2D array. In this case
    each row is a stream segment, and each column is a parameter run. Each
    column will be used to solve the model for (only) the associated parameter
    run. This allows use of different values for a variable. An example use
    case could be testing the model using different datasets to derive one or
    more variables.

    solve(..., *, always_3d = True)
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

    # Validate vectors
    vectors = {"p": p, "B": B, "Ct": Ct, "Cf": Cf, "Cs": Cs}
    for name, value in vectors.items():
        vectors[name] = validate.vector(value, name, dtype=real)

    # Validate variable matrices
    variables = {"T": T, "F": F, "S": S}
    for name, value in variables.items():
        variables[name] = validate.matrix(value, name, dtype=real)

    # Get sizes
    nPvalues = vectors["p"].size
    nRuns = vectors["B"].size
    nSegments = variables["T"].shape[0]

    # Process vectors. Reshape p for broadcasting....
    for name, value in vectors.items():
        if name == "p":
            vectors[name] = value.reshape(1, 1, nPvalues)

        # Check parameters have the same number of runs
        elif value.size != nRuns:
            raise ValueError(
                f"Model parameters (B, Ct, Cf, Cs) must have the same number of elements (runs). "
                f"But B has {B.size} element(s), whereas {name} has {value.size}."
            )

        # Reshape parameters for broadcasting
        else:
            vectors[name] = value.reshape(1, nRuns, 1)

    # Check that variables have the same number of rows, and either 1 or nRuns columns
    for name, value in variables.items():
        nrows, ncols = value.shape
        if nrows != nSegments:
            raise ValueError(
                f"Variables (T, F, S) must have the same number of rows (stream segments). "
                f"But T has {nSegments} row(s), whereas {name} has {value.shape[0]}."
            )
        elif ncols != 1 and ncols != nRuns:
            raise ValueError(
                f"Variables (T, F, S) must have either 1 or {nRuns} columns. "
                f"But {name} has {value.shape[1]} column(s)."
            )

        # Reshape variables for broadcasting
        variables[name] = value.reshape(nrows, ncols, 1)

    # Get direct references to variables (makes the math look nicer)
    p, B, Ct, Cf, Cs = vectors.values()
    T, F, S = variables.values()

    # Solve the model
    numerator = np.log(p / (1 - p)) - B
    denominator = Ct * T + Cf * F + Cs * S
    rainfall = numerator / denominator

    # Optionally remove trailing singletons
    if not always_3d:
        rainfall = np.atleast_1d(np.squeeze(rainfall))
    return rainfall


#####
# Variables
#####


def burn_gradient(
    segments: Segments,
    flow_directions: Raster,
    gradient: Raster,
    isburned: Raster,
    *,
    check: bool = True,
) -> SegmentValues:
    """
    burn_gradient  Returns the mean gradient of upslope pixels burned at a given severity
    ----------
    burn_gradient(segments, flow_directions, gradients, isburned)
    Computes the mean gradient of upslope pixels burned at a given severity for
    each stream segment. Note that gradients are defined as sin(theta) here.
    Returns a numpy 1D array with the gradient for each segment.

    burn_gradient(..., *, check=False)
    Disables validation checks of input rasters. This can speed up the
    processing of large rasters, but may produce unexpected results if any
    of the input rasters contain invalid values.
    ----------
    Inputs:
        segments: A set of stream segments
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels.
        gradients: A raster holding the gradients - sin(theta) - for the DEM pixels.
        isburned: A raster indicating the DEM pixels that are burned at the
            desired severity level. Pixels meeting the criteria should have a
            value of 1. All other pixels should be 0.
        check: True (default) to validate input rasters before processing.
            False to disable these checks.

    Outputs:
        numpy 1D array: The mean gradients for the stream segments.
    """

    return segments.catchment_mean(
        flow_directions,
        gradient,
        mask=isburned,
        check=check,
    )


def _kf_factor(*args, **kwargs) -> SegmentValues:
    """This function is just an alias to kf_factor. It exists so that users can
    use kf_factor to refer to variables in functions that also call the
    kf_factor function."""
    return kf_factor(*args, **kwargs)


def kf_factor(
    segments: Segments,
    npixels: SegmentValues,
    flow_directions: Raster,
    kf_factor: Raster,
    *,
    check: bool = True,
) -> SegmentValues:
    """
    kf_factor  Returns the mean KF-Factor for a set of stream segment catchments
    ----------
    kf_factor(segments, npixels, flow_directions, kf_factor)
    Computes the mean KF-factors for a set of stream segments. Mean KF-factor is
    calculated over the full catchment area of each stream segment.

    kf_factor(..., *, check=False)
    Disables validation checks of input rasters. This can speed up the
    processing of large rasters, but may produce unexpected results if any
    of the input rasters contain invalid values.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels.
        kf_factor: A raster holding KF-factor values for the DEM pixels.
        check: True (default) to validate input rasters before processing.
            False to disable these checks.

    Outputs:
        numpy 1D array: The mean KF-factor for each stream segment.
    """

    return segments.catchment_mean(
        flow_directions,
        values=kf_factor,
        npixels=npixels,
        check=check,
    )


def ruggedness(
    segments: Segments,
    areas: SegmentValues,
    relief: Raster,
) -> SegmentValues:
    """
    ruggedness  Computes topographic ruggedness for a set of stream segments
    ----------
    ruggedness(segments, areas, relief)
    Computes topographic ruggedness for a set of stream segments. Ruggedness
    is calculated via:

        Ruggedness = vertical relief / sqrt(upslope area)

    Returns the ruggedness values as a numpy 1D array.
    ----------
    Inputs:
        segments: A set of stream segments
        areas: The total upslope area of each stream segment (as determined
            for the most downstream pixel). All values must be positive.
        relief: A raster holding the vertical relief of the DEM pixels. (See
            the "dem.relief" function to calculate this raster). Must have the
            same shape as the raster used to derive the stream segments.

    Outputs:
        numpy 1D array: The ruggedness of each stream segment.
    """

    validate.vector(areas, "areas", dtype=real, length=len(segments))
    validate.positive(areas, "areas")
    relief = segments.summary("max", relief)
    return relief / np.sqrt(areas)


def scaled_dnbr(
    segments: Segments,
    npixels: SegmentValues,
    flow_directions: Raster,
    dNBR: Raster,
    *,
    check: bool = True,
) -> SegmentValues:
    """
    scaled_dnbr  Computes mean dNBR/1000 for a set of stream segment catchments
    ----------
    scaled_dnbr(segments, npixels, flow_directions, dNBR)
    Computes mean scaled dNBR for a set of stream segments. Mean dNBR is first
    calculated over all pixels in the catchment area of each stream segment. This
    value is then divided by 1000 to place the final value roughly on an interval
    from 0 to 1.

    scaled_dnbr(..., *, check=False)
    Disables validation checks of input rasters. This can speed up the
    processing of large rasters, but may produce unexpected results if any
    of the input rasters contain invalid values.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment.
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        dNBR: A raster holding dNBR values for the DEM pixels. Must have the same
            shape as the raster used to derive the stream segments.
        check: True (default) to validate input rasters before processing.
            False to disable these checks.

    Outputs:
        numpy 1D array: The scaled dNBR values for the stream segments
    """

    dNBR = segments.catchment_mean(
        flow_directions,
        values=dNBR,
        npixels=npixels,
        check=check,
    )
    return dNBR / 1000


def scaled_thickness(
    segments: Segments,
    npixels: SegmentValues,
    flow_directions: Raster,
    soil_thickness: Raster,
    *,
    check: bool = True,
) -> SegmentValues:
    """
    scaled_thickness  Returns mean soil thickness / 100 for a set of stream segments
    ----------
    scaled_thickness(segments, npixels, flow_directions, soil_thickness)
    Computes mean scaled soil thickness for a set of stream segments. Mean soil
    thickness is computed over all pixels in the catchment area of each stream
    segment. These values are then divided by 100 to place them roughly on the
    interval from 0 to 1.

    scaled_thicknesss(..., *, check=False)
    Disables validation checks of input rasters. This can speed up the
    processing of large rasters, but may produce unexpected results if any
    of the input rasters contain invalid values.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        soil_thickness: A raster holding the soil thickness for the DEM pixels.
            Must have the same shape as the raster used to derive the stream segments.
        check: True (default) to validate input rasters before processing.
            False to disable these checks.

    Outputs:
        numpy 1D array: The mean scaled soil thickness for each stream segment
    """

    thickness = segments.catchment_mean(
        flow_directions,
        values=soil_thickness,
        npixels=npixels,
        check=check,
    )
    return thickness / 100


def upslope_ratio(
    segments: Segments,
    npixels: SegmentValues,
    flow_directions: Raster,
    meets_criteria: Raster,
    *,
    check: bool = True,
) -> SegmentValues:
    """
    upslope_ratio  Computes the proportion of upslope pixels that meet a criterion
    ----------
    upslope_ratio(segments, npixels, flow_directions, meets_criteria)
    Computes the proportion of upslope pixels that meet a criterion. The
    "meets_criteria" input is a raster indicating which DEM pixels meet the
    desired criteria. Pixels meeting the criteria should have a value of 1. All
    others should be 0.

    Note that this function is generalizable to a number of model variables.
    For example it can be used to compute:

        M1, T: The proportion of upslope pixels burned at high-or-moderate severity
               with slopes greater than 23 degrees.
        M3, F: The proportion of upslope pixels burned at high-or-moderate severity
        M4, T: The proportion of upslope pixels burned at low-moderate-high severity
               with slopes greater than 30 degrees.

    upslope_ratio(..., *, check=False)
    Disables validation checks of input rasters. This can speed up the
    processing of large rasters, but may produce unexpected results if any
    of the input rasters contain invalid values.
    ----------
    Inputs:
        segments: A set of stream segments
        npixels: The number of upslope pixels for each stream segment.
        flow_directions: A raster holding TauDEM-style D8 flow directions for the
            DEM pixels. Must have the same shape as the raster used to derive
            the stream segments.
        meets_criteria: A raster indicating which DEM pixels meet the desired
            criteria. Must have the same shape as the raster used to derive the
            stream segments.
        check: True (default) to validate input rasters before processing.
            False to disable these checks.

    Outputs:
        numpy 1D array: The burn ratio for each stream segment
    """

    return segments.catchment_mean(
        flow_directions,
        values=meets_criteria,
        npixels=npixels,
        check=check,
    )


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

    Methods:
        parameters      - Returns the model parameters for a queried set of durations

    Abstract Methods:
        variables       - Returns the terrain, fire, and soil variables for a set of stream segments

    Internal:
        _variable_dict  - Returns a dict holding terrain, fire, and soil variables
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
    def parameters(cls, durations: Durations = durations) -> ParameterDict:
        """
        parameters  Return model parameters for the queried durations.
        ----------
        Model.parameters()
        Returns a dict with the logistic model intercepts (B), terrain coefficients (Ct),
        fire coefficients (Cf), and soil coefficients (Cs) for a model. Each
        value in the dict is a numpy 1D array with 3 elements. The three elements
        are for 15-minute, 30-minute, and 60-minute rainfall durations (in that order).

        Model.parameters(durations)
        Returns values for the queried rainfall durations. Each value in the dict
        will have one element per queried duration, in the same order as the queries.
        Valid durations to query are 15, 30, and 60.
        ----------
        Inputs:
            durations: A list of rainfall durations for which to return model parameters

        Outputs:
            Dict[str, numpy 1D array]: The queried coefficients for the model.
                'B': Logistic model intercepts
                'Ct': Terrain coefficients
                'Cf': Fire coefficients
                'Cs': Soil coefficients
        """
        # Validate durations
        durations = validate.vector(durations, "durations", dtype=real)
        valid = np.isin(durations, cls.durations)
        if not all(valid):
            raise DurationsError(durations, cls.durations)

        # Get duration indices
        indices = np.empty(durations.shape, dtype=int)
        for d, duration in enumerate(cls.durations):
            elements = np.argwhere(durations == duration)
            indices[elements] = d

        # Get parameters at the specified duration indices
        parameters = [cls.B, cls.Ct, cls.Cf, cls.Cs]
        names = ["B", "Ct", "Cf", "Cs"]
        return {
            name: np.array(values)[indices] for name, values in zip(names, parameters)
        }

    @staticmethod
    @abstractmethod
    def variables(segments: Segments, *args, **kwargs) -> VariableDict:
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
            Dict[str, numpy 1D array]: The variables needed to run the model
                for the stream segments.
                'T': The terrain variable for each stream segment
                'F': The fire variable for each stream segment
                'S': The soil variable for each stream segment
        """

    @staticmethod
    def _variable_dict(
        T: SegmentValues, F: SegmentValues, S: SegmentValues
    ) -> VariableDict:
        "Groups models variables into a dict"
        return {"T": T, "F": F, "S": S}


class M1(Model):
    """
    M1  Implements the M1 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: The proportion of upslope area with both high-or-moderate severity
        burn AND slopes greater than 23 degree.

    Fire: Mean catchment dNBR / 1000

    Soil: Mean catchment KF-factor
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

    @staticmethod
    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        high_moderate_23: Raster,
        dNBR: Raster,
        kf_factor: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M1 terrain, fire, and soil variables for a set of stream segments
        ----------
        M1.variables(segments, npixels, flow_directions,
                                              high_moderate_23, dNBR, kf_factor)
        Returns the terrain, fire, and soil variables required to run the M1 model
        for a set of stream segments. The terrain variable is the ratio of upslope
        pixels that have both moderate-or-high burn severity, and slopes greater
        than 23 degrees. The fire variable is mean catchment dNBR / 1000, and
        the soil variable is the mean catchment KF-factor. Returns a dict mapping
        each variable to a numpy 1D array with the values of the variable for the
        stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels.
            high_moderate_23: A raster indicating DEM pixels that have both
                high-or-moderate burn severity, and slopes >= 23 degrees. Pixels
                that meet this criteria should have a value of 1. All other pixels
                should be 0.
            dNBR: A raster holding dNBR values for the DEM pixels.
            kf_factor: A raster holding KF-factor values for the DEM pixels.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': The proportion of upslope area burned at high-or-moderate
                    severity with slopes greater than 23 degrees.
                'F': Mean catchment dNBR / 1000
                'S': Mean catchment KF-factor
        """
        T = upslope_ratio(segments, npixels, flow_directions, high_moderate_23)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = _kf_factor(segments, npixels, flow_directions, kf_factor)
        return Model._variable_dict(T, F, S)


class M2(Model):
    """
    M2  Implements the M2 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: The mean gradient of upslope area burned with high-or-moderate severity

    Fire: Mean catchment dNBR / 1000

    Soil: Mean catchment KF-factor
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic model intercepts
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

    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        gradient: Raster,
        high_moderate: Raster,
        dNBR: Raster,
        kf_factor: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M2 terrain, fire, and soil variables for a set of stream segments
        ----------
        M2.variables(segments, npixels, flow_directions,
                                        gradient, high_moderate, dNBR, kf_factor)
        Returns the terrain, fire, and soil variables required to run the M1 model
        for a set of stream segments. The terrain variable is the mean gradient of
        upslope pixels burned with high-or-moderate severity. The fire variable
        is mean catchment dNBR / 1000. The soil variable is mean catchment KF-factor.
        Returns a dict mapping each variable to a numpy 1D array with the values
        of the variable for the stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels.
            gradient: A raster indicating the gradients - sin(theta) - of the DEM
                pixels.
            high_moderate: A raster indicating DEM pixels that have high-or-moderate
                burn severity. Pixels that meet this criteria should have a value
                of 1. All other pixels should be 0.
            dNBR: A raster holding dNBR values for the DEM pixels.
            kf_factor: A raster holding KF-factor values for the DEM pixels.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': The mean gradient of upslope area burned at high-or-moderate severity
                'F': Mean catchment dNBR / 1000
                'S': Mean catchment KF-factor
        """

        T = burn_gradient(segments, flow_directions, gradient, high_moderate)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = _kf_factor(segments, npixels, flow_directions, kf_factor)
        return Model._variable_dict(T, F, S)


class M3(Model):
    """
    M3  Implements the M3 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: Topographic ruggedness

    Fire: The proportion of upslope area burned at high-or-moderate severity

    Soil: Mean catchment soil-thickness / 100
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic model intercepts
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

    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        relief: Raster,
        areas: SegmentValues,
        high_moderate: Raster,
        soil_thickness: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M2 terrain, fire, and soil variables for a set of stream segments
        ----------
        M3.variables(segments, npixels, flow_directions,
                                   relief, areas, high_moderate, soil_thickness)
        Returns the terrain, fire, and soil variables required to run the M3 model
        for a set of stream segments. The terrain variable is topographic ruggedness.
        The fire variable is the proportion of upslope area burned at high-or-moderate
        severity. The soil variable is mean catchment soil thickness / 100.
        Returns a dict mapping each variable to a numpy 1D array with the values
        of the variable for the stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels.
            relief: A raster holding the vertical relief of the DEM pixels.
            areas: The total upslope area for each stream segment. Should be in the
                same units as the data in the vertical relief raster.
            high_moderate: A raster indicating DEM pixels that have high-or-moderate
                burn severity. Pixels that meet this criteria should have a value
                of 1. All other pixels should be 0.
            soil_thickness: A raster holding the soil thickness of the DEM pixels.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': Topographic ruggedness
                'F': The proportion of upslope area burned at high-or-moderate severity
                'S': Mean catchment soil thickness / 100
        """

        T = ruggedness(segments, areas, relief)
        F = upslope_ratio(segments, npixels, flow_directions, high_moderate)
        S = scaled_thickness(segments, npixels, flow_directions, soil_thickness)
        return Model._variable_dict(T, F, S)


class M4(Model):
    """
    M4  Implements the M4 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

    Terrain: The proportion of upslope area burned at any severity (low-moderate-high)
        with slopes greater than 30 degrees.

    Fire: Mean catchment dNBR / 1000

    Soil: Mean catchment soil-thickness / 100
    ----------
    Properties:
        durations       - Rainfall durations used to calibrate model parameters
        B               - Logistic model intercepts
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

    def variables(
        segments: Segments,
        npixels: SegmentValues,
        flow_directions: Raster,
        burned_30: Raster,
        dNBR: Raster,
        soil_thickness: Raster,
    ) -> VariableDict:
        """
        variables  Returns the M4 terrain, fire, and soil variables for a set of stream segments
        ----------
        M4.variables(segments, npixels, flow_directions,
                                                burned_30, dNBR, soil_thickness)
        Returns the terrain, fire, and soil variables required to run the M3 model
        for a set of stream segments. The terrain variable is the proportion of
        upslope area burned at any severity (low-moderate-high) with slopes
        greater than 30. The fire variable is mean catchment dNBR / 1000. The
        soil variable is mean catchment soil thickness / 100. Returns a dict
        mapping each variable to a numpy 1D array with the values of the variable
        for the stream segments.
        ----------
        Inputs:
            segments: A set of stream segments
            npixels: The number of upslope pixels for each stream segment.
            flow_directions: A raster holding TauDEM-style D8 flow directions for the
                DEM pixels.
            burned_30: A raster indicating DEM pixels that are both burned at
                any level of severity (low-moderate-high) and have slopes greater
                than 30 degrees. Pixels that meet this criteria should have a value
                of 1. All other pixels should be 0.
            dNBR: A raster holding dNBR values for the DEM pixels.
            soil_thickness: A raster holding the soil thickness of the DEM pixels.

        Output:
            Dict[str, numpy 1D array]: The values of the model variables for the
                input stream segments.
                'T': The proportion of upslope area burned at low-moderate-high
                    severity with slopes greater than 30
                'F': Mean catchment dNBR / 1000
                'S': Mean catchment soil / 100
        """

        T = upslope_ratio(segments, npixels, flow_directions, burned_30)
        F = scaled_dnbr(segments, npixels, flow_directions, dNBR)
        S = scaled_thickness(segments, npixels, flow_directions, soil_thickness)
        return Model._variable_dict(T, F, S)
