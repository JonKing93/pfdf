import pytest
from pandas import DataFrame

from pfdf.utils import driver


def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


class TestInfo:
    @pytest.mark.parametrize(
        "input, expected",
        (
            (
                "CSV",
                DataFrame(
                    [["Comma Separated Value", ".csv"]],
                    ["CSV"],
                    columns=["Description", "Extensions"],
                ),
            ),
            (
                "GTiff",
                DataFrame(
                    [["GeoTIFF File Format", ".tif, .tiff"]],
                    ["GTiff"],
                    columns=["Description", "Extensions"],
                ),
            ),
        ),
    )
    def test(_, input, expected):
        output = driver.info(input)
        assert all(output == expected)

    def test_unrecognized(_):
        with pytest.raises(ValueError) as error:
            driver.info("invalid")
        assert_contains(error, "Unrecognized driver name (invalid)")


def test_rasters():
    names = [
        "ADRG",
        "BMP",
        "BT",
        "BYN",
        "EHdr",
        "ERS",
        "GTiff",
        "HFA",
        "ILWIS",
        "ISIS3",
        "KRO",
        "MFF",
        "NITF",
        "NTv2",
        "NWT_GRD",
        "PCIDSK",
        "PCRaster",
        "PDS4",
        "RMF",
        "SAGA",
        "SGI",
        "Terragen",
        "USGSDEM",
        "VRT",
    ]
    data = [
        ["ADRG/ARC Digitized Raster Graphics", ".gen"],
        ["Bitmap", ".bmp"],
        ["VTP Binary Terrain Format", ".bt"],
        ["Natural Resources Canada's Geoid file format", ".byn, .err"],
        ["ESRI labelled hdr", ".bil"],
        ["ERMapper", ".ers"],
        ["GeoTIFF File Format", ".tif, .tiff"],
        ["Erdas Imagine", ".img"],
        ["Raster Map", ".mpr, .mpl"],
        ["USGS Astrogeology ISIS Cube (Version 3)", ".lbl, .cub"],
        ["KOLOR Raw Format", ".kro"],
        ["Vexcel MFF Raster", ".hdr"],
        ["National Imagery Transmission Format", ".ntf"],
        ["NTv2 Datum Grid Shift", ".gsb, .gvb"],
        ["Northwood/Vertical Mapper File Format", ".grd"],
        ["PCI Geomatics Database File", ".pix"],
        ["PCRaster raster file format", ".map"],
        ["NASA Planetary Data System (Version 4)", ".xml"],
        ["Raster Matrix Format", ".rsw"],
        ["SAGA GIS Binary Grid File Format", ".sdat, .sg-grd-z"],
        ["SGI Image Format", ".rgb"],
        ["Terragen Terrain File", ".ter"],
        ["USGS ASCII DEM (and CDED)", ".dem"],
        ["GDAL Virtual Format", ".vrt"],
    ]
    output = driver.rasters()
    expected = DataFrame(data, names, columns=["Description", "Extensions"])
    assert all(output == expected)


def test_vectors():
    names = [
        "CSV",
        "DGN",
        "DXF",
        "FlatGeobuf",
        "GML",
        "GPKG",
        "GPX",
        "GeoJSON",
        "GeoJSONSeq",
        "MapInfo File",
        "OGR_GMT",
        "OpenFileGDB",
        "Shapefile",
        "SQLite",
    ]
    data = [
        ["Comma Separated Value", ".csv"],
        ["Microstation DGN", ".dgn"],
        ["AutoCAD DXF", ".dxf"],
        ["FlatGeobuf", ".fgb"],
        ["Geography Markup Language", ".gml, .xml"],
        ["GeoPackage vector", ".gpkg"],
        ["GPS Exchange Format", ".gpx"],
        ["GeoJSON", ".json, .geojson"],
        ["Sequence of GeoJSON features", ".geojsons, .geojsonl"],
        ["MapInfo TAB and MIF/MID", ".tab, .mid, .mif"],
        ["GMT ASCII Vectors", ".gmt"],
        ["ESRI File Geodatabase Vector", ".gdb"],
        ["ESRI Shapefile / DBF", ".shp, .dbf, .shz, .shp.zip"],
        ["SQLite / Spatialite RDBMS", ".sqlite, .db"],
    ]
    output = driver.vectors()
    expected = DataFrame(data, names, columns=["Description", "Extensions"])
    assert all(output == expected)


