import os
from math import nan
from pathlib import Path

import numpy as np
import pytest
import rasterio
from pysheds.sview import Raster as PyshedsRaster
from pysheds.sview import ViewFinder

from pfdf.errors import CRSError, DimensionError, MissingCRSError, MissingTransformError
from pfdf.projection import CRS, BoundingBox, Transform
from pfdf.raster import RasterMetadata
from pfdf.utils.nodata import default as default_nodata

#####
# Dunders / built-ins
#####


class TestInit:
    def test_shape_only(_):
        a = RasterMetadata((2, 3))
        assert a.shape == (2, 3)
        assert a.dtype is None
        assert a.nodata is None
        assert a.crs is None
        assert a.transform is None
        assert a.name == "raster"

    def test_invalid_shape(_, assert_contains):
        with pytest.raises(DimensionError) as error:
            RasterMetadata((1, 2, 3))
        assert_contains(error, "shape must have exactly 2 elements")

    def test_default_shape(_):
        assert RasterMetadata().shape == (0, 0)

    @pytest.mark.parametrize("dtype", (bool, "float32", int, "uint16"))
    def test_dtype_only(_, dtype):
        a = RasterMetadata(dtype=dtype)
        assert isinstance(a.dtype, np.dtype)
        assert a.dtype == dtype

    def test_nodata_only(_):
        a = RasterMetadata(nodata=9)
        assert a.dtype == int
        assert a.nodata == 9
        assert a.nodata.dtype == a.dtype

    def test_dtype_nodata(_):
        a = RasterMetadata(dtype="int8", nodata=9)
        assert a.dtype == "int8"
        assert a.nodata.dtype == a.dtype
        assert a.nodata == 9

    def test_nodata_casting(_):
        a = RasterMetadata(dtype=int, nodata=1.2, casting="unsafe")
        assert a.dtype == int
        assert a.nodata == 1
        assert a.nodata.dtype == a.dtype

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            RasterMetadata(dtype=int, nodata=1.2)
        assert_contains(error, "Cannot cast the NoData value")

    def test_invalid_casting_option(_, assert_contains):
        with pytest.raises(ValueError) as error:
            RasterMetadata(dtype=int, nodata=9, casting="invalid")
        assert_contains(error, "casting (invalid) is not a recognized option")

    def test_crs(_):
        a = RasterMetadata(crs=4326)
        assert isinstance(a.crs, CRS)
        assert a.crs == 4326

    def test_invalid_crs(_, assert_contains):
        with pytest.raises(CRSError) as error:
            RasterMetadata(crs="invalid")
        assert_contains(error, "Unsupported CRS")

    def test_crs_and_transform(_):
        a = RasterMetadata((10, 20), crs=26911, transform=(10, -10, 0, 100))
        assert isinstance(a.crs, CRS)
        assert a.crs == 26911
        assert isinstance(a.transform, Transform)
        assert a.transform == Transform(10, -10, 0, 100, 26911)
        assert isinstance(a.bounds, BoundingBox)
        assert a.bounds == BoundingBox(0, 0, 200, 100, 26911)

    def test_crs_and_bounds(_):
        a = RasterMetadata((10, 20), crs=26911, bounds=(0, 0, 200, 100))
        assert isinstance(a.crs, CRS)
        assert a.crs == 26911
        assert isinstance(a.transform, Transform)
        assert a.transform == Transform(10, -10, 0, 100, 26911)
        assert isinstance(a.bounds, BoundingBox)
        assert a.bounds == BoundingBox(0, 0, 200, 100, 26911)

    def test_transform_nocrs(_):
        a = RasterMetadata((10, 20), transform=(10, -10, 0, 100))
        assert a.crs is None
        assert isinstance(a.transform, Transform)
        assert a.transform == Transform(10, -10, 0, 100)
        assert isinstance(a.bounds, BoundingBox)
        assert a.bounds == BoundingBox(0, 0, 200, 100)

    def test_bounds_nocrs(_):
        a = RasterMetadata((10, 20), bounds=(0, 0, 200, 100))
        assert a.crs is None
        assert isinstance(a.transform, Transform)
        assert a.transform == Transform(10, -10, 0, 100)
        assert isinstance(a.bounds, BoundingBox)
        assert a.bounds == BoundingBox(0, 0, 200, 100)

    def test_transform_inherit_crs(_):
        a = RasterMetadata((10, 20), transform=(10, -10, 0, 100, 4326))
        assert isinstance(a.crs, CRS)
        assert a.crs == 4326
        assert isinstance(a.transform, Transform)
        assert a.transform == Transform(10, -10, 0, 100, 4326)
        assert isinstance(a.bounds, BoundingBox)
        assert a.bounds == BoundingBox(0, 0, 200, 100, 4326)

    def test_bounds_inherit_crs(_):
        a = RasterMetadata((10, 20), bounds=(0, 0, 200, 100, 4326))
        assert isinstance(a.crs, CRS)
        assert a.crs == 4326
        assert isinstance(a.transform, Transform)
        assert a.transform == Transform(10, -10, 0, 100, 4326)
        assert isinstance(a.bounds, BoundingBox)
        assert a.bounds == BoundingBox(0, 0, 200, 100, 4326)

    def test_invalid_transform(_, assert_contains):
        with pytest.raises(TypeError) as error:
            RasterMetadata((10, 20), transform="invalid")
        assert_contains(
            error,
            "transform must be a Transform, Raster, RasterMetadata, dict, list, tuple, or affine.Affine",
        )

    def test_invalid_bounds(_, assert_contains):
        with pytest.raises(TypeError) as error:
            RasterMetadata((10, 20), bounds="invalid")
        assert_contains(
            error,
            "bounds must be a BoundingBox, Raster, RasterMetadata, dict, list, or tuple.",
        )

    def test_both_transform_bounds(_, assert_contains):
        with pytest.raises(ValueError) as error:
            RasterMetadata(
                (10, 20), bounds=(0, 0, 200, 100), transform=(10, -10, 0, 100)
            )
        assert_contains(
            error,
            'You cannot provide both "transform" and "bounds" metadata. The two inputs are mutually exclusive.',
        )

    def test_linear_reproject_transform(_):
        shape = (10, 20)
        transform = Transform(10, -10, 0, 100, 26911)
        bounds = BoundingBox(0, 0, 200, 100, 26911)

        a = RasterMetadata(shape, crs=26910, transform=transform)
        assert a.crs == 26910
        assert a.transform == bounds.reproject(26910).transform(*shape)
        assert a.transform != transform.reproject(26910)
        assert a.bounds == bounds.reproject(26910)

    def test_linear_reproject_bounds(_):
        shape = (10, 20)
        transform = Transform(10, -10, 0, 100, 26911)
        bounds = BoundingBox(0, 0, 200, 100, 26911)

        a = RasterMetadata(shape, crs=26910, bounds=bounds)
        assert a.crs == 26910
        assert a.transform == bounds.reproject(26910).transform(*shape)
        assert a.transform != transform.reproject(26910)
        assert a.bounds == bounds.reproject(26910)

    def test_angular_reproject_transform(_):
        shape = (10, 20)
        transform = Transform(10, -10, 0, 100, 26911)
        bounds = BoundingBox(0, 0, 200, 100, 26911)

        a = RasterMetadata(shape, crs=4326, transform=transform)
        assert a.crs == 4326
        assert a.transform == bounds.reproject(4326).transform(*shape)
        assert a.transform != transform.reproject(4326)
        assert a.bounds == bounds.reproject(4326)

    def test_angular_reproject_bounds(_):
        shape = (10, 20)
        transform = Transform(10, -10, 0, 100, 26911)
        bounds = BoundingBox(0, 0, 200, 100, 26911)

        a = RasterMetadata(shape, crs=4326, bounds=bounds)
        assert a.crs == 4326
        assert a.transform == bounds.reproject(4326).transform(*shape)
        assert a.transform != transform.reproject(4326)
        assert a.bounds == bounds.reproject(4326)

    def test_name(_):
        a = RasterMetadata(name="test")
        assert a.name == "test"

    def test_invalid_name(_, assert_contains):
        with pytest.raises(TypeError) as error:
            RasterMetadata(name=5)
        assert_contains(error, "name must be a string")

    def test_transform_0_shape(_):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        assert a.bounds == BoundingBox(3, 4, 3, 4)

    @pytest.mark.parametrize("shape", ((0, 0), (1, 0), (0, 1)))
    def test_bounds_0_shape(_, shape, assert_contains):
        with pytest.raises(ValueError) as error:
            RasterMetadata(shape, bounds=(1, 2, 3, 4))
        assert_contains(
            error, 'cannot specify "bounds" metadata when the shape includes 0 values'
        )


