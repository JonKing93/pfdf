from unittest.mock import patch

import pytest

from pfdf.data.usgs.tnm import nhd
from pfdf.errors import NoTNMProductsError


class TestDataset:
    def test(_):
        assert nhd.dataset() == "National Hydrography Dataset (NHD) Best Resolution"


class TestNoHucError:
    def test(_, assert_contains):
        with pytest.raises(NoTNMProductsError) as error:
            nhd._no_huc_error("1234")
        assert_contains(
            error,
            "Could not locate a matching hydrologic unit.",
            "The HUC (1234) may not be a valid code.",
        )


class TestProduct:
    def test_huc_2(_, assert_contains):
        with pytest.raises(ValueError) as error:
            nhd.product("14")
        assert_contains(
            error,
            "huc must be an HU-4 or HU-8 code. This command does not support HU-2",
        )

    def test_invalid_format(_, assert_contains):
        with pytest.raises(ValueError) as error:
            nhd.product("1400", format="Geodatabase")
        assert_contains(
            error,
            "format (Geodatabase) is not a recognized option. Supported options are: shapefile, geopackage, filegdb",
        )

    @patch("requests.get")
    def test_invalid_huc(_, mock, response, assert_contains):
        mock.return_value = response(200, b"Not valid JSON")
        with pytest.raises(NoTNMProductsError) as error:
            nhd.product("9999")
        assert_contains(
            error,
            "Could not locate a matching hydrologic unit. The HUC (9999) may not be a valid code.",
        )

    @patch("pfdf.data.usgs.tnm.api.products")
    def test_missing_huc(_, mock, assert_contains):
        mock.return_value = [{"title": "test"} for _ in range(5)]
        with pytest.raises(NoTNMProductsError) as error:
            nhd.product("15019999")
        assert_contains(
            error,
            "Could not locate a matching hydrologic unit. The HUC (15019999) may not be a valid code",
        )

    @patch("pfdf.data.usgs.tnm.api.products")
    def test_valid(_, mock):
        mock.return_value = [
            {"title": f"Hydrological Unit (HU) 4 - 150{k}", "value": k}
            for k in range(9)
        ]
        output = nhd.product("1506")
        assert output == {
            "title": "Hydrological Unit (HU) 4 - 1506",
            "value": 6,
        }


def data_bundle():
    return {
        "test-15.shp": "An example HU2 in a data bundle",
        "test-1506.shp": "An example HU4 in a data bundle",
    }


@pytest.fixture
def zip_data(tmp_path, zip_bytes):

    folder = tmp_path / "data-folder"
    folder.mkdir()
    return zip_bytes(folder, data_bundle())


class TestDownload:
    @staticmethod
    def check_data(folder):
        assert folder.exists()
        for file, content in data_bundle().items():
            path = folder / file
            assert path.exists()
            assert path.read_text() == content

    @patch("pfdf.data._utils.requests.content")
    @patch("pfdf.data.usgs.tnm.nhd.product")
    def test_default_path(
        self, product_mock, content_mock, zip_data, tmp_path, monkeypatch
    ):
        product_mock.return_value = {
            "title": "Hydrological Unit (HU) 4 - 1506",
            "value": 6,
            "downloadURL": "https://www.usgs.gov/test-download-link.zip",
        }
        content_mock.return_value = zip_data
        monkeypatch.chdir(tmp_path)

        path = tmp_path / "huc4-1506"
        assert not path.exists()
        output = nhd.download("1506")
        assert output == path
        self.check_data(path)

    @patch("pfdf.data._utils.requests.content")
    @patch("pfdf.data.usgs.tnm.nhd.product")
    def test_custom_path(self, product_mock, content_mock, zip_data, tmp_path):
        product_mock.return_value = {
            "title": "Hydrological Unit (HU) 4 - 1506",
            "value": 6,
            "downloadURL": "https://www.usgs.gov/test-download-link.zip",
        }
        content_mock.return_value = zip_data

        path = tmp_path / "test"
        assert not path.exists()
        output = nhd.download("1506", path=path)
        assert output == path
        self.check_data(path)


@pytest.mark.web
class TestLive:
    def test(_, tmp_path):

        path = tmp_path / "test"
        output = nhd.download("15010006", path)
        assert output == path

        contents = list(path.iterdir())
        assert path / "NHD_H_15010006_HU8_Shape.jpg" in contents
        assert path / "NHD_H_15010006_HU8_Shape.xml" in contents

        bundle = path / "Shape"
        assert bundle in contents
        assert bundle.is_dir()
        assert (bundle / "NHDArea.shp").exists()
