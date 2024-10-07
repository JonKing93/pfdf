import pytest
from fiona import Collection

from pfdf.errors import FeatureFileError
from pfdf.raster._features._ffile import FeatureFile


class TestInit:
    def test_valid(_, fraster):
        a = FeatureFile(fraster, 1, "ShapeFile", "test")
        assert isinstance(a, FeatureFile)
        assert a.path == fraster.resolve()
        assert a.layer == 1
        assert a.driver == "ShapeFile"
        assert a.encoding == "test"

    def test_nones(_, fraster):
        a = FeatureFile(fraster, None, None, None)
        assert a.path == fraster.resolve()
        assert a.layer is None
        assert a.driver is None
        assert a.encoding is None


class TestEnter:
    def test_invalid(_, fraster, assert_contains):
        with pytest.raises(FeatureFileError) as error:
            FeatureFile(fraster, None, None, None).__enter__()
        assert_contains(error, "Could not read data from the feature file")

    def test_valid(_, polygons, crs):
        with FeatureFile(polygons, None, None, None) as file:
            assert isinstance(file.file, Collection)
            assert file.crs == crs
            assert file.file.closed == False


class TestExit:
    def test(_, polygons):
        with FeatureFile(polygons, None, None, None) as file:
            pass
        assert file.file.closed == True
