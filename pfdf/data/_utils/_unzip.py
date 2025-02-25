"""
Function to extract zip archives downloaded via a HTTP request
----------
Function:
    unzip   - Extracts a zip archive represented as a byte string
"""

from __future__ import annotations

import shutil
import typing
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

if typing.TYPE_CHECKING:
    from typing import Optional


def unzip(data: bytes, path: Path, item: Optional[str] = None) -> None:
    """Extracts a zip archive provided in bytes (as is the case for zip files downloaded
    via HTTP request)"""

    # Save the archive to disk in a temp folder
    with TemporaryDirectory() as temp:
        temp = Path(temp)
        zipped = temp / "archive.zip"
        zipped.write_bytes(data)

        # Extract the zip archive
        extracted = temp / "extracted"
        with ZipFile(zipped) as zipped:
            zipped.extractall(extracted)

        # Get the final output folder and move to the requested path
        if item is not None:
            extracted = extracted / item
        shutil.copytree(src=extracted, dst=path)
