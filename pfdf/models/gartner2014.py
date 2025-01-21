"""
gartner2014  Functions that implement the debris-flow volume models of Gartner et al., 2014
----------
This module contains functions that solve the two debris-flow volume models
presented as Equations 2 and 3 in Gartner et al., 2014 (see citation below). 
In brief, these are an emergency assessment, and a long-term assessment model.

CITATION:
Gartner, J. E., Cannon, S. H., & Santi, P. M. (2014). Empirical models for 
predicting volumes of sediment deposited by debris flows and sediment-laden floods
 in the transverse ranges of southern California. Engineering Geology, 176, 45-56.
https://doi.org/10.1016/j.enggeo.2014.04.008
----------
User Functions:
    emergency   - Runs the emergency assessment model
    longterm    - Runs the long-term assessment model

Internal:
    _volumes                - Converts lnV to volume, Vmin, and Vmax
    _validate_parameters    - Checks that input parameters are valid
    _validate_variables     - Checks that input variables are valid
"""

from __future__ import annotations

import typing

import numpy as np
from numpy import exp, log, nan, sqrt
from scipy.stats import norm

import pfdf._validate.core as validate
from pfdf._utils import clean_dims, real
from pfdf.errors import ShapeError

if typing.TYPE_CHECKING:
    from typing import Any

    from pfdf.typing.core import MatrixArray, RealArray, VectorArray
    from pfdf.typing.models import Parameter, Variable, Volume, Volumes

    ValidatedParameters = tuple[VectorArray, ...]
    nRuns = int

#####
# Models
#####


