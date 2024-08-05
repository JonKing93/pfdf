"Code for the parameter sweep tutorial"

import numpy as np
from pfdf.models import s17
import assessment

# Load values from the assessment
segments = assessment.segments
T = assessment.T
F = assessment.F
S = assessment.S

# Get M1 variables and rainfall parameters
duration_min = 15
R_mm = 6

# Solve model using multiple values of a parameter
B, _, Cf, Cs = s17.M1.parameters(durations=duration_min)
Ct = np.arange(0.01, 1.01, 0.01)
p1 = s17.likelihood(R_mm, B, Ct, T, Cf, F, Cs, S)

# Solve model using multiple values of multiple parameters
Ct = 0.4 + 0.25 * np.random.rand(1000)
Cf = 0.67 + 0.3 * np.random.rand(1000)
p2 = s17.likelihood(R_mm, B, Ct, T, Cf, F, Cs, S)
