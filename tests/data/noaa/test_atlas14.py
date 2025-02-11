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
        assert output == tmp_path / "noaa-atlas14-mean-pds-intensity-metric.csv"
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv",
            params={
                "lat": 39,
                "lon": -105,
                "data": "intensity",
                "series": "pds",
                "units": "metric",
            },
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_options_default_path(_, mock, response, monkeypatch, tmp_path):
        mock.return_value = response
        monkeypatch.chdir(tmp_path)
        output = atlas14.download(
            39, -105, statistic="upper", data="depth", series="ams", units="english"
        )
        assert output == tmp_path / "noaa-atlas14-upper-ams-depth-english.csv"
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_uppr.csv",
            params={
                "lat": 39,
                "lon": -105,
                "data": "depth",
                "series": "ams",
                "units": "english",
            },
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_custom_path(_, mock, response, tmp_path):
        mock.return_value = response

        parent = tmp_path
        name = "test.csv"
        path = parent / name

        output = atlas14.download(39, -105, parent=parent, name=name)
        assert output == path
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv",
            params={
                "lat": 39,
                "lon": -105,
                "data": "intensity",
                "series": "pds",
                "units": "metric",
            },
            timeout=10,
        )

    @patch("requests.get", spec=True)
    def test_valid_overwrite(_, mock, response, tmp_path):
        mock.return_value = response

        parent = tmp_path
        name = "test.csv"
        path = parent / name
        path.write_text("This file already exists")

        output = atlas14.download(39, -105, parent=parent, name=name, overwrite=True)
        assert output == path
        assert output.read_text() == "Here is some content"
        mock.assert_called_with(
            url="https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv",
            params={
                "lat": 39,
                "lon": -105,
                "data": "intensity",
                "series": "pds",
                "units": "metric",
            },
            timeout=10,
        )

    def test_invalid_overwrite(_, tmp_path, assert_contains):
        parent = tmp_path
        name = "test.csv"
        path = parent / name
        path.write_text("This file already exists")

        with pytest.raises(FileExistsError) as error:
            atlas14.download(39, -105, parent=parent, name=name)
        assert_contains(error, "Download path already exists")

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
        output = atlas14.download(39, -105, parent=tmp_path, name="test.csv")
        assert output == path
        content = output.read_text()

        expected = (
            "Point precipitation frequency estimates (millimeters/hour)\n"
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
            "5-min:, 73,88,116,140,176,205,237,270,316,353\n"
            "10-min:, 53,65,85,103,129,150,173,198,231,259\n"
            "15-min:, 43,53,69,83,105,122,141,161,188,210\n"
            "30-min:, 28,35,45,55,69,80,92,105,123,137\n"
            "60-min:, 18,21,27,32,40,48,55,64,76,85\n"
            "2-hr:, 10,12,15,18,23,28,32,37,45,51\n"
            "3-hr:, 8,9,11,13,17,20,24,28,33,38\n"
            "6-hr:, 5,6,7,8,10,12,15,17,21,24\n"
            "12-hr:, 3,4,4,5,7,8,9,11,13,15\n"
            "24-hr:, 2,2,3,3,4,5,6,7,8,9\n"
            "2-day:, 1,1,2,2,3,3,4,4,5,6\n"
            "3-day:, 1,1,1,1,2,2,3,3,3,4\n"
            "4-day:, 1,1,1,1,1,2,2,2,3,3\n"
            "7-day:, 0,1,1,1,1,1,1,1,2,2\n"
            "10-day:, 0,0,0,1,1,1,1,1,1,1\n"
            "20-day:, 0,0,0,0,0,1,1,1,1,1\n"
            "30-day:, 0,0,0,0,0,0,0,0,1,1\n"
            "45-day:, 0,0,0,0,0,0,0,0,0,0\n"
            "60-day:, 0,0,0,0,0,0,0,0,0,0\n"
        )
        assert expected in content
