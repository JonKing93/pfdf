from unittest.mock import patch

import pytest

from pfdf.data.noaa import atlas14


@pytest.fixture
def response(response):
    return response(200, b"Here is some content")


class TestBaseUrl:
    def test(_):
        assert atlas14.base_url() == "https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new"


class TestValidateStatistic:
    @pytest.mark.parametrize("value", ("mean", "upper", "lower", "all"))
    def test_valid(_, value):
        output = atlas14._validate_statistic(value)
        assert output == value

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14._validate_statistic("median")
        assert_contains(
            error,
            "statistic (median) is not a recognized option. Supported options are: mean, upper, lower, all",
        )


class TestQueryUrl:
    @pytest.mark.parametrize(
        "statistic, key",
        (
            ("mean", "_mean"),
            ("upper", "_uppr"),
            ("lower", "_lwr"),
            ("all", ""),
        ),
    )
    def test_valid(_, statistic, key):
        output = atlas14.query_url(statistic)
        assert output == f"https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text{key}.csv"

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14.query_url("median")
        assert_contains(
            error,
            "statistic (median) is not a recognized option. Supported options are: mean, upper, lower, all",
        )


class TestDownload:
    @patch("requests.get", spec=True)
    def test_default_path(_, mock, response, monkeypatch, tmp_path):
        mock.return_value = response
        monkeypatch.chdir(tmp_path)
        output = atlas14.download(39, -105)
        assert output == tmp_path / "noaa-atlas14-mean-pds-intensity.csv"
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv",
            params={"lat": 39, "lon": -105, "data": "intensity", "series": "pds"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_options_default_path(_, mock, response, monkeypatch, tmp_path):
        mock.return_value = response
        monkeypatch.chdir(tmp_path)
        output = atlas14.download(
            39, -105, statistic="upper", data="depth", series="ams"
        )
        assert output == tmp_path / "noaa-atlas14-upper-ams-depth.csv"
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_uppr.csv",
            params={"lat": 39, "lon": -105, "data": "depth", "series": "ams"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_custom_path(_, mock, response, tmp_path):
        mock.return_value = response
        path = tmp_path / "test.csv"
        output = atlas14.download(39, -105, path)
        assert output == path
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv",
            params={"lat": 39, "lon": -105, "data": "intensity", "series": "pds"},
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_valid_overwrite(_, mock, response, tmp_path):
        mock.return_value = response
        path = tmp_path / "test.csv"
        path.write_text("This file already exists")
        output = atlas14.download(39, -105, path, overwrite=True)
        assert output == path
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv",
            params={"lat": 39, "lon": -105, "data": "intensity", "series": "pds"},
            timeout=10,
        )

    def test_invalid_overwrite(_, tmp_path, assert_contains):
        path = tmp_path / "test.csv"
        path.write_text("This file already exists")
        with pytest.raises(FileExistsError) as error:
            atlas14.download(39, -105, path)
        assert_contains(error, "Output file already exists")

    def test_invalid_lat(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14.download(100, -105)
        assert_contains(error, "lat must be less than or equal to 90")

    def test_invalid_lon(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14.download(39, 200)
        assert_contains(error, "lon must be less than or equal to 180")

    def test_invalid_data(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14.download(39, -105, data="test")
        assert_contains(
            error,
            "data (test) is not a recognized option. Supported options are: depth, intensity",
        )

    def test_invalid_series(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14.download(39, -105, series="test")
        assert_contains(
            error,
            "series (test) is not a recognized option. Supported options are: pds, ams",
        )

    def test_invalid_statistic(_, assert_contains):
        with pytest.raises(ValueError) as error:
            atlas14.download(39, -105, statistic="median")
        assert_contains(
            error,
            "statistic (median) is not a recognized option. Supported options are: mean, upper, lower, all",
        )


@pytest.mark.web(api="atlas14")
class TestLive:
    def test(_, tmp_path):

        path = tmp_path / "test.csv"
        output = atlas14.download(39, -105, path)
        assert output == path
        content = output.read_text()

        expected = (
            "Point precipitation frequency estimates (inches/hour)\n"
            "NOAA Atlas 14 Volume 8 Version 2\n"
            "Data type: Precipitation intensity\n"
            "Time series type: Partial duration\n"
            "Project area: Midwestern States\n"
            "Location name (ESRI Maps): None\n"
            "Station Name: None\n"
            "Latitude: 39.0 Degree\n"
            "Longitude: -105.0 Degree\n"
            "Elevation (USGS): None None\n"
            "\n"
            "\n"
            "PRECIPITATION FREQUENCY ESTIMATES\n"
            "by duration for ARI (years):, 1,2,5,10,25,50,100,200,500,1000\n"
            "5-min:, 2.87,3.48,4.56,5.52,6.92,8.09,9.31,10.6,12.4,13.9\n"
            "10-min:, 2.10,2.55,3.34,4.04,5.07,5.92,6.82,7.78,9.11,10.2\n"
            "15-min:, 1.70,2.08,2.72,3.28,4.12,4.82,5.54,6.32,7.41,8.28\n"
            "30-min:, 1.12,1.36,1.78,2.15,2.70,3.15,3.63,4.13,4.84,5.41\n"
            "60-min:, 0.690,0.818,1.05,1.26,1.59,1.87,2.18,2.51,2.98,3.36\n"
            "2-hr:, 0.410,0.477,0.604,0.726,0.918,1.09,1.27,1.47,1.77,2.01\n"
            "3-hr:, 0.305,0.348,0.434,0.520,0.661,0.786,0.926,1.08,1.32,1.51\n"
            "6-hr:, 0.192,0.217,0.268,0.321,0.407,0.486,0.574,0.674,0.822,0.946\n"
            "12-hr:, 0.123,0.141,0.177,0.212,0.268,0.317,0.372,0.434,0.523,0.598\n"
            "24-hr:, 0.077,0.090,0.113,0.136,0.171,0.202,0.236,0.273,0.327,0.371\n"
            "2-day:, 0.046,0.053,0.067,0.080,0.101,0.119,0.138,0.160,0.191,0.217\n"
            "3-day:, 0.033,0.039,0.048,0.058,0.072,0.085,0.099,0.114,0.136,0.154\n"
            "4-day:, 0.027,0.031,0.038,0.045,0.057,0.066,0.077,0.089,0.106,0.119\n"
            "7-day:, 0.018,0.020,0.025,0.029,0.035,0.041,0.047,0.054,0.064,0.073\n"
            "10-day:, 0.014,0.016,0.019,0.023,0.027,0.031,0.036,0.041,0.048,0.054\n"
            "20-day:, 0.010,0.011,0.013,0.015,0.018,0.020,0.023,0.025,0.029,0.032\n"
            "30-day:, 0.008,0.009,0.011,0.012,0.014,0.016,0.018,0.019,0.022,0.023\n"
            "45-day:, 0.006,0.007,0.009,0.010,0.011,0.013,0.014,0.015,0.016,0.017\n"
            "60-day:, 0.005,0.006,0.007,0.008,0.010,0.010,0.011,0.012,0.013,0.014"
        )
        assert expected in content
