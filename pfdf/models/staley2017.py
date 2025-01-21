"""
staley2017  Implements the logistic regression models presented in Staley et al., 2017
----------
This module implements the logistic regression models presented in Staley et al., 2017 
(see citation below). These models describe debris-flow likelihood as a function 
of terrain (T), fire burn severity (F), soil (S), and rainfall accumulation (R).
The models can also be inverted to solve for rainfall accumulation given design
probability levels for debris-flow events.

The module also provides classes to implement the M1-4 models presented in the
paper. These classes provide methods to return the parameters, and compute the
variables specific to each model.

CITATION:
Staley, D. M., Negri, J. A., Kean, J. W., Laber, J. L., Tillery, A. C., & 
Youberg, A. M. (2017). Prediction of spatially explicit rainfall intensity-duration
thresholds for post-fire debris-flow generation in the western United States. 
Geomorphology, 278, 149-162.
https://doi.org/10.1016/j.geomorph.2016.10.019
----------
Key Functions:
    likelihood          - Solves for debris-flow likelihoods given rainfall accumulations
    accumulation        - Solves for the rainfall accumulations needed to achieve given probability levels

Model Classes:
    M1, M2, M3, M4      - Classes that implement the 4 models described in Staley et al., 2017
    .parameters(...)    - Return a model's B, Ct, Cf, and Cs parameters for queried rainfall durations
    .variables(...)     - Calculate the T, F, and S variables for a model
    .terrain(...)       - Calculate the terrain variable (T) for a model
    .fire(...)          - Calculate the fire variable (F) for a model
    .soil(...)          - Calculate the soil variable (S) for a model

Internal:
    Model               - Abstract base class implementing common functionality for the M1-4 models
    _validate           - Validates parameters/variables and reshapes for broadcasting
"""

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from math import nan

import numpy as np

import pfdf._validate.core as validate
from pfdf._utils import clean_dims, real
from pfdf._utils.nodata import NodataMask
from pfdf.errors import DurationsError, ShapeError
from pfdf.raster import Raster
from pfdf.segments import Segments
from pfdf.segments._validate import raster as validate_raster
from pfdf.utils import slope

if typing.TYPE_CHECKING:
    from typing import Any, Optional

    from pfdf.typing.core import BooleanMatrix, scalar
    from pfdf.typing.models import (
        Accumulations,
        AccumulationVector,
        Durations,
        Likelihoods,
        Parameter,
        Parameters,
        Probabilities,
        Variable,
        Variables,
    )
    from pfdf.typing.raster import RasterInput
    from pfdf.typing.segments import CatchmentValues, SegmentValues


# Type hint
OmitnanDict = dict[str, bool]
omitnan = bool | OmitnanDict

#####
# Generic solvers
#####