@np.errstate(divide="ignore")  # Suppress divide-by-zero warning for log(0)
def emergency(
    i15: Variable,
    Bmh: Variable,
    R: Variable,
    *,
    B: Parameter = 4.22,
    Ci: Parameter = 0.39,
    Cb: Parameter = 0.36,
    Cr: Parameter = 0.13,
    CI: Parameter | None = 0.95,
    RSE: Parameter = 1.04,
    keepdims: bool = False,
) -> Volumes:
    """
    Solves the emergency assessment model (Equation 3 from Gartner et al., 2014)
    ----------
    emergency(i15, Bmh, R)
    Solves the emergency assessment model given peak 15-minute rainfall intensity
    in mm/h (i15), the catchment area burned at moderate-or-high intensity
    in km^2 (Bmh), and the watershed relief in meter (R). Returns the predicted
    volume of debris-flow sediment in m^3 (V), the lower bounds of the 95% confidence
    interval (Vmin), and the upper bound of the 95% confidence interval (Vmax).

    The model solves the equation:
        lnV = 4.22 +  0.39 * sqrt(i15)  +  0.36 * ln(Bmh)  +  0.13 * sqrt(R)
        V = exp(lnV)

    and uses residual standard error (RSE = 1.04) to estimate the bounds of the
    95% confidence interval:
        Vmin = exp(lnV - 1.96 * 1.04)
        Vmax = exp(lnV + 1.96 * 1.04)
    Note that the volume confidence interval is estimated using a normal distribution,
    hence the 1.96 percentile multiplier for a 95% interval.

    Most commonly, the Bmh and R variables should be vectors or scalars (although see
    below for a less common 2D option). If one of these variables is a vector, then it
    should have one element per segment in the network. If a scalar, then the same value
    is used to assess potential sediment volume for each segment in the network. The
    i15 variable should be a vector with one element per rainfall intensity. The model
    will be run over the entire stream network for each i15 value.

    The output will be a tuple of 3 numpy arrays, in order: V, Vmin, and Vmax. The
    V array will have up to two dimensions. The first dimension is is stream segments,
    and the second dimension is rainfall intensities. By default, the second dimension
    will be removed if there is a single rainfall intensity (and see the keepdims option
    below to return arrays with constant numbers of dimensions). For this base syntax,
    the Vmin and Vmax arrays will always match the shape of the V array, but this is not
    always the case for the more complex syntaxes detailed below.

    emergency(..., *, B, Ci, Cb, Cr)
    Also specifies the parameters to use in the model. These are the intercept (B),
    rainfall intensity coefficient (Ci), burned area coefficient (Cb), and relief
    coefficient (Cr). By default, each coefficient is set to the value presented
    in Gartner et al., 2014. This syntax allows you to run the model using different
    parameter values - for example, for an updated model calibration.

    In this case, the model solves the generalized equation:
        lnV = B +  Ci * sqrt(i15)  +  Cb * ln(Bmh)  +  Cr * sqrt(R)
        V = exp(lnV)

    In many cases, input parameters will be scalar. However, this syntax also allows
    parameters to be vectors, in which each value is used for a distinct model run.
    Here, a "run" is defined as a unique set of model parameters. All parameters with
    more than one value must have the same number of runs. Parameters with a single
    value will use the same value for each run. This setup can be useful for comparing
    results for different parameters - for example, using a Monte Carlo process to
    calibrate model parameters.

    The Bmh and R variables also support values for distinct runs. In this case, Bmh
    and/or R should be a matrix. Note that whenever Bmh or R have more than one
    dimension, then the variable is parsed as a matrix. In this case, each row is a
    stream segment, and each column is a parameter run. Each column will be used to
    solve the model for (only) the associated parameter run. If B, Ci, Cb, and Cr are
    all scalar, then this syntax effectively allows you to test multiple values for each
    Bmh and R variable - for example, to test the model using different datasets to
    derive input variables.

    When implementing multiple runs, then the output V array will have up to three
    dimensions (stream segments x rainfall intensities x parameter runs). The Vmax and
    Vmin arrays will match the shape of the V array. By default, this function removes
    singleton dimensions from the output arrays. The first dimension is always retained,
    but the second is removed if there is a single rainfall intensity, and the third is
    removed if there is a single run. (And see the keepdims option below to return
    arrays with constant numbers of dimensions).

    emergency(..., *, CI, RSE)
    Also specifies parameters for estimating confidence intervals. CI are the
    confidence intervals and should be values between 0 and 1. For example, use 0.95 to
    estimate the 95% confidence interval. RSE is the residual standard error of the
    model. When using these parameters, the confidence interval is calculated using:
        Vmin = exp(lnV - X * RSE)
        Vmax = exp(lnV + X * RSE)

    Here, X is a percentile multiplier computed from a normal distribution, such that:
        q = 1 - (1 - CI)/2
        X = norm.ppf(q)

    The CI input should be a vector with one element per confidence interval that should
    be calculated. Alternatively, set CI to None or an empty vector to disable the
    confidence interval calculations. When specifying confidence intervals, the output
    V array will have up to 3 dimensions (segments x i15 x runs). By contrast, the Vmax
    and Vmin arrays may have up to 4 dimensions (segments x i15 x runs x CIs). By default,
    removes singleton dimensions from the output arrays, but see the keepdims option to
    return arrays with a fixed number of dimensions. If the confidence intervals are
    disabled, then Vmax and Vmin will be empty arrays, such that the length of their
    final dimension is 0.

    The RSE input may be a scalar, vector, or matrix. If scalar, uses the same RSE for
    all confidence interval calculations. If a vector, then each element is interpreted
    as the RSE for a distinct parameter run. This can be useful when calculating
    confidence intervals for different model calibrations. If RSE has more than one
    dimension, then it is interpreted as a matrix. Each row holds the values for a
    parameter run, and each column is the value for one of the input confidence
    intervals. This can be useful for calculating the same CI using different RSE
    values.

    emergency(..., *, keepdims = True)
    Returns arrays with a fixed number of dimensions. The V array will always have 3
    dimensions (segments x i15 x parameter runs), whereas the Vmax and Vmin arrays will
    always have 4 dimensions (segments x i15 x parameter runs x confidence intervals).
    ----------
    Inputs:
        i15: Peak 15-minute rainfall intensities in mm/hour.
        Bmh: Catchment area burned at moderate or high intensity in km^2
        R: Watershed relief in meters
        B: The model intercept
        Ci: The coefficient of the i15 rainfall intensity term
        Cb: The coefficient of the Bmh burned area term
        Cr: The coefficient of the R watershed relief term
        CI: The confidence interval to calculate. Values on the interval from 0 to 1.
        RSE: The residual standard error of the model. Used to compute confidence intervals
        keepdims: True to return arrays with constant numbers of dimensions. False (default)
            to remove singleton dimensions.

    Outputs:
        numpy array (Segments x i15 x Runs): The predicted debris-flow sediment volumes in m^3
        numpy array (Segments x i15 x Runs x CIs): The lower bound of the confidence interval
        numpy array (Segments x i15 x Runs x CIs): The upper bound of the confidence interval
    """

    # Validate rainfall, parameters, variables, confidence intervals
    parameters = {"B": B, "Ci": Ci, "Cb": Cb, "Cr": Cr}
    variables = {"Bmh": Bmh, "R": R}
    i15, (B, Ci, Cb, Cr), (Bmh, R), CI, RSE = _validate(
        i15, "i15", parameters, variables, CI, RSE
    )

    # Solve the model. Compute CIs. Optionally remove trailing singletons
    lnV = B + Ci * sqrt(i15) + Cb * log(Bmh) + Cr * sqrt(R)
    return _volumes(lnV, CI, RSE, keepdims)


