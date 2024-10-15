"""
Type hints for assessment model outputs
"""

from numpy import ndarray

from pfdf.typing.core import MatrixArray, vector
from pfdf.typing.segments import SegmentValues

# Generic
Variable = SegmentValues | MatrixArray
Parameter = vector  # Vector of parameter values

# G14
Volume = ndarray  # Segments x I15 x Parameters x CI
Volumes = tuple[Volume, Volume, Volume]

# S17 P-values and R-values
Probabilities = vector  # Input vector of p-values
Likelihoods = ndarray  # Segments x Accumulations x Runs
AccumulationVector = vector  # Input vector of accumulations
Accumulations = ndarray  # Segments x p-values x Runs

# S17 variables and parameters
Durations = vector  # Vector of input rainfall durations
Variables = tuple[Variable, Variable, Variable]
Parameters = tuple[Parameter, Parameter, Parameter, Parameter]
