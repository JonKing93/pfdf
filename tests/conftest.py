import numpy as np
import pytest
from affine import Affine

from pfdf.projection import CRS, Transform
from pfdf.raster import Raster
from pfdf.segments import Segments

#####
# Misc
#####


def _assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


@pytest.fixture
def assert_contains():
    return _assert_contains


@pytest.fixture
def araster():
    "A numpy array raster"
    return np.array([1, 2, 3, 4, 5, 6, 7, 8]).reshape(2, 4).astype(float)


#####
# Metadata
#####


@pytest.fixture
def crs():
    return CRS(26911)


@pytest.fixture
def affine():
    return Affine(0.03, 0, -4, 0, 0.03, -3)


@pytest.fixture
def transform(affine):
    return Transform.from_affine(affine)


#####
# Basic segments
#####


@pytest.fixture
def flow(transform):
    flow = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 3, 3, 7, 3, 0],
            [0, 7, 3, 3, 7, 3, 0],
            [0, 1, 7, 3, 6, 5, 0],
            [0, 5, 1, 7, 1, 1, 0],
            [0, 5, 5, 7, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(flow, nodata=0, transform=transform, crs=26911)


@pytest.fixture
def mask():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 1, 1, 0, 1, 1, 0],
            [0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype(bool)


@pytest.fixture
def mask2(mask):
    mask[:, 1:4] = False
    return mask


@pytest.fixture
def segments(flow, mask):
    return Segments(flow, mask)
