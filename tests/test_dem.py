"""
test_dem  Unit tests for the dem module
----------
The tests for the dem module are grouped into classes. Each class holds the test
for one function in the the dem module. Tests progress from module utilities,
to the low-level TauDEM wrappers, to the user-facing functions.

The tests rely on scientifically validated outputs from a test fire. Test fire
validation data is located in tests/data/<fire code> and consists of a number of
validated TIF rasters produced by TauDEM.

Note that many fires don't have debris-retention basins. However, the computation
for debris-basin flow routing is identical to that of burned upslope area. As
such, you can use copies of the "isburned" and "burned_area" rasters as stand ins
for the debris basin flow routing rasters.

RUNNING THE TESTS:
To run the tests, you will need to:
    * Fulfill any requirements needed to run the dem module
    * Install pytest and rasterio
    * Move to the root of the repository
    * Run `pytest tests/test_dem.py --cov=. --cov-fail-under=80`
"""

import pytest, rasterio
import numpy, subprocess, os
from pathlib import Path
from dfha import dem

# Locate testing data
data = Path(__file__).parent / "data"
testfire = data / "col2022"


###
# Utilites for running the testes
###

# Fixture to create temporary output directories
@pytest.fixture
def tempdir(tmp_path):
    folder = tmp_path / "output"
    folder.mkdir()
    return folder


# Utility to check output raster values
def validate(output, expected):
    assert output.is_file()
    output = rasterio.open(output).read(1)
    expected = rasterio.open(expected).read(1)
    assert numpy.array_equal(output, expected, equal_nan=True)


# Utility to check TauDEM verbosity
def check_verbosity(capfd, verbose):
    stdout = capfd.readouterr().out
    if verbose:
        assert stdout != ""
    else:
        assert stdout == ""


# Return user paths as string or Path
def set_path_type(type, *paths):
    if type == "string":
        return (str(path) for path in paths)
    else:
        return paths


# Base class for TauDEM file names
class UsesPaths:
    dem = "dem.tif"
    isburned = "isburned.tif"
    isdeveloped = "isdeveloped.tif"
    pitfilled = "pitfilled.tif"
    flow_d8 = "flow_d8.tif"
    slopes_d8 = "slopes_d8.tif"
    flow_dinf = "flow_dinf.tif"
    slopes_dinf = "slopes_dinf.tif"
    total_area = "total_area.tif"
    burned_area = "burned_area.tif"
    developed_area = "developed_area.tif"
    isbasin = "isbasin.tif"
    nbasins = "upslope_basins.tif"
    relief = "relief.tif"
    fire = testfire


# Simulates a user-provided Path dict
@pytest.fixture
def user_paths():
    paths = {
        "dem": UsesPaths.dem,
        "isburned": UsesPaths.isburned,
        "isdeveloped": UsesPaths.isdeveloped,
        "pitfilled": UsesPaths.pitfilled,
        "flow_directions_dinf": UsesPaths.flow_dinf,
        "slopes_dinf": UsesPaths.slopes_dinf,
        "flow_directions": UsesPaths.flow_d8,
        "total_area": UsesPaths.total_area,
        "burned_area": UsesPaths.burned_area,
        "developed_area": UsesPaths.developed_area,
        "relief": UsesPaths.relief,
        "extra_key": "some-file.tif",
        "another_key": "another-file.tif",
    }
    return {key: UsesPaths.fire / value for key, value in paths.items()}


@pytest.fixture
def user_paths_basins(user_paths):
    user_paths["isbasin"] = UsesPaths.fire / UsesPaths.isbasin
    user_paths["upslope_basins"] = UsesPaths.fire / UsesPaths.nbasins
    return user_paths


###
# Module utilities
###


class TestRunTaudem(UsesPaths):
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
        try:
            dem.verbose_by_default = True
            verbose = dem._verbosity(None)
            assert verbose == True
        finally:
            dem.verbose_by_default = False


class TestInputPath(UsesPaths):
    path = UsesPaths.fire / UsesPaths.dem

    # Test a string and path
    @pytest.mark.parametrize("input", (str(path), path))
    def test_standard(_, input):
        output = dem._input_path(input)
        assert output == Path(input)

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            output = dem._input_path(self.fire / "not-a-real-file.tif")


