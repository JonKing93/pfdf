"""
Functions to validate buffering distances
----------
Functions:
    buffers     - Checks inputs represent buffering distances for a rectangle
    _distance   - Checks a buffering distance is a positive scalar
"""

from pfdf._utils import all_nones
from pfdf._validate._array import scalar
from pfdf._validate._elements import positive

#####
# Buffers
#####


def _distance(distance, name):
    "Checks that a buffering distance is a positive scalar"
    distance = scalar(distance, name)
    positive(distance, name, allow_zero=True)
    return distance


def buffers(distance, left, bottom, right, top):
    # Require a buffer
    if all_nones(distance, left, right, top, bottom):
        raise ValueError("You must specify at least one buffering distance.")

    # Validate default distance
    if distance is None:
        distance = 0
    else:
        distance = _distance(distance, "distance")

    # Parse and validate the buffers
    buffers = {"left": left, "bottom": bottom, "right": right, "top": top}
    for name, buffer in buffers.items():
        if buffer is None:
            buffer = distance
        else:
            buffer = _distance(buffer, name)
        buffers[name] = buffer

    # Require at least one non-zero buffer
    if not any(buffers.values()):
        raise ValueError("Buffering distances cannot all be 0.")
    return buffers
