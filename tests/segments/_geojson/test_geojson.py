from pyproj import CRS

from pfdf.segments._geojson import _geojson


class TestValues:
    def test(_, propcon):
        output = _geojson._values(propcon, 2)
        assert output == {"id": 3, "afloat": 2.2, "anint": 2, "astr": "string"}
        output = _geojson._values(propcon, 3)
        assert output == {"id": 4, "afloat": 3.2, "anint": 3, "astr": "and"}


class TestBasins:
    def test(_, segments, terminal_propcon):
        output = _geojson._basins(segments, terminal_propcon, CRS(26910))
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
                "properties": {"id": 3, "afloat": 2.2, "anint": 2, "astr": "string"},
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
                "properties": {"id": 6, "afloat": 5.2, "anint": 5, "astr": "one"},
                "type": "Feature",
            },
        ]


class TestFromShapely:
    def test_segments(_, segments, propcon):
        output = _geojson._from_shapely(segments, "segments", propcon, CRS(26910))
        assert output == [
            {
                "geometry": {
                    "coordinates": [
                        [668186.098233, 1.495892],
                        [668186.098233, 2.493153],
                        [668186.098233, 3.490414],
                        [668187.095494, 3.490415],
                        [668187.095494, 4.487676],
                        [668188.092755, 4.487676],
                    ],
                    "type": "LineString",
                },
                "properties": {"afloat": 0.2, "anint": 0, "astr": "a", "id": 1},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [
                        [668189.090017, 1.495892],
                        [668189.090017, 2.493153],
                        [668189.090017, 3.490415],
                    ],
                    "type": "LineString",
                },
                "properties": {"afloat": 1.2, "anint": 1, "astr": "test", "id": 2},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [
                        [668190.087278, 2.493153],
                        [668190.087278, 1.495892],
                        [668190.087278, 0.498631],
                    ],
                    "type": "LineString",
                },
                "properties": {"afloat": 2.2, "anint": 2, "astr": "string", "id": 3},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [
                        [668190.087278, 3.490415],
                        [668189.090017, 3.490415],
                    ],
                    "type": "LineString",
                },
                "properties": {"afloat": 3.2, "anint": 3, "astr": "and", "id": 4},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [
                        [668189.090017, 3.490415],
                        [668188.092755, 4.487676],
                    ],
                    "type": "LineString",
                },
                "properties": {"afloat": 4.2, "anint": 4, "astr": "another", "id": 5},
                "type": "Feature",
            },
            {
                "geometry": {
                    "coordinates": [
                        [668188.092755, 4.487676],
                        [668188.092755, 5.484937],
                        [668188.092755, 6.482198],
                    ],
                    "type": "LineString",
                },
                "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                "type": "Feature",
            },
        ]

    def test_segment_outlets(_, segments, propcon):
        output = _geojson._from_shapely(
            segments, "segment outlets", propcon, CRS(26910)
        )
        assert output == [
            {
                "geometry": {"coordinates": [668188.092755, 4.487676], "type": "Point"},
                "properties": {"afloat": 0.2, "anint": 0, "astr": "a", "id": 1},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [668189.090017, 3.490415], "type": "Point"},
                "properties": {"afloat": 1.2, "anint": 1, "astr": "test", "id": 2},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [668190.087278, 0.498631], "type": "Point"},
                "properties": {"afloat": 2.2, "anint": 2, "astr": "string", "id": 3},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [668189.090017, 3.490415], "type": "Point"},
                "properties": {"afloat": 3.2, "anint": 3, "astr": "and", "id": 4},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [668188.092755, 4.487676], "type": "Point"},
                "properties": {"afloat": 4.2, "anint": 4, "astr": "another", "id": 5},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [668188.092755, 6.482198], "type": "Point"},
                "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                "type": "Feature",
            },
        ]

    def test_outlets(_, segments, terminal_propcon):
        output = _geojson._from_shapely(
            segments, "outlets", terminal_propcon, CRS(26910)
        )
        assert output == [
            {
                "geometry": {"coordinates": [668190.087278, 0.498631], "type": "Point"},
                "properties": {"afloat": 2.2, "anint": 2, "astr": "string", "id": 3},
                "type": "Feature",
            },
            {
                "geometry": {"coordinates": [668188.092755, 6.482198], "type": "Point"},
                "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                "type": "Feature",
            },
        ]