class TestEq:
    def test_same(_):
        a = RasterMetadata(
            (1, 2), dtype=bool, nodata=False, crs=26911, transform=(1, 2, 3, 4)
        )
        b = RasterMetadata(
            (1, 2), dtype=bool, nodata=False, crs=26911, transform=(1, 2, 3, 4)
        )
        assert a == b

    def test_same_none(_):
        a = RasterMetadata((1, 2))
        b = RasterMetadata((1, 2))
        assert a == b

    def test_same_nan_nodata(_):
        a = RasterMetadata(
            (1, 2), dtype=float, nodata=nan, crs=26911, transform=(1, 2, 3, 4)
        )
        b = RasterMetadata(
            (1, 2), dtype=float, nodata=nan, crs=26911, transform=(1, 2, 3, 4)
        )
        assert a == b

    def test_not_object(_):
        a = RasterMetadata((1, 2))
        b = a.todict()
        assert a != b

    def test_different_shape(_):
        a = RasterMetadata((1, 2))
        b = RasterMetadata((2, 2))
        assert a != b

    @pytest.mark.parametrize("dtype", ("int16", None))
    def test_different_dtype(_, dtype):
        a = RasterMetadata((1, 2), dtype="int8")
        b = RasterMetadata((1, 2), dtype=dtype)
        assert a != b

    @pytest.mark.parametrize("nodata", (2, None))
    def test_different_nodata(_, nodata):
        a = RasterMetadata((1, 2), dtype="int8", nodata=1)
        b = RasterMetadata((1, 2), dtype="int8", nodata=nodata)
        assert a != b

    @pytest.mark.parametrize("crs", (26910, None))
    def test_different_crs(_, crs):
        a = RasterMetadata((1, 2), crs=26911)
        b = RasterMetadata((1, 2), crs=crs)
        assert a != b

    @pytest.mark.parametrize(
        "transform",
        (
            (1, 2, 3, 4),
            (1, 2, 3, 4, 26910),
            (4, 3, 2, 1, 26911),
        ),
    )
    def test_different_transform(_, transform):
        a = RasterMetadata((1, 2), transform=(1, 2, 3, 4, 26911))
        b = RasterMetadata((1, 2), transform=transform)
        assert a != b