@pytest.mark.parametrize("use_str", (True, False))  # Both string and Path inputs
class TestOutputPath(UsesPaths):
    path = (UsesPaths.fire / UsesPaths.dem).with_suffix(".tif")

    def check(_, input, expected, use_str):
        if use_str:
            input = str(input)
        output = dem._output_path(input)
        assert output == expected

    @pytest.mark.parametrize("ext", (".tif", ".tiff", ".TIF", ".TIFF", ".tIf", ".TiFf"))
    def test_tif(self, ext, use_str):
        input = self.path.with_suffix(ext)
        self.check(input, self.path, use_str)

    @pytest.mark.parametrize("tail", ("", ".other", ".test"))
    def test_other(self, tail, use_str):
        stem = self.path.stem
        expected = self.path.with_stem(stem + tail)
        input = expected.with_suffix("")
        self.check(input, expected, use_str)


class TestTemporary(UsesPaths):
    @pytest.mark.parametrize("prefix", ("slopes", "flow_directions"))
    def test(_, prefix, tempdir):
        output = dem._temporary(prefix, tempdir)
        assert output.parent == tempdir

        name = output.name
        assert len(name) == len(prefix) + 1 + dem._tmp_string_length + 4
        assert name[0 : len(prefix) + 1] == prefix + "_"
        assert name[-4:] == ".tif"

        random = name[len(prefix) + 1 : -4]
        assert random.isascii()
        assert random.isalpha()


class TestSetup(UsesPaths):
    required = dem._INPUTS + dem._INTERMEDIATE + dem._FINAL

    def set_type(self, type, paths):
        for key in self.required:
            if type == "string" and (key in paths) and (paths[key] is not None):
                paths[key] = str(paths[key])
        return paths

    def validate(self, output, temporary, paths, tmp):
        assert temporary.sort() == tmp.sort()
        assert isinstance(output, dict)
        tmpdir = output["flow_directions"].parent
        for key in self.required:
            assert key in output
            if key in temporary:
                assert isinstance(output[key], Path)
                assert output[key].parent == tmpdir
                assert output[key].name.startswith(key)
                assert output[key].suffix == ".tif"
            else:
                assert output[key] == Path(paths[key])

    # Parametrizes required input and output
    @pytest.mark.parametrize("missing", ("dem", "relief"))
    def test_required_missing(_, missing, user_paths):
        user_paths.pop(missing)
        with pytest.raises(KeyError):
            dem._setup(user_paths)

    @pytest.mark.parametrize("missing", ("dem", "relief"))
    def test_required_none(_, missing, user_paths):
        user_paths[missing] = None
        with pytest.raises(TypeError) as error:
            dem._setup(user_paths)
        assert "expected str, bytes or os.PathLike" in str(error.value)

    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_no_tmp(self, user_paths, path_type):
        paths = self.set_type(path_type, user_paths)
        (output, temporary, _) = dem._setup(paths)
        self.validate(output, temporary, paths, [])

    @pytest.mark.parametrize(
        "tmp", (["slopes_dinf"], ["flow_directions_dinf", "pitfilled"])
    )
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_missing_tmp(self, user_paths, path_type, tmp):
        paths = self.set_type(path_type, user_paths)
        for file in tmp:
            paths.pop(file)
        (output, temporary, _) = dem._setup(paths)
        self.validate(output, temporary, paths, tmp)

    @pytest.mark.parametrize(
        "tmp", (["slopes_dinf"], ["flow_directions_dinf", "pitfilled"])
    )
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_none_tmp(self, user_paths, path_type, tmp):
        paths = self.set_type(path_type, user_paths)
        for file in tmp:
            paths[file] = None
        (output, temporary, _) = dem._setup(paths)
        self.validate(output, temporary, paths, tmp)

    def test_no_basins(self, user_paths):
        (output, temporary, hasbasins) = dem._setup(user_paths)
        self.validate(output, temporary, user_paths, tmp=[])
        assert not hasbasins
        for file in dem._BASINS:
            assert file not in output

    def test_missing_inbasins(self, user_paths):
        user_paths[dem._BASINS[1]] = str(self.nbasins)
        (output, temporary, hasbasins) = dem._setup(user_paths)
        self.validate(output, temporary, user_paths, tmp=[])
        assert not hasbasins
        assert dem._BASINS[0] not in output
        assert dem._BASINS[1] in output
        assert not isinstance(dem._BASINS[1], Path)

    def test_none_inbasins(self, user_paths):
        [isbasin, nbasins] = dem._BASINS
        user_paths[isbasin] = None
        user_paths[nbasins] = str(self.nbasins)
        (output, temporary, hasbasins) = dem._setup(user_paths)
        self.validate(output, temporary, user_paths, tmp=[])
        assert not hasbasins
        assert isbasin in output
        assert output[isbasin] is None
        assert nbasins in output
        assert output[nbasins] == str(self.nbasins)

    def test_missing_outbasins(self, user_paths_basins):
        user_paths_basins.pop(dem._BASINS[1])
        with pytest.raises(KeyError):
            dem._setup(user_paths_basins)

    def test_none_outbasins(self, user_paths_basins):
        user_paths_basins[dem._BASINS[1]] = None
        with pytest.raises(TypeError):
            dem._setup(user_paths_basins)

    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_with_basins(self, user_paths_basins, path_type):
        isbasin, nbasins = dem._BASINS
        paths = user_paths_basins
        paths[isbasin], paths[nbasins] = set_path_type(
            path_type, paths[isbasin], paths[nbasins]
        )
        (output, temporary, hasbasins) = dem._setup(paths)

        self.validate(output, temporary, paths, tmp=[])
        assert hasbasins
        assert isbasin in output
        assert nbasins in output
        assert output[isbasin] == user_paths_basins[isbasin]
        assert output[nbasins] == user_paths_basins[nbasins]


