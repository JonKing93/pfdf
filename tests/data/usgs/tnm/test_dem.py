from datetime import date
from unittest.mock import patch

import numpy as np
import pytest

from pfdf.data.usgs.tnm import dem
from pfdf.errors import CRSError, NoTNMProductsError, TooManyTNMProductsError
from pfdf.projection import BoundingBox
from pfdf.raster import Raster, RasterMetadata

#####
# Testing fixtures
#####


@pytest.fixture
def tile():
    return {
        "title": "USGS 1/3 Arc Second n37w114 20240614",
        "sourceId": "66711653d34e84915adb3db9",
        "sourceName": "ScienceBase",
        "sourceOriginId": None,
        "sourceOriginName": "gda",
        "metaUrl": "https://www.sciencebase.gov/catalog/item/66711653d34e84915adb3db9",
        "vendorMetaUrl": "https://prd-tnm.s3.amazonaws.com/index.html?prefix=StagedProducts/Elevation/metadata/AZ_CentralCoconino_B22/AZ_CenCoconino_3_B22",
        "publicationDate": "2024-06-14",
        "lastUpdated": "2024-06-17T23:08:51.226-06:00",
        "dateCreated": "2024-06-17T23:08:35.524-06:00",
        "sizeInBytes": 430590023,
        "extent": "1 x 1 degree",
        "format": "GeoTIFF",
        "downloadURL": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n37w114/USGS_13_n37w114_20240614.tif",
        "downloadURLRaster": None,
        "previewGraphicURL": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n37w114/USGS_13_n37w114_20240614.jpg",
        "downloadLazURL": None,
        "urls": {
            "TIFF": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n37w114/USGS_13_n37w114_20240614.tif"
        },
        "datasets": [],
        "boundingBox": {
            "minX": -114,
            "maxX": -113,
            "minY": 36,
            "maxY": 37,
        },
        "bestFitIndex": 0.0,
        "processingUrl": "processingUrl",
        "modificationInfo": "2024-06-18",
    }


@pytest.fixture
def tile_info():
    return {
        "title": "USGS 1/3 Arc Second n37w114 20240614",
        "publication_date": date(2024, 6, 14),
        "download_url": "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n37w114/USGS_13_n37w114_20240614.tif",
        "sciencebase_id": "66711653d34e84915adb3db9",
        "sciencebase_url": "https://www.sciencebase.gov/catalog/item/66711653d34e84915adb3db9",
        "filename": "USGS_13_n37w114_20240614.tif",
        "format": "GeoTIFF",
        "nbytes": 430590023,
        "bounds": BoundingBox(-114, 36, -113, 37, 4326),
        "extent": "1 x 1 degree",
    }


@pytest.fixture
def metamock():
    def metamock(url, *args, **kwargs):

        # Error tests
        if url == 4:
            return RasterMetadata((100, 0), transform=(1e-5, -1e-5, 0, 0, 4326))
        elif url == 5:
            return RasterMetadata((100, 100), transform=(10, -10, 0, 0, 26911))

        # Standard tests
        elif url == 0:
            shape = (2, 5)
            bounds = [-105.5, 33, -105, 33.2, 4326]
        elif url == 1:
            shape = (2, 5)
            bounds = [-105, 33, -104.5, 33.2, 4326]
        elif url == 2:
            shape = (5, 5)
            bounds = [-105.5, 32.5, -105, 33, 4326]
        elif url == 3:
            shape = (5, 5)
            bounds = [-105, 32.5, -104.5, 33, 4326]
        return RasterMetadata(shape, bounds=bounds, dtype="int16", nodata=-1)

    return metamock


@pytest.fixture
def metatiles():
    shape_bounds = [
        ((2, 5), [-105.5, 33, -105, 33.2, 4326]),
        ((2, 5), [-105, 33, -104.5, 33.2, 4326]),
        ((5, 5), [-105.5, 32.5, -105, 33, 4326]),
        ((5, 5), [-105, 32.5, -104.5, 33, 4326]),
    ]
    metas = {}
    for k, (shape, bounds) in enumerate(shape_bounds):
        metas[k] = RasterMetadata(shape, bounds=bounds, nodata=-1, dtype="int16")
    return metas