class TestFeatures:
    def test_basins(_, segments, properties):
        json, schema, crs = _geojson.features(segments, "basins", properties, None)
        assert json == {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [[5.0, 1.0], [5.0, 3.0], [6.0, 3.0], [6.0, 1.0], [5.0, 1.0]]
                        ],
                        "type": "Polygon",
                    },
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [
                                [1.0, 1.0],
                                [1.0, 4.0],
                                [2.0, 4.0],
                                [2.0, 5.0],
                                [3.0, 5.0],
                                [3.0, 6.0],
                                [4.0, 6.0],
                                [4.0, 4.0],
                                [6.0, 4.0],
                                [6.0, 3.0],
                                [5.0, 3.0],
                                [5.0, 1.0],
                                [4.0, 1.0],
                                [4.0, 4.0],
                                [3.0, 4.0],
                                [3.0, 3.0],
                                [2.0, 3.0],
                                [2.0, 1.0],
                                [1.0, 1.0],
                            ]
                        ],
                        "type": "Polygon",
                    },
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == segments.crs

    def test_segments(_, segments, properties):
        json, schema, crs = _geojson.features(segments, "segments", properties, None)
        assert json == {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [1.5, 1.5],
                            [1.5, 2.5],
                            [1.5, 3.5],
                            [2.5, 3.5],
                            [2.5, 4.5],
                            [3.5, 4.5],
                        ],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 0.2, "anint": 0, "astr": "a", "id": 1},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 1.2, "anint": 1, "astr": "test", "id": 2},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[5.5, 2.5], [5.5, 1.5], [5.5, 0.5]],
                        "type": "LineString",
                    },
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[5.5, 3.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 3.2, "anint": 3, "astr": "and", "id": 4},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[4.5, 3.5], [3.5, 4.5]],
                        "type": "LineString",
                    },
                    "properties": {
                        "afloat": 4.2,
                        "anint": 4,
                        "astr": "another",
                        "id": 5,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[3.5, 4.5], [3.5, 5.5], [3.5, 6.5]],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == segments.crs

    def test_outlets(_, segments, properties):
        json, schema, crs = _geojson.features(segments, "outlets", properties, None)
        assert json == {
            "features": [
                {
                    "geometry": {"coordinates": [5.5, 0.5], "type": "Point"},
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 6.5], "type": "Point"},
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == segments.crs

    def test_segment_outlets(_, segments, properties):
        json, schema, crs = _geojson.features(
            segments, "segment outlets", properties, None
        )
        assert json == {
            "features": [
                {
                    "geometry": {"coordinates": [3.5, 4.5], "type": "Point"},
                    "properties": {"afloat": 0.2, "anint": 0, "astr": "a", "id": 1},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [4.5, 3.5], "type": "Point"},
                    "properties": {"afloat": 1.2, "anint": 1, "astr": "test", "id": 2},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [5.5, 0.5], "type": "Point"},
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [4.5, 3.5], "type": "Point"},
                    "properties": {"afloat": 3.2, "anint": 3, "astr": "and", "id": 4},
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 4.5], "type": "Point"},
                    "properties": {
                        "afloat": 4.2,
                        "anint": 4,
                        "astr": "another",
                        "id": 5,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 6.5], "type": "Point"},
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == segments.crs

    def test_no_crs(_, segments, properties):
        json, schema, crs = _geojson.features(segments, "segments", properties, None)
        assert json == {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [1.5, 1.5],
                            [1.5, 2.5],
                            [1.5, 3.5],
                            [2.5, 3.5],
                            [2.5, 4.5],
                            [3.5, 4.5],
                        ],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 0.2, "anint": 0, "astr": "a", "id": 1},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[4.5, 1.5], [4.5, 2.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 1.2, "anint": 1, "astr": "test", "id": 2},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[5.5, 2.5], [5.5, 1.5], [5.5, 0.5]],
                        "type": "LineString",
                    },
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[5.5, 3.5], [4.5, 3.5]],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 3.2, "anint": 3, "astr": "and", "id": 4},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[4.5, 3.5], [3.5, 4.5]],
                        "type": "LineString",
                    },
                    "properties": {
                        "afloat": 4.2,
                        "anint": 4,
                        "astr": "another",
                        "id": 5,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [[3.5, 4.5], [3.5, 5.5], [3.5, 6.5]],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == segments.crs

    def test_new_crs(_, segments, properties):
        json, schema, crs = _geojson.features(segments, "segments", properties, 26910)
        assert json == {
            "features": [
                {
                    "geometry": {
                        "coordinates": [
                            [668186.098233, 1.495892],
                            [668186.098233, 2.493153],
                            [668186.098233, 3.490414],
                            [668187.095494, 3.490415],
                            [668187.095494, 4.487676],
                            [668188.092755, 4.487676],
                        ],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 0.2, "anint": 0, "astr": "a", "id": 1},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [668189.090017, 1.495892],
                            [668189.090017, 2.493153],
                            [668189.090017, 3.490415],
                        ],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 1.2, "anint": 1, "astr": "test", "id": 2},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [668190.087278, 2.493153],
                            [668190.087278, 1.495892],
                            [668190.087278, 0.498631],
                        ],
                        "type": "LineString",
                    },
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [668190.087278, 3.490415],
                            [668189.090017, 3.490415],
                        ],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 3.2, "anint": 3, "astr": "and", "id": 4},
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [668189.090017, 3.490415],
                            [668188.092755, 4.487676],
                        ],
                        "type": "LineString",
                    },
                    "properties": {
                        "afloat": 4.2,
                        "anint": 4,
                        "astr": "another",
                        "id": 5,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {
                        "coordinates": [
                            [668188.092755, 4.487676],
                            [668188.092755, 5.484937],
                            [668188.092755, 6.482198],
                        ],
                        "type": "LineString",
                    },
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == CRS(26910)

    def test_terminal_properties(_, segments, terminal_props):
        json, schema, crs = _geojson.features(segments, "outlets", terminal_props, None)
        assert json == {
            "features": [
                {
                    "geometry": {"coordinates": [5.5, 0.5], "type": "Point"},
                    "properties": {
                        "afloat": 2.2,
                        "anint": 2,
                        "astr": "string",
                        "id": 3,
                    },
                    "type": "Feature",
                },
                {
                    "geometry": {"coordinates": [3.5, 6.5], "type": "Point"},
                    "properties": {"afloat": 5.2, "anint": 5, "astr": "one", "id": 6},
                    "type": "Feature",
                },
            ],
            "type": "FeatureCollection",
        }
        assert schema == {
            "id": "int",
            "afloat": "float",
            "anint": "int",
            "astr": "str:7",
        }
        assert crs == segments.crs
