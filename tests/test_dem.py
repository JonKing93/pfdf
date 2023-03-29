"""
test_dem  Unit tests for the dem module
"""

import pytest
import numpy, subprocess, rasterio, os
from pathlib import Path
from contextlib import nullcontext
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
    pitfilled = "pitfilled.tif"
    flow_d8 = "flow_d8.tif"
    slopes_d8 = "slopes_d8.tif"
    flow_dinf = "flow_dinf.tif"
    slopes_dinf = "slopes_dinf.tif"
    total_area = "total_area.tif"
    burned_area = "burned_area.tif"
    relief = "relief.tif"
    fire = testfire


# Simulates a user-provided Path dict
@pytest.fixture
def user_paths():
    paths = {
        "dem": UsesPaths.dem,
        "isburned": UsesPaths.isburned,
        "pitfilled": UsesPaths.pitfilled,
        "flow_directions_dinf": UsesPaths.flow_dinf,
        "slopes_dinf": UsesPaths.slopes_dinf,
        "flow_directions": UsesPaths.flow_d8,
        "total_area": UsesPaths.total_area,
        "burned_area": UsesPaths.burned_area,
        "relief": UsesPaths.relief,
        "extra_key": "some-file.tif",
        "another_key": "another-file.tif",
    }
    return {key: UsesPaths.fire / value for key, value in paths.items()}


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


class TestSetupDict(UsesPaths):
    required = dem._inputs + dem._intermediate + dem._final

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
            dem._setup_dict(user_paths)

    @pytest.mark.parametrize("missing", ("dem", "relief"))
    def test_required_none(_, missing, user_paths):
        user_paths[missing] = None
        with pytest.raises(TypeError) as error:
            dem._setup_dict(user_paths)
        assert "expected str, bytes or os.PathLike" in str(error.value)

    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_no_tmp(self, user_paths, path_type):
        paths = self.set_type(path_type, user_paths)
        (output, temporary) = dem._setup_dict(paths)
        self.validate(output, temporary, paths, [])

    @pytest.mark.parametrize(
        "tmp", (["slopes_dinf"], ["flow_directions_dinf", "pitfilled"])
    )
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_missing_tmp(self, user_paths, path_type, tmp):
        paths = self.set_type(path_type, user_paths)
        for file in tmp:
            paths.pop(file)
        (output, temporary) = dem._setup_dict(paths)
        self.validate(output, temporary, paths, tmp)

    @pytest.mark.parametrize(
        "tmp", (["slopes_dinf"], ["flow_directions_dinf", "pitfilled"])
    )
    @pytest.mark.parametrize("path_type", ("string", "path"))
    def test_none_tmp(self, user_paths, path_type, tmp):
        paths = self.set_type(path_type, user_paths)
        for file in tmp:
            paths[file] = None
        (output, temporary) = dem._setup_dict(paths)
        self.validate(output, temporary, paths, tmp)


class TestOutputDict(UsesPaths):
    def run(self, option, required, paths):
        temporary = ["slopes_dinf"]
        output = dem._output_dict(paths, option, temporary)
        assert isinstance(output, dict)

        keys = output.keys()
        assert len(keys) == len(required)

        for key in required:
            assert key in keys
            if option == "all" and key in temporary:
                assert output[key] is None
            else:
                assert output[key] == paths[key]

    def test_default(self, user_paths):
        required = dem._final
        self.run("default", required, user_paths)

    def test_saved(self, user_paths):
        required = dem._final + ["pitfilled", "flow_directions_dinf"]
        self.run("saved", required, user_paths)

    def test_all(self, user_paths):
        required = dem._final + dem._intermediate
        self.run("all", required, user_paths)


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

# Base class for testing user functions. Includes file names and paths
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
