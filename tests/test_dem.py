"""
test_dem  Unit tests for the dem module
"""

import pytest
import subprocess
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
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

class TestRunTaudem:
    dem = "dem.tif"
    pitfilled = "pitfilled.tif"

    def command(self, input_folder, output_folder):
        input = input_folder / self.dem
        output = output_folder / self.pitfilled
        return f"PitRemove -z {input} -fel {output}"

    def test_quiet(self, fire, tempdir, capsys):
        command = self.command(fire, tempdir)
        dem._run_taudem(self.command, verbose=False)
        stdout = capsys.readouterr().out
        assert stdout == ""

    def test_verbose(self, capsys):
        command = self.command(fire, tempdir)
        dem._run_taudem(self.command, verbose=True)
        stdout = capsys.readouterr().out
        assert stdout == ""

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