def test_table():
    names = [
        "CSV",
        "DGN",
        "DXF",
        "FlatGeobuf",
        "GML",
        "GPKG",
        "GPX",
        "GeoJSON",
        "GeoJSONSeq",
        "MapInfo File",
        "OGR_GMT",
        "OpenFileGDB",
        "Shapefile",
        "SQLite",
    ]
    data = [
        ["Comma Separated Value", ".csv"],
        ["Microstation DGN", ".dgn"],
        ["AutoCAD DXF", ".dxf"],
        ["FlatGeobuf", ".fgb"],
        ["Geography Markup Language", ".gml, .xml"],
        ["GeoPackage vector", ".gpkg"],
        ["GPS Exchange Format", ".gpx"],
        ["GeoJSON", ".json, .geojson"],
        ["Sequence of GeoJSON features", ".geojsons, .geojsonl"],
        ["MapInfo TAB and MIF/MID", ".tab, .mid, .mif"],
        ["GMT ASCII Vectors", ".gmt"],
        ["ESRI File Geodatabase Vector", ".gdb"],
        ["ESRI Shapefile / DBF", ".shp, .dbf, .shz, .shp.zip"],
        ["SQLite / Spatialite RDBMS", ".sqlite, .db"],
    ]
    output = driver._table(driver._VECTOR_DRIVERS)
    expected = DataFrame(data, names, columns=["Description", "Extensions"])
    assert all(output == expected)


class TestExtensions:
    def test_vector(_):
        exts = [
            ".csv",
            ".db",
            ".dbf",
            ".dgn",
            ".dxf",
            ".fgb",
            ".gdb",
            ".geojson",
            ".geojsonl",
            ".geojsons",
            ".gml",
            ".gmt",
            ".gpkg",
            ".gpx",
            ".json",
            ".mid",
            ".mif",
            ".shp",
            ".shp.zip",
            ".shz",
            ".sqlite",
            ".tab",
            ".xml",
        ]
        data = [
            ["CSV", "Comma Separated Value"],
            ["SQLite", "SQLite / Spatialite RDBMS"],
            ["Shapefile", "ESRI Shapefile / DBF"],
            ["DGN", "Microstation DGN"],
            ["DXF", "AutoCAD DXF"],
            ["FlatGeobuf", "FlatGeobuf"],
            ["OpenFileGDB", "ESRI File Geodatabase Vector"],
            ["GeoJSON", "GeoJSON"],
            ["GeoJSONSeq", "Sequence of GeoJSON features"],
            ["GeoJSONSeq", "Sequence of GeoJSON features"],
            ["GML", "Geography Markup Language"],
            ["OGR_GMT", "GMT ASCII Vectors"],
            ["GPKG", "GeoPackage vector"],
            ["GPX", "GPS Exchange Format"],
            ["GeoJSON", "GeoJSON"],
            ["MapInfo File", "MapInfo TAB and MIF/MID"],
            ["MapInfo File", "MapInfo TAB and MIF/MID"],
            ["Shapefile", "ESRI Shapefile / DBF"],
            ["Shapefile", "ESRI Shapefile / DBF"],
            ["Shapefile", "ESRI Shapefile / DBF"],
            ["SQLite", "SQLite / Spatialite RDBMS"],
            ["MapInfo File", "MapInfo TAB and MIF/MID"],
            ["GML", "Geography Markup Language"],
        ]
        output = driver.extensions("vector")
        expected = DataFrame(data, exts, columns=["Driver", "Description"])
        assert all(output == expected)

    def test_raster(_):
        exts = [
            ".bil",
            ".bmp",
            ".bt",
            ".byn",
            ".cub",
            ".dem",
            ".err",
            ".ers",
            ".gen",
            ".grd",
            ".gsb",
            ".gvb",
            ".hdr",
            ".img",
            ".kro",
            ".lbl",
            ".map",
            ".mpl",
            ".mpr",
            ".ntf",
            ".pix",
            ".rgb",
            ".rsw",
            ".sdat",
            ".sg-grd-z",
            ".ter",
            ".tif",
            ".tiff",
            ".vrt",
            ".xml",
        ]
        data = [
            ["EHdr", "ESRI labelled hdr"],
            ["BMP", "Bitmap"],
            ["BT", "VTP Binary Terrain Format"],
            ["BYN", "Natural Resources Canada's Geoid file format"],
            ["ISIS3", "USGS Astrogeology ISIS Cube (Version 3)"],
            ["USGSDEM", "USGS ASCII DEM (and CDED)"],
            ["BYN", "Natural Resources Canada's Geoid file format"],
            ["ERS", "ERMapper"],
            ["ADRG", "ADRG/ARC Digitized Raster Graphics"],
            ["NWT_GRD", "Northwood/Vertical Mapper File Format"],
            ["NTv2", "NTv2 Datum Grid Shift"],
            ["NTv2", "NTv2 Datum Grid Shift"],
            ["MFF", "Vexcel MFF Raster"],
            ["HFA", "Erdas Imagine"],
            ["KRO", "KOLOR Raw Format"],
            ["ISIS3", "USGS Astrogeology ISIS Cube (Version 3)"],
            ["PCRaster", "PCRaster raster file format"],
            ["ILWIS", "Raster Map"],
            ["ILWIS", "Raster Map"],
            ["NITF", "National Imagery Transmission Format"],
            ["PCIDSK", "PCI Geomatics Database File"],
            ["SGI", "SGI Image Format"],
            ["RMF", "Raster Matrix Format"],
            ["SAGA", "SAGA GIS Binary Grid File Format"],
            ["SAGA", "SAGA GIS Binary Grid File Format"],
            ["Terragen", "Terragen Terrain File"],
            ["GTiff", "GeoTIFF File Format"],
            ["GTiff", "GeoTIFF File Format"],
            ["VRT", "GDAL Virtual Format"],
            ["PDS4", "NASA Planetary Data System (Version 4)"],
        ]
        output = driver.extensions("raster")
        expected = DataFrame(data, exts, columns=["Driver", "Description"])
        assert all(output == expected)

    def test_invalid_type(_):
        with pytest.raises(ValueError) as error:
            driver.extensions("invalid")
        assert_contains(error, "type", "not a recognized option")


