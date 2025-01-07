from pathlib import Path

import fiona
import numpy as np
import pytest
import rasterio
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder
from rasterio.windows import Window

from pfdf.projection import BoundingBox
from pfdf.raster import RasterMetadata
from pfdf.raster._utils import factory


@pytest.fixture
def fmetadata(crs, affine):
    return RasterMetadata((2, 4), dtype=float, nodata=-999, crs=crs, transform=affine)


#####
# Standard factories
#####


class TestFile:
    def test_valid(_, fraster, fmetadata):
        with rasterio.open(fraster) as reader:
            output = factory.file(reader, 1, "test")
        expected = fmetadata.update(name="test")
        assert output == expected

    def test_band(_, araster, fmetadata, tmp_path):
        file = Path(tmp_path) / "test.tif"
        with rasterio.open(
            file,
            "w",
            dtype=araster.dtype,
            driver="GTiff",
            width=araster.shape[1],
            height=araster.shape[0],
            count=2,
            nodata=-999,
            transform=fmetadata.affine,
            crs=fmetadata.crs,
        ) as writer:
            writer.write(araster, 1)
            writer.write(araster, 2)

        with rasterio.open(file) as reader:
            output = factory.file(reader, 2, "")
        assert output == fmetadata


class TestWindow:
    def test_interior(_):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        bounds = BoundingBox(14, 14, 79, 89)
        metadata, window = factory.window(metadata, bounds)
        assert metadata == RasterMetadata((8, 7), bounds=(10, 10, 80, 90))
        assert window == Window.from_slices(rows=[1, 9], cols=[1, 8])

    def test_exterior(_):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        bounds = BoundingBox(-200, -200, 200, 200)
        output, window = factory.window(metadata, bounds)
        assert output == metadata
        assert window == Window.from_slices(rows=[0, 10], cols=[0, 10])

    def test_mixed(_):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        bounds = BoundingBox(-200, 14, 79, 200)
        metadata, window = factory.window(metadata, bounds)
        assert metadata == RasterMetadata((9, 8), bounds=(0, 10, 80, 100))
        assert window == Window.from_slices(rows=[0, 9], cols=[0, 8])

    @pytest.mark.parametrize(
        "bounds",
        (
            (-100, 20, -50, 80),
            (105, 20, 200, 80),
            (10, 200, 80, 300),
            (10, -200, 80, -100),
        ),
    )
    def test_no_overlap(_, bounds, assert_contains):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        bounds = BoundingBox(*bounds)
        for quadrant in [1, 2, 3, 4]:
            bounds = bounds.orient(quadrant)
            with pytest.raises(ValueError) as error:
                factory.window(metadata, bounds)
            assert_contains(
                error, "bounds must overlap the file dataset for at least 1 pixel"
            )


class TestPysheds:
    def test_valid(_, araster, transform, crs):
        view = ViewFinder(
            affine=transform.affine, crs=crs, nodata=np.array(-999), shape=araster.shape
        )
        input = PyshedsRaster(araster, view)
        output = factory.pysheds(input, "test")
        assert output == RasterMetadata(
            araster.shape,
            dtype=input.dtype,
            nodata=input.nodata,
            crs=crs,
            transform=transform,
            name="test",
        )

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            factory.pysheds(5, "test")
        assert_contains(error, "input raster must be a pysheds.sview.Raster object")


