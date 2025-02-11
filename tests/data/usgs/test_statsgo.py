from unittest.mock import patch

import numpy as np
import pytest
from pandas import DataFrame

from pfdf.data.usgs import statsgo
from pfdf.errors import DataAPIError, MissingAPIFieldError, MissingCRSError
from pfdf.projection import BoundingBox
from pfdf.raster import Raster, RasterMetadata


@pytest.fixture
def item():
    "Mock ScienceBase info on a STATSGO item"
    return {
        "title": "Some title",
        "summary": "A long description",
        "files": [
            {"name": "STATSGO-THICK-COG.xml"},
            {
                "name": "STATSGO-THICK.tif",
                "publishedS3Uri": "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/675721b9d34e5c5dfd05c575/STATSGO-THICK.tif",
            },
        ],
    }


@pytest.fixture
def download_mock(json_response, response, item):
    "Returns a function that mocks requests.get for acquiring data"

    def download_mock(url, *args, **kwargs):

        if url == "https://www.sciencebase.gov/catalog/item/675721b9d34e5c5dfd05c575":
            return json_response(item)

        elif (
            url
            == "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/675721b9d34e5c5dfd05c575/STATSGO-THICK.tif"
        ):
            return response(200, b"Here is some content")

    return download_mock


class TestFields:
    def test(_):
        output = statsgo.fields()
        assert isinstance(output, DataFrame)
        assert output.index.tolist() == ["KFFACT", "THICK"]
        assert output.columns.tolist() == ["Description", "Units", "URL"]
        assert output["Description"].tolist() == ["Soil KF-factors", "Soil thickness"]
        assert output["Units"].tolist() == ["inches per hour", "inches"]
        assert output["URL"].tolist() == [
            "https://www.sciencebase.gov/catalog/item/6750c172d34ed8d3858534d8",
            "https://www.sciencebase.gov/catalog/item/675721b9d34e5c5dfd05c575",
        ]


class TestValidateField:
    @pytest.mark.parametrize(
        "input, expected", (("kffact", "KFFACT"), ("ThIcK", "THICK"))
    )
    def test_valid(_, input, expected):
        output = statsgo._validate_field(input)
        assert output == expected

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            statsgo._validate_field("invalid")
        assert_contains(
            error,
            "field (invalid) is not a recognized option. Supported options are: kffact, thick",
        )


class Test_Url:
    @pytest.mark.parametrize(
        "field, url",
        (
            (
                "KFFACT",
                "https://www.sciencebase.gov/catalog/item/6750c172d34ed8d3858534d8",
            ),
            (
                "THICK",
                "https://www.sciencebase.gov/catalog/item/675721b9d34e5c5dfd05c575",
            ),
        ),
    )
    def test(_, field, url):
        output = statsgo._url(field)
        assert output == url


class TestUrl:
    def test_collection(_):
        output = statsgo.url()
        assert (
            output
            == "https://www.sciencebase.gov/catalog/item/675083c6d34ea60e894354ad"
        )

    @pytest.mark.parametrize(
        "field, url",
        (
            (
                "kffact",
                "https://www.sciencebase.gov/catalog/item/6750c172d34ed8d3858534d8",
            ),
            (
                "ThIcK",
                "https://www.sciencebase.gov/catalog/item/675721b9d34e5c5dfd05c575",
            ),
        ),
    )
    def test(_, field, url):
        output = statsgo.url(field)
        assert output == url

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            statsgo.url("invalid")
        assert_contains(error, "field (invalid) is not a recognized option")


class TestQuery:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {
            "title": "A title",
            "summary": "A long summary about the item",
            "files": ["File 1", "File 2"],
        }
        mock.return_value = json_response(content)
        output = statsgo.query("kffact")
        assert output == content
        mock.assert_called_with(
            "https://www.sciencebase.gov/catalog/item/6750c172d34ed8d3858534d8",
            params={"format": "json"},
            timeout=60,
        )


