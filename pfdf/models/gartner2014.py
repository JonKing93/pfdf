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
    _validate_parameters    Checks that input parameters are valid
    _validate_variables     - Checks that input variables are valid


"""

from typing import Any, Dict, Tuple

import numpy as np
from numpy import exp, log, nan, sqrt

import pfdf._validate.core as validate
from pfdf._utils import clean_dims, real
from pfdf.errors import ShapeError
from pfdf.typing import MatrixArray, Parameters, Variables, VectorArray, Volumes

#####
# User Functions
#####


@np.errstate(divide="ignore")  # Suppress divide-by-zero warning for log(0)
def emergency(
    i15: Variables,
    Bmh: Variables,
    R: Variables,
    *,
    B: Parameters = 4.22,
    Ci: Parameters = 0.39,
    Cb: Parameters = 0.36,
    Cr: Parameters = 0.13,
    keepdims: bool = False,
) -> Volumes:
    """
    emergency  Solves the emergency assessment model (Equation 3 from Gartner et al., 2014)
    ----------
    emergency(i15, Bmh, R)
    Solves the emergency assessment model given peak 15-minute rainfall intensity
    in mm/h (i15), the catchment area burned at moderate-or-high intensity
    in km^2 (Bmh), and the watershed relief in meter (R). Returns the potential
    volume of debris-flow sediment in m^3 (V).

    The model solves the equation:
        V = exp[ 4.22 +  0.39 * sqrt(i15)  +  0.36 * ln(Bmh)  +  0.13 * sqrt(R) ]

    Each of the three input variables may either be a scalar, vector, or matrix
    of data values. If a variable is scalar, then the same value is used to assess
    potential sediment volume for each segment in the network.

    If Bmh or R are a 1D array, then they should have one element per segment in
    the network. By contrast, if i15 is a 1D array, then each element is interpreted
    as a parameter for a distinct run of the model. Essentially, the model is run
    over the stream network for each value of i15.

    If a variable has more than 1 dimension, then it is parsed as a matrix. Rows
    are interpreted as values for segments, and columns are runs of the model. A
    variable may have either 1 row or one row per segment. If it has 1 row, then the
    same value is used for every segment per run. The matrix may have either 1
    column or one column per run. If it has 1 column, then the same values are
    used for each run.

    The output volumes will either be a 1D array (for a single run), or a
    2D array (for multiple runs). Each row holds the values for one stream segment,
    and each column is a run. (And see below for an option to always return 2D output).

    emergency(..., *, B, Ci, Cb, Cr)
    Also specifies the parameters to use in the model. These are the intercept (B),
    rainfall intensity coefficient (Ci), burned area coefficient (Cb), and relief
    coefficient (Cr). By default, each coefficient is set to the value presented
    in Gartner et al., 2014. This syntax allows you to run the model using different
    parameter values - for example, for an updated model calibration.

    In this case, the model solves the generalized equation:
        V = exp[ B +  Ci * sqrt(i15)  +  Cb * ln(Bmh)  +  Cr * sqrt(R) ]

    In many cases, input parameters will be scalar. However, this syntax also allows
    parameters to be vectors, in which each value is used for a distinct model run.
    All parameters with more than one value must have the same number of runs.
    Parameters with a single value will use the same value for each run. This setup
    can be useful for comparing results for different parameters - for example,
    using a Monte Carlo process to calibrate model parameters.

    emergency(..., *, keepdims = True)
    Always returns output as a 2D array, regardless of the number of parameter runs.
    ----------
    Inputs:
        i15: Peak 15-minute rainfall intensities in mm/hour.
        Bmh: Catchment area burned at moderate or high intensity in km^2
        R: Watershed relief in meters
        B: The model intercept
        Ci: The coefficient of the i15 rainfall intensity term
        Cb: The coefficient of the Bmh burned area term
        Cr: The coefficient of the R watershed relief term
        keepdims: True to always return a 2D numpy array. If False (default),
            returns a 1D array when there is a single parameter run.

    Outputs:
        numpy 2D array (Segments x Parameter Runs): The predicted debris-flow
            sediment volumes in m^3
    """

    # Validate
    parameters = {"B": B, "Ci": Ci, "Cb": Cb, "Cr": Cr}
    variables = {"i15": i15, "Bmh": Bmh, "R": R}
    (B, Ci, Cb, Cr), nruns = _validate_parameters(parameters)
    i15, Bmh, R = _validate_variables(variables, nruns)

    # Solve the model. Optionally remove trailing singletons
    lnV = B + Ci * sqrt(i15) + Cb * log(Bmh) + Cr * sqrt(R)
    V = exp(lnV)
    return clean_dims(V, keepdims)


@np.errstate(divide="ignore")  # Suppress divide-by-zero warning for log(0)
def longterm(
    i60: Variables,
    Bt: Variables,
    T: Variables,
    A: Variables,
    R: Variables,
    *,
    B: Parameters = 6.07,
    Ci: Parameters = 0.71,
    Cb: Parameters = 0.22,
    Ct: Parameters = -0.24,
    Ca: Parameters = 0.49,
    Cr: Parameters = 0.03,
    keepdims=False,
) -> Volumes:
    """
    longterm  Solves the long-term model (Equation 2)
    ----------
    longterm(i60, Bt, T, A, R)
    Solves the emergency assessment model given peak 60-minute rainfall intensity
    in mm/h (i60), the catchment area burned at any severity level in km^2 (Bt),
    time since the most recent fire in years (T), total watershed area in km^2 (A),
    and watershed relief in m (R). Returns the predicted volume of debris-flow
    sediment in m^3 (V).

    The model solves the equation:
        V = exp[ 6.07 + 0.71*ln(i60) + 0.22*ln(Bt) - 0.24*ln(T) + 0.49*ln(A) + 0.03*sqrt(R) ]

    Each of the input variables may either be a scalar, vector, or matrix of data values.
    If a variable is scalar, then the same value is used to compute potential sediment
    volume for each segment in the network.

    If Bt, A, or R are a 1D array, then they should have one element per segment
    in the network. By contrast, if i60 or T are a 1D array, then each element is
    interpreted as a parameter for a distinct run of the model. Essentially, the
    model is run over the stream network for each pair of i15 and T values.

    If a variable has more than 1 dimension, then it is parsed as a matrix. Rows
    are interpreted as values for segments, and columns are runs of the model. A
    variable may have either 1 row or one row per segment. If it has 1 row, then the
    same value is used for every segment per run. The matrix may have either 1
    column or one column per run. If it has 1 column, then the same values are
    used for each run.

    The output volumes will either be a 1D array (for a single run), or a
    2D array (for multiple runs). Each row holds the values for one stream segment,
    and each column is a run. (And see below for an option to always return 2D output).

    longterm(..., *, B, Ci, Cb, Ct, Ca, Cr)
    Also specifies the parameters to use in the model. These are the intercept (B),
    rainfall intensitiy coefficient (Ci), burned area coefficient (Cb), elapsed
    time coefficient (Ct), total area coefficient (Ca), and relief coefficient (Cr).
    By default, each coefficient is set to the value presented in Gartner et al., 2014.
    This syntax allows you to run the model using different parameter values -
    for example, for an updated model calibration.

    In this case, the model solves the generalized equation:
        V = exp[ B + Ci*ln(i60) + Cb*ln(Bt) + Ct*ln(T) + Ca*ln(A) + Cr*sqrt(R) ]

    In many cases, input parameters will be scalar. However, this syntax also allows
    parameters to be vectors, in which each value is used for a distinct model run.
    All parameters with more than one value must have the same number of runs.
    Parameters with a single value will use the same value for each run. This setup
    can be useful for comparing results for different parameters - for example,
    using a Monte Carlo process to calibrate model parameters.

    longterm(..., *, keepdims = True)
    Always returns output as a 2D array, regardless of the number of parameter runs.
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
        keepdims: True to always return a 2D numpy array. If False (default),
            returns a 1D array when there is a single parameter run.

    Outputs:
        numpy 2D array (Segments x Parameter Runs): The predicted debris-flow
            sediment volumes in m^3
    """

    # Validate
    parameters = {"B": B, "Ci": Ci, "Cb": Cb, "Ct": Ct, "Ca": Ca, "Cr": Cr}
    variables = {"i60": i60, "Bt": Bt, "T": T, "A": A, "R": R}
    (B, Ci, Cb, Ct, Ca, Cr), nruns = _validate_parameters(parameters)
    i60, Bt, T, A, R = _validate_variables(variables, nruns)

    # Solve the model. Optionally remove trailing singletons
    lnV = B + Ci * log(i60) + Cb * log(Bt) + Ct * log(T) + Ca * log(A) + Cr * sqrt(R)
    V = exp(lnV)
    return clean_dims(V, keepdims)


#####
# Internal Utilities
#####


def _validate_parameters(
    parameters: Dict[str, Any]
) -> tuple[tuple[VectorArray, ...], int]:
    """Checks that parameters are real-valued vectors with broadcastable shapes.
    Returns the number of runs and a tuple of validated arrays"""

    # Check each parameter is a real-valued vector
    nruns = 1
    for name, parameter in parameters.items():
        parameter = validate.vector(parameter, name, dtype=real)
        parameters[name] = parameter

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
    return tuple(parameters.values()), nruns


def _validate_variables(
    variables: Dict[str, Any], nruns: int
) -> Tuple[MatrixArray, ...]:
    "Checks that variables are positive, real-valued matrices with allowed shapes"

    # Check each variable is a real-valued matrix. Interpret 1D intensity/time
    # as runs, rather than segments
    nsegments = 1
    for name, variable in variables.items():
        if name in ["i15", "i60", "T"]:
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
                    "All variables with multiple stream segments must have the same number of segments. "
                    f"However, {set_segments} has {nsegments} segments, whereas {name} has {nrows}."
                )

        # Elements must be positive
        validate.positive(variable, name, allow_zero=True, ignore=nan)
        variables[name] = variable
    return tuple(variables.values())