class TestArray:
    def test_no_metadata(_, araster):
        metadata, values = factory.array(
            araster, None, None, "safe", None, None, None, None, True
        )
        assert metadata == RasterMetadata(araster.shape, dtype=araster.dtype)
        assert np.array_equal(values, araster)

    def test_with_metadata(_, araster, crs, transform):
        metadata, values = factory.array(
            araster, "test", 5, "safe", crs, transform, None, None, True
        )
        assert metadata == RasterMetadata(
            araster.shape,
            dtype=araster.dtype,
            nodata=5,
            crs=crs,
            transform=transform,
            name="test",
        )
        assert np.array_equal(values, araster)

    def test_arraylike(_, araster):
        input = araster.tolist()
        metadata, values = factory.array(
            input, None, None, "safe", None, None, None, None, False
        )
        assert metadata == RasterMetadata(araster.shape, dtype=araster.dtype)
        assert np.array_equal(values, araster)

    def test_copy(_, araster):
        metadata, values = factory.array(
            araster, None, None, "safe", None, None, None, None, copy=True
        )
        assert metadata == RasterMetadata(araster.shape, dtype=araster.dtype)
        assert np.array_equal(values, araster)
        assert araster.base is None
        assert values.base is not araster

    def test_no_copy(_, araster):
        metadata, values = factory.array(
            araster, None, None, "safe", None, None, None, None, copy=False
        )
        assert metadata == RasterMetadata(araster.shape, dtype=araster.dtype)
        assert np.array_equal(values, araster)
        assert araster.base is None
        assert values.base is araster

    def test_template(_, araster, crs, affine):
        template = RasterMetadata(
            (1, 1), crs=crs, transform=affine, name="other", dtype=bool, nodata=False
        )
        metadata, values = factory.array(
            araster, "test", None, "safe", None, None, None, template, True
        )
        expected = RasterMetadata(
            araster.shape, dtype=araster.dtype, crs=crs, transform=affine, name="test"
        )
        assert metadata == expected
        assert np.array_equal(values, araster)

    def test_template_override(_, araster, crs, transform):
        template = RasterMetadata(
            (1, 1),
            crs=crs,
            transform=(1, 2, 3, 4),
            name="other",
            dtype=bool,
            nodata=False,
        )
        metadata, values = factory.array(
            araster, "test", None, "safe", None, transform, None, template, True
        )
        assert metadata == RasterMetadata(
            araster.shape,
            dtype=araster.dtype,
            crs=crs,
            transform=transform,
            name="test",
        )
        assert np.array_equal(values, araster)


#####
# Vector features
#####


class TestPoints:
    def test_points(_, points, crs):
        geomvals, metadata = factory.points(
            # General
            points,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert metadata == RasterMetadata(
            (5, 5), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 10, 60)
        )

    def test_multipoints(_, multipoints, crs):
        geomvals, metadata = factory.points(
            # General
            multipoints,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(multipoints) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert metadata == RasterMetadata(
            (8, 8), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 10, 90)
        )

    def test_bounded(_, points, crs):
        bounds = BoundingBox(0, 0, 30, 30)
        geomvals, metadata = factory.points(
            # General
            points,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            bounds,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(points) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features][0:1]
        assert metadata == RasterMetadata(
            (3, 3), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 0, 30)
        )


class TestPolygons:
    def test_invalid_dtype(_, polygons, assert_contains):
        with pytest.raises(ValueError) as error:
            factory.polygons(
                polygons,
                "test",
                # Field
                "int64",
                None,
                None,
                None,
                None,
                # Spatial
                None,
                10,
                "meters",
                # File IO
                None,
                None,
                None,
            )
        assert_contains(
            error,
            "dtype (int64) is not a recognized option",
            "bool, int16, int32, uint8, uint16, uint32, float32, float64",
        )

    def test_polygons(_, polygons, crs):
        geomvals, metadata = factory.polygons(
            # General
            polygons,
            None,
            # Field
            None,
            None,
            None,
            None,
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert metadata == RasterMetadata(
            (7, 7), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_multipolygons(_, multipolygons, crs):
        geomvals, metadata = factory.polygons(
            # General
            multipolygons,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            None,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(multipolygons) as file:
            features = list(file)
        assert geomvals == [(feature["geometry"], True) for feature in features]
        assert metadata == RasterMetadata(
            (7, 7), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_bounded(_, polygons, crs):
        bounds = (30, 10, 50, 30, crs)
        geomvals, metadata = factory.polygons(
            # General
            polygons,
            None,
            # Field
            None,
            None,
            None,
            "safe",
            None,
            # Spatial
            bounds,
            10,
            "meters",
            # File IO
            None,
            None,
            None,
        )
        with fiona.open(polygons) as file:
            features = list(file)
        assert geomvals == [(features[0]["geometry"], True)]
        assert metadata == RasterMetadata(
            (2, 2), dtype=bool, nodata=False, crs=crs, bounds=(30, 10, 50, 30)
        )
