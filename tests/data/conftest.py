import json
from io import BytesIO
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

import pytest
from requests import Response


@pytest.fixture
def response() -> Callable:
    "Returns a function to build customizable requests.Response objects"

    def response(status_code: int = 200, content: bytes = None) -> Response:
        "Returns a Response object suitable for mocking requests.get"
        response = Response()
        response.status_code = status_code
        if content is not None:
            response.raw = BytesIO(content)
        return response

    return response


@pytest.fixture
def json_response(response) -> Callable:
    "Returns a function to build requests.Response objects with JSON content"

    def json_response(content: dict, status_code: int = 200) -> Response:
        content = json.dumps(content).encode()
        return response(status_code, content)

    return json_response


@pytest.fixture
def zip_bytes() -> Callable:
    "Returns a function that zips a dataset and returns its bytes"

    def zip_bytes(tmp_path: Path, files: dict) -> bytes:

        # Build the archive
        zipped = tmp_path / "zipped"
        with ZipFile(zipped, "w") as archive:
            for arcname, data in files.items():
                if isinstance(data, str):
                    archive.writestr(arcname, data)
                else:
                    archive.write(data, arcname)

        # Extract the bytes
        with open(zipped, "rb") as file:
            return file.read()

    return zip_bytes


@pytest.fixture
def zip_response(zip_bytes, response) -> Callable:
    "Returns a function to build a requests.Response with zip archive"

    def zip_response(tmp_path: Path, files: dict) -> Response:

        content = zip_bytes(tmp_path, files)
        return response(200, content)

    return zip_response