class TestRepr:
    def test_none(_):
        a = RasterMetadata((1, 2))
        assert repr(a) == (
            "RasterMetadata:\n"
            "    Name: raster\n"
            "    Shape: (1, 2)\n"
            "    Dtype: None\n"
            "    NoData: None\n"
            "    CRS: None\n"
            "    Transform: None\n"
            "    BoundingBox: None\n"
        )

    def test_all(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        assert repr(a) == (
            "RasterMetadata:\n"
            "    Name: Test\n"
            "    Shape: (10, 20)\n"
            "    Dtype: int8\n"
            "    NoData: 2\n"
            '    CRS("NAD83 / UTM zone 10N")\n'
            '    Transform(dx=10, dy=-10, left=0, top=100, crs="NAD83 / UTM zone 10N")\n'
            '    BoundingBox(left=0, bottom=0, right=200, top=100, crs="NAD83 / UTM zone 10N")\n'
        )


class TestGetItem:
    def test_no_transform(_):
        a = RasterMetadata((100, 100))
        b = a[2:-1, :]
        assert b == RasterMetadata((97, 100))

    def test_from_transform(_):
        a = RasterMetadata((100, 200), transform=(10, -10, 0, 100))
        b = a[2:-1, 5]
        assert b == RasterMetadata(
            (97, 1),
            transform=Transform(10, -10, 50, 80),
        )

    def test_from_bounds(_):
        a = RasterMetadata((100, 200), bounds=(0, -900, 2000, 100))
        b = a[2:-1, 5]
        assert b == RasterMetadata(
            (97, 1),
            transform=Transform(10, -10, 50, 80),
        )

    def test_bounds_only(_):
        a = RasterMetadata((10, 10), transform=(10, -10, 0, 100))
        b = a[0:3, :]
        assert b == RasterMetadata((3, 10), transform=(10, -10, 0, 100))
        assert b.bounds == BoundingBox(0, 70, 100, 100)

    def test_zero(_, assert_contains):
        a = RasterMetadata()
        with pytest.raises(IndexError) as error:
            a[0, 0]
        assert_contains(
            error, "Indexing is not supported when the raster shape contains a 0"
        )

    def test_empty(_, assert_contains):
        a = RasterMetadata((10, 10))
        with pytest.raises(IndexError) as error:
            a[4:3, 5]
        assert_contains(error, "row indices must select at least one element")

    def test_step_size(_, assert_contains):
        a = RasterMetadata((10, 10))
        with pytest.raises(IndexError) as error:
            a[5, 1:10:2]
        assert_contains(error, "column indices must have a step size of 1")

    def test_1d(_, assert_contains):
        a = RasterMetadata((10, 10))
        with pytest.raises(IndexError) as error:
            a[5]
        assert_contains(error, "You must provide indices for exactly 2 dimensions")

    def test_3d(_, assert_contains):
        a = RasterMetadata((10, 10))
        with pytest.raises(IndexError) as error:
            a[1, 1, 1]
        assert_contains(error, "You must provide indices for exactly 2 dimensions")

    def test_return_slices(_):
        a = RasterMetadata((100, 200), transform=(10, -10, 0, 100))
        indices = (slice(2, -1), 5)
        b, rows, cols = a.__getitem__(indices, return_slices=True)
        assert b == RasterMetadata(
            (97, 1),
            transform=Transform(10, -10, 50, 80),
        )
        assert rows == slice(2, 99, 1)
        assert cols == slice(5, 6, 1)


class TestToDict:
    def test(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        output = a.todict()
        assert isinstance(output, dict)
        assert output == {
            "shape": (10, 20),
            "dtype": np.dtype("int8"),
            "nodata": 2,
            "crs": CRS(26910),
            "transform": Transform(10, -10, 0, 100, 26910),
            "bounds": BoundingBox(0, 0, 200, 100, 26910),
            "name": "Test",
        }


#####
# Updated objects
#####


class TestUpdate:
    def test_array(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(dtype="int16", nodata=1, name="new name")
        assert b == RasterMetadata(
            (10, 20),
            dtype="int16",
            nodata=1,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="new name",
        )
        assert a == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_transform(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(transform=(1, 2, 3, 4))
        assert b == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(1, 2, 3, 4),
            name="Test",
        )
        assert a == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_bounds(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(bounds=(1, 2, 3, 4))
        assert b == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            bounds=(1, 2, 3, 4),
            name="Test",
        )
        assert a == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_both_transform_bounds(_, assert_contains):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        with pytest.raises(ValueError) as error:
            a.update(transform=(1, 2, 3, 4), bounds=(1, 2, 3, 4))
        assert_contains(
            error, 'You cannot provide both "transform" and "bounds" metadata'
        )

    def test_invalid_nodata(_, assert_contains):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        with pytest.raises(TypeError) as error:
            a.update(nodata=1.2)
        assert_contains(
            error,
            "Cannot cast the NoData value (value = 1.2) to the raster dtype (int8) using 'safe' casting",
        )

    def test_invalid_dtype(_, assert_contains):
        a = RasterMetadata(
            (10, 20),
            dtype=float,
            nodata=1.2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        with pytest.raises(TypeError) as error:
            a.update(dtype=int)
        assert_contains(
            error,
            "Cannot cast the NoData value (value = 1.2) to the raster dtype",
        )

    def test_nodata_casting(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(nodata=1.2, casting="unsafe")
        assert b == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=1,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_dtype_casting(_):
        a = RasterMetadata(
            (10, 20),
            dtype=float,
            nodata=1.2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(dtype=int, casting="unsafe")
        assert b == RasterMetadata(
            (10, 20),
            dtype=int,
            nodata=1,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_both_dtype_nodata(_):
        a = RasterMetadata(
            (10, 20),
            dtype=float,
            nodata=1.2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(dtype=bool, nodata=False)
        assert b == RasterMetadata(
            (10, 20),
            dtype=bool,
            nodata=False,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_add_crs(_):
        a = RasterMetadata(
            (10, 20), dtype=float, nodata=1.2, transform=(10, -10, 0, 100), name="Test"
        )
        b = a.update(crs=26910)
        assert b == RasterMetadata(
            (10, 20),
            dtype=float,
            nodata=1.2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )

    def test_new_crs(_):
        bounds = BoundingBox(0, 0, 200, 100, 26911)
        a = RasterMetadata(
            (10, 20), dtype="int8", nodata=2, crs=26911, bounds=bounds, name="Test"
        )
        b = a.update(crs=26910)
        expected = bounds.reproject(26910)
        assert b == RasterMetadata(
            (10, 20), dtype="int8", nodata=2, crs=26910, bounds=expected, name="Test"
        )

    def test_reproject_new_bounds(_):
        base_bounds = BoundingBox(0, 0, 200, 100, 26911)
        new_bounds = BoundingBox(0, 0, 200, 100, 26910)
        final_bounds = new_bounds.reproject(26911)
        a = RasterMetadata(
            (10, 20), dtype="int8", nodata=2, crs=26911, bounds=base_bounds, name="Test"
        )
        b = a.update(bounds=new_bounds)
        assert b.bounds == final_bounds
        assert b == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26911,
            bounds=final_bounds,
            name="Test",
        )

    def test_reproject_new_transform(_):
        shape = (10, 20)
        base_transform = Transform(10, -10, 0, 100, 26911)
        new_transform = Transform(10, -10, 0, 100, 26910)
        final_transform = (
            new_transform.bounds(*shape).reproject(26911).transform(*shape)
        )
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26911,
            transform=base_transform,
            name="Test",
        )
        b = a.update(transform=new_transform)
        assert b.transform == final_transform
        assert b == RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26911,
            transform=final_transform,
            name="Test",
        )

    def test_new_shape_keep_transform(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        assert a.bounds == BoundingBox(0, 0, 200, 100, 26910)
        b = a.update(shape=(5, 10))
        assert b == RasterMetadata(
            (5, 10),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        assert b.bounds == BoundingBox(0, 50, 100, 100, 26910)

    def test_new_shape_keep_bounds(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            bounds=(0, 0, 200, 100),
            name="Test",
        )
        assert a.transform == Transform(10, -10, 0, 100, 26910)
        b = a.update(shape=(5, 10), keep_bounds=True)
        assert b == RasterMetadata(
            (5, 10),
            dtype="int8",
            nodata=2,
            crs=26910,
            bounds=(0, 0, 200, 100),
            name="Test",
        )
        assert b.transform == Transform(20, -20, 0, 100, 26910)

    def test_new_shape_new_transform(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(10, -10, 0, 100),
            name="Test",
        )
        b = a.update(shape=(5, 10), transform=(1, 2, 3, 4))
        assert b == RasterMetadata(
            (5, 10),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(1, 2, 3, 4),
            name="Test",
        )

    def test_new_shape_new_bounds(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(0, 0, 200, 10),
            name="Test",
        )
        b = a.update(shape=(5, 10), bounds=(1, 2, 3, 4))
        assert b == RasterMetadata(
            (5, 10), dtype="int8", nodata=2, crs=26910, bounds=(1, 2, 3, 4), name="Test"
        )


class TestCopy:
    def test(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(0, 0, 200, 10),
            name="Test",
        )
        b = a.copy()
        assert a == b
        assert a is not b


class TestAsBool:
    def test_initialize(_):
        a = RasterMetadata((1, 2))
        b = a.as_bool()
        assert b == RasterMetadata((1, 2), dtype=bool, nodata=False)

    def test_reset(_):
        a = RasterMetadata(
            (10, 20),
            dtype="int8",
            nodata=2,
            crs=26910,
            transform=(0, 0, 200, 10),
            name="Test",
        )
        b = a.as_bool()
        assert b == RasterMetadata(
            (10, 20),
            dtype=bool,
            nodata=False,
            crs=26910,
            transform=(0, 0, 200, 10),
            name="Test",
        )


class TestEnsureNodata:
    def test_has_nodata(_):
        a = RasterMetadata((1, 2), dtype=int, nodata=2)
        b = a.ensure_nodata()
        assert a == b
        assert a is not b

    def test_no_dtype(_, assert_contains):
        a = RasterMetadata((1, 2))
        with pytest.raises(ValueError) as error:
            a.ensure_nodata()
        assert_contains(
            error,
            "Cannot ensure nodata because the raster metadata does not have a dtype",
        )

    def test_auto_nodata(_):
        a = RasterMetadata((1, 2), dtype="int16")
        b = a.ensure_nodata()
        assert b == RasterMetadata(
            (1, 2), dtype="int16", nodata=default_nodata("int16")
        )

    def test_user_default(_):
        a = RasterMetadata((1, 2), dtype="int16")
        b = a.ensure_nodata(default=2)
        assert b == RasterMetadata((1, 2), dtype="int16", nodata=2)

    def test_casting(_):
        a = RasterMetadata((1, 2), dtype="int16")
        b = a.ensure_nodata(default=2.2, casting="unsafe")
        assert b == RasterMetadata((1, 2), dtype="int16", nodata=2)

    def test_invalid_casting(_, assert_contains):
        a = RasterMetadata((1, 2), dtype="int16")
        with pytest.raises(TypeError) as error:
            a.ensure_nodata(default=1.2)
        assert_contains(
            error,
            "Cannot cast the NoData value (value = 1.2) to the raster dtype (int16) using 'safe' casting.",
        )

    def test_invalid_casting_option(_, assert_contains):
        a = RasterMetadata((1, 2), dtype="int16")
        with pytest.raises(ValueError) as error:
            a.ensure_nodata(default=2, casting="invalid")
        assert_contains(
            error,
            "casting (invalid) is not a recognized option. Supported options are: no, equiv, safe, same_kind, unsafe",
        )


class TestCreate:
    def test_both_and_empty(_):
        a = RasterMetadata((10, 20))
        b = a._create(isbool=True, ensure_nodata=True)
        assert b == RasterMetadata((10, 20), dtype=bool, nodata=False)

    def test_both_and_full(_):
        a = RasterMetadata((10, 20), dtype="int32", nodata=2)
        b = a._create(isbool=True, ensure_nodata=True)
        assert b == RasterMetadata((10, 20), dtype=bool, nodata=False)

    def test_isbool(_):
        a = RasterMetadata((10, 20), dtype="int32", nodata=2)
        b = a._create(isbool=True, ensure_nodata=False)
        assert b == RasterMetadata((10, 20), dtype=bool, nodata=False)

    def test_ensure_nodata(_):
        a = RasterMetadata((10, 20), dtype="int32")
        b = a._create(
            isbool=False, ensure_nodata=True, default_nodata=3, casting="safe"
        )
        assert b == RasterMetadata((10, 20), dtype="int32", nodata=3)

    def test_neither_and_empty(_):
        a = RasterMetadata((10, 20))
        b = a._create(isbool=False, ensure_nodata=False)
        assert b == RasterMetadata((10, 20))
        assert b is a

    def test_neither_and_full(_):
        a = RasterMetadata((10, 20), dtype="int32", nodata=2)
        b = a._create(isbool=False, ensure_nodata=False)
        assert b is a
        assert b == RasterMetadata((10, 20), dtype="int32", nodata=2)


#####
# Factories
#####


class TestFromFile:
    def test(_, fraster, fmetadata):
        assert RasterMetadata.from_file(fraster) == fmetadata
        assert RasterMetadata.from_file(fraster, name="test") == fmetadata.update(
            name="test"
        )

    def test_driver(_, tmp_path, fraster, fmetadata):
        path = Path(tmp_path) / "test.unusual"
        os.rename(fraster, path)
        assert RasterMetadata.from_file(path, driver="GTiff") == fmetadata

    def test_bounded_exact(_, fraster, fmetadata):
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97)
        output = RasterMetadata.from_file(fraster, bounds=bounds)
        expected = fmetadata.update(shape=(1, 2), transform=(0.03, 0.03, -3.97, -2.97))
        assert output == expected

    def test_bounded_clipped(_, fraster, fmetadata):
        bounds = BoundingBox(-3.97, 0, 0, -2.97)
        output = RasterMetadata.from_file(fraster, bounds=bounds)
        expected = fmetadata.update(shape=(1, 3), transform=(0.03, 0.03, -3.97, -2.97))
        print(output)
        print(expected)
        assert output == expected

    def test_isbool(_, fraster, fmetadata):
        output = RasterMetadata.from_file(fraster, isbool=True)
        assert output == fmetadata.update(dtype=bool, nodata=False)

    def test_ensure_nodata(_, fraster, fmetadata):
        with rasterio.open(fraster) as file:
            araster = file.read(1)

        with rasterio.open(
            fraster,
            "w",
            dtype=fmetadata.dtype,
            height=fmetadata.height,
            width=fmetadata.width,
            transform=fmetadata.affine,
            crs=fmetadata.crs,
            count=1,
        ) as file:
            file.write(araster, 1)

        output = RasterMetadata.from_file(fraster, ensure_nodata=True, default_nodata=2)
        expected = fmetadata.update(nodata=2)
        assert output == expected


class TestFromRasterio:
    @staticmethod
    def reader(path):
        with rasterio.open(path) as reader:
            return reader

    def test(self, fraster, fmetadata):
        reader = self.reader(fraster)
        assert RasterMetadata.from_rasterio(reader) == fmetadata
        assert RasterMetadata.from_rasterio(reader, name="test") == fmetadata.update(
            name="test"
        )

    def test_driver(self, tmp_path, fraster, fmetadata):
        path = Path(tmp_path) / "test.unusual"
        os.rename(fraster, path)
        with rasterio.open(path, driver="GTiff") as reader:
            pass
        assert RasterMetadata.from_rasterio(reader) == fmetadata

    def test_bounded_exact(self, fraster, fmetadata):
        reader = self.reader(fraster)
        bounds = BoundingBox(-3.97, -2.94, -3.91, -2.97)
        output = RasterMetadata.from_rasterio(reader, bounds=bounds)
        expected = fmetadata.update(shape=(1, 2), transform=(0.03, 0.03, -3.97, -2.97))
        assert output == expected

    def test_bounded_clipped(self, fraster, fmetadata):
        reader = self.reader(fraster)
        bounds = BoundingBox(-3.97, 0, 0, -2.97)
        output = RasterMetadata.from_rasterio(reader, bounds=bounds)
        expected = fmetadata.update(shape=(1, 3), transform=(0.03, 0.03, -3.97, -2.97))
        assert output == expected

    def test_isbool(self, fraster, fmetadata):
        reader = self.reader(fraster)
        output = RasterMetadata.from_rasterio(reader, isbool=True)
        assert output == fmetadata.update(dtype=bool, nodata=False)

    def test_ensure_nodata(self, fraster, fmetadata):
        with rasterio.open(fraster) as file:
            araster = file.read(1)

        with rasterio.open(
            fraster,
            "w",
            dtype=fmetadata.dtype,
            height=fmetadata.height,
            width=fmetadata.width,
            transform=fmetadata.affine,
            crs=fmetadata.crs,
            count=1,
        ) as file:
            file.write(araster, 1)

        reader = self.reader(fraster)
        output = RasterMetadata.from_rasterio(
            reader, ensure_nodata=True, default_nodata=2
        )
        assert output == fmetadata.update(nodata=2)


class TestFromPysheds:
    def test(_, araster, affine, crs):
        view = ViewFinder(affine=affine, crs=crs, nodata=-999, shape=araster.shape)
        input = PyshedsRaster(araster, view)
        output = RasterMetadata.from_pysheds(input)
        expected = RasterMetadata(
            araster.shape,
            dtype=araster.dtype,
            nodata=input.nodata,
            crs=crs,
            transform=affine,
        )
        assert output == expected

        output = RasterMetadata.from_pysheds(input, name="test")
        expected = RasterMetadata(
            araster.shape,
            name="test",
            dtype=araster.dtype,
            nodata=input.nodata,
            crs=crs,
            transform=affine,
        )
        assert output == expected

    def test_isbool(_, araster, affine, crs):
        view = ViewFinder(affine=affine, crs=crs, nodata=-999, shape=araster.shape)
        input = PyshedsRaster(araster, view)
        output = RasterMetadata.from_pysheds(input, isbool=True)
        expected = RasterMetadata(
            araster.shape, dtype=bool, nodata=False, crs=crs, transform=affine
        )
        assert output == expected


class TestFromArray:
    def test_no_metadata(_, araster):
        output = RasterMetadata.from_array(araster)
        expected = RasterMetadata(araster.shape, dtype=araster.dtype, nodata=nan)
        assert output == expected

    def test_metadata(_, araster, crs, transform):
        output = RasterMetadata.from_array(
            araster, name="test", crs=crs, transform=transform, nodata=5
        )
        assert output == RasterMetadata(
            araster.shape,
            dtype=araster.dtype,
            nodata=5,
            crs=crs,
            transform=transform,
            name="test",
        )

    def test_template(_, araster, crs, transform):
        template = RasterMetadata(
            (1, 1), dtype=int, nodata=9, crs=crs, transform=transform, name="unused"
        )
        output = RasterMetadata.from_array(araster, spatial=template)
        expected = RasterMetadata(
            araster.shape, dtype=araster.dtype, nodata=nan, crs=crs, transform=transform
        )
        assert output == expected

    def test_template_override(_, araster, crs, transform):
        template = RasterMetadata(
            (1, 1), dtype=int, nodata=9, crs=crs, transform=(1, 2, 3, 4), name="unused"
        )
        output = RasterMetadata.from_array(
            araster, spatial=template, transform=transform
        )
        expected = RasterMetadata(
            araster.shape, dtype=araster.dtype, nodata=nan, crs=crs, transform=transform
        )
        assert output == expected

    def test_isbool(_, araster):
        output = RasterMetadata.from_array(araster, isbool=True)
        assert output == RasterMetadata(araster.shape, dtype=bool, nodata=False)

    def test_no_ensure_nodata(_, araster):
        output = RasterMetadata.from_array(araster, ensure_nodata=False)
        assert output == RasterMetadata(araster.shape, dtype=float)


#####
# Vector factories
#####


class TestFromPoints:
    def test_invalid_path(_):
        with pytest.raises(FileNotFoundError):
            RasterMetadata.from_points("not-a-file")

    def test_points(_, points, crs):
        metadata = RasterMetadata.from_points(points)
        assert metadata == RasterMetadata(
            (5, 5), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 10, 60)
        )

    def test_multipoints(_, multipoints, crs):
        metadata = RasterMetadata.from_points(multipoints)
        assert metadata == RasterMetadata(
            (8, 8), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 10, 90)
        )

    def test_fixed_res(_, points, crs):
        metadata = RasterMetadata.from_points(points, resolution=20)
        assert metadata == RasterMetadata(
            (3, 3), dtype=bool, nodata=False, crs=crs, transform=(20, -20, 10, 60)
        )

    def test_mixed_res(_, points, crs):
        metadata = RasterMetadata.from_points(points, resolution=(20, 10))
        assert metadata == RasterMetadata(
            (5, 3), dtype=bool, nodata=False, crs=crs, transform=(20, -10, 10, 60)
        )

    def test_units(_, points, crs):
        meta = RasterMetadata.from_points(
            points, resolution=(0.02, 0.01), units="kilometers"
        )
        assert meta == RasterMetadata(
            (5, 3), dtype=bool, nodata=False, crs=crs, transform=(20, -10, 10, 60)
        )

    def test_driver(_, points, crs):
        newfile = points.parent / "test.unusual"
        os.rename(points, newfile)
        meta = RasterMetadata.from_points(newfile, driver="GeoJSON")
        assert meta == RasterMetadata(
            (5, 5), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 10, 60)
        )

    def test_int_field(_, points, crs):
        meta = RasterMetadata.from_points(points, field="test")
        assert meta == RasterMetadata(
            (5, 5),
            dtype="int32",
            nodata=np.iinfo("int32").min,
            crs=crs,
            transform=(10, -10, 10, 60),
        )

    def test_float_field(_, points, crs):
        meta = RasterMetadata.from_points(points, "test-float")
        assert meta == RasterMetadata(
            (5, 5), dtype=float, nodata=nan, crs=crs, transform=(10, -10, 10, 60)
        )

    def test_dtype_casting(_, points, crs):
        meta = RasterMetadata.from_points(
            points, field="test-float", dtype="int32", field_casting="unsafe"
        )
        assert meta == RasterMetadata(
            (5, 5),
            dtype="int32",
            nodata=np.iinfo("int32").min,
            crs=crs,
            transform=(10, -10, 10, 60),
        )

    def test_invalid_dtype_casting(_, points, assert_contains):
        with pytest.raises(TypeError) as error:
            RasterMetadata.from_points(
                points, field="test-float", dtype="int32", field_casting="safe"
            )
        assert_contains(
            error, "Cannot cast the value for feature 0", "to the raster dtype"
        )

    def test_operation(_, points, crs):
        def times100(value):
            return value * 100

        meta = RasterMetadata.from_points(
            points, field="test-float", operation=times100
        )
        assert meta == RasterMetadata(
            (5, 5), dtype=float, nodata=nan, crs=crs, transform=(10, -10, 10, 60)
        )

    def test_invalid_field(_, points):
        with pytest.raises(KeyError):
            RasterMetadata.from_points(points, field="missing")

    def test_windowed(_, points, crs):
        bounds = BoundingBox(10, 0, 30, 30, crs)
        meta = RasterMetadata.from_points(points, bounds=bounds)
        assert meta == RasterMetadata(
            (3, 2), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 10, 30)
        )


class TestFromPolygons:
    def test_invalid_path(_):
        with pytest.raises(FileNotFoundError):
            RasterMetadata.from_polygons("not-a-file")

    def test_polygons(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(polygons)
        assert metadata == RasterMetadata(
            (7, 7), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_multipolygons(_, multipolygons, crs):
        metadata = RasterMetadata.from_polygons(multipolygons)
        assert metadata == RasterMetadata(
            (7, 7), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_fixed_res(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(polygons, resolution=30)
        expected = RasterMetadata(
            (3, 3), dtype=bool, nodata=False, crs=crs, transform=(30, -30, 20, 90)
        )
        print(metadata)
        print(expected)
        assert metadata == expected

    def test_mixed_res(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(polygons, resolution=[30, 10])
        assert metadata == RasterMetadata(
            (7, 3), dtype=bool, nodata=False, crs=crs, transform=(30, -10, 20, 90)
        )

    def test_units(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(
            polygons, resolution=[0.030, 0.010], units="kilometers"
        )
        assert metadata == RasterMetadata(
            (7, 3), dtype=bool, nodata=False, crs=crs, transform=(30, -10, 20, 90)
        )

    def test_template_res(_, polygons, crs, araster):
        template = RasterMetadata.from_array(araster, transform=(30, -10, -90, -90))
        metadata = RasterMetadata.from_polygons(polygons, resolution=template)
        assert metadata == RasterMetadata(
            (7, 3), dtype=bool, nodata=False, crs=crs, transform=(30, -10, 20, 90)
        )

    def test_driver(_, polygons, crs):
        newfile = polygons.parent / "test.unusual"
        os.rename(polygons, newfile)
        metadata = RasterMetadata.from_polygons(newfile, driver="GeoJSON")
        assert metadata == RasterMetadata(
            (7, 7), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_int_field(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(polygons, field="test")
        assert metadata == RasterMetadata(
            (7, 7),
            dtype="int32",
            nodata=np.iinfo("int32").min,
            crs=crs,
            transform=(10, -10, 20, 90),
        )

    def test_float_field(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(polygons, field="test-float")
        assert metadata == RasterMetadata(
            (7, 7), dtype="float64", nodata=nan, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_dtype_casting(_, polygons, crs):
        metadata = RasterMetadata.from_polygons(
            polygons, field="test-float", dtype="int32", field_casting="unsafe"
        )
        assert metadata == RasterMetadata(
            (7, 7),
            dtype="int32",
            nodata=np.iinfo("int32").min,
            crs=crs,
            transform=(10, -10, 20, 90),
        )

    def test_invalid_dtype_casting(_, polygons, assert_contains):
        with pytest.raises(TypeError) as error:
            RasterMetadata.from_polygons(
                polygons, field="test-float", dtype="int32", field_casting="safe"
            )
        assert_contains(
            error, "Cannot cast the value for feature 0", "to the raster dtype"
        )

    def test_unsupported_dtype(_, polygons, assert_contains):
        with pytest.raises(ValueError) as error:
            RasterMetadata.from_polygons(
                polygons, field="test-field", dtype="int64", field_casting="unsafe"
            )
        assert_contains(
            error,
            "dtype (int64) is not a recognized option",
            "bool, int16, int32, uint8, uint16, uint32, float32, float64",
        )

    def test_operation(_, polygons, crs):
        def times100(value):
            return value * 100

        metadata = RasterMetadata.from_polygons(
            polygons, field="test-float", operation=times100
        )
        assert metadata == RasterMetadata(
            (7, 7), dtype="float64", nodata=nan, crs=crs, transform=(10, -10, 20, 90)
        )

    def test_invalid_field(_, polygons):
        with pytest.raises(KeyError):
            RasterMetadata.from_polygons(polygons, field="missing")

    def test_windowed(_, polygons, crs):
        bounds = BoundingBox(50, 0, 70, 40, crs)
        metadata = RasterMetadata.from_polygons(polygons, bounds=bounds)
        assert metadata == RasterMetadata(
            (4, 2), dtype=bool, nodata=False, crs=crs, transform=(10, -10, 50, 40)
        )


#####
# Preprocessing
#####


class TestFill:
    def test_no_nodata(_):
        a = RasterMetadata(dtype=float, nodata=None)
        b = a.fill()
        assert b is not a
        assert b == a
        assert b.nodata is None

    def test_with_nodata(_):
        a = RasterMetadata(dtype=float, nodata=4)
        b = a.fill()
        assert b == RasterMetadata(dtype=float, nodata=None)


class TestBuffer:
    def test_no_return_buffers(_, fmetadata):
        output = fmetadata.buffer(0.09)
        expected = RasterMetadata(
            (fmetadata.height + 6, fmetadata.width + 6),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.09, -3.09),
        )
        assert output.isclose(expected)

    def test_all_default(_, fmetadata):
        output, buffers = fmetadata.buffer(0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 6, fmetadata.width + 6),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.09, -3.09),
        )
        assert buffers == {"left": 3, "right": 3, "bottom": 3, "top": 3}
        assert output.isclose(expected)

    def test_left(_, fmetadata):
        output, buffers = fmetadata.buffer(left=0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height, fmetadata.width + 3),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.09, -3),
        )
        assert buffers == {"left": 3, "right": 0, "bottom": 0, "top": 0}
        assert output.isclose(expected)

    def test_right(_, fmetadata):
        output, buffers = fmetadata.buffer(right=0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height, fmetadata.width + 3),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4, -3),
        )
        assert buffers == {"left": 0, "right": 3, "bottom": 0, "top": 0}
        assert output.isclose(expected)

    def test_top(_, fmetadata):
        output, buffers = fmetadata.buffer(top=0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 3, fmetadata.width),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4, -3.09),
        )
        assert buffers == {"left": 0, "right": 0, "bottom": 0, "top": 3}
        assert output.isclose(expected)

    def test_bottom(_, fmetadata):
        output, buffers = fmetadata.buffer(bottom=0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 3, fmetadata.width),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4, -3),
        )
        assert buffers == {"left": 0, "right": 0, "bottom": 3, "top": 0}
        assert output.isclose(expected)

    def test_mixed(_, fmetadata):
        output, buffers = fmetadata.buffer(
            0.09, left=0.06, top=0.03, return_buffers=True
        )
        expected = RasterMetadata(
            (fmetadata.height + 4, fmetadata.width + 5),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.06, -3.03),
        )
        assert buffers == {"left": 2, "right": 3, "bottom": 3, "top": 1}
        assert output.isclose(expected)

    def test_inexact_buffer(_, fmetadata):
        output, buffers = fmetadata.buffer(0.08, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 6, fmetadata.width + 6),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.09, -3.09),
        )
        assert buffers == {"left": 3, "right": 3, "bottom": 3, "top": 3}
        assert output.isclose(expected)

    def test_invert_transform(_, fmetadata):
        fmetadata = fmetadata.update(transform=(-0.03, -0.03, -4, -3))
        output, buffers = fmetadata.buffer(0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 6, fmetadata.width + 6),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(-0.03, -0.03, -3.91, -2.91),
        )
        assert buffers == {"left": 3, "right": 3, "bottom": 3, "top": 3}
        assert output.isclose(expected)

    def test_pixels(_, fmetadata):
        output, buffers = fmetadata.buffer(2, units="pixels", return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 4, fmetadata.width + 4),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.06, -3.06),
        )
        assert buffers == {"left": 2, "right": 2, "bottom": 2, "top": 2}
        assert output.isclose(expected)

    def test_pixels_no_transform(_, fmetadata):
        fmetadata = RasterMetadata(
            fmetadata.shape,
            dtype=fmetadata.dtype,
            nodata=fmetadata.nodata,
            crs=fmetadata.crs,
        )
        output, buffers = fmetadata.buffer(2, units="pixels", return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 4, fmetadata.width + 4),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
        )
        assert buffers == {"left": 2, "right": 2, "bottom": 2, "top": 2}
        assert output.isclose(expected)

    def test_meters(_, fmetadata):
        output, buffers = fmetadata.buffer(0.09, units="meters", return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 6, fmetadata.width + 6),
            dtype=fmetadata.dtype,
            nodata=-999,
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.09, -3.09),
        )
        assert buffers == {"left": 3, "right": 3, "bottom": 3, "top": 3}
        assert output.isclose(expected)

    def test_meters_no_crs(_, assert_contains):
        fmetadata = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            fmetadata.buffer(0.09)
        assert_contains(error, "Cannot convert buffering distances from meters")

    def test_no_transform(_, assert_contains):
        fmetadata = RasterMetadata()
        with pytest.raises(MissingTransformError) as error:
            fmetadata.buffer(0.09, units="base")
        assert_contains(error, "does not have an affine transform")

    def test_no_buffer(_, assert_contains):
        metadata = RasterMetadata(crs=26910, transform=(10, -10, 0, 0))
        with pytest.raises(ValueError) as error:
            metadata.buffer()
        assert_contains(error, "must specify at least one buffer")

    def test_no_nodata(_, fmetadata):
        fmetadata = RasterMetadata(fmetadata.shape, transform=fmetadata.transform)
        output, buffers = fmetadata.buffer(0.09, return_buffers=True)
        expected = RasterMetadata(
            (fmetadata.height + 6, fmetadata.width + 6),
            crs=fmetadata.crs,
            transform=(0.03, 0.03, -4.09, -3.09),
        )
        assert buffers == {"left": 3, "right": 3, "bottom": 3, "top": 3}
        assert output.isclose(expected)

    def test_0_buffer(_, fmetadata, assert_contains):
        with pytest.raises(ValueError) as error:
            fmetadata.buffer(distance=0)
        assert_contains(error, "Buffering distances cannot all be 0")


