"""
Functions to print tutorial results in user-friendly formats
----------
Functions:
    print_path      - Prints a file path, stripping folders outside the tutorial workspace
    print_contents  - Prints folder content that end in a given extension
"""

from pathlib import Path


def print_path(path: Path):
    "Prints a data path, removing folders outside of the tutorial workspace"

    tutorials = Path(__file__).parents[1]
    path = Path("...") / path.relative_to(tutorials)
    print(path)


def print_contents(path: Path, extension: str):
    "Prints the contents of a folder that end with the given extension"

    contents = [item.name for item in path.iterdir() if item.suffix == extension]
    print(contents)
