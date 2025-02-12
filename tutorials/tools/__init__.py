"""
Tools to help implement the tutorials
----------
Functions:
    print_path      - Prints a path, removing folders outside the tutorial workspace
    print_contents  - Prints folder contents that end in a given extension

Modules:
    workspace       - Functions to clean and validate the tutorial workspace
    examples        - Functions to build example datasets
    plot            - Functions to plot tutorial results
    _print          - Module implementing the print functions
"""

from ._print import print_contents, print_path