class TestClip:
    def test_different_crs(_, crs):
        bounds = BoundingBox(2, 8, 8, 3, crs).reproject(4326)
        metadata = RasterMetadata((10, 10), crs=crs, transform=(1, 1, 0, 0))
        output, rows, cols = metadata.clip(bounds, return_limits=True)

        expected = RasterMetadata((5, 6), transform=(1, 1, 2, 3), crs=crs)
        assert output.isclose(expected)
        assert rows == (3, 8)
        assert cols == (2, 8)

    def test_no_transform(_, assert_contains):
        bounds = BoundingBox(1, 2, 3, 4)
        metadata = RasterMetadata((10, 10))
        with pytest.raises(MissingTransformError) as error:
            metadata.clip(bounds)
        assert_contains(error, "does not have an affine Transform")

    def test_interior(_):
        bounds = BoundingBox(2, 8, 8, 3)
        metadata = RasterMetadata((10, 10), transform=(1, 1, 0, 0))
        output, rows, cols = metadata.clip(bounds, return_limits=True)
        expected = RasterMetadata((5, 6), transform=(1, 1, 2, 3))
        assert output.isclose(expected)
        assert rows == (3, 8)
        assert cols == (2, 8)

    def test_exterior(_):
        bounds = BoundingBox(-5, 15, 8, 3)
        metadata = RasterMetadata((10, 10), transform=(1, 1, 0, 0))
        output, rows, cols = metadata.clip(bounds, return_limits=True)
        expected = RasterMetadata((12, 13), transform=(1, 1, -5, 3))
        assert output.isclose(expected)
        assert rows == (3, 15)
        assert cols == (-5, 8)

    def test_inherit_crs(_):
        bounds = BoundingBox(2, 8, 8, 3, 4326)
        metadata = RasterMetadata((10, 10), transform=(1, 1, 0, 0))
        output, rows, cols = metadata.clip(bounds, return_limits=True)
        expected = RasterMetadata((5, 6), crs=4326, transform=(1, 1, 2, 3))
        assert output.isclose(expected)
        assert rows == (3, 8)
        assert cols == (2, 8)

    def test_no_return_limits(_):
        bounds = BoundingBox(2, 8, 8, 3)
        metadata = RasterMetadata((10, 10), transform=(1, 1, 0, 0))
        output = metadata.clip(bounds)
        expected = RasterMetadata((5, 6), transform=(1, 1, 2, 3))
        assert output.isclose(expected)


