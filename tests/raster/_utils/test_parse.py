import pytest

from pfdf.raster import Raster, RasterMetadata
from pfdf.raster._utils import parse


class TestTemplate:
    def test_no_template(_):
        kwargs = RasterMetadata((1, 1), crs=26911, transform=(10, 10, 0, 0))
        output = parse.template(kwargs, None, "test")
        assert output == kwargs

    def test_metadata_template(_):
        kwargs = RasterMetadata((1, 1))
        template = RasterMetadata((1, 1), crs=4326, transform=(1, 2, 3, 4))
        output = parse.template(kwargs, template, "test")
        assert output == template

    def test_raster_template(_):
        kwargs = RasterMetadata((1, 1))
        template = Raster.from_array(
            [[1, 2], [3, 4]], crs=26911, transform=(1, 2, 3, 4)
        )
        output = parse.template(kwargs, template, "test")
        assert output == RasterMetadata((1, 1), crs=26911, transform=(1, 2, 3, 4))

    def test_mixed(_):
        kwargs = RasterMetadata((1, 1), crs=4326)
        template = RasterMetadata((1, 1), transform=(1, 2, 3, 4))
        output = parse.template(kwargs, template, "test")
        assert output == RasterMetadata((1, 1), crs=4326, transform=(1, 2, 3, 4))

    def test_override(_):
        kwargs = RasterMetadata((1, 1), transform=(1, 2, 3, 4))
        template = RasterMetadata((1, 1), crs=4326, transform=(5, 6, 7, 8))
        output = parse.template(kwargs, template, "test")
        assert output == RasterMetadata((1, 1), crs=4326, transform=(1, 2, 3, 4))

    def test_invalid(_, assert_contains):
        kwargs = RasterMetadata((1, 1))
        with pytest.raises(TypeError) as error:
            parse.template(kwargs, "invalid", "test")
        assert_contains(error, "test must be a Raster or RasterMetadata object")