def accumulation(
    p: Probabilities,
    B: Parameter,
    Ct: Parameter,
    T: Variable,
    Cf: Parameter,
    F: Variable,
    Cs: Parameter,
    S: Variable,
    *,
    keepdims: bool = False,
    screen: bool = True,
) -> Accumulations:
    """
    Computes rainfall accumulations needed for specified debris-flow probability levels
    ----------
    accumulation(p, B, Ct, T, Cf, F, Cs, S)
    Returns the rainfall accumulations required to achieve the specified p-values.
    This function is agnostic to the actual model being run, and thus can
    implement all 4 of the models presented in the paper (as well as any other
    model following the form of Equation 1).

    All of the inputs to this function should be real-valued numpy arrays.
    The p-values - p - are the design probabilities for which the model should be solved.
    For example, p=0.5 estimates the rainfall accumulation that would result in a 50%
    probability of a debris flow event. Here, `p` should be a 1D array listing all the
    design probabilities that should be solved for.

    The three variables - T, F, and S - represent the terrain steepness,
    wildfire severity, and surface properties variables for the model. In
    most cases, these are 1D arrays with one element per stream segment
    being assessed. Variables can also be scalar (in which the same value is used
    for every segment), or 2D arrays (see below for details of this less common
    use case).

    The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic
    model link equation. B is the intercept, and each C parameter
    is the coefficient of the associated variable. Parameters can be used to
    implement multiple runs of the assessment model. Here, we define a "run" as
    an implementation of the hazard model using a unique set of logistic model
    parameters. Each parameter should be either a scalar, or vector of parameter
    values. If a vector, the input should have one element per run. If a scalar,
    then the same value is used for every run of the model. A common use case is
    solving the model for multiple rainfall durations (for example: 15, 30, and
    60 minute intervals). In the example with 3 durations, each parameter should
    have 3 elements - each element corresponds to parameter value for the corresponding
    rainfall duration. Another use case for multiple runs is implementing a
    parameter sweep to validate model parameters.

    This function solves the rainfall accumulations for all stream segments,
    p-values, and parameter runs provided. Each accumulation describes the total
    rainfall required within the rainfall duration associated with its parameters.
    For example, if using parameters for a 15-minute rainfall duration, the accumulation
    describes the total rainfall required within a 15-minute window. Accumulation
    units are the units of the rainfall values used to calibrate the model's parameters.
    For the 4 models described in the paper, accumulations are in mm.

    The returned output will be a numpy array with up to 3 dimensions. The first
    dimension is stream segments, second dimension is p-values, and third dimension is
    parameter runs. By default, this command will remove singleton dimensions from the
    output array. The first dimension is always retained, but the second is removed if
    there is a single design probability, and the third is removed if there is a single
    parameter run. Alternatively, set keepdims=True to always return a 3D array.

    As mentioned, one or more variable can also be a 2D array. In this case
    each row is a stream segment, and each column is a parameter run. Each
    column will be used to solve the model for (only) the associated parameter
    run. This allows use of different values for a variable. An example use
    case could be testing the model using different datasets to derive one or
    more variables.

    accumulation(..., *, keepdims = True)
    Always returns the output as a 3D numpy array, regardless of the number
    of p-values and parameter runs.

    accumulation(..., *, screen = False)
    Disables the screening of negative accumulations. When screening is disabled,
    negative accumulations are retained in the output, instead of being replaced
    by nan.
    ----------
    Inputs:
        p: The design probabilities for which to solve the model
        B: The intercepts of the link equation
        Ct: The coefficients for the terrain steepness variable
        T: The terrain steepness variable
        Cf: The coefficients for the wildfire severity variable
        F: The wildfire severity variable
        Cs: The coefficients for the surface properties variable
        S: The surface properties variable
        keepdims: True to always return a 3D numpy array. If false (default),
            returns a 2D array when there is 1 p-value, and a 1D array if there
            is 1 p-value and 1 parameter run.
        screen: True (default) to replace negative accumulations with NaN. False
            to disable this screening.

    Outputs:
        numpy 3D array (Segments x P-values x Parameter Runs): The rainfall
            accumulations required to achieve the specified p-values.
    """

    # Validate and reshape for broadcasting.
    p, B, Ct, Cf, Cs, T, F, S = _validate(p, B, Ct, Cf, Cs, T, F, S)
    validate.inrange(p, "p", min=0, max=1, ignore=np.nan)

    # Solve the model
    numerator = np.log(p / (1 - p)) - B
    denominator = Ct * T + Cf * F + Cs * S
    accumulation = numerator / denominator

    # Optionally screen negative values and remove trailing dimensions
    if screen:
        negative = accumulation < 0
        if np.any(negative):
            accumulation = accumulation.astype(float)
            accumulation[negative] = np.nan
    return clean_dims(accumulation, keepdims)


def likelihood(
    R: AccumulationVector,
    B: Parameter,
    Ct: Parameter,
    T: Variable,
    Cf: Parameter,
    F: Variable,
    Cs: Parameter,
    S: Variable,
    *,
    keepdims: bool = False,
) -> Likelihoods:
    """
    Computes debris-flow likelihood for specified rainfall accumulations
    ----------
    likelihood(R, B, Ct, T, Cf, F, Cs, S)
    likelihood(..., keepdims=True)
    Solves the debris-flow likelihoods for the specified rainfall accumulations.
    This function is agnostic to the actual model being run, and thus can
    implement all 4 of the models presented in the paper (as well as any other
    model following the form of Equation 1).

    All of the inputs to this function should be real-valued numpy arrays.
    The R values are the rainfall accumulations for which the model should be solved.
    For example, R = 6 solves for debris-flow likelihood when rainfall accumulation
    is 6 mm/duration. R should be a 1D array listing all the accumulations that should
    be solved for.

    The three variables - T, F, and S - represent the terrain steepness,
    wildfire severity, and surface properties variables for the model. In
    most cases, these are 1D arrays with one element per stream segment
    being assessed. Variables can also be scalar (in which the same value is used
    for every segment), or 2D arrays (see below for details of this less common
    use case).

    The four parameters - B, Ct, Cf, and Cs - are the parameters of the logistic
    model link equation. B is the intercept, and each C parameter
    is the coefficient of the associated variable. Parameters can be used to
    implement multiple runs of the assessment model. Here, we define a "run" as
    an implementation of the hazard model using a unique set of logistic model
    parameters. Each parameter should be either a scalar, or vector of parameter
    values. If a vector, the input should have one element per run. If a scalar,
    then the same value is used for every run of the model. A common use case is
    solving the model for multiple rainfall durations (for example: 15, 30, and
    60 minute intervals). In the example with 3 durations, each parameter should
    have 3 elements - each element corresponds to parameter value for the corresponding
    rainfall duration. Another use case for multiple runs is implementing a
    parameter sweep to validate model parameters.

    This function solves the debris-flow likelihoods for all stream segments, rainfall
    accumulations, and parameter runs provided. Note that rainfall accumulations should
    be relative to the rainfall durations associated with each set of parameters. For
    example, if using parameters for 15-minute and 30-minute rainfall durations, then
    the input rainfall accumulations should be for 15-minute and 30-minute intervals,
    respectively. Accumulation units are the units of the rainfall values used to
    calibrate the model's parameters. For the 4 models described in the paoer,
    accumulations are millimeters of accumulations per rainfall duration.

    The returned output will be a numpy array with up to 3 dimensions. The first
    dimension is stream segments, second dimension is rainfall accumulations, and third
    dimension is parameter runs. By default, this command will remove singleton
    dimensions from the output array. The first dimension is always retained, but the
    second is removed if there is a single rainfall accumulation, and the third is
    removed if there is a single parameter run. Alternatively, set keepdims=True to
    always return a 3D array.

    As mentioned, one or more variables can also be a 2D array. In this case
    each row is a stream segment, and each column is a parameter run. Each
    column will be used to solve the model for (only) the associated parameter
    run. This allows use of different values for a variable. An example use
    case could be testing the model using different datasets to derive one or
    more variables.
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
        keepdims: True to always return a 3D numpy array. If False (default), removes
            dimensions 2 and/or 3 when singleton

    Outputs:
        numpy 3D array (Segments x R values x Parameter Runs): The estimated likelihoods
    """

    # Validate and reshape for broadcasting.
    R, B, Ct, Cf, Cs, T, F, S = _validate(R, B, Ct, Cf, Cs, T, F, S)
    validate.positive(R, "R", allow_zero=True, ignore=np.nan)

    # Solve the model. Optionally remove singleton dimensions
    eX = np.exp(B + Ct * T * R + Cf * F * R + Cs * S * R)
    likelihood = eX / (1 + eX)
    return clean_dims(likelihood, keepdims)