@pytest.fixture
def mock_raster():
    def mock_raster(url, *args, **kwargs):
        if url == 0:
            shape = (2, 5)
            bounds = [-105.5, 33, -105, 33.2, 4326]
        elif url == 1:
            shape = (2, 5)
            bounds = [-105, 33, -104.5, 33.2, 4326]
        elif url == 2:
            shape = (5, 5)
            bounds = [-105.5, 32.5, -105, 33, 4326]
        elif url == 3:
            shape = (5, 5)
            bounds = [-105, 32.5, -104.5, 33, 4326]
        array = np.full(shape, url + 1, "int16")
        return Raster.from_array(array, bounds=bounds, nodata=-1)

    return mock_raster


@pytest.fixture
def read_raster():
    return np.array(
        [
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3, 4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3, 4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3, 4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3, 4, 4, 4, 4, 4],
            [3, 3, 3, 3, 3, 4, 4, 4, 4, 4],
        ]
    )


#####
# API Queries
#####


class TestResolutions:
    def test(_):
        output = dem.resolutions()
        assert output == {
            "1 arc-second": "National Elevation Dataset (NED) 1 arc-second Current",
            "1 meter": "Digital Elevation Model (DEM) 1 meter",
            "1/3 arc-second": "National Elevation Dataset (NED) 1/3 arc-second Current",
            "1/9 arc-second": "National Elevation Dataset (NED) 1/9 arc-second",
            "2 arc-second": "National Elevation Dataset (NED) Alaska 2 arc-second Current",
            "5 meter": "Alaska IFSAR 5 meter DEM",
        }


class TestDataset:
    @pytest.mark.parametrize(
        "input, expected",
        (
            ("1 ARC-SECOND", "National Elevation Dataset (NED) 1 arc-second Current"),
            ("1 MeTeR", "Digital Elevation Model (DEM) 1 meter"),
            (
                "1/3 ARC-second",
                "National Elevation Dataset (NED) 1/3 arc-second Current",
            ),
            ("1/9 Arc-Second", "National Elevation Dataset (NED) 1/9 arc-second"),
            (
                "2 arc-second",
                "National Elevation Dataset (NED) Alaska 2 arc-second Current",
            ),
            ("5 meter", "Alaska IFSAR 5 meter DEM"),
        ),
    )
    def test(_, input, expected):
        output = dem.dataset(input)
        assert output == expected


class TestQuery:
    def test_unsupported(_, assert_contains):
        with pytest.raises(ValueError) as error:
            dem.query(None, "10 meter")
        assert_contains(
            error,
            "resolution (10 meter) is not a recognized option.",
            "Supported options are: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, 5 meter",
        )

    @patch("requests.get")
    def test(_, mock, json_response):
        content = {"total": 10, "items": [{"value": k} for k in range(10)]}
        mock.return_value = json_response(content)
        output = dem.query()
        assert output == content
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={
                "datasets": "National Elevation Dataset (NED) 1/3 arc-second Current",
                "outputFormat": "JSON",
            },
            timeout=60.0,
        )


class TestNTiles:
    def test_unsupported(_, assert_contains):
        with pytest.raises(ValueError) as error:
            dem.ntiles(None, "10 meter")
        assert_contains(
            error,
            "resolution (10 meter) is not a recognized option.",
            "Supported options are: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, 5 meter",
        )

    @patch("requests.get")
    def test(_, mock, json_response):
        content = {"total": 10, "items": [{"value": k} for k in range(10)]}
        mock.return_value = json_response(content)
        output = dem.ntiles()
        assert output == 10
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={
                "datasets": "National Elevation Dataset (NED) 1/3 arc-second Current",
                "max": 1,
                "offset": 0,
                "outputFormat": "JSON",
            },
            timeout=60.0,
        )


class TestTileInfo:
    def test(_, tile, tile_info):
        assert dem._tile_info(tile) == tile_info


