import numpy as np
import pytest
from pysheds.sview import Raster, ViewFinder

from pfdf._utils.patches import NodataPatch


class TestNodataPatch:
    def test(_):
        values = np.arange(100).reshape(10, 10)
        view = ViewFinder(shape=values.shape, nodata=0)
        with pytest.raises(TypeError):
            Raster(values, view)
        with NodataPatch():
            Raster(values, view)
