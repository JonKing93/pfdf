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

    def test_item(_, tmp_path, path):

        # Build two example files
        data = tmp_path / "data"
        data.mkdir()
        path1 = data / "file1.txt"
        path1.write_text("here is a file")
        path2 = data / "file2.txt"
        path2.write_text("and here is another file")

        # Build a zip archive with nested folders
        zipped = tmp_path / "source"
        with ZipFile(zipped, "w") as archive:
            archive.write(path1, "nested/file1.txt")
            archive.write(path2, "nested/file2.txt")

        # Get the archive bytes
        with open(zipped, "br") as file:
            zbytes = file.read()

        # Test
        assert not path.exists()
        unzip(zbytes, path, item="nested")
        assert path.exists()

        path1 = path / "file1.txt"
        assert path1.exists()
        assert path1.read_text() == "here is a file"

        path2 = path / "file2.txt"
        assert path2.exists()
        assert path2.read_text() == "and here is another file"