class TestOutputDict(UsesPaths):
    def run(self, option, required, paths, hasbasins):
        temporary = ["slopes_dinf"]
        output = dem._output_dict(paths, option, temporary, hasbasins)
        assert isinstance(output, dict)

        keys = output.keys()
        assert len(keys) == len(required)

        for key in required:
            assert key in keys
            if option == "all" and key in temporary:
                assert output[key] is None
            else:
                assert output[key] == paths[key]

    def test_default_nobasin(self, user_paths):
        required = dem._FINAL
        print(required)
        self.run("default", required, user_paths, False)

    def test_default_basin(self, user_paths_basins):
        required = dem._FINAL + [dem._BASINS[1]]
        self.run("default", required, user_paths_basins, True)

    def test_saved_nobasin(self, user_paths):
        required = dem._FINAL + ["pitfilled", "flow_directions_dinf"]
        print(required)
        self.run("saved", required, user_paths, False)

    def test_saved_basin(self, user_paths_basins):
        required = dem._FINAL + ["pitfilled", "flow_directions_dinf"] + [dem._BASINS[1]]
        print(required)
        self.run("saved", required, user_paths_basins, True)

    def test_all_nobasin(self, user_paths):
        required = dem._FINAL + dem._INTERMEDIATE
        print(required)
        self.run("all", required, user_paths, False)

    def test_all_basin(self, user_paths_basins):
        required = dem._FINAL + dem._INTERMEDIATE + [dem._BASINS[1]]
        print(required)
        self.run("all", required, user_paths_basins, True)


###
# Low-level Taudem wrappers
###


# Base class for TauDEM wrappers. Checks both verbosity settings
@pytest.mark.parametrize("verbose", (True, False))
class WrapsTaudem(UsesPaths):
    pass


class TestPitRemove(WrapsTaudem):
    def test(self, tempdir, capfd, verbose):
        input = self.fire / self.dem
        output = tempdir / self.pitfilled
        expected = self.fire / self.pitfilled

        dem.pitremove(input, output, verbose)
        check_verbosity(capfd, verbose)
        validate(output, expected)


# Base class for testing D8/D-infinity flow direction wrappers
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
# User functions
###

# Base class for testing user functions. Includes file names and output checker
class UserFunction(UsesPaths):
    missing = "not-a-real-file.tif"

    def check_output(_, output, intended_path, expected_values):
        assert output == Path(intended_path)
        validate(output, expected_values)


class TestPitfill(UserFunction):
    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.pitfill(self.missing, self.missing, verbose=False)

    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_standard(self, tempdir, path_type, verbose, capfd):

        input = self.fire / self.dem
        pitfilled = tempdir / self.pitfilled
        expected = self.fire / self.pitfilled
        (input, pitfilled) = set_path_type(path_type, input, pitfilled)

        output = dem.pitfill(input, pitfilled, verbose=verbose)
        check_verbosity(capfd, verbose)
        self.check_output(output, pitfilled, expected)