def _validate(
    PR: Any, B: Any, Ct: Any, Cf: Any, Cs: Any, T: Any, F: Any, S: Any
) -> tuple[Parameter, Parameter, Parameter, Parameter, Variable, Variable, Variable]:
    "Validates parameters and variables and reshapes for broadcasting"

    # Validate parameter vectors
    vectors = {"PR": PR, "B": B, "Ct": Ct, "Cf": Cf, "Cs": Cs}
    for name, value in vectors.items():
        vectors[name] = validate.vector(value, name, dtype=real)

    # Validate variable matrices
    variables = {"T": T, "F": F, "S": S}
    for name, value in variables.items():
        variables[name] = validate.matrix(value, name, dtype=real)

    # Initialize sizes
    nSegments = 1
    nRuns = 1
    nQueries = vectors["PR"].size

    # Process vectors. Reshape p for broadcasting....
    for name, value in vectors.items():
        if name == "PR":
            vectors[name] = value.reshape(1, nQueries, 1)
            continue

        # Update nRuns if this is the first parameter with multiple runs.
        # Otherwise, must have 1 or nRuns elements
        elif nRuns == 1 and value.size > 1:
            nRuns = value.size
            set_runs = name
        elif value.size != 1 and value.size != nRuns:
            raise ShapeError(
                f"Model parameters (B, Ct, Cf, Cs) must have the same number of runs. "
                f"But {set_runs} has {nRuns} elements, whereas {name} has {value.size}."
            )

        # Reshape parameters for broadcasting
        vectors[name] = value.reshape(1, 1, -1)

    # Get variable shapes. Update nRuns and nSegments when appropriate
    for name, value in variables.items():
        nrows, ncols = value.shape
        if nSegments == 1 and nrows > 1:
            nSegments = nrows
            set_segments = name
        if nRuns == 1 and ncols > 1:
            nRuns = ncols
            set_runs = name

        # Check that variables have 1 or nSegments rows
        if nrows != 1 and nrows != nSegments:
            raise ShapeError(
                "Variables (T, F, S) must have the same number of stream segments. "
                f"But {set_segments} has {nSegments} rows, whereas {name} has {nrows}."
            )

        # Also require 1 or nRuns columns
        elif ncols != 1 and ncols != nRuns:
            raise ShapeError(
                f"{set_runs} has {nRuns} runs, so {name} must have either 1 or {nRuns} columns. "
                f"But {name} has {ncols} columns instead."
            )

        # Reshape variables for broadcasting
        variables[name] = value.reshape(nrows, 1, ncols)

    # Return direct references to values (makes the math look nicer)
    PR, B, Ct, Cf, Cs = vectors.values()
    T, F, S = variables.values()
    return PR, B, Ct, Cf, Cs, T, F, S


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
        durations           - Rainfall durations used to calibrate model parameters

    Abstract Properties:
        B                   - Logistic Model intercepts
        Ct                  - Coefficients for the (t)errain variable
        Cf                  - Coefficients for the (f)ire variable
        Cs                  - Coefficients for the (s)oil variable

    Class Methods:
        parameters          - Returns the model parameters for a queried set of durations

    Abstract Methods:
        variables           - Returns the terrain, fire, and soil variables for a set of stream segments

    Static Methods:
        _validate           - Validates a Segments object and input rasters for calculating variables
        _validate_omitnan   - Validates omitnan options for input rasters
        _terrain_mask       - Locates pixels that are sufficiently burned and steep
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
    def parameters(cls, durations: Durations = durations) -> Parameters:
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
    def variables(cls, segments: Segments, *args, **kwargs) -> Variables:
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

        validate.type(segments, "segments", Segments, "pfdf.segments.Segments object")
        for r, raster, name in zip(range(len(rasters)), rasters, names):
            rasters[r] = validate_raster(segments, raster, name)
        return rasters

    @staticmethod
    def _validate_omitnan(omitnan: Any, rasters: list[str]) -> OmitnanDict:
        "Validates omitnan options for input rasters"

        # If a boolean, use the same value for each raster
        if isinstance(omitnan, bool):
            return {raster: omitnan for raster in rasters}

        # If a dict, check the keys and values
        elif isinstance(omitnan, dict):
            for key, value in omitnan.items():
                if key not in rasters:
                    allowed = ", ".join(rasters)
                    raise ValueError(
                        f"The omitnan dict contains an unrecognized key ({key=}). "
                        f"Allowed keys are: {allowed}"
                    )
                elif not isinstance(value, bool):
                    raise TypeError(f"The value for omitnan['{key}'] is not a bool.")

            # Build the final dict. Unspecified keys are set to omitnan=False
            final = {}
            for raster in rasters:
                if raster in omitnan.keys():
                    final[raster] = omitnan[raster]
                else:
                    final[raster] = False
            return final

        # Anything else if not allowed
        else:
            raise TypeError("omitnan must either be a boolean or a dict.")

    @staticmethod
    def _terrain_mask(
        burned: Raster, slopes: Raster, threshold_degrees: float
    ) -> BooleanMatrix:
        "Returns a mask of pixels that are sufficiently burned, and that have"
        "slopes steeper than a threshold"

        # Validate burn mask and convert threshold from degrees to gradient
        burned = validate.boolean(burned.values, burned.name, ignore=burned.nodata)
        threshold = slope.from_degrees(threshold_degrees)

        # Build the mask. Preserve NoData
        mask = burned & (slopes.values >= threshold)
        nodatas = NodataMask(slopes.values, slopes.nodata)
        return nodatas.fill(mask, False)


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

    #####
    # Internal variables (validated)
    #####

    @staticmethod
    def _terrain(
        segments: Segments, moderate_high: Raster, slopes: Raster
    ) -> CatchmentValues:
        "Computes the M1 terrain variable"
        mask = Model._terrain_mask(moderate_high, slopes, threshold_degrees=23)
        return segments.catchment_ratio(mask)

    @staticmethod
    def _fire(segments: Segments, dnbr: Raster, omitnan: bool) -> CatchmentValues:
        "Computes the M1 fire variable"
        return segments.scaled_dnbr(dnbr, omitnan=omitnan)

    @staticmethod
    def _soil(segments: Segments, kf_factor: Raster, omitnan: bool) -> CatchmentValues:
        "Computes the M1 soil variable"
        return segments.kf_factor(kf_factor, omitnan=omitnan)

    #####
    # Variables
    #####

    @staticmethod
    def terrain(
        segments: Segments, moderate_high: RasterInput, slopes: RasterInput
    ) -> CatchmentValues:
        """
        Computes the M1 terrain variable
        ----------
        M1.terrain(segments, moderate_high, slopes)
        Returns the M1 terrain variable for the network.
        ----------
        Inputs:
            segments: A stream segment network
            moderate_high: The moderate-high burn severity mask
            slopes: Slope raster

        Outputs:
            numpy 1D array: The M1 terrain variable (T)
        """
        moderate_high, slopes = Model._validate(
            segments, [moderate_high, slopes], ["moderate_high", "slopes"]
        )
        return M1._terrain(segments, moderate_high, slopes)

    @staticmethod
    def fire(
        segments: Segments, dnbr: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M1 fire variable
        ----------
        M1.fire(segments, dnbr)
        M1.fire(segments, dnbr, omitnan=True)
        Returns the M1 fire variable for the network. Use "omitnan" to ignore
        NaN and NoData values in the dNBR raster.
        ----------
        Inputs:
            segments: A stream segment network
            dnbr: A dNBR raster
            omitnan: True to ignore NaN and NoData values in the dNBR raster.
                Default is False.

        Outputs:
            numpy 1D array: The M1 fire variable (F)
        """
        (dnbr,) = Model._validate(segments, [dnbr], ["dnbr"])
        return M1._fire(segments, dnbr, omitnan)

    @staticmethod
    def soil(
        segments: Segments, kf_factor: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M1 soil variable
        ----------
        M1.soil(segments, kf_factor)
        M1.soil(segments, kf_factor, omitnan=True)
        Returns the M1 soil variable for the network. Use "omitnan" to ignore NaN
        and NoData values in the KF-factor raster.
        ----------
        Inputs:
            segments: A stream segment network
            kf_factor: A KF-factor raster
            omitnan: True to ignore NaN and NoData values in the KF-factor raster.
                Default is False

        Outputs:
            numpy 1D array: The M1 soil variable (S)
        """
        (kf_factor,) = Model._validate(segments, [kf_factor], ["kf_factor"])
        return M1._soil(segments, kf_factor, omitnan)

    @staticmethod
    def variables(
        segments: Segments,
        moderate_high: RasterInput,
        slopes: RasterInput,
        dnbr: RasterInput,
        kf_factor: RasterInput,
        omitnan: omitnan = False,
    ) -> Variables:
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

        M1.variables(..., omitnan)
        Specifies how to treat NaN and NoData values in the dnbr and kf_factor
        rasters. The omitnan option may either be a boolean or a dict. In the
        default setting (omitnan=False), when a raster contains a NaN or Nodata
        value in a catchment basin, then the associated variable for the basin
        will be NaN. For example, if the dnbr raster contains NaN in a segment's
        catchment, then the F variable will be NaN for that segment. If omitnan=True,
        NaN and NoData values are ignored. Note that if a raster only contains
        NaN and NoData values in a catchment, then the variable will still be NaN
        for the catchment.

        If omitnan is a dict, then it may have the keys "dnbr", and/or "kf_factor".
        The value of each key should be a boolean indicating whether to omit NaN
        and NoData values for that raster. If a key is not included, then the
        omitnan setting for the raster is set to False. Raises a ValueError
        if the dict includes other keys.
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
            omitnan: A boolean or dict indicating whether to ignore NaN and NoData
                values in the dnbr and kf_factor rasters

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate
        moderate_high, slopes, dnbr, kf_factor = Model._validate(
            segments,
            [moderate_high, slopes, dnbr, kf_factor],
            ["moderate_high", "slopes", "dnbr", "kf_factor"],
        )
        omitnan = Model._validate_omitnan(omitnan, rasters=["dnbr", "kf_factor"])

        # Get variables
        T = M1._terrain(segments, moderate_high, slopes)
        F = M1._fire(segments, dnbr, omitnan["dnbr"])
        S = M1._soil(segments, kf_factor, omitnan["kf_factor"])
        return T, F, S


class M2(Model):
    """
    M2  Implements the M2 model from Staley et al., 2017
    ----------
    This model's variables are as follows:

        T: The mean sin(theta) of catchment area burned at moderate or high severity.
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

    #####
    # Internal variables (validated)
    #####

    @staticmethod
    def _terrain(
        segments: Segments, slopes: Raster, moderate_high: Raster, omitnan: bool
    ) -> CatchmentValues:
        "Computes the M2 terrain variable"

        # Convert slopes to sine-thetas, but preserve nodata
        sine_thetas = slope.to_sine(slopes.values)
        sine_thetas = sine_thetas.astype(float, copy=False)
        nodatas = NodataMask(slopes.values, slopes.nodata)
        nodatas.fill(sine_thetas, nan)
        sine_thetas = Raster.from_array(
            sine_thetas,
            crs=slopes.crs,
            transform=slopes.transform,
            nodata=nan,
            copy=False,
        )

        # Compute variable
        return segments.sine_theta(sine_thetas, moderate_high, omitnan=omitnan)

    @staticmethod
    def _fire(segments: Segments, dnbr: Raster, omitnan: bool) -> CatchmentValues:
        "Computes the M2 fire variable"
        return segments.scaled_dnbr(dnbr, omitnan=omitnan)

    @staticmethod
    def _soil(segments: Segments, kf_factor: Raster, omitnan: bool) -> CatchmentValues:
        "Computes the M2 soil variable"
        return segments.kf_factor(kf_factor, omitnan=omitnan)

    #####
    # Variables
    #####

    @staticmethod
    def terrain(
        segments: Segments,
        slopes: RasterInput,
        moderate_high: RasterInput,
        omitnan=False,
    ) -> CatchmentValues:
        """
        Computes the M2 terrain variable
        ----------
        M2.terrain(segments, slopes, moderate_high)
        M2.terrain(..., omitnan=True)
        Computes the M2 terrain variable. Set omitnan=True to ignore NaN and NoData
        values in the slopes raster.
        ----------
        Inputs:
            segments: A stream segment network
            slope: A slope raster
            moderate_high: Moderate-high burn severity raster mask
            omitnan: True to ignore NaN and NoData values in the slopes raster.
                Default is False

        Outputs:
            numpy 1D array: The M2 terrain variable (T)
        """
        slopes, moderate_high = Model._validate(
            segments, [slopes, moderate_high], ["slopes", "moderate_high"]
        )
        return M2._terrain(segments, slopes, moderate_high, omitnan)

    @staticmethod
    def fire(
        segments: Segments, dnbr: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M2 fire variable
        ----------
        M2.fire(segments, dnbr)
        M2.fire(segments, dnbr, omitnan=True)
        Computes the M2 fire variable. Set omitnan=True to ignore NaN and NoData
        values in the dNBR raster.
        ----------
        Inputs:
            segments: A stream segment network
            dnbr: A dNBR raster
            omitnan: True to ignore NaN and NoData values in the dNBR raster.
                Default is False.

        Outputs:
            numpy 1D array: The M2 fire variable (F)
        """
        (dnbr,) = Model._validate(segments, [dnbr], ["dnbr"])
        return M2._fire(segments, dnbr, omitnan)

    @staticmethod
    def soil(
        segments: Segments, kf_factor: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M2 soil variable
        ----------
        M2.soil(segments, kf_factor)
        M2.soil(..., omitnan=True)
        Computes the M2 soil variable. Set omitnan=True to ignore NaN and NoData
        values in the KF-factor raster.
        ----------
        Inputs:
            segments: A stream segment network
            kf_factor: A KF-factor raster
            omitnan: True to ignore NaN and NoData values in the KF-factor raster.
                Default is False.

        Outputs:
            numpy 1D array: The M2 soil variable (S)
        """
        (kf_factor,) = Model._validate(segments, [kf_factor], ["kf_factor"])
        return M2._soil(segments, kf_factor, omitnan)

    @staticmethod
    def variables(
        segments: Segments,
        moderate_high: RasterInput,
        slopes: RasterInput,
        dnbr: RasterInput,
        kf_factor: RasterInput,
        omitnan: omitnan = False,
    ) -> Variables:
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

        M2.variables(..., omitnan)
        Specifies how to treat NaN and NoData values in the slopes, dnbr and kf_factor
        rasters. The omitnan option may either be a boolean or a dict. In the
        default setting (omitnan=False), when a raster contains a NaN or Nodata
        value in a catchment basin, then the associated variable for the basin
        will be NaN. For example, if the dnbr raster contains NaN in a segment's
        catchment, then the F variable will be NaN for that segment. If omitnan=True,
        NaN and NoData values are ignored. Note that if a raster only contains
        NaN and NoData values in a catchment, then the variable will still be NaN
        for the catchment.

        If omitnan is a dict, then it may have the keys "slopes", "dnbr", and/or
        "kf_factor". The value of each key should be a boolean indicating whether
        to omit NaN and NoData values for that raster. If a key is not included,
        then the omitnan setting for the raster is set to False. Raises a ValueError
        if the dict includes other keys.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            moderate_high: A Raster mask indicating watershed pixels with
                moderate or high burn severity. True pixels indicate moderate or
                high severity. False pixels are not burned at these levels.
            slopes: A raster with the slope gradients (not angles) for the watershed
            dnbr: A dNBR raster for the watershed
            kf_factor: A KF-factor raster for the watershed
            omitnan: A boolean or dict indicating whether to ignore NaN and NoData
                values in the slopes, dnbr, and kf_factor rasters

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate
        moderate_high, slopes, dnbr, kf_factor = Model._validate(
            segments,
            [moderate_high, slopes, dnbr, kf_factor],
            ["moderate_high", "slopes", "dnbr", "kf_factor"],
        )
        omitnan = Model._validate_omitnan(
            omitnan, rasters=["slopes", "dnbr", "kf_factor"]
        )

        # Compute variables
        T = M2._terrain(segments, slopes, moderate_high, omitnan["slopes"])
        F = M2._fire(segments, dnbr, omitnan["dnbr"])
        S = M2._soil(segments, kf_factor, omitnan["kf_factor"])
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

    #####
    # Internal variables (validated)
    #####

    @staticmethod
    def _terrain(
        segments: Segments, relief: Raster, relief_per_m: scalar | None
    ) -> SegmentValues:
        "Computes the M3 terrain variable"
        return segments.ruggedness(relief, relief_per_m)

    @staticmethod
    def _fire(segments: Segments, moderate_high: Raster) -> CatchmentValues:
        "Computes the M3 fire variable"
        return segments.catchment_ratio(moderate_high)

    @staticmethod
    def _soil(
        segments: Segments, soil_thickness: Raster, omitnan: bool
    ) -> CatchmentValues:
        "Computes the M3 soil variable"
        return segments.scaled_thickness(soil_thickness, omitnan=omitnan)

    #####
    # Variables
    #####

    @staticmethod
    def terrain(
        segments: Segments, relief: RasterInput, relief_per_m: Optional[scalar] = None
    ) -> SegmentValues:
        """
        Computes the M3 terrain variable
        ----------
        M3.terrain(segments, relief)
        M3.terrain(segments, relief, relief_per_m)
        Computes the M3 terrain variable. By default, the relief values are interpreted
        as meters. If this is not the case, use the "relief_per_m" input to provide
        a conversion factor (number of relief units per meter).
        ----------
        Inputs:
            segments: A stream segment network
            relief: A vertical relief raster
            relief_per_m: The number of relief units per meter if the relief values
                are not already in meters.

        Outputs:
            numpy 1D array: The M3 terrain variable (T)
        """
        (relief,) = Model._validate(segments, [relief], ["relief"])
        return M3._terrain(segments, relief, relief_per_m)

    @staticmethod
    def fire(segments: Segments, moderate_high: RasterInput) -> CatchmentValues:
        """
        Computes the M3 fire variable
        ----------
        M3.fire(segments, moderate_high)
        Computes the M3 fire variable.
        ----------
        Inputs:
            segments: A stream segment network
            moderate_high: A moderate-high burn severity raster mask

        Outputs:
            numpy 1D array: The M3 fire variable (F)
        """
        (moderate_high,) = Model._validate(segments, [moderate_high], ["moderate_high"])
        return M3._fire(segments, moderate_high)

    @staticmethod
    def soil(
        segments: Segments, soil_thickness: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M3 soil variable
        ----------
        M3.soil(segments, soil_thickness)
        M3.soil(..., omitnan=True)
        Computes the M3 soil variable. Set omitnan=True to ignore NaN and NoData
        values in the soil_thickness raster.
        ----------
        Inputs:
            segments: A stream segment network
            soil_thickness: A soil thickness raster
            omitnan: True to ignore NaN and NoData values in the soil thickness raster.
                Default is False.

        Outputs:
            numpy 1D array: The M3 soil variable (S)
        """
        (soil_thickness,) = Model._validate(
            segments, [soil_thickness], ["soil_thickness"]
        )
        return M3._soil(segments, soil_thickness, omitnan)

    @staticmethod
    def variables(
        segments: Segments,
        moderate_high: RasterInput,
        relief: RasterInput,
        soil_thickness: RasterInput,
        relief_per_m: Optional[scalar] = None,
        omitnan: omitnan = False,
    ) -> Variables:
        """
        variables  Computes the T, F, and S variables for the M3 model
        ----------
        M3.variables(segments, moderate_high, relief, soil_thickness)
        M3.variables(..., relief_per_m)
        Computes the (T)errain, (F)ire, and (S)oil variables from the M3 model
        for each stream segment in a network. T is the topographic ruggedness of
        each segment. This is defined as a segment's vertical relief, divided by
        the square root of its catchment area. F is the proportion of catchment
        area burned at moderate or high severity. S is mean catchment soil thickness
        divided by 100. Returns these outputs as numpy 1D arrays with one element
        per stream segment.

        By default, the relief dataset is interpreted in units of meters. If this
        is not the case, use the "relief_per_m" input to specify a conversion
        factor (number of relief units per meter).

        M3.variables(..., omitnan)
        Specifies how to treat NaN and NoData values in the soil_thickness
        raster. The omitnan option may either be a boolean or a dict. In the
        default setting (omitnan=False), when the soil_thickness raster contains
        a NaN or Nodata value in a catchment basin, then the S variable for the
        basin will be NaN. If omitnan=True, NaN and NoData values are ignored.
        Note that if the soil_thickness raster only contains NaN and NoData values
        in a catchment, then S will still be NaN for that catchment.

        Alternatively, omitnan may be a dict with the single key "soil_thickness".
        The value of the key should be a boolean indicating whether to omit NaN
        and NoData values for the soil_thickness raster. Raises a ValueError if
        the dict includes other keys.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            moderate_high: A Raster mask indicating watershed pixels with
                moderate or high burn severity. True pixels indicate moderate or
                high severity. False pixels are not burned at these levels.
            relief: A vertical relief raster for the watershed
            soil_thickness: A soil thickness raster for the watershed
            relief_per_m: A conversion factor between relief units and meters
            omitnan: A boolean or dict indicating whether to ignore NaN and NoData
                values in the soil_thickness raster

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate
        moderate_high, relief, soil_thickness = Model._validate(
            segments,
            [moderate_high, relief, soil_thickness],
            ["moderate_high", "relief", "soil_thickness"],
        )
        omitnan = Model._validate_omitnan(omitnan, rasters=["soil_thickness"])
        relief_per_m = validate.conversion(relief_per_m, "relief_per_m")

        # Get variables
        T = M3._terrain(segments, relief, relief_per_m)
        F = M3._fire(segments, moderate_high)
        S = M3._soil(segments, soil_thickness, omitnan["soil_thickness"])
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

    #####
    # Internal variables (validated)
    #####

    @staticmethod
    def _terrain(
        segments: Segments, isburned: Raster, slopes: Raster
    ) -> CatchmentValues:
        "Computes the M4 terrain variable"
        mask = Model._terrain_mask(isburned, slopes, threshold_degrees=30)
        return segments.catchment_ratio(mask)

    @staticmethod
    def _fire(segments: Segments, dnbr: Raster, omitnan: bool) -> CatchmentValues:
        "Computes the M4 fire variable"
        return segments.scaled_dnbr(dnbr, omitnan=omitnan)

    @staticmethod
    def _soil(
        segments: Segments, soil_thickness: Raster, omitnan: bool
    ) -> CatchmentValues:
        "Computes the M4 soil variable"
        return segments.scaled_thickness(soil_thickness, omitnan=omitnan)

    #####
    # Variables
    #####

    @staticmethod
    def terrain(
        segments: Segments, isburned: RasterInput, slopes: Raster
    ) -> CatchmentValues:
        """
        Computes the M4 terrain variable
        ----------
        M4.terrain(segments, isburned, slopes)
        Computes the M4 terrain variable.
        ----------
        Inputs:
            segments: A stream segment network
            isburned: A burned pixel raster mask
            slopes: A slope raster

        Outputs:
            numpy 1D array: The M4 terrain variable (T)
        """
        isburned, slopes = Model._validate(
            segments, [isburned, slopes], ["isburned", "slopes"]
        )
        return M4._terrain(segments, isburned, slopes)

    @staticmethod
    def fire(
        segments: Segments, dnbr: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M4 fire variable
        ----------
        M4.fire(segments, dnbr)
        M4.fire(segments, dnbr, omitnan=True)
        Computes the M4 fire variable. Set omitnan=True to ignore NaN and NoData
        values in the dNBR raster.
        ----------
        Inputs:
            segments: A stream segment network
            dnbr: A dNBR raster
            omitnan: True to ignore NaN and NoData values in the dNBR raster.
                Default is False.

        Outputs:
            numpy 1D array: The M4 fire variable (F)
        """
        (dnbr,) = Model._validate(segments, [dnbr], ["dnbr"])
        return M4._fire(segments, dnbr, omitnan)

    @staticmethod
    def soil(
        segments: Segments, soil_thickness: RasterInput, omitnan: bool = False
    ) -> CatchmentValues:
        """
        Computes the M4 soil variable
        ----------
        M4.soil(segments, soil_thickness)
        M4.soil(..., omitnan=True)
        Computes the M4 soil variable. Set omitnan=True to ignore NaN and NoData
        values in the soil_thickness raster.
        ----------
        Inputs:
            segments: A stream segment network
            soil_thickness: A soil thickness raster
            omitnan: True to ignore NaN and NoData values in the soil thickness raster.
                Default is False.

        Outputs:
            numpy 1D array: The M4 soil variable (S)
        """
        (soil_thickness,) = Model._validate(
            segments, [soil_thickness], ["soil_thickness"]
        )
        return M4._soil(segments, soil_thickness, omitnan)

    @staticmethod
    def variables(
        segments: Segments,
        isburned: RasterInput,
        slopes: RasterInput,
        dnbr: RasterInput,
        soil_thickness: RasterInput,
        omitnan: omitnan = False,
    ) -> Variables:
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

        M4.variables(..., omitnan)
        Specifies how to treat NaN and NoData values in the dnbr and soil_thickness
        rasters. The omitnan option may either be a boolean or a dict. In the
        default setting (omitnan=False), when a raster contains a NaN or Nodata
        value in a catchment basin, then the associated variable for the basin
        will be NaN. For example, if the dnbr raster contains NaN in a segment's
        catchment, then the F variable will be NaN for that segment. If omitnan=True,
        NaN and NoData values are ignored. Note that if a raster only contains
        NaN and NoData values in a catchment, then the variable will still be NaN
        for the catchment.

        If omitnan is a dict, then it may have the keys "dnbr" and/or "soil_thickness".
        The value of each key should be a boolean indicating whether to omit NaN
        and NoData values for that raster. If a key is not included, then the
        omitnan setting for the raster is set to False. Raises a ValueError
        if the dict includes other keys.
        ----------
        Inputs:
            segments: A Segments object defining a stream segment network
            isburend: A Raster mask indicating watershed pixels that were burned
                (low, moderate or high severity). True elements indicate burned
                pixels, False elements are not burned.
            slopes: A raster of slope gradients (not angles) for the watershed
            dnbr: A dNBR raster for the watershed
            soil_thickness: A soil thickness raster for the watershed
            omitnan: A boolean or dict indicating whether to ignore NaN and NoData
                values in the dnbr and soil_thickness rasters

        Outputs:
            numpy 1D array: The terrain variable (T) for each stream segment
            numpy 1D array: The fire variable (F) for each stream segment
            numpy 1D array: The soil variable (S) for each stream segment
        """

        # Validate segments and rasters
        isburned, slopes, dnbr, soil_thickness = Model._validate(
            segments,
            [isburned, slopes, dnbr, soil_thickness],
            ["isburned", "slopes", "dnbr", "soil_thickness"],
        )
        omitnan = Model._validate_omitnan(omitnan, rasters=["dnbr", "soil_thickness"])

        # Get variables
        T = M4._terrain(segments, isburned, slopes)
        F = M4._fire(segments, dnbr, omitnan["dnbr"])
        S = M4._soil(segments, soil_thickness, omitnan["soil_thickness"])
        return T, F, S
