"""
cannon2010  Implements a combined hazard (probability + volume) assessment model
----------
This module implements the combined relative hazard classification model presented
in Cannon et al., 2010 (see citation below). This model determines a relative
hazard class for a debris flow by considering both the probability and potential
sediment volume of the debris flow. In brief, the model classifies both probability
and volume hazards and assigns a score to each class. These two scores are then 
added together, and the combined score is used to determine a final hazard 
classification.

CITATION:
Cannon, S. H., Gartner, J. E., Rupert, M. G., Michael, J. A., Rea, A. H., 
& Parrett, C. (2010). Predicting the probability and volume of postwildfire debris 
flows in the intermountain western United States. Geological Society of America
Bulletin, 122(1-2), 127-144. 
https://doi.org/10.1130/B26459.1
----------
User Functions:
    hazard  - Determines the combined relative hazard classes for a set of debris flows
    pscore  - Returns the classification score for debris flow probabilities
    vscore  - Returns the classification score for debris flow sediment volumes
    hscore  - Returns the combined hazard class given combined hazard scores

Internal validaters:
    _validate_probabilities - Checks that input probabilities are valid
    _validate_thresholds    - Checks that input class thresholds are valid
    _validate_volumes       - Checks that input sediment volumes are valid
"""


from typing import Any, Tuple

import numpy as np

from pfdf._utils import real, validate
from pfdf._utils.classify import classify
from pfdf.typing import RealArray, VectorArray, scalar, vector

#####
# User Functions
#####


def hazard(
    probabilities: RealArray,
    volumes: RealArray,
    *,
    p_thresholds: vector = [0.25, 0.5, 0.75],
    v_thresholds: vector = [1e3, 1e4, 1e5],
    h_thresholds: vector = [3, 6],
) -> RealArray:
    """
    hazard  Computes the combined relative hazard scores for a set of debris flows
    ----------
    hazard(probabilities, volumes)
    Computes combined relative hazard classes, given a set of debris flow
    probabilities and potential sediment volumes (meters^3). The shapes of the
    probability and volume arrays must be broadcastable.

    hazard(..., *, p_thresholds)
    hazard(..., *, v_thresholds)
    hazard(..., *, h_thresholds)
    Specify custom thresholds for the (p)robability, (v)olume, and (h)azard
    classification scores. Each set of thresholds must be a set of N positive values
    in an increasing order. Note that N defines the number of breakpoints, so
    the number of classifications will be N+1. Elements of p_thresholds must be
    on the interval from 0 to 1, v_thresholds must be positive, and h_thresholds
    must be positive integers.

    Specifying v_thresholds relaxes the unit requirements for the input sediment
    volumes. When this is the case, v_thresholds and volumes must use the same
    units, but any units are permitted.
    ----------
    Inputs:
        probabilities: An array of debris flow probabilities. Values should be
            on the interval from 0 to 1.
        volumes: An array of debris flow volumes. If not specifying v_thresholds,
            then units should be meters^3. Otherwise, units should be the same as
            v_thresholds. The shape of this array must be broadcastable with the
            probabilities array.
        p_thresholds: Custom thresholds for the probability scores. Elements must
            be on the interval 0 to 1, in ascending order.
        v_thresholds: Custom thresholds for the volume scores. Elements must be
            positive values, in ascending order.
        h_thresholds: Custom thresholds for the combined hazard classification.
            Elements must be positive integers, in ascending order.

    Outputs:
        numpy array: The combined relative hazard classifications for the debris
            flows. The shape of this array is the shape obtained by broadcasting
            the probability scores with the volume scores.
    """

    # Validate thresholds
    Tp = _validate_thresholds(p_thresholds, "p_thresholds", range=[0, 1])
    Tv = _validate_thresholds(v_thresholds, "v_thresholds")
    Th = _validate_thresholds(h_thresholds, "h_thresholds", integers=True)

    # Validate arrays
    p = _validate_probabilities(probabilities)
    v = _validate_volumes(volumes)
    validate.broadcastable(p.shape, "probabilities", v.shape, "volumes")

    # Compute combined hazard score and classify
    pscore = classify(p, Tp)
    vscore = classify(v, Tv)
    combined = pscore + vscore
    return classify(combined, Th)


def pscore(
    probabilities: RealArray, thresholds: vector = [0.25, 0.5, 0.75]
) -> RealArray:
    """
    pscore  Scores a set of debris flow probabilities
    ----------
    pscore(probabilities)
    Returns the classification scores for a set of debris flow probabilities. (Note
    that probabilities should be on the interval from 0 to 1). Scores are assigned as
    follows:

        Probability | Score
        ----------- | -----
        [0, 0.25]   |   1
        (0.25, 0.5] |   2
        (0.5, 0.75] |   3
        (0.75, 1]   |   4
        NaN         |   NaN

    pscore(probabilities, thresholds)
    Specifies the thresholds used to score the probabilities. Each element in
    thresholds is the dividing point between two scores. The "thresholds"
    input should be a vector of N increasing values on the interval from 0 to 1,
    such that thresholds = [T1, T2, ..., Tn]. Scores are then assigned as follows:

        Probability | Score
        ----------- | -----
        [0, T1]     |   1
        (T1, T2]    |   2
        ...         |   ...
        (T_n-1, Tn] |   N
        (Tn, 1]     |   N+1
        NaN         |   NaN

    Note that N is the number of breakpoints, so the number of classification
    groups will be N+1.
    ----------
    Inputs:
        probabilities: An array of debris flow probabilities. Values should be on
            the interval from 0 to 1. NaN values are allowed and are given a
            score of NaN.
        thresholds: The probability thresholds to use for scoring. Must be a vector
            of increasing values on the interval from 0 to 1.

    Outputs:
        numpy array (float): The scores for the debris-flow probabilities
    """

    T = _validate_thresholds(thresholds, "thresholds", range=[0, 1])
    p = _validate_probabilities(probabilities)
    return classify(p, T)