class TestReproject:
    def test_no_parameters(_, assert_contains):
        metadata = RasterMetadata(crs=4326, transform=(1, 2, 3, 4))
        with pytest.raises(ValueError) as error:
            metadata.reproject()
        assert_contains(error, "cannot all be None")

    def test_missing_transform(_, assert_contains):
        metadata = RasterMetadata(crs=26910)
        with pytest.raises(MissingTransformError) as error:
            metadata.reproject(crs=26911)
        assert_contains(error, "does not have an affine Transform")

    def test_invalid_crs(_):
        metadata = RasterMetadata(crs=26911, transform=(1, 2, 3, 4))
        with pytest.raises(CRSError):
            metadata.reproject(crs="invalid")

    def test_invalid_transform(_, assert_contains):
        metadata = RasterMetadata(crs=26910, transform=(1, 2, 3, 4))
        with pytest.raises(TypeError) as error:
            metadata.reproject(transform="invalid")
        assert_contains(
            error,
            "transform must be a Transform, Raster, RasterMetadata, dict, list, tuple, or affine.Affine",
        )

    def test_nocrs_crs(_):
        metadata = RasterMetadata((10, 10), transform=(1, 2, 3, 4))
        output = metadata.reproject(crs=26911)
        assert output == RasterMetadata((10, 10), crs=26911, transform=(1, 2, 3, 4))

    def test_nocrs_transform(_):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        output = metadata.reproject(transform=(5, -5, 3, 107))
        assert output == RasterMetadata((21, 21), bounds=(-2, -3, 103, 102))

    def test_nocrs_both(_):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        output = metadata.reproject(crs=26911, transform=(5, -5, 3, 107))
        assert output == RasterMetadata((21, 21), crs=26911, bounds=(-2, -3, 103, 102))

    def test_crs_crs(_):
        metadata = RasterMetadata(
            (10, 10), crs=26911, transform=(10, -10, 492850, 3787000)
        )
        output = metadata.reproject(crs=26910)
        expected = RasterMetadata(
            (10, 10),
            crs=26910,
            transform=(
                10.611507906054612,
                -10.611507906066254,
                1045837.212456758,
                3802903.3056026916,
            ),
        )
        assert output.transform.isclose(expected.transform)
        assert output.isclose(expected)

    def test_crs_transform(_):
        metadata = RasterMetadata(
            (10, 10), crs=26911, transform=(10, -10, 492850, 3787000)
        )
        output = metadata.reproject(transform=(20, -20, 1045830, 3802910))
        expected = RasterMetadata(
            (6, 5), crs=26911, transform=(20, -20, 492850, 3787010)
        )
        assert output.isclose(expected)

    def test_crs_both(_):
        metadata = RasterMetadata(
            (10, 10), crs=26911, transform=(10, -10, 492850, 3787000)
        )
        output = metadata.reproject(crs=26910, transform=(20, -20, 0, 0))
        expected = RasterMetadata(
            (7, 7), crs=26910, transform=(20, -20, 1045820, 3802920)
        )
        assert output.isclose(expected)

    def test_inherit_crs(_):
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        output = metadata.reproject(transform=(5, -5, 3, 107, 26911))
        assert output == RasterMetadata((21, 21), crs=26911, bounds=(-2, -3, 103, 102))

    def test_reproject_template_transform(_):
        transform = Transform(5, -5, 3, 107, 26911).reproject(26910)
        metadata = RasterMetadata((10, 10), bounds=(0, 0, 100, 100))
        output = metadata.reproject(crs=26911, transform=transform)
        expected = RasterMetadata(
            (21, 21),
            crs=26911,
            bounds=(
                -2.0000812358979605,
                -2.9999182678848086,
                103.00020307314117,
                102.0000037150961,
            ),
        )
        assert output.transform.isclose(expected.transform)
        assert output.isclose(expected)

    def test_kwargs(_):
        metadata = RasterMetadata(
            (10, 10), crs=26911, transform=(10, -10, 492850, 3787000)
        )
        output = metadata.reproject(crs=26910, transform=(20, -20, 0, 0))
        expected = RasterMetadata(
            (7, 7), crs=26910, transform=(20, -20, 1045820, 3802920)
        )
        assert output.isclose(expected)

    def test_template(_):
        metadata = RasterMetadata(
            (10, 10), crs=26911, transform=(10, -10, 492850, 3787000)
        )
        template = RasterMetadata(crs=26910, transform=(20, -20, 0, 0))
        output = metadata.reproject(template)
        expected = RasterMetadata(
            (7, 7), crs=26910, transform=(20, -20, 1045820, 3802920)
        )
        assert output.isclose(expected)

    def test_template_override(_):
        metadata = RasterMetadata(
            (10, 10), crs=26911, transform=(10, -10, 492850, 3787000)
        )
        template = RasterMetadata(crs=26910, transform=(1, 2, 3, 4))
        output = metadata.reproject(template, transform=(20, -20, 0, 0))
        expected = RasterMetadata(
            (7, 7), crs=26910, transform=(20, -20, 1045820, 3802920)
        )
        assert output.isclose(expected)


