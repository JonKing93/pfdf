import numpy as np
import pytest

from pfdf.errors import ShapeError
from pfdf.segments._validate import _export


class TestProperties:
    def test_valid(_, segments):
        props = {"ones": np.ones(6, float), "twos": [2, 2, 2, 2, 2, 2]}
        output, schema = _export._properties(segments, props, terminal=False)
        expected = {"ones": np.ones(6), "twos": np.full(6, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        print(schema)
        assert schema == {"ones": "float", "twos": "int"}

    def test_none(_, segments):
        output, schema = _export._properties(segments, None, terminal=False)
        assert output == {}
        assert schema == {}

    def test_terminal(_, segments):
        props = {"ones": np.ones(2, float), "twos": [2, 2]}
        output, schema = _export._properties(segments, props, terminal=True)
        expected = {"ones": np.ones(2), "twos": np.full(2, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"ones": "float", "twos": "int"}

    def test_not_dict(_, segments, assert_contains):
        with pytest.raises(TypeError) as error:
            _export._properties(segments, "invalid", terminal=False)
        assert_contains(error, "properties must be a dict")

    def test_bad_keys(_, segments, assert_contains):
        props = {1: np.ones(6)}
        with pytest.raises(TypeError) as error:
            _export._properties(segments, props, terminal=False)
        assert_contains(error, "key 0")

    def test_wrong_length(_, segments, assert_contains):
        props = {"values": np.ones(7)}
        with pytest.raises(ShapeError) as error:
            _export._properties(segments, props, terminal=False)
        assert_contains(error, "properties['values']")

    def test_nsegments_basins(_, segments):
        props = {"ones": np.ones(6, float), "twos": [2, 2, 2, 2, 2, 2]}
        output, schema = _export._properties(segments, props, terminal=True)
        expected = {"ones": np.ones(2), "twos": np.full(2, 2)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"ones": "float", "twos": "int"}

    def test_bool(_, segments):
        props = {"test": np.ones(6, bool)}
        output, schema = _export._properties(segments, props, False)
        expected = {"test": np.ones(6, int)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "int"}

    def test_str(_, segments):
        props = {"test": np.full(6, "test"), "test2": np.full(6, "longer")}
        output, schema = _export._properties(segments, props, False)
        expected = props
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "str:4", "test2": "str:6"}

    def test_int(_, segments):
        props = {"test": np.ones(6, int)}
        output, schema = _export._properties(segments, props, False)
        expected = {"test": np.ones(6, int)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "int"}

    def test_float(_, segments):
        props = {"test": np.ones(6, "float32")}
        output, schema = _export._properties(segments, props, False)
        expected = {"test": np.ones(6, float)}
        assert output.keys() == expected.keys()
        for key in output.keys():
            assert np.array_equal(output[key], expected[key])
        assert schema == {"test": "float"}


class TestExport:
    def test_valid_no_properties(_, segments):
        type, properties, schema = _export.export(segments, None, "segments")
        assert properties == {}
        assert type == "segments"
        assert schema == {}

    @pytest.mark.parametrize("type", ("segments", "segment outlets"))
    def test_valid_segments_props(_, segments, type):
        props = {"slope": [1, 2, 3, 4, 5, 6]}
        output_type, properties, schema = _export.export(segments, props, type)
        assert isinstance(properties, dict)
        assert list(properties.keys()) == ["slope"]
        assert np.array_equal(
            properties["slope"], np.array([1, 2, 3, 4, 5, 6]).astype(float)
        )
        assert output_type == type
        assert schema == {"slope": "int"}

    @pytest.mark.parametrize("type", ("basins", "outlets"))
    def test_valid_terminal_props(_, segments, type):
        props = {"slope": [1, 2]}
        outtype, properties, schema = _export.export(segments, props, type)
        assert isinstance(properties, dict)
        assert list(properties.keys()) == ["slope"]
        assert np.array_equal(properties["slope"], np.array([1, 2]).astype(float))
        assert outtype == type
        assert schema == {"slope": "int"}

    @pytest.mark.parametrize(
        "type", ("segments", "basins", "outlets", "segment outlets")
    )
    def test_valid_type(_, segments, type):
        outtype, properties, schema = _export.export(segments, None, type)
        assert properties == {}
        assert outtype == type
        assert schema == {}

    def test_type_casing(_, segments):
        outtype, _, _ = _export.export(segments, None, "SeGmEnTs")
        assert outtype == "segments"

    def test_invalid_type(_, segments, assert_contains):
        with pytest.raises(ValueError) as error:
            _export.export(segments, None, "invalid")
        assert_contains(error, "type", "segments", "outlets", "basins")

    def test_invalid_props(_, segments, assert_contains):
        with pytest.raises(TypeError) as error:
            _export.export(segments, "invalid", "segments")
        assert_contains(error, "properties must be a dict")