class TestS3Url:
    def test_valid(_):
        item = {
            "title": "Some title",
            "summary": "A long description",
            "files": [
                {"name": "STATSGO-THICK-COG.xml"},
                {
                    "name": "STATSGO-THICK.tif",
                    "publishedS3Uri": "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/675721b9d34e5c5dfd05c575/STATSGO-THICK.tif",
                },
            ],
        }
        output = statsgo._s3_url(item, "THICK")
        assert (
            output
            == "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/675721b9d34e5c5dfd05c575/STATSGO-THICK.tif"
        )

    def test_no_files(_, assert_contains):
        item = {
            "title": "Some title",
            "summary": "A long description",
        }
        with pytest.raises(MissingAPIFieldError) as error:
            statsgo._s3_url(item, "THICK")
        assert_contains(
            error, 'ScienceBase failed to return "files" metadata for the item'
        )

    def test_missing_file(_, assert_contains):
        item = {
            "title": "Some title",
            "summary": "A long description",
            "files": [
                {"name": "STATSGO-THICK-COG.xml"},
            ],
        }
        with pytest.raises(DataAPIError) as error:
            statsgo._s3_url(item, "THICK")
        assert_contains(
            error,
            "Could not locate the statsgo-thick.tif file in the ScienceBase item info",
        )

    def test_no_uri(_, assert_contains):
        item = {
            "title": "Some title",
            "summary": "A long description",
            "files": [
                {"name": "STATSGO-THICK-COG.xml"},
                {"name": "STATSGO-THICK.tif"},
            ],
        }
        with pytest.raises(MissingAPIFieldError) as error:
            statsgo._s3_url(item, "THICK")
        assert_contains(error, "ScienceBase failed to return an S3 download Uri")


class TestDownload:
    @patch("requests.get", spec=True)
    def test_default_path(_, mock, download_mock, monkeypatch, tmp_path):
        mock.side_effect = download_mock
        monkeypatch.chdir(tmp_path)
        output = statsgo.download(field="thick")
        assert output == tmp_path / "STATSGO-THICK.tif"
        assert output.read_text() == "Here is some content"

    @patch("requests.get", spec=True)
    def test_custom_path(_, mock, download_mock, tmp_path):
        mock.side_effect = download_mock

        parent = tmp_path
        name = "test.txt"
        path = parent / name

        output = statsgo.download("thick", parent=parent, name=name)
        assert output == path
        assert output.read_text() == "Here is some content"

    @patch("requests.get", spec=True)
    def test_valid_overwrite(_, mock, download_mock, tmp_path):
        mock.side_effect = download_mock

        parent = tmp_path
        name = "test.txt"
        path = parent / name
        path.write_text("This file exists")

        assert path.exists()
        output = statsgo.download("thick", overwrite=True, parent=parent, name=name)
        assert output == path
        assert output.read_text() == "Here is some content"

    @patch("requests.get", spec=True)
    def test_invalid_overwrite(_, mock, download_mock, tmp_path, assert_contains):
        mock.side_effect = download_mock

        parent = tmp_path
        name = "test.txt"
        path = parent / name
        path.write_text("This file exists")

        with pytest.raises(FileExistsError) as error:
            statsgo.download("thick", parent=parent, name=name)
        assert_contains(error, "Download path already exists")


class TestRead:
    @patch("pfdf.raster.Raster.from_url", spec=True)
    @patch("requests.get", spec=True)
    def test(_, get_mock, read_mock, json_response, item):
        get_mock.return_value = json_response(item)
        expected = Raster(np.ones((10, 10)))
        read_mock.return_value = expected
        output = statsgo.read("thick", bounds=[1, 2, 3, 4, 4326])

        assert output == expected
        read_mock.assert_called_with(
            "https://prod-is-usgs-sb-prod-publish.s3.amazonaws.com/675721b9d34e5c5dfd05c575/STATSGO-THICK.tif",
            bounds=BoundingBox(1, 2, 3, 4, 4326),
            check_status=False,
            timeout=60,
        )

    def test_bounds_crs(_, assert_contains):
        with pytest.raises(MissingCRSError) as error:
            statsgo.read("thick", bounds=[1, 2, 3, 4])
        assert_contains(error, "bounds must have a CRS")


@pytest.mark.web
class TestLive:
    def test(_):
        bounds = [-105.1, 32.9, -104.9, 33.1, 4326]
        expected = RasterMetadata(
            shape=(800, 686),
            dtype="float32",
            nodata=np.nan,
            casting="same_kind",
            crs=5069,
            bounds=(-844846.75, 1130785.75, -824266.75, 1154785.75),
        )

        output = statsgo.read("KFFACT", bounds)
        assert isinstance(output, Raster)
        assert output.metadata == expected
        assert np.nanmean(output.values) == 0.155546

        output = statsgo.read("THICK", bounds)
        assert isinstance(output, Raster)
        assert output.metadata == expected
        assert np.nanmean(output.values) == 42.743263