class TestTiles:
    def test_unsupported(_, assert_contains):
        with pytest.raises(ValueError) as error:
            dem.tiles(None, "10 meter")
        assert_contains(
            error,
            "resolution (10 meter) is not a recognized option.",
            "Supported options are: 1/3 arc-second, 1 arc-second, 1 meter, 1/9 arc-second, 2 arc-second, 5 meter",
        )

    @patch("requests.get")
    def test(_, mock, json_response, tile, tile_info):
        content = {"total": 3, "items": [tile] * 3}
        mock.return_value = json_response(content)
        output = dem.tiles()
        assert output == [tile_info] * 3
        mock.assert_called_with(
            "https://tnmaccess.nationalmap.gov/api/v1/products",
            params={
                "datasets": "National Elevation Dataset (NED) 1/3 arc-second Current",
                "max": 500,
                "offset": 0,
                "outputFormat": "JSON",
            },
            timeout=60.0,
        )


#####
# Data reads
#####


class TestQueryTiles:
    @patch("requests.get")
    def test_too_many(_, mock, json_response, tile, assert_contains):
        content = {"total": 501, "items": [tile] * 3}
        mock.return_value = json_response(content)
        with pytest.raises(TooManyTNMProductsError) as error:
            dem._query_tiles(
                BoundingBox(1, 2, 3, 4, 4326),
                resolution="1/3 arc-second",
                timeout=60,
            )
        assert_contains(
            error, "There are over 500 DEM tiles matching the search criteria."
        )

    @patch("requests.get")
    def test_valid(_, mock, json_response, tile, tile_info):
        content = {"total": 3, "items": [tile] * 3}
        mock.return_value = json_response(content)
        output = dem._query_tiles(
            BoundingBox(1, 2, 3, 4, 4326),
            resolution="1/3 arc-second",
            timeout=60,
        )
        assert output == [tile_info] * 3


class TestValidateNtiles:
    def test_too_many(_, assert_contains):
        with pytest.raises(TooManyTNMProductsError) as error:
            dem._validate_ntiles(ntiles=15, max_tiles=10)
        assert_contains(
            error,
            "There are 15 DEM tiles in the search area, which is greater the maximum allowed number of tiles (10)",
        )

    def test_none(_, assert_contains):
        with pytest.raises(NoTNMProductsError) as error:
            dem._validate_ntiles(ntiles=0, max_tiles=10)
        assert_contains(error, "There are no DEM tiles in the search area")

    def test_valid(_):
        dem._validate_ntiles(ntiles=3, max_tiles=10)


class TestTileMetadata:
    @patch("pfdf.raster.RasterMetadata.from_url")
    def test_basic(_, mock, metamock, tile_info, metatiles):
        mock.side_effect = metamock
        tiles = []
        for t in range(4):
            tile = tile_info.copy()
            tile["download_url"] = t
            tiles.append(tile)

        bounds = BoundingBox(-105.5, 32.2, -104.5, 33.2, 4326)
        output = dem._tile_metadata(tiles, bounds)
        assert output == metatiles

    @patch("pfdf.raster.RasterMetadata.from_url")
    def test_skip_tiles(_, mock, metamock, tile_info, metatiles):
        mock.side_effect = metamock
        tiles = []
        for t in range(4):
            tile = tile_info.copy()
            tile["download_url"] = t
            tiles.append(tile)
        tiles[3]["download_url"] = 4

        bounds = BoundingBox(-105.5, 32.2, -104.5, 33.2, 4326)
        output = dem._tile_metadata(tiles, bounds)
        del metatiles[3]
        assert output == metatiles

    @patch("pfdf.raster.RasterMetadata.from_url")
    def test_different_crs(_, mock, metamock, tile_info, assert_contains):
        mock.side_effect = metamock
        tiles = []
        for t in range(4):
            tile = tile_info.copy()
            tile["download_url"] = t
            tiles.append(tile)
        tiles[3]["download_url"] = 5

        bounds = BoundingBox(-105.5, 32.2, -104.5, 33.2, 4326)
        with pytest.raises(CRSError) as error:
            dem._tile_metadata(tiles, bounds)
        assert_contains(
            error,
            "All the DEM tiles being read must have the same CRS",
            "the CRS of tile 0 (WGS 84) differs from the CRS of tile 3 (NAD83 / UTM zone 11N)",
        )

    @patch("pfdf.raster.RasterMetadata.from_url")
    def test_no_overlap(_, mock, metamock, tile_info, assert_contains):
        tile_info["download_url"] = 4
        tiles = [tile_info]
        mock.side_effect = metamock
        bounds = BoundingBox(-105.5, 32.2, -104.5, 33.2, 4326)
        with pytest.raises(NoTNMProductsError) as error:
            dem._tile_metadata(tiles, bounds)
        assert_contains(
            error,
            "The bounds must cover at least 1 pixel of DEM data",
        )


