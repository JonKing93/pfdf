"""
test_dem  Unit tests for the dem module
"""

import os
import pytest
import numpy, subprocess, rasterio
from pathlib import Path
from dfha import dem

# Locate testing data
data = Path(__file__).parent / "data"
testfire = data / "col2022"


###
# Utilites for running the testes
###

# Fixture to pass in test fire data
@pytest.fixture
def fire():
    return testfire


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
def check_verbosity(capfd, verbose):
    stdout = capfd.readouterr().out
    if verbose:
        assert stdout != ""
    else:
        assert stdout == ""


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
    fire = testfire


###
# Module utilities
###


class TestRunTaudem(UsesTaudem):
    def command(self, tempdir):
        input = self.fire / self.dem
        output = tempdir / self.pitfilled
        return f"PitRemove -z {input} -fel {output}"

    @pytest.mark.parametrize("verbose", (True, False))
    def test_succeed(self, tempdir, capfd, verbose):
        command = self.command(tempdir)
        dem._run_taudem(command, verbose)
        check_verbosity(capfd, verbose)

    def test_failed(self, tempdir):
        command = self.command(tempdir)
        command = command.replace(self.dem, "not-a-real-file.tif")
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


###
# Low-level Taudem wrappers
###


@pytest.mark.parametrize("verbose", (True, False))
class WrapsTaudem(UsesTaudem):
    pass


class TestPitRemove(WrapsTaudem):
    def test(self, tempdir, capfd, verbose):
        input = self.fire / self.dem
        output = tempdir / self.pitfilled
        expected = self.fire / self.pitfilled

        dem.pitremove(input, output, verbose)
        check_verbosity(capfd, verbose)
        validate(output, expected)


class TaudemFlow(WrapsTaudem):
    def run(self, tempdir, capfd, verbose, function, flow, slopes):
        pitfilled = self.fire / self.pitfilled
        output_flow = tempdir / flow
        output_slopes = tempdir / slopes
        expected_flow = self.fire / flow
        expected_slopes = self.fire / slopes

        function(pitfilled, output_flow, output_slopes, verbose)
        check_verbosity(capfd, verbose)
        validate(output_flow, expected_flow)
        validate(output_slopes, expected_slopes)


class TestFlowD8(TaudemFlow):
    def test(self, tempdir, capfd, verbose):
        function = dem.flow_d8
        flow = self.flow_d8
        slopes = self.slopes_d8
        self.run(tempdir, capfd, verbose, function, flow, slopes)


class TestFlowDInf(TaudemFlow):
    def test(self, tempdir, capfd, verbose):
        function = dem.flow_dinf
        flow = self.flow_dinf
        slopes = self.slopes_dinf
        self.run(tempdir, capfd, verbose, function, flow, slopes)


class TestAreaD8(WrapsTaudem):
    def run(self, tempdir, capfd, verbose, weights, area):
        flow = self.fire / self.flow_d8
        output = tempdir / area
        expected = self.fire / area

        dem.area_d8(flow, weights, output, verbose)
        check_verbosity(capfd, verbose)
        validate(output, expected)

    def test_weighted(self, tempdir, capfd, verbose):
        weights = self.fire / self.isburned
        area = self.burned_area
        self.run(tempdir, capfd, verbose, weights, area)

    def test_unweighted(self, tempdir, capfd, verbose):
        weights = None
        area = self.total_area
        self.run(tempdir, capfd, verbose, weights, area)


class TestReliefDInf(WrapsTaudem):
    def test(self, tempdir, capfd, verbose):
        pitfilled = self.fire / self.pitfilled
        flow = self.fire / self.flow_dinf
        slopes = self.fire / self.slopes_dinf
        output = tempdir / self.relief
        expected = self.fire / self.relief

        dem.relief_dinf(pitfilled, flow, slopes, output, verbose)
        check_verbosity(capfd, verbose)
        validate(output, expected)


###
# Utilities
###


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