@np.errstate(divide="ignore")  # Suppress divide-by-zero warning for log(0)
def longterm(
    i60: Variable,
    Bt: Variable,
    T: Variable,
    A: Variable,
    R: Variable,
    *,
    B: Parameter = 6.07,
    Ci: Parameter = 0.71,
    Cb: Parameter = 0.22,
    Ct: Parameter = -0.24,
    Ca: Parameter = 0.49,
    Cr: Parameter = 0.03,
    CI: Parameter | None = 0.95,
    RSE: Parameter = 1.25,
    keepdims: bool = False,
) -> Volumes:
    """
    Solves the long-term model (Equation 2)
    ----------
    longterm(i60, Bt, T, A, R)
    Solves the emergency assessment model given peak 60-minute rainfall intensity
    in mm/h (i60), the catchment area burned at any severity level in km^2 (Bt),
    time since the most recent fire in years (T), total watershed area in km^2 (A),
    and watershed relief in m (R). Returns the predicted volume of debris-flow
    sediment in m^3 (V), the lower bounds of the 95% confidence interval (Vmin),
    and the upper bound of the 95% confidence interval (Vmax).

    The model solves the equation:
        lnV = 6.07 + 0.71*ln(i60) + 0.22*ln(Bt) - 0.24*ln(T) + 0.49*ln(A) + 0.03*sqrt(R)
        V = exp(lnV)

    and uses residual standard error (RSE = 1.25) to estimate the bounds of the
    95% confidence interval:
        Vmin = exp(lnV - 1.96 * 1.25)
        Vmax = exp(lnV + 1.96 * 1.25)
    Note that the volume confidence interval is estimated using a normal distribution,
    hence the 1.96 percentile multiplier for a 95% interval.

    Most commonly, the Bt, T, A, and R variables should be vectors or scalars (although
    see below for a less common 2D option). If a variable is scalar, then the same value
    is used to assess potential sediment volume for each segment in the network. T is
    often a scalar, although see the next syntax for its vector case. If Bt, A, or R is
    a vector, then the variable should have one element per segment in the network. The
    i60 variable should be a vector with one element per rainfall intensity. The model
    will be run over the entire stream network for each i60 value.

    The output will be a tuple of 3 numpy arrays, in order: V, Vmin, and Vmax. The
    V array will have up to two dimensions. The first dimension is is stream segments,
    and the second dimension is rainfall intensities. By default, the second dimension
    will be removed if there is a single rainfall intensity (and see the keepdims option
    below to return arrays with constant numbers of dimensions). For this base syntax,
    the Vmin and Vmax arrays will always match the shape of the V array, but this is not
    always the case for the more complex syntaxes detailed below.

    longterm(..., *, B, Ci, Cb, Ct, Ca, Cr)
    Also specifies the parameters to use in the model. These are the intercept (B),
    rainfall intensitiy coefficient (Ci), burned area coefficient (Cb), elapsed
    time coefficient (Ct), total area coefficient (Ca), and relief coefficient (Cr).
    By default, each coefficient is set to the value presented in Gartner et al., 2014.
    This syntax allows you to run the model using different parameter values. For
    example, for an updated model calibration.

    In this case, the model solves the generalized equation:
        lnV = B + Ci*ln(i60) + Cb*ln(Bt) + Ct*ln(T) + Ca*ln(A) + Cr*sqrt(R)
        V = exp(lnV)

    In many cases, input parameters will be scalar. However, this syntax also allows
    parameters to be vectors, in which each value is used for a distinct model run.
    Here, a "run" is defined as a unique set of model parameters. All parameters with
    more than one value must have the same number of runs. Parameters with a single
    value will use the same value for each run. This setup can be useful for comparing
    results for different parameters - for example, using a Monte Carlo process to
    calibrate model parameters.

    The Bt, T, A, and R variables also support values for distinct runs. If T is a
    vector, then it is interpreted as one value per parameter run. Otherwise, a variable
    should be a matrix to support multiple runs. Note that whenever one of these variables
    has more than one dimension, then the variable is parsed as a matrix. In this case,
    each row is a stream segment, and each column is a parameter run. Each column will
    be used to solve the model for (only) the associated parameter run. If B, Ci, Cb,
    Ct, Ca, and Cr are all scalar, then this syntax effectively allows you to test
    multiple values of the Bt, T, A, and/or R variables - for example, to run the model
    using different numbers of years of recovery.

    When implementing multiple runs, then the output V array will have up to three
    dimensions (stream segments x rainfall intensities x parameter runs). The Vmax and
    Vmin arrays will match the shape of the V array. By default, this function removes
    singleton dimensions from the output arrays. The first dimension is always retained,
    but the second is removed if there is a single rainfall intensity, and the third is
    removed if there is a single run. (And see the keepdims option below to return
    arrays with constant numbers of dimensions).

    longterm(..., *, CI, RSE)
    Also specifies parameters for estimating confidence intervals. CI are the
    confidence intervals and should be values between 0 and 1. For example, use
    CI=0.95 to estimate the 95% confidence interval. RSE is the residual standard
    error of the model. When using these parameters, the confidence interval is
    calculated using:
        Vmin = exp[lnV - X * RSE]
        Vmax = exp[lnV + X * RSE]

    Here, X is a percentile multiplier computed from a normal distribution, such
    that:
        q = 1 - (1 - CI)/2
        X = norm.ppf(q)

    The CI input should be a vector with one element per confidence interval that should
    be calculated. Alternatively, set CI to None or an empty vector to disable the
    confidence interval calculations. When specifying confidence intervals, the output
    V array will have up to 3 dimensions (segments x i60 x runs). By contrast, the Vmax
    and Vmin arrays may have up to 4 dimensions (segments x i60 x runs x CIs). By default,
    removes singleton dimensions from the output arrays, but see the keepdims option to
    return arrays with a fixed number of dimensions. If the confidence intervals are
    disabled, then Vmax and Vmin will be empty arrays, such that the length of their
    final dimension is 0.

    The RSE input may be a scalar, vector, or matrix. If scalar, uses the
    same RSE for all confidence interval calculations. If a vector, then each element
    is interpreted as the RSE for a distinct parameter run. This can be useful when
    calculating confidence intervals for different model calibrations. If RSE has more
    than one dimension, then it is interpreted as a matrix. Each row holds the values
    for a parameter run, and each column is the value for one of the input confidence
    intervals. This can be useful for calculating the same CI using different RSE
    values.

    longterm(..., *, keepdims = True)
    Returns arrays with a fixed number of dimensions. The V array will always have 3
    dimensions (segments x i60 x parameter runs), whereas the Vmax and Vmin arrays will
    always have 4 dimensions (segments x i60 x parameter runs x confidence intervals).
    ----------
    Inputs:
        i60: Peak 60-minute rainfall intensities in mm/hour
        Bt: Total burned catchment area in km^2
        T: Time elapsed since fire in years
        A: Total catchment area in km^2
        R: Watershed relief in meters
        B: The model intercept
        Ci: The coefficient of the i60 rainfall intensity term
        Cb: The coefficient of the Bt burned area term
        Ct: The coefficient of the T elapsed time term
        Ca: The coefficient of the A total area term
        Cr: The coefficient of the R watershed relief term
        CI: The confidence interval to calculate. Should be on the interval from 0 to 1.
        RSE: The residual standard error of the model. Used to compute confidence intervals
        keepdims: True to return arrays with constant numbers of dimensions. False (default)
            to remove singleton dimensions.

    Outputs:
        numpy array (Segments x i15 x Runs): The predicted debris-flow sediment volumes in m^3
        numpy array (Segments x i15 x Runs x CIs): The lower bound of the confidence interval
        numpy array (Segments x i15 x Runs x CIs): The upper bound of the confidence interval
    """

    # Validate rainfall, parameters, variables, confidence intervals
    parameters = {"B": B, "Ci": Ci, "Cb": Cb, "Ct": Ct, "Ca": Ca, "Cr": Cr}
    variables = {"Bt": Bt, "T": T, "A": A, "R": R}
    i60, (B, Ci, Cb, Ct, Ca, Cr), (Bt, T, A, R), CI, RSE = _validate(
        i60, "i60", parameters, variables, CI, RSE
    )

    # Solve model. Compute CIs. Optionally remove singletons
    lnV = B + Ci * log(i60) + Cb * log(Bt) + Ct * log(T) + Ca * log(A) + Cr * sqrt(R)
    return _volumes(lnV, CI, RSE, keepdims)