class TestEdges:
    def test(_):
        metadatas = {
            0: RasterMetadata((100, 100), bounds=[-106, 32, -105, 33, 4326]),
            1: RasterMetadata((100, 100), bounds=[-106, 33, -105, 34, 4326]),
            2: RasterMetadata((100, 100), bounds=[-105, 32, -104, 33, 4326]),
            3: RasterMetadata((100, 100), bounds=[-105, 33, -104, 34, 4326]),
        }

        minval, maxval = dem._edges(metadatas, min_edge="left", max_edge="right")
        assert minval == -106
        assert maxval == -104

        minval, maxval = dem._edges(metadatas, min_edge="bottom", max_edge="top")
        assert minval == 32
        assert maxval == 34


class TestPreallocate:
    def test_valid(_):
        metadata = RasterMetadata((10, 10), nodata=0, dtype=int)
        output = dem._preallocate(metadata)
        assert isinstance(output, np.ndarray)
        assert np.array_equal(output, np.full((10, 10), 0, int))

    def test_merror(_, assert_contains):
        metadata = RasterMetadata((1e100, 1e100), nodata=0, dtype="float64")
        with pytest.raises(MemoryError) as error:
            dem._preallocate(metadata)
        assert_contains(
            error, "Cannot read DEM data because the data array is too large for memory"
        )


class TestReadTiles:
    @patch("pfdf.raster.Raster.from_url")
    def test(_, mock, mock_raster, read_raster):
        mock.side_effect = mock_raster
        tiles = {k: RasterMetadata() for k in range(4)}
        metadata = RasterMetadata((7, 10), bounds=[-105.5, 32.5, -104.5, 33.2, 4326])
        values = np.full(metadata.shape, -1, int)
        assert not np.array_equal(values, read_raster)
        dem._read_tiles(tiles, metadata, values)
        assert np.array_equal(values, read_raster)


class TestRead:
    @patch("pfdf.raster.Raster.from_url")
    @patch("pfdf.raster.RasterMetadata.from_url")
    @patch("pfdf.data.usgs.tnm.dem._query_tiles")
    def test(
        _,
        tile_mock,
        meta_mock,
        raster_mock,
        tile_info,
        metamock,
        mock_raster,
        read_raster,
    ):

        # Mock tile info such that download URLs are replaced with int switches
        tiles = []
        for t in range(4):
            tile = tile_info.copy()
            tile["download_url"] = t
            tiles.append(tile)
        tile_mock.return_value = tiles

        # Mock from_url factories
        meta_mock.side_effect = metamock
        raster_mock.side_effect = mock_raster

        # Read array
        bounds = [-105.5, 32.5, -104.5, 33.2, 4326]
        output = dem.read(bounds)
        assert isinstance(output, Raster)
        assert np.array_equal(output.values, read_raster)

        # Also check the metadata
        expected = RasterMetadata((7, 10), dtype="int16", nodata=-1, bounds=bounds)
        assert output.metadata.isclose(expected)


@pytest.mark.web
class TestLive:
    def test(_):
        bounds = [-105.1, 32.9, -104.9, 33.1, 4326]
        output = dem.read(bounds)
        assert isinstance(output, Raster)
        expected = RasterMetadata(
            (2160, 2160),
            dtype="float32",
            nodata=-999999,
            bounds=(
                -105.09999999915978,
                32.89999999905562,
                -104.89999999894462,
                33.09999999927078,
                "NAD83",
            ),
        )
        assert output.metadata.isclose(expected)