class TestFlowDirections(UserFunction):
    d8 = {"type": "D8", "file": UsesPaths.flow_d8, "slopes": UsesPaths.slopes_d8}
    dinf = {
        "type": "DInf",
        "file": UsesPaths.flow_dinf,
        "slopes": UsesPaths.slopes_dinf,
    }

    def paths(self, tempdir, flow, path_type):
        pitfilled = self.fire / self.pitfilled
        output_flow = tempdir / flow["file"]
        expected_flow = self.fire / flow["file"]
        (pitfilled, output_flow) = set_path_type(path_type, pitfilled, output_flow)
        return (pitfilled, output_flow, expected_flow)

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.flow_directions("D8", self.missing, self.missing)

    @pytest.mark.parametrize("flow", (d8, dinf))
    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_no_slopes(self, flow, tempdir, path_type, verbose, capfd):
        (pitfilled, output_flow, expected_flow) = self.paths(tempdir, flow, path_type)
        output = dem.flow_directions(
            flow["type"], pitfilled, output_flow, verbose=verbose
        )
        check_verbosity(capfd, verbose)
        self.check_output(output, output_flow, expected_flow)
        outputs = os.listdir(tempdir)
        assert not any(file.startswith("slopes") for file in outputs)

    @pytest.mark.parametrize("flow", (d8, dinf))
    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_with_slopes(self, flow, tempdir, path_type, verbose, capfd):
        (pitfilled, flow_path, expected_flow) = self.paths(tempdir, flow, path_type)
        slopes_path = tempdir / flow["slopes"]
        expected_slopes = self.fire / flow["slopes"]
        (output_flow, output_slopes) = dem.flow_directions(
            flow["type"], pitfilled, flow_path, slopes_path=slopes_path, verbose=verbose
        )
        check_verbosity(capfd, verbose)
        self.check_output(output_flow, flow_path, expected_flow)
        self.check_output(output_slopes, slopes_path, expected_slopes)


class TestUpslopeArea(UserFunction):
    unweighted = {"weights": None, "name": UsesPaths.total_area}
    weighted = {
        "weights": UsesPaths.fire / UsesPaths.isburned,
        "name": UsesPaths.burned_area,
    }

    @pytest.mark.parametrize("area", (unweighted, weighted))
    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_standard(self, tempdir, path_type, verbose, capfd, area):
        flow = self.fire / self.flow_d8
        area_path = tempdir / area["name"]
        expected = self.fire / area["name"]
        (flow, area_path) = set_path_type(path_type, flow, area_path)

        output = dem.upslope_area(
            flow, area_path, weights_path=area["weights"], verbose=verbose
        )
        check_verbosity(capfd, verbose)
        self.check_output(output, area_path, expected)

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.upslope_area(self.missing, self.missing)


class TestUpslopeBasins(UserFunction):
    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_standard(self, tempdir, path_type, verbose, capfd):
        flow = self.fire / self.flow_d8
        isbasin = self.fire / self.isbasin
        nbasins = tempdir / self.nbasins
        expected = self.fire / self.nbasins
        (flow, isbasin, nbasins) = set_path_type(path_type, flow, isbasin, nbasins)

        output = dem.upslope_basins(flow, isbasin, nbasins, verbose=verbose)
        check_verbosity(capfd, verbose)
        self.check_output(output, nbasins, expected)

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.upslope_basins(self.missing, self.missing, self.missing)


class TestUpslopeBurn(UserFunction):
    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_standard(self, tempdir, path_type, verbose, capfd):
        flow = self.fire / self.flow_d8
        isburned = self.fire / self.isburned
        area = tempdir / self.burned_area
        expected = self.fire / self.burned_area
        (flow, isburned, area) = set_path_type(path_type, flow, isburned, area)

        output = dem.upslope_burn(flow, isburned, area, verbose=verbose)
        check_verbosity(capfd, verbose)
        self.check_output(output, area, expected)

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.upslope_burn(self.missing, self.missing, self.missing)


