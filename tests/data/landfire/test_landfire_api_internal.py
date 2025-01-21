from unittest.mock import patch

import pytest

from pfdf.data.landfire import _api
from pfdf.errors import DataAPIError, MissingAPIFieldError


class TestLfpsUrl:
    def test(_):
        output = _api.lfps_url()
        assert (
            output
            == "https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer/LandfireProductService/"
        )


class TestJson:
    @patch("requests.get")
    def test(_, mock, json_response):
        content = {
            "test": "some text",
            "test2": 5,
        }
        mock.return_value = json_response(content)

        url = "https://www.usgs.gov"
        output = _api.json(url, {}, None)
        assert output == content
        mock.assert_called_with(url, params={"f": "json"}, timeout=None)


class TestField:
    def test(_):
        response = {
            "field1": 1,
            "field2": 2,
            "field3": 3,
        }
        output = _api.field(response, "field2", "")
        assert output == 2

    def test_missing(_, assert_contains):
        response = {
            "field1": 1,
            "field2": 2,
        }
        with pytest.raises(MissingAPIFieldError) as error:
            _api.field(response, "field3", "test field")
        assert_contains(error, "LANDFIRE LFPS failed to return the test field")


class TestReportJobError:
    def test_missing_job(_, assert_contains):
        error = {"message": "Job not found on server"}
        with pytest.raises(ValueError) as err:
            _api.report_job_error(error, "12345")
        assert_contains(
            err,
            "The queried job (12345) does not exist on the LFPS server",
            "Try checking that the job ID is spelled correctly",
        )

    def test_message(_, assert_contains):
        error = {"message": "An example error message"}
        with pytest.raises(DataAPIError) as err:
            _api.report_job_error(error, "12345")
        assert_contains(
            err,
            "LANDFIRE LFPS reported the following error in the API query for job 12345",
            "An example error message",
        )

    def test_no_message(_, assert_contains):
        error = {}
        with pytest.raises(DataAPIError) as err:
            _api.report_job_error(error, "12345")
        assert_contains(
            err, "LANDFIRE LFPS reported an error in the API query for job 12345"
        )


class TestStatus:
    def test(_):
        job = {"field1": 1, "jobStatus": "esriJobSucceeded", "field2": 2}
        output = _api.status(job)
        assert output == "esriJobSucceeded"
