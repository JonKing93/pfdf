"""
test_dem  Unit tests for the dem module
"""

import pytest
import numpy, subprocess, rasterio
from pathlib import Path
from dfha import dem

# Locate testing data
data = Path(__file__).parent / "data"
fire = data / "col2022"

# Fixture to create temporary output directories
@pytest.fixture
def tempdir(tmp_path):
    folder = tmp_path / "output"
    folder.mkdir()
    return folder

# Utility to read raster data
def read(raster):
    return rasterio.open(raster).read(1)

# Utility to validate output raster values
def validate(output, expected):
    assert output.is_file()
    output = read(output)
    expected = read(expected)
    assert numpy.array_equal(output, expected, equal_nan=True)

# Utility to check verbosity
def check_verbosity(capsys, verbose):
    stdout = capsys.readouterr().out
    if verbose:
        assert stdout != ''
    else:
        assert stdout == ''

# Base class for TauDEM file names
class UsesTaudem:
    dem = "dem.tif"
    isburned = "isburned.tif"
    pitfilled = "pitfilled.tif"
    flow_d8 = "flow_d8.tif"
    slopes_d8 = "slopes_d8.tif"
    flow_dinf = "flow_dinf.tif"
    slopes_dinf = "slopes_dinf.tif"
    total_area = "total_area.tif"
    burned_area = "burned_area.tif"
    relief = "relief.tif"

# Base class for low-level TauDEM wrappers
class WrapsTaudem(UsesTaudem):




###
# Low-level Taudem wrappers
###

class TestPitRemove(UsesTaudem):

    def test_quiet(self, fire, tempdir, capsys):
        input = fire / "dem.tif"
        output = tempdir / "pitfilled.tif"
        expected = fire / "pitfilled.tif"

        command = f"PitRemove -z {input} -fel {output}"
        dem._run_taudem(command, verbose=False)
        validate(output, expected)

        stdout = 











###
# Utilities
###
class TestRunTaudem(UsesTaudem):

    def command(self, fire, tempdir):
        input = fire / self.dem
        output = tempdir / self.pitfilled
        return f"PitRemove -z {input} -fel {output}"

    @pytest.mark.parametrize("verbose", (True, False))
    def test_success(self, fire, tempdir, capsys, verbose):
        command = self.command(fire, tempdir)
        dem._run_taudem(command, verbose)
        check_verbosity(capsys, verbose)

    def test_failed(self):
        command = self.command(fire, tempdir).replace(self.dem, "not-a-real-file.tif")
        with pytest.raises(subprocess.CalledProcessError):
            dem._run_taudem(command, verbose=False)


class TestVerbosity:
    @pytest.mark.parametrize("tf", [True, False])
    def test_bool(_, tf):
        verbose = dem._verbosity(tf)
        assert verbose == tf

    def test_none(_):
        verbose = dem._verbosity(None)
        assert verbose == False

    def test_changed_default(_):
        dem.verbose_by_default = True
        verbose = dem._verbosity(None)
        assert verbose == True


# class TestOutputPath:
#     file = "dem"
#     path = str(fire / file)
#     expected = Path(fire / (file + ".tif")).resolve()
#     tif_extensions = (".tif", ".tiff", ".TIF", ".TIFF", ".tIf", ".TiFf")
#     other_extensions = ("", ".other")

#     def check_path(self, tail, use_path, change_stem):
#         path = self.path + tail
#         if use_path:
#             path = Path(path)
#         output = dem._output_path(path)
#         expected = self.expected
#         if change_stem:
#             expected = self.expected.with_stem(self.file + tail)
#         assert output == expected

#     @pytest.mark.parametrize("ext", tif_extensions)
#     def test_str_tif(self, ext):
#         self.check_path(ext, use_path=False, change_stem=False)

#     @pytest.mark.parametrize("ext", tif_extensions)
#     def test_Path_tif(self, ext):
#         self.check_path(ext, use_path=True, change_stem=False)

#     @pytest.mark.parametrize("tail", other_extensions)
#     def test_str_other(self, tail):
#         self.check_path(tail, use_path=False, change_stem=True)

#     @pytest.mark.parametrize("tail", other_extensions)
#     def test_Path_other(self, tail):
#         self.check_path(tail, use_path=True, change_stem=True)