#####
# Testing
#####


class TestIsClose:
    def test_none(_):
        a = RasterMetadata((1, 2))
        b = RasterMetadata((1, 2))
        c = RasterMetadata((3, 4))
        assert a.isclose(b)
        assert not a.isclose(c)

    def test_all(_):
        a = RasterMetadata(
            (1, 1), dtype=float, nodata=nan, crs=26911, transform=(10, -10, 0, 10)
        )
        b = RasterMetadata(
            (1, 1), dtype=float, nodata=nan, crs=26911, bounds=(0, 0, 10, 10)
        )
        assert a.isclose(b)

    def test_close_transform(_):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        b = RasterMetadata(transform=(1.000000000001, 2, 3, 4))
        assert a.isclose(b)

    def test_not_close_transform(_):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        b = RasterMetadata(transform=(1.1, 2, 3, 4))
        assert not a.isclose(b)

    def test_invalid(_, assert_contains):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(TypeError) as error:
            a.isclose(Transform(1, 2, 3, 4))
        assert_contains(error, "other must be a RasterMetadata object")

    def test_different_crs(_):
        a = RasterMetadata(crs=26911, transform=(1, 2, 3, 4))
        b = RasterMetadata(crs=26910, transform=(1, 2, 3, 4))
        assert not a.isclose(b)

    def test_none_crs(_):
        a = RasterMetadata(crs=26911, transform=(1, 2, 3, 4))
        b = RasterMetadata(transform=(1, 2, 3, 4))
        assert a.isclose(b)