class TestUpslopeDevelopment(UserFunction):
    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_standard(self, tempdir, path_type, verbose, capfd):
        flow = self.fire / self.flow_d8
        isdeveloped = self.fire / self.isdeveloped
        area = tempdir / self.developed_area
        expected = self.fire / self.developed_area
        (flow, isdeveloped, area) = set_path_type(path_type, flow, isdeveloped, area)

        output = dem.upslope_development(flow, isdeveloped, area, verbose=verbose)
        check_verbosity(capfd, verbose)
        self.check_output(output, area, expected)

    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.upslope_development(self.missing, self.missing, self.missing)


class TestRelief(UserFunction):
    def test_missing(self):
        with pytest.raises(FileNotFoundError):
            dem.relief(self.missing, self.missing, self.missing, self.missing)

    @pytest.mark.parametrize("verbose", (True, False, None))
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_standard(self, tempdir, path_type, verbose, capfd):
        pitfilled = self.fire / self.pitfilled
        flow = self.fire / self.flow_dinf
        slopes = self.fire / self.slopes_dinf
        relief = tempdir / self.relief
        expected = self.fire / self.relief
        (pitfilled, flow, slopes, relief) = set_path_type(
            path_type, pitfilled, flow, slopes, relief
        )

        output = dem.relief(pitfilled, flow, slopes, relief, verbose=verbose)
        check_verbosity(capfd, verbose)
        self.check_output(output, relief, expected)


class TestAnalyze:
    missing_tmps = ["flow_directions_dinf"]
    none_tmps = ["pitfilled"]
    saved_tmps = ["slopes_dinf"]

    def setup_paths(self, paths, tmpdir, hasbasins):
        outputs = dem._FINAL + self.saved_tmps
        if hasbasins:
            outputs += [dem._BASINS[1]]
        else:
            paths.pop(dem._BASINS[0])
            paths.pop(dem._BASINS[1])
        for file in outputs:
            paths[file] = tmpdir / paths[file].name
        for file in self.missing_tmps:
            paths.pop(file)
        for file in self.none_tmps:
            paths[file] = None
        return paths

    def check_outputs(self, output, required, tmpdir, input_paths, all_paths, hasbasins):
        assert isinstance(output, dict)

        # Get lists of tmp files, saved output files, expected output files for core analysis
        temporary = self.missing_tmps + self.none_tmps
        saved = os.listdir(tmpdir)
        expected = dem._FINAL + self.saved_tmps

        # Add optional basin files and get final file list
        if hasbasins:
            nbasins = [dem._BASINS[1]]
            expected += nbasins
            required += nbasins
        expected_files = [all_paths[file].name for file in expected]

        # Check the dict has the expected keys/values
        keys = output.keys()
        assert sorted(keys) == sorted(required)
        for key in required:
            if key in temporary:
                assert output[key] is None
            else:
                assert output[key] == input_paths[key]

        # Validate the saved files
        assert sorted(saved) == sorted(expected_files)
        for file in expected:
            validate(input_paths[file], all_paths[file])

        # Check that tmp files were deleted
        for tmp in temporary:
            stem = all_paths[tmp].stem
            assert not any(file.startswith(stem) for file in saved)

    def test_missing_required(self, user_paths):
        user_paths.pop("dem")
        with pytest.raises(KeyError):
            dem.analyze(user_paths)

    @pytest.mark.parametrize('hasbasins', (True, False))
    def test_default(self, user_paths_basins, tmpdir, hasbasins):
        paths = self.setup_paths(user_paths_basins, tmpdir, hasbasins)
        output = dem.analyze(paths)
        required = dem._FINAL.copy()
        self.check_outputs(output, required, tmpdir, paths, user_paths_basins, hasbasins)

    @pytest.mark.parametrize('hasbasins', (True, False))
    def test_saved(self, user_paths_basins, tmpdir, hasbasins):
        paths = self.setup_paths(user_paths_basins, tmpdir, hasbasins)
        output = dem.analyze(paths, outputs="saved")
        required = dem._FINAL + self.saved_tmps
        self.check_outputs(output, required, tmpdir, paths, user_paths_basins, hasbasins)

    @pytest.mark.parametrize('hasbasins', (True, False))
    def test_all(self, user_paths_basins, tmpdir, hasbasins):
        paths = self.setup_paths(user_paths_basins, tmpdir, hasbasins)
        output = dem.analyze(paths, outputs="all")
        required = dem._FINAL + dem._INTERMEDIATE
        self.check_outputs(output, required, tmpdir, paths, user_paths_basins, hasbasins)
