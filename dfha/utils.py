"""
utils  Utility functions
"""


def aslist(input):
    "Place input in a list if not already a list"
    if not isinstance(input, list):
        input = [input]
    return input