def vscore(volumes: RealArray, thresholds: vector = [1e3, 1e4, 1e5]):
    """
    vscore  Scores a set of debris flow sediment volumes
    ----------
    vscore(volumes)
    Returns the classification scores for a set of debris flow sediment volumes
    (in units of meters^3). Scores are calculated as follows:

        Volume (m^3) | Score
        ------------ | -----
        [0, 1e3]     |   1
        (1e3, 1e4]   |   2
        (1e4, 1e5]   |   3
         > 1e5       |   4
         NaN         |  NaN

    vscore(volumes, thresholds)
    Specifies the thresholds to use for classifying debris flow sediment volumes.
    Each element in thresholds is the dividing point between two scores. The "thresholds"
    input should be a vector of N positive values in increasing order, such that
    thresholds = [T1, T2, ..., Tn]. Scores are then assigned as follows:

          Volume    | Score
        ----------- | -----
        [0, T1]     |   1
        (T1, T2]    |   2
        ...         |   ...
        (T_n-1, Tn] |   N
        (Tn, 1]     |   N+1
        NaN         |   NaN

    Note that this syntax permits any units for volumes, so long as the values in
    the volumes and thresholds arrays use the same units. Also note that N is the
    number of breakpoints, so the number of classification groups will be N+1.
    ----------
    Inputs:
        volumes: An array of potential debris-flow sediment volumes. If specifying
            thresholds, should use the same units as the thresholds. Otherwise,
            units should be meters^3. NaN values are allowed and are given a score
            of NaN.
        thresholds:
            The thresholds to use for classifying debris flow volumes. Must use
            the same units as the volumes.

    Outputs:
        numpy array (float): The classification scores of the debris flow volumes
    """

    T = _validate_thresholds(thresholds, "thresholds")
    v = _validate_volumes(volumes)
    return classify(v, T)


def hscore(combined: RealArray, thresholds: vector = [3, 6]):
    """
     hscore  Computes a combined hazard assessment score
     ----------
     hscore(combined)
     Classifies debris-flow hazard using the combined probability and volume
     classification score (i.e. combined = pscore + vscore). Hazards are then
     classified as follows:

        Combined Score | Hazard Class
        -------------- | ------------
            1 - 3      |   1 - Low
            4 - 6      |   2 - Moderate
             >7        |   3 - High
            NaN        |   NaN - Missing Data

    hscore(combined, thresholds)
    Specifies the thresholds to use for classifying debris flow hazards.
    Each element in thresholds is the dividing point between two classes. The
    "thresholds" input should be a vector of N positive integers, in
    increasing order, such that thresholds = [T1, T2, ..., Tn]. Hazard classes
    are then assigned as follows:

        Combined Score | Hazard Class
        -------------- | ------------
        [0, T1]        |   1
        (T1, T2]       |   2
        ...            |   ...
        (T_n-1, Tn]    |   N
        (Tn, 1]        |   N+1
        NaN            |   NaN

    Note that N is the number of breakpoints, so the number of classification
    groups will be N+1.
    ----------
    Inputs:
        combined: The combined relative hazard scores. This is the sum of the
            classification scores for probability and volume. NaN values are allowed
            and will receive a hazard class of NaN.
        thresholds: The thresholds to use to determine hazard classes. Should be
            a vector of N positive integers in ascending order.

    Outputs:
        numpy array (float): The hazard classes
    """

    T = _validate_thresholds(thresholds, "thresholds", integers=True)
    combined = validate.array(combined, "combined", dtype=real)
    validate.integers(combined, "combined", ignore=np.nan)
    validate.positive(combined, "combined", ignore=np.nan)
    return classify(combined, T)


#####
# Internal
#####


def _validate_probabilities(p: Any) -> RealArray:
    "Checks that input debris flow probabilities are valid"
    name = "probabilities"
    p = validate.array(p, name, dtype=real)
    validate.inrange(p, name, min=0, max=1, ignore=np.nan)
    return p


def _validate_volumes(v: Any) -> RealArray:
    "Checks that input sediment volumes are valid"
    name = "volumes"
    v = validate.array(v, name, dtype=real)
    validate.positive(v, name, allow_zero=True, ignore=np.nan)
    return v


def _validate_thresholds(
    thresholds: Any,
    name: str,
    range: Tuple[scalar, scalar] = [0, np.inf],
    integers: bool = False,
) -> VectorArray:
    "Checks that input thresholds are valid"
    thresholds = validate.vector(thresholds, name, dtype=real)
    validate.inrange(thresholds, name, min=range[0], max=range[1])
    validate.sorted(thresholds, name)
    if integers:
        validate.integers(thresholds, name)
    return thresholds
