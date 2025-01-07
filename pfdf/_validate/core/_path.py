"""
Functions that validate file/folder paths
----------
Functions:
    _path           - Checks an input represents a Path. Returns the resolved path
    input_file      - Checks an input is an existing path. Note that folders are permitted
    output_file     - Checks an output is a path, optionally allowed overwriting
    output_folder   - Checks output is the path to a non-existent or empty folder
"""

from __future__ import annotations

import typing
from pathlib import Path

import pfdf._validate.core._low as validate

if typing.TYPE_CHECKING:
    from typing import Any


def _path(path: Any) -> Path:
    "Checks an input represents a Path object and returns the resolved path"

    if isinstance(path, str):
        path = Path(path)
    validate.type(path, "path", Path, "filepath")
    return path.resolve()


def input_file(path: Any) -> Path:
    """Checks an input is an existing path. Note that folders are permitted because
    many GIS "files" are actually a structured folder (e.g. geodatabases)"""

    path = _path(path)
    return path.resolve(strict=True)


def output_file(path: Any, overwrite: bool) -> Path:
    "Checks a path is suitable for an output file, optionally allowing overwriting"

    path = _path(path)
    if (not overwrite) and path.exists():
        raise FileExistsError(
            f"Output file already exists:\n\t{path}\n"
            'If you want to replace existing files, set "overwrite=True"'
        )
    return path


def output_folder(path: Any, default: str) -> Path:
    """Checks an input represents a path for an output folder. If the path exists,
    then it must be empty. Overwriting contents is not permitted."""

    # Default if unset
    if path is None:
        path = Path.cwd() / default

    # Convert to path. Prevent existing folders
    path = _path(path)
    if path.exists():
        raise FileExistsError(f"`path` already exists:\n\t{path}")
    return path
