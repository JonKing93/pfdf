"""
Functions to build example datasets
----------
Data Grids:
    values          - Returns example raster data values
    mask            - Returns an example raster mask

Saving Files:
    _write          - Saves a data grid to file
    build_raster    - Saves an example raster
    build_mask      - Saves an example raster mask
"""

import fiona
import numpy as np
import rasterio
from affine import Affine
from rasterio import CRS

from .workspace import workspace


def values():
    "Returns an example raster data grid"

    rng = np.random.default_rng(seed=123456789)
    values = rng.integers(low=0, high=100, size=(50, 75), dtype="int16")
    values[[0, -1], :] = -999
    values[:, [0, -1]] = -999
    return values


def mask():
    "Returns an example raster data mask"
    return values() > 50


def _folder():
    "Ensures the examples folder exists"
    path = workspace() / "examples"
    path.mkdir(exist_ok=True)
    return path


def _write(filename, values, nodata):
    "Writes data values to file"

    with rasterio.open(
        _folder() / filename,
        "w",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        crs=CRS.from_epsg(26911),
        transform=Affine(10, 0, 0, 0, -10, 0),
        dtype=values.dtype,
        nodata=nodata,
    ) as file:
        file.write(values, 1)


def build_raster():
    "Saves an example raster file"
    _write("raster.tif", values(), nodata=-999)
    print("Built example raster")


def build_mask():
    "Saves and example raster mask"
    _write("mask.tif", mask().astype("int8"), nodata=0)
    print("Built example raster mask")


def _polygon(xs, ys, value):
    coords = [
        [
            (xs[0], ys[0]),
            (xs[0], ys[1]),
            (xs[1], ys[1]),
            (xs[1], ys[0]),
            (xs[0], ys[0]),
        ]
    ]
    return {
        "geometry": {"type": "Polygon", "coordinates": coords},
        "properties": {"my-data": value},
    }


def build_polygons():
    "Saves an example polygon file"

    records = [
        _polygon((0, 20), (0, 20), 1),
        _polygon((0, 20), (80, 100), 2),
        _polygon((80, 100), (80, 100), 3),
        _polygon((80, 100), (0, 20), 4),
        _polygon((40, 60), (40, 60), 5),
    ]
    with fiona.open(
        _folder() / "polygons.geojson",
        "w",
        schema={"geometry": "Polygon", "properties": {"my-data": "int"}},
        crs=CRS.from_epsg(26911),
    ) as file:
        file.writerecords(records)
    print("Built example polygon collection")


def build_segments():
    "Builds an example stream segment network"

    # Keep the imports here so the other examples can build quickly
    from pfdf import severity, watershed
    from pfdf.raster import Raster
    from pfdf.segments import Segments

    # Network delineation
    min_area_km2 = 0.025
    min_burned_area_km2 = 0.01
    max_length_m = 500

    # Load datasets
    perimeter = Raster.from_file("preprocessed/perimeter.tif", isbool=True).values
    dem = Raster.from_file("preprocessed/dem.tif")
    barc4 = Raster.from_file("preprocessed/barc4.tif")
    iswater = Raster.from_file("preprocessed/iswater.tif", isbool=True).values
    isretainment = Raster.from_file("preprocessed/retainments.tif", isbool=True)

    # Watershed
    isburned = severity.mask(barc4, "burned")
    conditioned = watershed.condition(dem)
    flow = watershed.flow(conditioned)

    # Flow accumulations
    pixel_area = dem.pixel_area(units="kilometers")
    area = watershed.accumulation(flow, times=pixel_area)
    burned_area = watershed.accumulation(flow, mask=isburned, times=pixel_area)
    nretainments = watershed.accumulation(flow, mask=isretainment)

    # Delineation mask
    large_enough = area.values >= min_area_km2
    below_burn = burned_area.values >= min_burned_area_km2
    below_retainment = nretainments.values > 0
    at_risk = perimeter | below_burn
    mask = large_enough & at_risk & ~iswater & ~below_retainment

    # Return initial network
    return Segments(flow, mask, max_length_m)