#####
# Shape
#####


class TestShape:
    def test_shape(_):
        assert RasterMetadata((10, 20)).shape == (10, 20)


class TestNRows:
    def test_nrows(_):
        assert RasterMetadata((10, 20)).nrows == 10


class TestHeight:
    def test_height(_):
        assert RasterMetadata((10, 20)).height == 10


class TestNCols:
    def test_ncols(_):
        assert RasterMetadata((10, 20)).ncols == 20


class TestWidth:
    def test_width(_):
        assert RasterMetadata((10, 20)).width == 20


class TestSize:
    def test_size(_):
        assert RasterMetadata((10, 20)).size == 200


#####
# Data Array
#####


class TestDtype:
    def test(_):
        assert RasterMetadata(dtype="int32").dtype == "int32"
        assert RasterMetadata().dtype is None


class TestNodata:
    def test(_):
        assert RasterMetadata(dtype=int, nodata=5).nodata == 5
        assert RasterMetadata().nodata is None


class TestName:
    def test(_):
        assert RasterMetadata().name == "raster"
        assert RasterMetadata(name="test").name == "test"


#####
# CRS
#####


class TestCRS:
    def test(_):
        output = RasterMetadata(crs=26911).crs
        assert isinstance(output, CRS)
        assert output == 26911

    def test_none(_):
        assert RasterMetadata().crs is None


