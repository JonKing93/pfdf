"""
Utilities for working with file format drivers
----------
The driver module contains various functions with information about file-format
drivers for saving raster and vector-feature files. The pfdf package uses rasterio
and fiona to write raster and vector files, respectively. These libraries support
a variety of file formats, which can be selected using an optional "driver" input.
Users can return a summary of the available drivers using the "vectors" and "rasters"
functions. Note that these summaries are for drivers expected to work by default -
that is, they do not require the installation of external libraries.

When a driver is not provided, pfdf will attempt to determine the appropriate
file format using the file extension. See the "extensions" command for a summary
of the drivers inferred from various extensions. Alternatively, use the "from_path"
or "from_extension" command to return a summary of the driver inferred from a specific
file path or extension.
----------
Summaries:
    vectors         - Returns a pandas data frame summarizing available vector drivers
    rasters         - Returns a pandas data frame summarizing available raster drivers
    info            - Returns a summary of the queried driver

File Extensions:
    extensions      - Returns a pandas data frame with the drivers inferred from various extensions
    from_path       - Summarize the driver inferred from a specified file path
    from_extension  - Summarize the driver inferred from an input file extension

Internal:
    _table          - Formats a pandas data frame with summary information
"""

from __future__ import annotations

import typing
from pathlib import Path

from pandas import DataFrame

import pfdf._validate.core as validate
from pfdf._utils import dataframe

# Type hints
if typing.TYPE_CHECKING:
    from typing import Literal, Optional

    from pfdf.typing.core import Pathlike

    Driver = tuple[str, str, str]
    Drivers = tuple[Driver, ...]
    FileType = Literal["raster", "vector"]

# Official summaries of drivers expected to work without external libraries
_FIELDS = ("Driver", "Description", "Extensions")
_VECTOR_DRIVERS = (
    ("CSV", "Comma Separated Value", ".csv"),
    ("DGN", "Microstation DGN", ".dgn"),
    ("DXF", "AutoCAD DXF", ".dxf"),
    ("FlatGeobuf", "FlatGeobuf", ".fgb"),
    ("GML", "Geography Markup Language", ".gml, .xml"),
    ("GPKG", "GeoPackage vector", ".gpkg"),
    ("GPX", "GPS Exchange Format", ".gpx"),
    ("GeoJSON", "GeoJSON", ".json, .geojson"),
    ("GeoJSONSeq", "Sequence of GeoJSON features", ".geojsons, .geojsonl"),
    ("MapInfo File", "MapInfo TAB and MIF/MID", ".tab, .mid, .mif"),
    ("OGR_GMT", "GMT ASCII Vectors", ".gmt"),
    ("OpenFileGDB", "ESRI File Geodatabase Vector", ".gdb"),
    ("Shapefile", "ESRI Shapefile / DBF", ".shp, .dbf, .shz, .shp.zip"),
    ("SQLite", "SQLite / Spatialite RDBMS", ".sqlite, .db"),
)
_RASTER_DRIVERS = (
    ("ADRG", "ADRG/ARC Digitized Raster Graphics", ".gen"),
    ("BMP", "Bitmap", ".bmp"),
    ("BT", "VTP Binary Terrain Format", ".bt"),
    ("BYN", "Natural Resources Canada's Geoid file format", ".byn, .err"),
    ("EHdr", "ESRI labelled hdr", ".bil"),
    ("ERS", "ERMapper", ".ers"),
    ("GTiff", "GeoTIFF File Format", ".tif, .tiff"),
    ("HFA", "Erdas Imagine", ".img"),
    ("ILWIS", "Raster Map", ".mpr, .mpl"),
    ("ISIS3", "USGS Astrogeology ISIS Cube (Version 3)", ".lbl, .cub"),
    ("KRO", "KOLOR Raw Format", ".kro"),
    ("MFF", "Vexcel MFF Raster", ".hdr"),
    ("NITF", "National Imagery Transmission Format", ".ntf"),
    ("NTv2", "NTv2 Datum Grid Shift", ".gsb, .gvb"),
    ("NWT_GRD", "Northwood/Vertical Mapper File Format", ".grd"),
    ("PCIDSK", "PCI Geomatics Database File", ".pix"),
    ("PCRaster", "PCRaster raster file format", ".map"),
    ("PDS4", "NASA Planetary Data System (Version 4)", ".xml"),
    ("RMF", "Raster Matrix Format", ".rsw"),
    ("SAGA", "SAGA GIS Binary Grid File Format", ".sdat, .sg-grd-z"),
    ("SGI", "SGI Image Format", ".rgb"),
    ("Terragen", "Terragen Terrain File", ".ter"),
    ("USGSDEM", "USGS ASCII DEM (and CDED)", ".dem"),
    ("VRT", "GDAL Virtual Format", ".vrt"),
)