class TestFromPath:
    @pytest.mark.parametrize(
        "path, expected",
        (
            ("test.csv", "CSV"),
            ("test.json", "GeoJSON"),
            ("test.geojson", "GeoJSON"),
            ("test.tif", "GTiff"),
        ),
    )
    def test_recognized(_, path, expected):
        output = driver.from_path(path)
        assert all(output == expected)

    @pytest.mark.parametrize("path", (("afile", "afile.weird")))
    def test_unrecognized(_, path):
        output = driver.from_path(path)
        assert output is None

    def test_bad_xml(_):
        with pytest.raises(ValueError) as error:
            driver.from_path("test.xml")
        assert_contains(error, ".xml", "must specify the type")

    @pytest.mark.parametrize(
        "path, type, expected",
        (
            ("test.csv", "vector", "CSV"),
            ("test.json", "vector", "GeoJSON"),
            ("test.geojson", "vector", "GeoJSON"),
            ("test.tif", "raster", "GTiff"),
            ("test.xml", "vector", "GML"),
            ("test.xml", "raster", "PDS4"),
        ),
    )
    def test_explicit_type(_, path, type, expected):
        output = driver.from_path(path, type)
        assert all(output == expected)

    @pytest.mark.parametrize(
        "path, type",
        (
            ("test.csv", "raster"),
            ("test.tif", "vector"),
            ("test.invalid", "vector"),
            ("test.invalid", "raster"),
        ),
    )
    def test_unrecognized_type(_, path, type):
        output = driver.from_path(path, type)
        assert output is None

    def test_invalid_type(_):
        with pytest.raises(ValueError) as error:
            driver.from_path("test.tif", "invalid")
        assert_contains(error, "type", "not a recognized option")


class TestFromExtension:
    @pytest.mark.parametrize(
        "ext, expected",
        (
            (".csv", "CSV"),
            ("csv", "CSV"),
            ("json", "GeoJSON"),
            (".geojson", "GeoJSON"),
            (".tif", "GTiff"),
        ),
    )
    def test_recognized(_, ext, expected):
        output = driver.from_extension(ext)
        assert all(output == expected)

    @pytest.mark.parametrize("ext", ("", ".weird"))
    def test_unrecognized(_, ext):
        output = driver.from_extension(ext)
        assert output is None

    def test_bad_xml(_):
        with pytest.raises(ValueError) as error:
            driver.from_extension(".xml")
        assert_contains(error, ".xml", "must specify the type")

    @pytest.mark.parametrize(
        "ext, type, expected",
        (
            (".csv", "vector", "CSV"),
            (".json", "vector", "GeoJSON"),
            (".geojson", "vector", "GeoJSON"),
            (".tif", "raster", "GTiff"),
            (".xml", "vector", "GML"),
            (".xml", "raster", "PDS4"),
        ),
    )
    def test_explicit_type(_, ext, type, expected):
        output = driver.from_extension(ext, type)
        assert all(output == expected)

    @pytest.mark.parametrize(
        "ext, type",
        (
            (".csv", "raster"),
            (".tif", "vector"),
            (".invalid", "vector"),
            (".invalid", "raster"),
        ),
    )
    def test_unrecognized_type(_, ext, type):
        output = driver.from_extension(ext, type)
        assert output is None

    def test_invalid_type(_):
        with pytest.raises(ValueError) as error:
            driver.from_extension(".tif", "invalid")
        assert_contains(error, "type", "not a recognized option")
