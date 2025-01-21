from unittest.mock import patch

import pytest

from pfdf.data.landfire import api
from pfdf.errors import MissingAPIFieldError, MissingCRSError


@pytest.fixture
def missing():
    return {"error": {"message": "Job not found on server"}}


@pytest.fixture
def missing_job(missing, json_response):
    return json_response(missing)


class TestLfpsUrl:
    def test(_):
        assert (
            api.lfps_url()
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/"
        )


class TestJobUrl:
    def test(_):
        output = api.job_url("12345")
        assert (
            output
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345"
        )


class TestSubmitJob:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {
            "jobId": "12345",
            "jobStatus": "esriJobSubmitted",
        }
        mock.return_value = json_response(content)

        layers = ["240EVT", "230EVT"]
        bounds = [-107.6, 32.2, -107.2, 32.8, 4326]
        output = api.submit_job(layers, bounds)
        assert output == "12345"
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/submitJob",
            params={
                "f": "json",
                "Layer_List": "240EVT;230EVT",
                "Area_of_Interest": "-107.6 32.2 -107.2 32.8",
            },
            timeout=10,
        )

    def test_no_crs(_, assert_contains):
        layers = "240EVT"
        bounds = [-107.6, 32.2, -107.2, 32.8]
        with pytest.raises(MissingCRSError) as error:
            api.submit_job(layers, bounds)
        assert_contains(error, "bounds must have a CRS")


class TestQueryJob:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {
            "jobId": "12345",
            "jobStatus": "esriJobSucceeded",
            "messages": ["Some", "messages"],
        }
        mock.return_value = json_response(content)
        output = api.query_job("12345")
        assert output == content
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_missing(_, mock, missing_job, assert_contains):
        mock.return_value = missing_job
        with pytest.raises(ValueError) as error:
            api.query_job("12345")
        assert_contains(
            error, "The queried job (12345) does not exist on the LFPS server"
        )
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_missing_not_strict(_, mock, missing_job, missing):
        mock.return_value = missing_job
        output = api.query_job("12345", strict=False)
        assert output == missing
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=10,
        )


class TestJobStatus:
    @patch("requests.get", spec=True)
    def test(_, mock, json_response):
        content = {"jobId": "12345", "jobStatus": "esriJobSucceeded"}
        mock.return_value = json_response(content)
        output = api.job_status("12345")
        assert output == "esriJobSucceeded"
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_missing(_, mock, missing_job, assert_contains):
        mock.return_value = missing_job
        with pytest.raises(ValueError) as error:
            api.job_status("12345")
        assert_contains(
            error, "The queried job (12345) does not exist on the LFPS server"
        )
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_no_status(_, mock, json_response, assert_contains):
        content = {"jobId": "12345"}
        mock.return_value = json_response(content)
        with pytest.raises(MissingAPIFieldError) as error:
            api.job_status("12345")
        assert_contains(error, "LANDFIRE LFPS failed to return the job status")
        mock.assert_called_with(
            url="https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/jobs/12345",
            params={"f": "json"},
            timeout=10,
        )
