import numpy as np
import rasterio
from rasterio.windows import Window

from pfdf._utils import window as _window
from pfdf.projection import BoundingBox, Transform


class TestBuild:
    def test_same_crs(_, fraster, crs):
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97, crs)
        with rasterio.open(fraster) as file:
            window, out_crs, transform = _window.build(file, bounds)

        assert window == Window(1, 1, 2, 1)
        assert out_crs == crs
        assert transform == Transform(0.03, 0.03, -3.97, -2.97)

    def test_set_crs(_, tmp_path, araster, affine, crs):
        # Save a raster with no CRS
        path = tmp_path / "raster.tif"
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=araster.shape[0],
            width=araster.shape[1],
            count=1,
            dtype=araster.dtype,
            nodata=-999,
            transform=affine,
        ) as file:
            file.write(araster, 1)

        # Run command
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97, crs)
        with rasterio.open(path) as file:
            assert file.crs is None
            window, out_crs, transform = _window.build(file, bounds)

        # Check outputs
        assert window == Window(1, 1, 2, 1)
        assert out_crs == crs
        assert transform == Transform(0.03, 0.03, -3.97, -2.97)

    def test_different_crs(_, fraster, crs):
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97, crs).reproject(26910)
        with rasterio.open(fraster) as file:
            window, out_crs, transform = _window.build(file, bounds)

        print(window)
        assert window == Window(1, 1, 2, 1)
        assert out_crs == crs
        assert transform == Transform(0.03, 0.03, -3.97, -2.97)

    def test_exact(_, fraster, crs):
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97, crs)
        with rasterio.open(fraster) as file:
            window, out_crs, transform = _window.build(file, bounds)

        assert window == Window(1, 1, 2, 1)
        assert out_crs == crs
        assert transform == Transform(0.03, 0.03, -3.97, -2.97)

    def test_max_clipped(_, fraster, crs):
        bounds = BoundingBox(-3.97, 0, 0, -2.97, crs)
        with rasterio.open(fraster) as file:
            window, out_crs, transform = _window.build(file, bounds)

        print(window)
        assert window == Window(1, 1, 3, 1)
        assert out_crs == crs
        assert transform == Transform(0.03, 0.03, -3.97, -2.97)

    def test_all_clipped(_, fraster, crs):
        bounds = BoundingBox(-5, 0, 0, -5, crs)
        with rasterio.open(fraster) as file:
            affine = file.transform
            window, out_crs, transform = _window.build(file, bounds)

        assert window == Window(0, 0, 4, 2)
        assert out_crs == crs
        assert transform == Transform.from_affine(affine)
