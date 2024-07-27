import numpy as np
import pytest
from pyproj import CRS

from pfdf.segments._geojson import _geojson


@pytest.fixture
def properties(segments):
    strs = ["a", "test", "string", "and", "another", "one"]
    return {
        "id": (segments.ids, int),
        "afloat": (np.arange(6, dtype=float) + 0.2, float),
        "anint": (np.arange(6, dtype=int), int),
        "astr": (np.array(strs), str),
    }


class TestValues:
    def test(_, properties):
        output = _geojson._values(properties, 2)
        assert output == {"id": 3, "afloat": 2.2, "anint": 2, "astr": "string"}
        output = _geojson._values(properties, 3)
        assert output == {"id": 4, "afloat": 3.2, "anint": 3, "astr": "and"}


class TestBasins:
    def test(_, segments, properties):
        output = _geojson._basins(segments, properties, CRS(26910))
        print(output)
        assert output == [
            {
                "geometry": {
                    "coordinates": [
                        [
                            [668189.588648, 0.997261],
                            [668189.588648, 2.991784],
                            [668190.585909, 2.991784],
                            [668190.585909, 0.997261],
                            [668189.588648, 0.997261],
                        ]
                    ],
                    "type": "Polygon",
                },
                "properties": {"id": 3, "afloat": 0.2, "anint": 0, "astr": "a"},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [
                        [
                            [668185.599602, 0.997261],
                            [668185.599602, 3.989045],
                            [668186.596864, 3.989045],
                            [668186.596863, 4.986306],
                            [668187.594125, 4.986306],
                            [668187.594125, 5.983568],
                            [668188.591386, 5.983568],
                            [668188.591386, 3.989045],
                            [668190.585909, 3.989045],
                            [668190.585909, 2.991784],
                            [668189.588648, 2.991784],
                            [668189.588648, 0.997261],
                            [668188.591386, 0.997261],
                            [668188.591386, 3.989045],
                            [668187.594125, 3.989045],
                            [668187.594125, 2.991784],
                            [668186.596864, 2.991784],
                            [668186.596864, 0.997261],
                            [668185.599602, 0.997261],
                        ]
                    ],
                    "type": "Polygon",
                },
                "properties": {"id": 6, "afloat": 1.2, "anint": 1, "astr": "test"},
                "type": "Feature",
            },
        ]