def _volumes(lnV: Volume, CI: Parameter, RSE: Parameter, keepdims: bool) -> Volumes:
    "Converts ln(V) to expected, min, and max volumes"

    # Compute the percentile multipliers
    q = 1 - (1 - CI) / 2
    X = norm.ppf(q)

    # Compute volume and CI
    V = exp(lnV)
    Vmin = exp(lnV - X * RSE)
    Vmax = exp(lnV + X * RSE)

    # Clean singleton dimensions
    V = V.reshape(V.shape[:-1])
    V = clean_dims(V, keepdims)
    Vmin = clean_dims(Vmin, keepdims)
    Vmax = clean_dims(Vmax, keepdims)
    return V, Vmin, Vmax


#####
# Validation
#####


def _validate(
    I: Any,
    Iname: str,
    parameters: dict[str, Any],
    variables: dict[str, Any],
    CI: Any,
    RSE: Any,
) -> tuple[
    RealArray, tuple[RealArray, ...], tuple[RealArray, ...], RealArray, RealArray
]:
    "Checks that model inputs are valid and reshapes for broadcasting"

    I = _validate_intensity(I, Iname)
    parameters, nruns = _validate_parameters(parameters)
    variables, nruns = _validate_variables(variables, nruns)
    CI, RSE = _validate_ci(CI, RSE, nruns)
    return I, parameters, variables, CI, RSE