#####
# Summaries
#####


def info(driver: str) -> DataFrame:
    """
    info  Returns a pandas data frame summarizing a queried driver
    ----------
    info(driver)
    Returns a pandas data frame summarizing the input driver. The summary includes
    a description, and list of associated file extensions. Raises a ValueError if
    the driver name is not recognized.
    ----------
    Inputs:
        driver: The name of a driver

    Outputs:
        pandas.DataFrame: The driver summary. Columns are as follows:
            index (str): The name of the driver
            Description (str): A description
            Extensions (str): File extensions associated with the driver
    """

    # Get a dataframe with all available drivers
    drivers = _VECTOR_DRIVERS + _RASTER_DRIVERS
    info = _table(drivers)

    # Return info or ValueError if unrecognized
    if driver in info.index:
        return info[driver:driver]
    else:
        raise ValueError(
            f'Unrecognized driver name ({driver}). See the "rasters" and "vectors" '
            "functions for lists of recognized driver names."
        )


def rasters() -> DataFrame:
    """
    rasters  Returns a pandas.DataFrame summarizing available raster drivers
    ----------
    rasters()
    Returns a pandas DataFrame summarizing the raster drivers expected to work
    in all cases. Essentially, these are the raster drivers that do not require
    installing any additional libraries. The summary includes a description and
    the associated file extensions for each raster driver.
    ----------
    Outputs:
        pandas.DataFrame: A summary of raster drivers. Columns are as follows:
            index (str): The name of each driver
            Description (str): A description of each driver
            Extensions (str): The file extensions associated with each driver
    """
    return _table(_RASTER_DRIVERS)


def vectors() -> DataFrame:
    """
    vectors  Returns a pandas.DataFrame summarizing available vector feature drivers
    ----------
    vectors()
    Returns a pandas DataFrame summarizing the vector feature drivers expected to work
    in all cases. Essentially, these are the vector feature drivers that do not require
    installing any additional libraries. The summary includes a description and
    the associated file extensions for each vector feature driver.
    ----------
    Outputs:
        pandas.DataFrame: A summary of vector feature drivers. Columns are as follows:
            index (str): The name of each driver
            Description (str): A description of each driver
            Extensions (str): The file extensions associated with each driver
    """
    return _table(_VECTOR_DRIVERS)


def _table(drivers: Drivers) -> DataFrame:
    "Builds a pandas DataFrame for a set of driver info records"
    return dataframe.table(drivers, columns=_FIELDS[1:])


#####
# File Extensions
#####


def extensions(type: FileType) -> DataFrame:
    """
    extensions  Summarizes the drivers inferred from recognized file extensions
    ----------
    extensions(type='vector')
    extensions(type='raster')
    Returns a pandas DataFrame summarizing the drivers inferred from various file
    extensions for the indicated type of file. These summaries indicate the drivers
    that are inferred when a driver is not provided as input to a file saving command.
    Each summary consists of a file extension, driver, and description of the driver.
    ----------
    Inputs:
        type: The type of file. Either 'vector' or 'raster'

    Outputs:
        pandas.DataFrame: A summary of the drivers inferred from various file
            extensions. Columns are as follows:
            index (str): A file extension
            Driver (str): The driver inferred from the file extension
            Description (str): A description of the driver
    """

    # Get the correct set of drivers
    type = validate.option(type, "type", allowed=["vector", "raster"])
    if type == "vector":
        drivers = _VECTOR_DRIVERS
    elif type == "raster":
        drivers = _RASTER_DRIVERS

    # Iterate through drivers and extract the associated extensions
    index = []
    data = []
    for name, description, extensions in drivers:
        extensions = extensions.split(", ")
        for ext in extensions:
            index.append(ext)
            data.append([name, description])

    # Build data frame and sort alphabetically by extension
    df = DataFrame(index=index, data=data, columns=_FIELDS[0:2])
    return df.sort_index()


