"""
test_dem  Unit tests for the dem module
"""

import pytest
from pathlib import Path
import arcpy, numpy
from dfha import dem

# Locate test geodatabases
data = Path(__file__).parent / "tests" / "data"
fire = data / "col2022.gdb"



class TestRunTaudem:
    command = f"PitRemove -z {fire/dem}"

    def test_standard:

    def test_verbose:

    def test_failed:




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


class TestOutputPath:
    file = "dem"
    path = str(fire / file)
    expected = Path(fire / (file + ".tif")).resolve()
    tif_extensions = (".tif", ".tiff", ".TIF", ".TIFF", ".tIf", ".TiFf")
    other_extensions = ("", ".other")

    def check_path(self, tail, use_path, change_stem):
        path = self.path + tail
        if use_path:
            path = Path(path)
        output = dem._output_path(path)
        expected = self.expected
        if change_stem:
            expected = self.expected.with_stem(self.file + tail)
        assert output == expected

    @pytest.mark.parametrize("ext", tif_extensions)
    def test_str_tif(self, ext):
        self.check_path(ext, use_path=False, change_stem=False)

    @pytest.mark.parametrize("ext", tif_extensions)
    def test_Path_tif(self, ext):
        self.check_path(ext, use_path=True, change_stem=False)

    @pytest.mark.parametrize("tail", other_extensions)
    def test_str_other(self, tail):
        self.check_path(tail, use_path=False, change_stem=True)

    @pytest.mark.parametrize("tail", other_extensions)
    def test_Path_other(self, tail):
        self.check_path(tail, use_path=True, change_stem=True)



