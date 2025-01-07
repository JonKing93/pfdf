import numpy as np
import pytest

from pfdf.data._utils import validate
from pfdf.errors import MissingCRSError
from pfdf.projection import BoundingBox


class TestBounds:
    def test_valid(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        assert validate.bounds(a) == "1.0,2.0,3.0,4.0"

    def test_not_bounds(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.bounds("invalid")
        assert_contains(
            error,
            "bounds must be a BoundingBox, Raster, RasterMetadata, dict, list, or tuple",
        )

    def test_no_crs(_, assert_contains):
        a = [1, 2, 3, 4]
        with pytest.raises(MissingCRSError) as error:
            validate.bounds(a)
        assert_contains(error, "bounds must have a CRS")

    def test_object(_):
        a = [1, 2, 3, 4, 26911]
        expected = BoundingBox(1, 2, 3, 4, 26911)
        output = validate.bounds(a, as_string=False)
        assert output == expected

    def test_delimited(_):
        a = BoundingBox(1, 2, 3, 4, 4326)
        output = validate.bounds(a, delimiter=" ")
        assert output == "1.0 2.0 3.0 4.0"

    def test_other_crs_delimited(_):
        a = BoundingBox(-107, 32, -106, 33, 4326)
        a = a.to_utm()
        output = validate.bounds(a)
        output = np.array(list(float(value) for value in output.split(",")))
        expected = [
            -107.02225666940984,
            31.98817998331647,
            -105.98899449757876,
            33.01201807770884,
        ]
        assert np.allclose(output, expected)

    def test_other_crs_object(_):
        a = BoundingBox(1, 2, 3, 4, 26911)
        output = validate.bounds(a, as_string=False)
        assert output == a


class TestStrings:
    def test_base_string(_):
        output = validate.strings("some text", "")
        assert output == "some text"

    def test_list_single_string(_):
        output = validate.strings(["some text"], "")
        assert output == "some text"

    def test_list_multiple_string(_):
        output = validate.strings(
            ["some", "text", "that", "should", "be", "delimited"], ""
        )
        assert output == "some,text,that,should,be,delimited"

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.strings(5, "test name")
        assert_contains(
            error,
            "test name must be a string or list of strings, but test name[0] is not a string",
        )

    def test_invalid_element(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.strings(["some", 5, "test"], "test name")
        assert_contains(
            error,
            "test name must be a string or list of strings, but test name[1] is not a string",
        )