def from_path(path: Pathlike, type: Optional[FileType] = None) -> DataFrame | None:
    """
    from_path  Returns information about the driver inferred from a given file path
    ----------
    from_path(path)
    Returns a pandas.DataFrame summarizing the driver inferred from the input file
    path. Returns None if the file path has an unrecognized extension. Attempts
    to determine whether the file path is intended for a raster file or vector
    feature file. Raises a ValueError if the path ends in a ".xml", as this
    extension is associated with both raster and vector feature drivers, and so
    requires the "type" input (see below).

    from_path(path, type='vector')
    from_path(path, type='raster')
    Also specifies whether the file path is intended for a raster or vector feature
    file. Returns None if the file has an unrecognized extension for the indicated
    type of file. So most paths with raster extensions will return None when
    type='vector', and vice versa.
    ----------
    Inputs:
        path: A file path whose driver should be inferred
        type: The type of file. Either 'vector' or 'raster'

    Outputs:
        pandas.DataFrame | None: A pandas.DataFrame summarizing the inferred
            driver, or None if the driver cannot be determined. DataFrame columns
            are as follows:
            index (str): The name of the driver
            Description (str): A description of the driver
            Extensions (str): The file extensions associated with the driver
    """

    extension = Path(path).suffix
    return from_extension(extension, type)


def from_extension(ext: str, type: Optional[FileType] = None) -> DataFrame:
    """
    from_extension  Returns information about the driver inferred from a given file extension
    ----------
    from_extension(ext)
    Returns a pandas.DataFrame summarizing the driver inferred from the input file
    extension. Returns None if the extension is unrecognized. Adds a "." to the
    input extension if the extension does not begin with one. Attempts to determine
    whether the extension is intended for a raster file or vector feature file.
    Raises a ValueError if the extension is ".xml", as this extension is associated
    with both raster and vector feature drivers, and so requires the "type" input
    (see below).

    from_extension(ext, type='vector')
    from_extension(ext, type='raster')
    Also specifies whether the extension is intended for a raster or vector feature
    file. Returns None if the extension is unrecognized for the indicated type of
    file. So most raster extensions will return None when type='vector', and vice versa.
    ----------
    Inputs:
        ext: A file extension whose driver should be inferred
        type: The type of file. Either 'vector' or 'raster'

    Outputs:
        pandas.DataFrame| None: A pandas.DataFrame summarizing the inferred driver
            or None if the driver cannot be determined. DataFrame columns are:
            index (str): The name of the driver
            Description (str): A description of the driver
            Extensions (str): The file extensions associated with the driver
    """

    # Validate type (if provided)
    if type is not None:
        type = validate.option(type, "type", allowed=["vector", "raster"])

    # Get the extension. Add a leading "." if necessary
    if not ext.startswith("."):
        ext = f".{ext}"
    ext = ext.lower()

    # XML is in both sets of drivers, so requires an input file type
    if ext == ".xml" and type is None:
        raise ValueError(
            ".xml is supported for both rasters and vector features, so you "
            "must specify the type of file (raster or vector) to obtain the driver"
        )

    # Build extension maps
    exts = {
        "vector": extensions("vector"),
        "raster": extensions("raster"),
    }

    # Try to guess file type
    if type is None:
        if ext in exts["vector"].index:
            type = "vector"
        elif ext in exts["raster"].index:
            type = "raster"

    # Get the driver summary
    if type is None or ext not in exts[type].index:
        return None
    else:
        return exts[type][ext:ext]
