from multiprocessing import cpu_count

import numpy as np
import pytest

from pfdf.errors import (
    DimensionError,
    RasterCRSError,
    RasterShapeError,
    RasterTransformError,
)
from pfdf.projection import CRS, Transform
from pfdf.raster import Raster
from pfdf.segments._validate import _misc


class TestRaster:
    def test_valid_raster(_, segments, flow):
        output = _misc.raster(segments, flow, "")
        assert output == flow

    def test_default_spatial(_, segments, flow):
        input = Raster.from_array(flow.values, nodata=0)
        output = _misc.raster(segments, input, "")
        assert output == flow

    def test_bad_shape(_, segments, flow, assert_contains):
        a = np.arange(10).reshape(2, 5)
        input = Raster.from_array(a, crs=flow.crs, transform=flow.transform)
        with pytest.raises(RasterShapeError) as error:
            _misc.raster(segments, input, "test name")
        assert_contains(error, "test name")

    def test_bad_transform(_, segments, flow, assert_contains):
        flow.override(transform=Transform(9, 9, 0, 0))
        with pytest.raises(RasterTransformError) as error:
            _misc.raster(segments, flow, "test name")
        assert_contains(error, "test name")

    def test_bad_crs(_, segments, flow, assert_contains):
        flow._crs = CRS.from_epsg(4000)
        with pytest.raises(RasterCRSError) as error:
            _misc.raster(segments, flow, "test name")
        assert_contains(error, "test name")

    @pytest.mark.parametrize(
        "input, error",
        (
            (5, TypeError),
            (np.ones((3, 3, 3)), DimensionError),
        ),
    )
    def test_invalid_raster(_, segments, input, error, assert_contains):
        with pytest.raises(error) as e:
            _misc.raster(segments, input, "test name")
        assert_contains(e, "test name")


class TestNprocess:
    def test_none(_):
        assert _misc.nprocess(None) == max(1, cpu_count() - 1)

    def test_valid(_):
        assert _misc.nprocess(12) == 12

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _misc.nprocess("invalid")
        assert_contains(error, "nprocess")

    def test_negative(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _misc.nprocess(-3)
        assert_contains(error, "nprocess", "must be greater than 0")

    def test_float(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _misc.nprocess(2.2)
        assert_contains(error, "nprocess", "must be integer")
