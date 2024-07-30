import numpy as np
import pytest
from affine import Affine
from shapely import LineString

from pfdf.raster import Raster
from pfdf.segments import Segments

#####
# Rasters
#####


@pytest.fixture
def transform():
    return Affine(1, 0, 0, 0, 1, 0)


@pytest.fixture
def dem():
    dem = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 61, 10, 10, 50, 10, 0],
            [0, 51, 61, 61, 40, 30, 0],
            [0, 41, 31, 99, 20, 30, 0],
            [0, 19, 21, 10, 22, 20, 0],
            [0, 15, 19, 10, 20, 16, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(dem)


@pytest.fixture
def stream_raster():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 2, 3, 0],
            [0, 1, 0, 0, 2, 3, 0],
            [0, 1, 1, 0, 5, 4, 0],
            [0, 0, 1, 6, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )


@pytest.fixture
def outlet_raster():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 6, 0, 0, 6, 3, 0],
            [0, 6, 0, 0, 6, 3, 0],
            [0, 6, 6, 0, 6, 6, 0],
            [0, 0, 6, 6, 0, 0, 0],
            [0, 0, 0, 6, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype("int32")


@pytest.fixture
def basin_raster():
    "The expected final basins raster"
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 0, 0, 7, 3, 0],
            [0, 7, 0, 0, 7, 3, 0],
            [0, 7, 7, 0, 7, 7, 0],
            [0, 0, 7, 7, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )


#####
# Segments and properties
#####


@pytest.fixture
def linestrings():
    segments = [
        [[1.5, 1.5], [1.5, 2.5], [1.5, 3.5], [2.5, 3.5], [2.5, 4.5], [3.5, 4.5]],
        [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
        [[5.5, 2.5], [5.5, 1.5], [5.5, 0.5]],
        [[5.5, 3.5], [4.5, 3.5]],
        [[4.5, 3.5], [3.5, 4.5]],
        [[3.5, 4.5], [3.5, 5.5], [3.5, 6.5]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def indices():
    return [
        ([1, 2, 3, 3, 4], [1, 1, 1, 2, 2]),
        ([1, 2], [4, 4]),
        ([2, 1], [5, 5]),
        ([3], [5]),
        ([3], [4]),
        ([4, 5], [3, 3]),
    ]


@pytest.fixture
def npixels():
    return np.array([5, 2, 2, 1, 4, 11])


@pytest.fixture
def child():
    return np.array([5, 4, -1, 4, 5, -1])


@pytest.fixture
def parents():
    return np.array(
        [
            [-1, -1],
            [-1, -1],
            [-1, -1],
            [-1, -1],
            [1, 3],
            [0, 4],
        ]
    )


#####
# Split-point segments
#####


@pytest.fixture
def linestrings_split():
    segments = [
        [[1.5, 1.5], [1.5, 2.5], [1.5, 3.5], [2, 3.5]],
        [[2, 3.5], [2.5, 3.5], [2.5, 4.5], [3.5, 4.5]],
        [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
        [[5.5, 2.5], [5.5, 1.5], [5.5, 0.5]],
        [[5.5, 3.5], [4.5, 3.5]],
        [[4.5, 3.5], [3.5, 4.5]],
        [[3.5, 4.5], [3.5, 5.5], [3.5, 6.5]],
    ]
    return [LineString(coords) for coords in segments]


@pytest.fixture
def indices_split():
    return [
        ([1, 2, 3], [1, 1, 1]),
        ([3, 4], [2, 2]),
        ([1, 2], [4, 4]),
        ([2, 1], [5, 5]),
        ([3], [5]),
        ([3], [4]),
        ([4, 5], [3, 3]),
    ]


#####
# Nested drainage basins
#####


@pytest.fixture
def bflow(transform):
    flow = np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 7, 5, 1, 7, 3, 0],
            [0, 7, 5, 1, 7, 3, 0],
            [0, 1, 7, 7, 6, 5, 0],
            [0, 5, 1, 7, 5, 1, 0],
            [0, 5, 5, 7, 5, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )
    return Raster.from_array(flow, nodata=0, transform=transform, crs=26911)


@pytest.fixture
def bsegments(bflow, mask):
    return Segments(bflow, mask)


@pytest.fixture
def basins():
    return np.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 6, 6, 6, 6, 3, 0],
            [0, 6, 6, 6, 6, 3, 0],
            [0, 6, 6, 6, 6, 6, 0],
            [0, 0, 6, 6, 6, 0, 0],
            [0, 0, 0, 6, 6, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    ).astype("int32")


@pytest.fixture
def bpixels():
    return np.array([7, 4, 2, 1, 6, 18])


#####
# Filtering
#####


@pytest.fixture
def linestrings245(linestrings):
    return [linestrings[1], linestrings[3], linestrings[4]]


@pytest.fixture
def indices245(indices):
    return [indices[1], indices[3], indices[4]]


@pytest.fixture
def bpixels245():
    return np.array([4, 1, 6])


@pytest.fixture
def child245():
    return np.array([2, 2, -1])


@pytest.fixture
def parents245():
    return np.array(
        [
            [-1, -1],
            [-1, -1],
            [0, 1],
        ]
    )


#####
# Catchment statistics
#####


@pytest.fixture
def values(flow):
    values = flow.values.copy()
    values[values == 3] = 0
    return Raster.from_array(values, nodata=0)


#####
# Export
#####


@pytest.fixture
def properties(segments):
    strs = ["a", "test", "string", "and", "another", "one"]
    return {
        "id": segments.ids,
        "afloat": np.arange(6, dtype=float) + 0.2,
        "anint": np.arange(6, dtype=int),
        "astr": np.array(strs),
    }


@pytest.fixture
def terminal_props(properties):
    keep = np.isin(properties["id"], [3, 6])
    for field, vector in properties.items():
        properties[field] = vector[keep]
    return properties


@pytest.fixture
def propcon(segments):
    strs = ["a", "test", "string", "and", "another", "one"]
    return {
        "id": (segments.ids, int),
        "afloat": (np.arange(6, dtype=float) + 0.2, float),
        "anint": (np.arange(6, dtype=int), int),
        "astr": (np.array(strs), str),
    }


@pytest.fixture
def terminal_propcon(propcon):
    keep = np.isin(propcon["id"][0], [3, 6])
    for field, (vector, convert) in propcon.items():
        propcon[field] = (vector[keep], convert)
    return propcon
