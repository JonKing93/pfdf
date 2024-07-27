import pytest
from pyproj import CRS, Transformer

from pfdf.segments._geojson import _reproject


@pytest.fixture
def transformer():
    return Transformer.from_crs(26911, 26910, always_xy=True)


@pytest.fixture
def line1():
    return [(1, 2), (3, 4), (5, 6), (7, 8)]


@pytest.fixture
def line2():
    return [
        (668185.5996023703, 1.9945225262230266),
        (668187.5941248297, 3.989045184176652),
        (668189.5886472922, 5.983567973860883),
        (668191.5831697518, 7.978090895275724),
    ]


@pytest.fixture
def segments1():
    return [
        [[1, 2], [3, 4], [5, 6], [7, 8]],
        [[5, 5], [6, 6], [7, 7]],
    ]


@pytest.fixture
def segments2():
    return [
        [
            (668185.5996023703, 1.9945225262230266),
            (668187.5941248297, 3.989045184176652),
            (668189.5886472922, 5.983567973860883),
            (668191.5831697518, 7.978090895275724),
        ],
        [
            (668189.588647383, 4.986306644884073),
            (668190.5859086297, 5.9835680726588425),
            (668191.5831698764, 6.980829533366266),
        ],
    ]


@pytest.fixture
def basins1():
    return [
        (  # basin 1
            {
                "type": "Polygon",
                "coordinates": [  # array of rings
                    [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]  # shell
                ],
            },
            1,
        ),
        (  # basin 2
            {
                "type": "Polygon",
                "coordinates": [  # array of rings
                    [[0, 0], [0, 5], [5, 5], [5, 0], [0, 0]],  # shell
                    [
                        [2, 2],
                        [2, 3],
                        [3, 3],
                        [3, 4],
                        [4, 4],
                        [4, 3],
                        [2, 2],
                    ],  # hole
                ],
            },
            2,
        ),
    ]


@pytest.fixture
def basins2():
    return [
        (
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        (668184.6023411495, 0.0),
                        (668184.602340325, 9.972612466451828),
                        (668194.5749536136, 9.97261411308446),
                        (668194.5749544381, 0.0),
                        (668184.6023411495, 0.0),
                    ]
                ],
            },
            1,
        ),
        (
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        (668184.6023411495, 0.0),
                        (668184.602340942, 4.986306233225937),
                        (668189.588647383, 4.986306644884073),
                        (668189.5886475877, 0.0),
                        (668184.6023411495, 0.0),
                    ],
                    [
                        (668186.596863643, 1.9945225591556772),
                        (668186.5968636014, 2.9917838387335136),
                        (668187.5941248896, 2.9917838881324905),
                        (668187.5941248297, 3.989045184176652),
                        (668188.5913861362, 3.9890452500419564),
                        (668188.5913861933, 2.991783937531468),
                        (668186.596863643, 1.9945225591556772),
                    ],
                ],
            },
            2,
        ),
    ]


class TestPoint:
    def test(_, transformer):
        output = _reproject._point((1, 2), transformer)
        print(output)
        assert output == (668185.5996023703, 1.9945225262230266)


class TestLine:
    def test(_, line1, line2, transformer):
        _reproject._line(line1, transformer)
        assert line1 == line2


class TestSegments:
    def test(_, segments1, segments2, transformer):
        _reproject._segments(segments1, transformer)
        assert segments1 == segments2


class TestBasins:
    def test_no_holes(_, basins1, basins2, transformer):
        _reproject._basins(basins1, transformer)
        assert basins1 == basins2


class TestGeometries:
    def test_segments(_, segments1, segments2):
        _reproject.geometries(segments1, "segments", CRS(26911), CRS(26910))
        assert segments1 == segments2

    def test_basins(_, basins1, basins2):
        _reproject.geometries(basins1, "basins", CRS(26911), CRS(26910))
        assert basins1 == basins2

    def test_outlets(_, line1, line2):
        _reproject.geometries(line1, "outlets", CRS(26911), CRS(26910))
        assert line1 == line2

    def test_segment_outlets(_, line1, line2):
        _reproject.geometries(line1, "segment outlets", CRS(26911), CRS(26910))
        assert line1 == line2