class TestCRSUnits:
    def test(_):
        assert RasterMetadata().crs_units == (None, None)
        assert RasterMetadata(crs=26911).crs_units == ("metre", "metre")
        assert RasterMetadata(crs=4326).crs_units == ("degree", "degree")


class TestCRSUnitsPerM:
    def test(_):
        assert RasterMetadata().crs_units_per_m == (None, None)

    def test_linear(_):
        assert RasterMetadata(crs=26911).crs_units_per_m == (1, 1)

    def test_angular_none(_):
        output = RasterMetadata(crs=4326).crs_units_per_m
        expected = (8.993216059187306e-06, 8.993216059187306e-06)
        assert np.allclose(output, expected)

    def test_angular(_):
        output = RasterMetadata((1, 1), crs=4326, bounds=(0, 0, 0, 0)).crs_units_per_m
        expected = (8.993216059187306e-06, 8.993216059187306e-06)
        assert np.allclose(output, expected)

    def test_angular_y(_):
        output = RasterMetadata((1, 1), crs=4326, bounds=(0, 30, 0, 30)).crs_units_per_m
        expected = (1.0384471425304483e-05, 8.993216059187306e-06)
        assert np.allclose(output, expected)


class TestUtmZone:
    def test(_):
        assert RasterMetadata().utm_zone is None
        assert RasterMetadata(crs=4326).utm_zone is None
        assert (
            RasterMetadata((1, 1), crs=4326, bounds=(-119, 30, -115, 50)).utm_zone
            == 32611
        )


#####
# Transform
#####


class TestTransform:
    def test(_):
        assert RasterMetadata().transform is None

        metadata = RasterMetadata(crs=26911, transform=(1, 2, 3, 4))
        assert metadata.transform == Transform(1, 2, 3, 4, 26911)

        metadata = RasterMetadata((1, 1), crs=26911, bounds=(0, 0, 10, 10))
        assert metadata.transform == Transform(10, -10, 0, 10, 26911)


class TestDx:
    def test(_, transform):
        assert RasterMetadata().dx() is None

        transform = Transform(1, 2, 3, 4, 26911)
        metadata = RasterMetadata(transform=transform)
        assert metadata.dx() == transform.dx("meters", y=metadata.center_y)
        assert metadata.dx("base") == transform.dx("base")

    def test_invalid(_, assert_contains):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            a.dx()
        assert_contains(error, "Cannot convert raster dx to meters")


class TestDy:
    def test(_):
        assert RasterMetadata().dy() is None

        transform = Transform(1, 2, 3, 4, 26911)
        metadata = RasterMetadata(transform=transform)
        assert metadata.dy() == transform.dy("meters")
        assert metadata.dy("base") == transform.dy("base")

    def test_invalid(_, assert_contains):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            a.dy()
        assert_contains(error, "Cannot convert raster dy to meters")


class TestResolution:
    def test(_):
        assert RasterMetadata().resolution() is None
        transform = Transform(1, 2, 3, 4, 26911)
        metadata = RasterMetadata(transform=transform)
        assert metadata.resolution() == transform.resolution(
            "meters", y=metadata.center_y
        )
        assert metadata.resolution("base") == transform.resolution("base")

    def test_invalid(_, assert_contains):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            a.resolution()
        assert_contains(error, "Cannot convert raster resolution to meters")


class TestPixelArea:
    def test(_):
        assert RasterMetadata().pixel_area() is None
        transform = Transform(1, 2, 3, 4, 26911)

        metadata = RasterMetadata(transform=transform)
        assert metadata.pixel_area() == transform.pixel_area(
            "meters", y=metadata.center_y
        )
        assert metadata.pixel_area("base") == transform.pixel_area("base")

    def test_invalid(_, assert_contains):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            a.pixel_area()
        assert_contains(error, "Cannot convert raster pixel_area to meters")


class TestPixelDiagonal:
    def test(_):
        assert RasterMetadata().pixel_diagonal() is None
        transform = Transform(1, 2, 3, 4, 26911)

        metadata = RasterMetadata(transform=transform)
        assert metadata.pixel_diagonal() == transform.pixel_diagonal(
            "meters", y=metadata.center_y
        )
        assert metadata.pixel_diagonal("base") == transform.pixel_diagonal("base")

    def test_invalid(_, assert_contains):
        a = RasterMetadata(transform=(1, 2, 3, 4))
        with pytest.raises(MissingCRSError) as error:
            a.pixel_diagonal()
        assert_contains(error, "Cannot convert raster pixel_diagonal to meters")


class TestAffine:
    def test(_):
        assert RasterMetadata().affine is None
        transform = Transform(1, 2, 3, 4, 26911)

        metadata = RasterMetadata(transform=transform)
        assert metadata.affine == transform.affine


#####
# BoundingBox
#####


class TestBounds:
    def test(_):
        assert RasterMetadata().bounds is None

        output = RasterMetadata(crs=26911, transform=(10, -10, 0, 10)).bounds
        assert output == BoundingBox(0, 10, 0, 10, 26911)

        output = RasterMetadata((1, 1), crs=26911, bounds=(0, 0, 10, 10)).bounds
        assert output == BoundingBox(0, 0, 10, 10, 26911)


class TestLeft:
    def test(_):
        assert RasterMetadata().left is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.left == 1


class TestRight:
    def test(_):
        assert RasterMetadata().right is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.right == 3


class TestTop:
    def test(_):
        assert RasterMetadata().top is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.top == 4


class TestBottom:
    def test(_):
        assert RasterMetadata().bottom is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.bottom == 2


class TestCenter:
    def test(_):
        assert RasterMetadata().center is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.center == (2, 3)


class TestCenterX:
    def test(_):
        assert RasterMetadata().center_x is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.center_x == 2


class TestCenterY:
    def test(_):
        assert RasterMetadata().center_y is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.center_y == 3


class TestOrientation:
    def test(_):
        assert RasterMetadata().orientation is None
        metadata = RasterMetadata((1, 1), bounds=(1, 2, 3, 4))
        assert metadata.orientation == 1
