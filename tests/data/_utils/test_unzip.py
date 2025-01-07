from zipfile import ZipFile

import pytest

from pfdf.data._utils import unzip


@pytest.fixture
def zbytes(zip_bytes, tmp_path):
    "A zip archive in bytes"

    files = {
        "file1.txt": "Here is a file",
        "file2.txt": "Here is another file",
    }
    return zip_bytes(tmp_path, files)


@pytest.fixture
def path(tmp_path):
    "Output path for zip extraction"
    return tmp_path / "final"


class TestUnzip:
    def test(_, zbytes, path):

        # Unzip and check the archive was created
        assert not path.exists()
        unzip(zbytes, path)
        assert path.exists()

        # First file
        file1 = path / "file1.txt"
        assert file1.exists()
        assert file1.read_text() == "Here is a file"

        # Second file
        file2 = path / "file2.txt"
        assert file2.exists()
        assert file2.read_text() == "Here is another file"

    def test_item(_, zbytes, path):

        path = path.parent / "test.txt"
        assert not path.exists()
        unzip(zbytes, path, "file1.txt")
        assert path.exists()
        assert path.read_text() == "Here is a file"