def _validate_intensity(I, Iname):
    "Validates rainfall intensities and reshapes for broadcasting"

    I = validate.vector(I, Iname, dtype=real)
    validate.positive(I, Iname, allow_zero=True, ignore=nan)
    return I.reshape(1, -1, 1, 1)


def _validate_parameters(
    parameters: dict[str, Any]
) -> tuple[ValidatedParameters, nRuns]:
    """Checks that parameters are real-valued vectors with broadcastable shapes.
    Returns the number of runs and a tuple of validated arrays"""

    # Check each parameter is a real-valued vector
    nruns = 1
    for name, parameter in parameters.items():
        parameter = validate.vector(parameter, name, dtype=real)

        # Record the length and name of the first parameter with multiple runs
        if parameter.size > 1:
            if nruns == 1:
                nruns = parameter.size
                set_nruns = name

            # Require parameters with multiple runs to have the same shape
            elif parameter.size != nruns:
                raise ShapeError(
                    "All parameters with multiple values must have the same number of runs. "
                    f"However {set_nruns} has {nruns} values, whereas {name} has {parameter.size}."
                )

        # Reshape for broadcasting and record array
        parameter = parameter.reshape(1, 1, -1, 1)
        parameters[name] = parameter
    return tuple(parameters.values()), nruns


