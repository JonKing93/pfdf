from unittest.mock import patch

import pytest

from pfdf.data.usgs.tnm import api
from pfdf.errors import DataAPIError, MissingAPIFieldError, TooManyTNMProductsError

#####
# Testing fixtures
#####


def infos(N):
    return list(range(N))


def content(items, total: int = None):
    return {"total": total or len(items), "items": items}


@pytest.fixture
def multiple_mock(json_response):
    def multiple_mock(url, params, *args, **kwargs):
        items = infos(67)
        if params["offset"] == 0 and params["max"] == 20:
            return json_response(content(items[0:20], 67))
        elif params["offset"] == 20 and params["max"] == 20:
            return json_response(content(items[20:40], 67))
        elif params["offset"] == 40 and params["max"] == 20:
            return json_response(content(items[40:60], 67))
        elif params["offset"] == 60 and params["max"] == 10:
            return json_response(content(items[60:], 67))

    return multiple_mock


#####
# Utilities
#####


class TestNtotal:
    def test(_):
        info = {"total": 5, "items": ["Some", "products"]}
        assert api._ntotal(info) == 5

    def test_missing(_, assert_contains):
        info = {"items": ["Some", "products"]}
        with pytest.raises(MissingAPIFieldError) as error:
            api._ntotal(info)
        assert_contains(error, "TNM failed to return a total product count")

    def test_not_int(_, assert_contains):
        info = {"total": "5", "items": ["Some", "products"]}
        with pytest.raises(MissingAPIFieldError) as error:
            api._ntotal(info)
        assert_contains(error, "TNM failed to return a total product count")


class TestParseMax:
    def test_small_multiple(_):
        max, padding = api._parse_max(nproducts=15, max_per_query=99)
        assert max == 15
        assert padding == 0

    def test_large_multiple(_):
        max, padding = api._parse_max(nproducts=999, max_per_query=100)
        assert max == 100
        padding == 0

    def test_small_not_multiple(_):
        max, padding = api._parse_max(nproducts=13, max_per_query=99)
        assert max == 15
        assert padding == 2

    def test_large_not_multiple(_):
        max, padding = api._parse_max(nproducts=999, max_per_query=12)
        assert max == 15
        assert padding == 3


class TestItems:
    def test_no_items(_, assert_contains):
        info = {"test": 1}
        with pytest.raises(MissingAPIFieldError) as error:
            api._items(info, max=5, padding=1)
        assert_contains(error, "TNM failed to return product information")

    def test_ideal(_):
        info = {"test": "a field", "items": [1, 2, 3, 4, 5]}
        output = api._items(info, max=5, padding=0)
        assert output == [1, 2, 3, 4, 5]

    def test_with_padding(_):
        info = {"test": "a field", "items": [1, 2, 3, 4, 5]}
        output = api._items(info, max=5, padding=2)
        assert output == [1, 2, 3]

    def test_fewer_than_max(_):
        info = {"test": "a field", "items": [1, 2, 3, 4, 5]}
        output = api._items(info, max=10, padding=0)
        assert output == [1, 2, 3, 4, 5]

    def test_padding_and_fewer(_):
        info = {"test": "a field", "items": [1, 2, 3, 4, 5]}
        output = api._items(info, max=10, padding=2)
        assert output == [1, 2, 3, 4, 5]


#####
# User Functions
#####


class TestApiUrl:
    def test(_):
        assert api.api_url() == "https://tnmaccess.nationalmap.gov/api/v1/products"


class TestQuery:
    @patch("requests.get", spec=True)
    def test_options(_, mock, json_response):
        content = {
            "total": 999,
            "items": ["Some", "products"],
        }
        mock.return_value = json_response(content)
        output = api.query(
            datasets=["test1", "test2"],
            bounds=[-107.8, 32.2, -107.2, 32.8, 4326],
            huc="15060002",
            formats="Shapefile",
            max=500,
            offset=10,
        )
        assert output == content

        params = {
            "datasets": "test1,test2",
            "bbox": "-107.8,32.2,-107.2,32.8",
            "polyCode": "15060002",
            "polyType": "huc8",
            "prodFormats": "Shapefile",
            "max": 500,
            "offset": 10,
            "outputFormat": "JSON",
        }
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params=params,
            timeout=60,
        )

    @patch("requests.get")
    def test_not_strict(_, mock, json_response):
        content = {"errors": "An error occurred"}
        mock.return_value = json_response(content)
        output = api.query("test1", strict=False)
        assert output == content
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={"datasets": "test1", "outputFormat": "JSON"},
            timeout=60,
        )

    @patch("requests.get")
    def test_errors_message(_, mock, json_response, assert_contains):
        content = {"errors": {"message": "Some error message"}}
        mock.return_value = json_response(content)
        with pytest.raises(DataAPIError) as error:
            api.query("test1")
        assert_contains(
            error,
            "TNM reported the following error for the API query",
            "Some error message",
        )
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={"datasets": "test1", "outputFormat": "JSON"},
            timeout=60,
        )

    @patch("requests.get")
    def test_error_no_message(_, mock, json_response, assert_contains):
        content = {"errors": ["Some", "errors"]}
        mock.return_value = json_response(content)
        with pytest.raises(DataAPIError) as error:
            api.query("test1")
        assert_contains(
            error,
            "TNM reported an error for the API query",
        )
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={"datasets": "test1", "outputFormat": "JSON"},
            timeout=60,
        )


