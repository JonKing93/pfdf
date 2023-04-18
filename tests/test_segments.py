"""
test_segments  Unit tests for stream segment filtering
"""

import pytest
import rasterio
import numpy as np
from dfha import validate, segments





#####
# Internal Tests
#####

class TestRasterShapeError:

    def test(_):

        name = 'test'
        cause = validate.ShapeError(name, 'rows', 0, required=(10,10), actual=(9,10))
        error = segments.RasterShapeError(name, cause)

        assert isinstance(error, Exception)
        assert error.args[0] == (
            'The shape of the test raster (9, 10) does not match the shape of the '
            'stream segment raster used to derive the segments (10, 10).'
        )

    
