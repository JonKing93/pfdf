from unittest.mock import patch
from zipfile import ZipFile

import pytest

from pfdf.data.retainments import la_county
from pfdf.raster import RasterMetadata

#####
# Testing fixtures
#####


@pytest.fixture
def response(tmp_path, zip_response):
    files = {
        "Debris_Basin.gdb/a0001.gdbindexes": "An index file in a gdb",
        "Debris_Basin.gdb/a0001.gdbtable": "A table file in a gdb",
    }
    return zip_response(tmp_path, files)


#####
# Tests
#####


class TestDataUrl:
    def test(_):
        output = la_county.data_url()
        assert (
            output
            == "https://pw.lacounty.gov/sur/nas/landbase/AGOL/Debris_Basin.gdb.zip"
        )


class TestDownload:
    @staticmethod
    def check_contents(output):
        "Checks the downloaded gdb was valid"

        file1 = output / "a0001.gdbindexes"
        file2 = output / "a0001.gdbtable"
        assert file1.exists()
        assert file2.exists()
        assert file1.read_text() == "An index file in a gdb"
        assert file2.read_text() == "A table file in a gdb"

    @patch("requests.get", spec=True)
    def test_default_path(self, mock, response, monkeypatch, tmp_path):
        mock.return_value = response
        monkeypatch.chdir(tmp_path)
        output = la_county.download()
        assert output == tmp_path / "la-county-retainments.gdb"
        self.check_contents(output)
        mock.assert_called_with(
            url="https://pw.lacounty.gov/sur/nas/landbase/AGOL/Debris_Basin.gdb.zip",
            params={},
            timeout=15,
        )

    @patch("requests.get", spec=True)
    def test_relative_path(self, mock, response, monkeypatch, tmp_path):
        mock.return_value = response
        monkeypatch.chdir(tmp_path)
        output = la_county.download("test.gdb")
        assert output == tmp_path / "test.gdb"
        self.check_contents(output)
        mock.assert_called_with(
            url="https://pw.lacounty.gov/sur/nas/landbase/AGOL/Debris_Basin.gdb.zip",
            params={},
            timeout=15,
        )

    @patch("requests.get", spec=True)
    def test_absolute_path(self, mock, response, tmp_path):
        mock.return_value = response
        path = tmp_path / "test.gdb"
        output = la_county.download(path)
        assert output == path
        self.check_contents(output)
        mock.assert_called_with(
            url="https://pw.lacounty.gov/sur/nas/landbase/AGOL/Debris_Basin.gdb.zip",
            params={},
            timeout=15,
        )


@pytest.mark.web(api="la-county")
class TestLive:
    def test(_, tmp_path):
        path = tmp_path / "test.gdb"
        output = la_county.download(tmp_path / "test.gdb")
        assert output == path
        assert output.is_dir()
        RasterMetadata.from_points(output)
