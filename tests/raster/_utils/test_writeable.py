import numpy as np
import pytest

from pfdf.raster._utils.writeable import WriteableArray


class TestInit:
    def test(_, araster):
        araster.setflags(write=False)
        output = WriteableArray(araster)
        assert output.array is araster
        assert output.initial == False


class TestEnter:
    def test(_, araster):
        araster.setflags(write=False)
        output = WriteableArray(araster)
        assert araster.flags.writeable == False
        output.__enter__()
        assert araster.flags.writeable == True

    def test_invalid(_, araster, assert_contains):
        araster.setflags(write=False)
        values = araster.view()
        output = WriteableArray(values)
        with pytest.raises(ValueError) as error:
            output.__enter__()
        assert_contains(
            error, "raster cannot set the write permissions of its data array"
        )


class TestExit:
    def test(_, araster):
        araster.setflags(write=False)
        output = WriteableArray(araster)
        assert araster.flags.writeable == False
        output.__enter__()
        assert araster.flags.writeable == True
        output.__exit__()
        assert araster.flags.writeable == False


class TestWith:
    def test(_, araster):
        expected = araster.copy()
        expected[araster < 3] = 3

        araster.setflags(write=False)
        assert araster.flags.writeable == False
        with WriteableArray(araster):
            araster[araster < 3] = 3
        assert araster.flags.writeable == False
        assert np.array_equal(araster, expected)