def _validate_variables(
    variables: dict[str, Any], nruns: int
) -> tuple[tuple[MatrixArray, ...], int]:
    "Checks that variables are positive, real-valued matrices with allowed shapes"

    # Vector T is a special case - interpret as multiple runs, not segments
    nsegments = 1
    for name, variable in variables.items():
        if name == "T":
            variable = validate.array(variable, name, dtype=real)
            if variable.ndim == 1:
                variable = variable.reshape(1, -1)
        variable = validate.matrix(variable, name, dtype=real)

        # Get shape. Update nruns if this is the first input with multiple runs
        nrows, ncols = variable.shape
        if ncols > 1 and nruns == 1:
            nruns = ncols

        # Otherwise must either have 1 or nruns columns
        elif ncols != 1 and ncols != nruns:
            raise ShapeError(
                f"Each variable must have either 1 or {nruns} runs. "
                f"However, {name} has {ncols} runs."
            )

        # Record the shape and name of the first variable with multiple rows
        if nrows > 1:
            if nsegments == 1:
                nsegments = nrows
                set_segments = name

            # Require variables with multiple rows to have the same shape
            elif nrows != nsegments:
                raise ShapeError(
                    f"All variables with multiple stream segments must have the same "
                    f"number of segments. "
                    f"However, {set_segments} has {nsegments} segments, "
                    f"whereas {name} has {nrows}."
                )

        # Elements must be positive
        validate.positive(variable, name, allow_zero=True, ignore=nan)

        # Reshape for broadcasting and record array
        variable = variable.reshape(nrows, 1, ncols, 1)
        variables[name] = variable
    return tuple(variables.values()), nruns


def _validate_ci(CI: Any, RSE: Any, nruns: int) -> tuple[RealArray, RealArray]:
    "Checks that CI and RSE are valid and reshapes for broadcasting"

    # Disable or validate CI
    if CI is None:
        CI = np.array([])
    else:
        CI = validate.vector(CI, "CI", dtype=real, allow_empty=True)
        validate.inrange(CI, "CI", min=0, max=1)
        CI = CI.reshape(1, 1, 1, -1)

    # Just exit if there are no confidence intervals
    if CI.size == 0:
        return CI, np.nan

    # RSE should be a matrix of positive values
    RSE = validate.matrix(RSE, "RSE", dtype=real)
    validate.positive(RSE, "RSE", allow_zero=True)

    # RSE should be 1|nruns x 1|nCI
    nrows, ncols = RSE.shape
    if (nrows > 1) and (nruns != 1) and (nrows != nruns):
        raise ShapeError(
            f"RSE must have either 1 or {nruns} rows, but it has {nrows} rows instead."
        )
    elif ncols not in [1, CI.size]:
        raise ShapeError(
            f"RSE must have either 1 or {CI.size} columns, but it has {ncols} columns instead."
        )
    RSE = RSE.reshape(1, 1, nrows, ncols)
    return CI, RSE