class TestNproducts:
    @patch("requests.get")
    def test(_, mock, json_response):
        content = {"total": 1234, "items": ["Some", "products"]}
        mock.return_value = json_response(content)
        output = api.nproducts("test1")
        assert isinstance(output, int)
        assert output == 1234
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={"datasets": "test1", "max": 1, "offset": 0, "outputFormat": "JSON"},
            timeout=60,
        )


class TestProducts:
    @patch("requests.get")
    def test_single_query(_, mock, json_response):
        items = infos(10)
        mock.return_value = json_response(content(items))
        output = api.products("test1", max_queries=1, max_products=10)
        assert output == items
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={
                "datasets": "test1",
                "max": 10,
                "offset": 0,
                "outputFormat": "JSON",
            },
            timeout=60,
        )

    @patch("requests.get")
    def test_offset_too_large(_, mock, json_response, assert_contains):
        items = infos(100)
        mock.return_value = json_response(content(items))
        with pytest.raises(IndexError) as error:
            api.products("test", offset=500)
        assert_contains(
            error,
            "offset must be less than the total number of search results (100)",
            "but the input offset (500) is not",
        )

    @patch("requests.get")
    def test_too_many_queries(_, mock, json_response, assert_contains):
        items = infos(100)
        mock.return_value = json_response(content(items, total=500))
        with pytest.raises(TooManyTNMProductsError) as error:
            api.products("test", max_queries=3, max_per_query=100)
        print(error.value.args[0])
        assert_contains(
            error,
            "There are 500 TNM products that match the search criteria",
            "You have allowed 100 products per query, so retrieving all",
            "these products will require 5 TNM API queries, which is greater",
            "than the maximum allowed number of queries (3)",
        )

    @patch("requests.get")
    def test_max_products_limited(_, mock, json_response):
        items = infos(50)
        mock.return_value = json_response(content(items, total=1000))
        output = api.products("test", max_queries=1, max_products=50)
        assert output == items

    @patch("requests.get")
    def test_offset(_, mock, json_response):
        items = infos(15)
        mock.return_value = json_response(content(items, total=1000))
        output = api.products("test", max_products=15, offset=500)
        assert output == items

    @patch("requests.get")
    def test_padded(_, mock, json_response):
        items = infos(20)
        mock.return_value = json_response(content(items, total=900))
        output = api.products("test", max_products=17)
        assert len(output) == 17
        assert output == items[:-3]

    @patch("requests.get")
    def test_fewer_than_max(_, mock, json_response):
        items = infos(13)
        mock.return_value = json_response(content(items))
        output = api.products("test", max_products=20)
        assert output == items

    @patch("requests.get")
    def test_multiple_queries_fewer_at_end(_, mock, multiple_mock):
        "Checks multiple queries with padding and fewer entries at the end"
        mock.side_effect = multiple_mock
        output = api.products("test", max_queries=5, max_per_query=20)
        assert output == infos(67)


@pytest.mark.web
class TestLive:
    def test(_):
        output = api.products(
            datasets="National Hydrography Dataset (NHD) Best Resolution",
            bounds=[-106, 39, -105, 40, 4326],
            formats="Shapefile",
        )
        assert len(output) == 13
        titles = [item["title"] for item in output]
        for t, title in enumerate(titles):
            title = title.removeprefix(
                "USGS National Hydrography Dataset Best Resolution (NHD) "
            )
            title = title.removeprefix("for Hydrological Unit ")
            title = title[:-31]
            titles[t] = title
        assert titles == [
            "- Colorado",
            "(HU) 4 - 1019",
            "(HU) 4 - 1102",
            "(HU) 4 - 1401",
            "(HU) 8 - 10190001",
            "(HU) 8 - 10190002",
            "(HU) 8 - 10190003",
            "(HU) 8 - 10190004",
            "(HU) 8 - 10190005",
            "(HU) 8 - 11020001",
            "(HU) 8 - 11020003",
            "(HU) 8 - 14010001",
            "(HU) 8 - 14010002",
        ]
