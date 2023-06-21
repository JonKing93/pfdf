"""
test_dem  Unit tests for the dem module
----------
The tests for the dem module are grouped into classes. Each class holds the test
for one function in the the dem module. Tests progress from module utilities,
to the low-level TauDEM wrappers, to the user-facing functions.

REQUIREMENTS:
    * Same as for the DEM module

RUNNING THE TESTS:
To run the tests, you will need to:
    * Fulfill any requirements needed to run the dem module
    * Install pytest and rasterio
    * Move to the root of the repository
    * Run `pytest tests/test_dem.py --cov=. --cov-fail-under=80`
"""

import subprocess
from pathlib import Path

import numpy as np
import pytest
import rasterio

from dfha import dem
from dfha.errors import DimensionError, ShapeError
from dfha.utils import load_raster, save_raster

#####
# Testing Utilities
#####

# TauDEM floating-point fill value
fmin = np.finfo("float32").min

# Raster data for a pre-existing output file
existing_raster = np.arange(0, 10).reshape(2, 5)


# A raster as a numpy array
@pytest.fixture
def araster():
    return np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]).astype(float)


# A file-based raster
@pytest.fixture
def fraster(araster, tmp_path):
    path = tmp_path / "raster.tif"
    save_raster(araster, path, nodata=200)
    return path


# Saves a file-based raster
def file_raster(raster, dtype, folder, name, nodata=None):
    path = folder / (name + ".tif")
    raster = raster.astype(dtype)
    save_raster(raster, path, nodata)
    return path


# Saves a 3x4 raster whose edges are fill values
def filled_raster(dtype, folder, name, center, fill):
    raster = np.array(
        [
            [fill, fill, fill, fill],
            [fill, center[0], center[1], fill],
            [fill, fill, fill, fill],
        ]
    )
    return file_raster(raster, dtype, folder, name, nodata=fill)


@pytest.fixture
def fdem(tmp_path):
    dem = np.array([[4, 5, 6, 6], [5, 1, 4, 5], [3, 2, 3, 4]])
    return file_raster(dem, "float32", tmp_path, "dem")


@pytest.fixture
def fpitfilled(tmp_path):
    pitfilled = np.array(
        [
            [4, 5, 6, 6],
            [5, 2, 4, 5],
            [3, 2, 3, 4],
        ]
    )
    return file_raster(pitfilled, "float32", tmp_path, "pitfilled")


@pytest.fixture
def fflow8(tmp_path):
    return filled_raster("int16", tmp_path, "flow8", center=[7, 5], fill=-32768)


@pytest.fixture
def fslopes8(tmp_path):
    return filled_raster("float32", tmp_path, "slopes8", center=[0, 2], fill=-1)


# D-infinity flow directions
@pytest.fixture
def fflowi(tmp_path):
    return filled_raster(
        "float32", tmp_path, "slopesi", center=[4.7123890, 3.1415927], fill=fmin
    )


# D-infinity slopes are the same as D8 for this simple example
@pytest.fixture
def fslopesi(fslopes8):
    return fslopes8


# Unweighted upslope area
@pytest.fixture
def fareau(tmp_path):
    return filled_raster("float32", tmp_path, "area_unweighted", center=[2, 1], fill=-1)


# Area weights
@pytest.fixture
def fweights(tmp_path):
    return filled_raster("float32", tmp_path, "weights", center=[2, 6], fill=-999)


# Valid data mask for upslope sums
@pytest.fixture
def fmask(tmp_path):
    return filled_raster("int8", tmp_path, "mask", center=[1, 0], fill=-1)


# Weighted area
@pytest.fixture
def fareaw(tmp_path):
    return filled_raster("float32", tmp_path, "area_weighted", center=[8, 6], fill=-1)


# Masked upslope sum
@pytest.fixture
def faream(tmp_path):
    return filled_raster("float32", tmp_path, "area_masked", center=[2, 0], fill=-1)


# Vertical relief
@pytest.fixture
def frelief(tmp_path):
    return filled_raster("float32", tmp_path, "relief", center=[2, 0], fill=fmin)


# Check string is in error message
def assert_contains(error, *strings):
    message = error.value.args[0]
    for string in strings:
        assert string in message


#####
# Loaded array validaters
#####


class TestValidateD8:
    def test_nocheck(_):
        dem._validate_d8(False, "invalid", None)

    def test_pass_nodata(_, fflow8):
        dem._validate_d8(True, fflow8, nodata=-32768)

    def test_fail(_, fflow8):
        with pytest.raises(ValueError) as error:
            dem._validate_d8(True, fflow8, None)
        assert_contains(error, "flow_directions")


class TestValidateDinf:
    def test_nocheck(_):
        dem._validate_dinf(False, "invalid", None, "invalid", None)

    def test_pass_nodata(_, fflowi, fslopesi):
        dem._validate_dinf(True, fflowi, fmin, fslopesi, -1)

    def test_fail_flow(_, fflowi, fslopesi):
        with pytest.raises(ValueError) as error:
            dem._validate_dinf(True, fflowi, None, fslopesi, -1)
        assert_contains(error, "flow_directions")

    def test_fail_slopes(_, fflowi, fslopesi):
        with pytest.raises(ValueError) as error:
            dem._validate_dinf(True, fflowi, fmin, fslopesi, None)
        assert_contains(error, "slopes")


class TestValidateMask:
    def test_invalid_shape(_, fmask):
        with pytest.raises(ShapeError) as error:
            dem._validate_mask(False, fmask, shape=(10, 10), nodata=-1)
        assert_contains(error, "mask")

    def test_invalid_raster(_):
        with pytest.raises(TypeError):
            dem._validate_mask(False, np, None, None)

    def test_pass(_, fmask):
        dem._validate_mask(True, fmask, shape=(3, 4), nodata=-1)

    def test_fail(_, fmask):
        fmask = load_raster(fmask)
        with pytest.raises(ValueError) as error:
            dem._validate_mask(True, fmask, shape=(3, 4), nodata=None)
        assert_contains(error, "mask")

    def test_nocheck(_, fmask):
        dem._validate_mask(False, fmask, None, None)


#####
# Module Utilities
#####


class TestOptions:
    @pytest.mark.parametrize("verbose", (True, False))
    @pytest.mark.parametrize("overwrite", (True, False))
    def test_bool(_, verbose, overwrite):
        verbose_out, overwrite_out = dem._options(verbose, overwrite)
        assert verbose_out == verbose
        assert overwrite_out == overwrite

    def test_none(_):
        verbose, overwrite = dem._options(None, None)
        assert verbose == False
        assert overwrite == False

    def test_changed_default(_):
        try:
            dem.verbose_by_default = True
            dem.overwrite_by_default = True
            verbose, overwrite = dem._options(None, None)
            assert verbose == True
            assert overwrite == True
        finally:
            dem.verbose_by_default = False
            dem.overwrite_by_default = False


class TestValidateInputs:
    def test_invalid(_):
        with pytest.raises(TypeError) as error:
            dem._validate_inputs([True], ["test name"], [None], [""])
        assert_contains(error, "test name")

    def test_invalid_array(_):
        a = np.arange(0, 27).reshape(3, 3, 3)
        with pytest.raises(DimensionError) as error:
            dem._validate_inputs([a], ["test name"], [None], [""])
        assert_contains(error, "test name")

    def test_invalid_file(_):
        file = "not-a-file"
        with pytest.raises(FileNotFoundError):
            dem._validate_inputs([file], ["test name"], [None], [""])

    def test_invalid_shapes(_, araster):
        raster1 = araster
        raster2 = araster.reshape(-1)
        with pytest.raises(ShapeError) as error:
            dem._validate_inputs(
                [raster1, raster2], ["test 1", "test 2"], [None, None], ["", ""]
            )
        assert_contains(error, "test 2")

    def test_invalid_nodata(_, araster):
        invalid = np.array([1, 2, 3])
        with pytest.raises(DimensionError) as error:
            dem._validate_inputs([araster], ["test raster"], [invalid], ["nodata name"])
        assert_contains(error, "nodata name")

    def test_valid_array(_, araster):
        rasters, nodata = dem._validate_inputs([araster], ["test name"], [-999], [""])
        assert isinstance(rasters, list)
        assert len(rasters) == 1
        assert np.array_equal(rasters[0], araster)
        assert isinstance(nodata, list)
        assert len(nodata) == 1
        assert nodata[0] == -999

    def test_valid_file(_, fraster):
        rasters, nodata = dem._validate_inputs([fraster], ["test 1"], [-999], [""])
        assert isinstance(rasters, list)
        assert len(rasters) == 1
        assert rasters[0] == fraster
        assert isinstance(nodata, list)
        assert len(nodata) == 1
        assert nodata[0] == 200

    def test_multiple(_, araster, fraster):
        rasters, nodata = dem._validate_inputs(
            [araster, fraster], ["test 1", "test 2"], [-999, None], ["", ""]
        )
        assert isinstance(rasters, list)
        assert len(rasters) == 2
        assert np.array_equal(rasters[0], araster)
        assert rasters[1] == fraster

        assert isinstance(nodata, list)
        assert len(nodata) == 2
        assert nodata[0] == -999
        assert nodata[1] == 200


class TestPaths:
    @pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
    def test(_, tmp_path, araster, fraster):
        output = dem._paths(
            tmp_path,
            rasters=[araster, fraster, fraster, None],
            save=[None, None, True, False],
            names=["input-1", "input-2", "output-1", "output-2"],
            nodata=[5, "ignored"],
        )

        assert isinstance(output, list)
        assert len(output) == 4
        assert output[0] == tmp_path / "input-1.tif"
        assert output[0].is_file()
        with rasterio.open(output[0]) as file:
            data = file.read(1)
            assert np.array_equal(data, araster)
            assert file.nodata == 5
        assert output[1] == fraster
        assert output[2] == fraster
        assert output[3] == tmp_path / "output-2.tif"


class TestRunTaudem:
    def test_verbose(_, tmp_path, fraster, capfd):
        dem_data = fraster
        pitfilled = tmp_path / "pitfilled.tif"
        command = f"PitRemove -z {dem_data} -fel {pitfilled}"
        dem._run_taudem(command, verbose=True)
        stdout = capfd.readouterr().out
        assert stdout != ""

    def test_quiet(_, tmp_path, fraster, capfd):
        dem_data = fraster
        pitfilled = tmp_path / "pitfilled.tif"
        command = f"PitRemove -z {dem_data} -fel {pitfilled}"
        dem._run_taudem(command, verbose=False)
        stdout = capfd.readouterr().out
        assert stdout == ""

    def test_failed(_, tmp_path):
        dem_data = tmp_path / "not-a-file.tif"
        pitfilled = tmp_path / "pitfilled.tif"
        command = f"PitRemove -z {dem_data} -fel {pitfilled}"
        with pytest.raises(subprocess.CalledProcessError):
            dem._run_taudem(command, verbose=False)


class TestOutput:
    def test_array(_, araster, fraster):
        output = dem._output(fraster, save=False)
        assert np.array_equal(output, araster)

    def test_path(_, fraster):
        output = dem._output(fraster, save=True)
        assert output == fraster


#####
# Low Level
#####


class TestPitRemove:
    def test(_, fdem, fpitfilled, tmp_path):
        pitfilled = tmp_path / "output.tif"
        assert not pitfilled.is_file()
        dem.pitremove(fdem, pitfilled, False)
        assert pitfilled.is_file()

        output = load_raster(pitfilled)
        expected = load_raster(fpitfilled)
        assert np.array_equal(output, expected)


class TestFlowD8:
    def test(_, fpitfilled, fflow8, fslopes8, tmp_path):
        flow = tmp_path / "output-1.tif"
        slopes = tmp_path / "output-2.tif"
        assert not flow.is_file()
        assert not slopes.is_file()
        dem.flow_d8(fpitfilled, flow, slopes, False)
        assert flow.is_file()
        assert slopes.is_file()

        output = load_raster(flow)
        expected = load_raster(fflow8)
        assert np.array_equal(output, expected)

        output = load_raster(slopes).astype(float)
        expected = load_raster(fslopes8).astype(float)
        print(output)
        print(expected)
        assert np.allclose(output, expected, rtol=0, atol=1e-7)


class TestFlowDinf:
    def test_flow_dinf(_, fpitfilled, fflowi, fslopesi, tmp_path):
        flow = tmp_path / "output-1.tif"
        slopes = tmp_path / "output-2.tif"
        assert not flow.is_file()
        assert not slopes.is_file()
        dem.flow_dinf(fpitfilled, flow, slopes, False)
        assert flow.is_file()
        assert slopes.is_file()

        output = load_raster(flow)[1, 1:3]
        expected = load_raster(fflowi)[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

        output = load_raster(slopes)[1, 1:3].astype(float)
        expected = load_raster(fslopesi)[1, 1:3].astype(float)
        assert np.allclose(output, expected, rtol=0, atol=1e-7)


class TestAreaD8:
    def test_unweighted(_, fflow8, fareau, tmp_path):
        area = tmp_path / "output.tif"
        assert not area.is_file()
        dem.area_d8(fflow8, None, area, False)
        assert area.is_file()

        output = load_raster(area)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)

    def test_weighted(_, fflow8, fweights, fareaw, tmp_path):
        area = tmp_path / "output.tif"
        assert not area.is_file()
        dem.area_d8(fflow8, fweights, area, False)
        assert area.is_file()

        output = load_raster(area)
        expected = load_raster(fareaw)
        assert np.array_equal(output, expected)


class TestReliefDinf:
    def test(_, fpitfilled, fflowi, fslopesi, frelief, tmp_path):
        relief = tmp_path / "output.tif"
        assert not relief.is_file()
        dem.relief_dinf(fpitfilled, fflowi, fslopesi, relief, False)
        assert relief.is_file()

        output = load_raster(relief)
        expected = load_raster(frelief)
        assert np.array_equal(output, expected)


#####
# User Functions
#####


class TestPitfill:
    def test_verbose(_, fdem, capfd):
        dem.pitfill(fdem, verbose=True)
        stdout = capfd.readouterr().out
        assert stdout != ""

    def test_quiet(_, fdem, capfd):
        dem.pitfill(fdem, verbose=False)
        stdout = capfd.readouterr().out
        assert stdout == ""

    def test_overwrite(_, fdem, fpitfilled, tmp_path):
        pitfilled = tmp_path / "output.tif"
        save_raster(existing_raster, pitfilled)
        dem.pitfill(fdem, path=pitfilled, overwrite=True)
        output = load_raster(pitfilled)
        expected = load_raster(fpitfilled)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fdem, tmp_path):
        pitfilled = tmp_path / "output.tif"
        save_raster(existing_raster, pitfilled)
        with pytest.raises(FileExistsError):
            dem.pitfill(fdem, path=pitfilled, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array(_, fdem, fpitfilled, load_input):
        if load_input:
            fdem = load_raster(fdem)
        output = dem.pitfill(fdem)
        expected = load_raster(fpitfilled)
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "dem.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save(_, fdem, fpitfilled, tmp_path, load_input):
        if load_input:
            fdem = load_raster(fdem)
        pitfilled = tmp_path / "output.tif"
        output = dem.pitfill(fdem, path=pitfilled)
        assert output == pitfilled
        output = load_raster(pitfilled)
        expected = load_raster(fpitfilled)
        assert np.array_equal(output, expected)

    def test_nodata(_, fdem):
        fdem = load_raster(fdem)
        output = dem.pitfill(fdem, nodata=4)
        fill = -3e38
        expected = fdem
        expected[expected == 4] = fill
        assert np.array_equal(output, expected)

    def test_ignore_nodata(_, fdem, fpitfilled):
        output = dem.pitfill(fdem, nodata=4)
        expected = load_raster(fpitfilled)
        assert np.array_equal(output, expected)


class TestFlowDirections:
    def test_verbose(_, fpitfilled, capfd):
        dem.flow_directions("D8", fpitfilled, verbose=True)
        stdout = capfd.readouterr().out
        assert stdout != ""

    def test_quiet(_, fpitfilled, capfd):
        dem.flow_directions("D8", fpitfilled, verbose=False)
        stdout = capfd.readouterr().out
        assert stdout == ""

    def test_overwrite(_, fpitfilled, fflow8, tmp_path):
        flow = tmp_path / "output.tif"
        save_raster(existing_raster, flow)
        dem.flow_directions("D8", fpitfilled, path=flow, overwrite=True)
        output = load_raster(flow)
        expected = load_raster(fflow8)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fpitfilled, tmp_path):
        flow = tmp_path / "output.tif"
        save_raster(existing_raster, flow)
        with pytest.raises(FileExistsError):
            dem.upslope_pixels(fpitfilled, path=flow, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array8(_, fpitfilled, fflow8, load_input):
        if load_input:
            fpitfilled = load_raster(fpitfilled)
        output = dem.flow_directions("D8", fpitfilled)
        expected = load_raster(fflow8)
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    def test_array8_slopes(_, fpitfilled, fflow8, fslopes8):
        output = dem.flow_directions("D8", fpitfilled, return_slopes=True)
        assert isinstance(output, tuple)
        assert len(output) == 2
        flow, slopes = output
        expected = load_raster(fflow8)
        assert np.array_equal(flow, expected)
        expected = load_raster(fslopes8)
        assert np.allclose(slopes, expected, rtol=0, atol=1e-7)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save8(_, fpitfilled, fflow8, tmp_path, load_input):
        if load_input:
            fpitfilled = load_raster(fpitfilled)
        flow = tmp_path / "output.tif"
        output = dem.flow_directions("D8", fpitfilled, path=flow)
        assert output == flow
        output = load_raster(flow)
        expected = load_raster(fflow8)
        assert np.array_equal(output, expected)

    def test_save8_slopes(_, fpitfilled, fflow8, fslopes8, tmp_path):
        flow_path = tmp_path / "output-1.tif"
        slopes_path = tmp_path / "output-2.tif"
        output = dem.flow_directions(
            "D8",
            fpitfilled,
            path=flow_path,
            return_slopes=True,
            slopes_path=slopes_path,
        )
        assert isinstance(output, tuple)
        assert len(output) == 2
        flow, slopes = output
        assert flow == flow_path
        output = load_raster(flow_path)
        expected = load_raster(fflow8)
        assert np.array_equal(output, expected)
        assert slopes == slopes_path
        output = load_raster(slopes_path)
        expected = load_raster(fslopes8)
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_arrayI(_, fpitfilled, fflowi, load_input):
        if load_input:
            fpitfilled = load_raster(fpitfilled)
        output = dem.flow_directions("DInf", fpitfilled)[1, 1:3]
        expected = load_raster(fflowi)[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    def test_arrayI_slopes(_, fpitfilled, fflowi, fslopesi):
        output = dem.flow_directions("DInf", fpitfilled, return_slopes=True)
        assert isinstance(output, tuple)
        assert len(output) == 2
        flow, slopes = output
        flow = flow[1, 1:3]
        slopes = slopes[1, 1:3]
        expected = load_raster(fflowi)[1, 1:3]
        assert np.allclose(flow, expected, rtol=0, atol=1e-7)
        expected = load_raster(fslopesi)[1, 1:3]
        assert np.allclose(slopes, expected, rtol=0, atol=1e-7)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_saveI(_, fpitfilled, fflowi, tmp_path, load_input):
        if load_input:
            fpitfilled = load_raster(fpitfilled)
        flow = tmp_path / "output.tif"
        output = dem.flow_directions("DInf", fpitfilled, path=flow)
        assert output == flow
        output = load_raster(flow)[1, 1:3]
        expected = load_raster(fflowi)[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

    def test_saveI_slopes(_, fpitfilled, fflowi, fslopesi, tmp_path):
        flow_path = tmp_path / "output-1.tif"
        slopes_path = tmp_path / "output-2.tif"
        output = dem.flow_directions(
            "DInf",
            fpitfilled,
            path=flow_path,
            return_slopes=True,
            slopes_path=slopes_path,
        )
        assert isinstance(output, tuple)
        assert len(output) == 2
        flow, slopes = output
        assert flow == flow_path
        output = load_raster(flow_path)[1, 1:3]
        expected = load_raster(fflowi)[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)
        assert slopes == slopes_path
        output = load_raster(slopes_path)[1, 1:3]
        expected = load_raster(fslopesi)[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

    def test_nodata(_, fpitfilled):
        pitfilled = load_raster(fpitfilled)
        output = dem.flow_directions("D8", pitfilled, nodata=4)
        expected = np.full(pitfilled.shape, -32768)
        assert np.array_equal(output, expected)

    def test_ignore_nodata(_, fpitfilled, fflow8):
        output = dem.flow_directions("D8", fpitfilled, nodata=4)
        expected = load_raster(fflow8)
        assert np.array_equal(output, expected)


class TestUpslopePixels:
    def test_warnings(_, fflow8, capfd):
        load_raster(fflow8)
        dem.upslope_pixels(fflow8)

    def test_verbose(_, fflow8, capfd):
        dem.upslope_pixels(fflow8, verbose=True)
        stdout = capfd.readouterr().out
        assert stdout != ""

    def test_quiet(_, fflow8, capfd):
        dem.upslope_pixels(fflow8, verbose=False)
        stdout = capfd.readouterr().out
        assert stdout == ""

    def test_overwrite(_, fflow8, fareau, tmp_path):
        area = tmp_path / "output.tif"
        save_raster(existing_raster, area)
        dem.upslope_pixels(fflow8, path=area, overwrite=True)
        output = load_raster(area)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fflow8, tmp_path):
        area = tmp_path / "output.tif"
        save_raster(existing_raster, area)
        with pytest.raises(FileExistsError):
            dem.upslope_pixels(fflow8, path=area, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array(_, fflow8, fareau, load_input):
        if load_input:
            fflow8 = load_raster(fflow8)
        output = dem.upslope_pixels(fflow8, nodata=-32768)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "upslope_pixels.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save(_, fflow8, fareau, tmp_path, load_input):
        if load_input:
            fflow8 = load_raster(fflow8)
        area = tmp_path / "output.tif"
        output = dem.upslope_pixels(fflow8, nodata=-32768, path=area)
        assert output == area
        output = load_raster(area)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)

    def test_nodata(_, fflow8, fareau):
        flow = load_raster(fflow8)
        output = dem.upslope_pixels(flow, nodata=-32768)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)

    def test_missing_nodata(_, fflow8, fareau):
        flow = load_raster(fflow8)
        output = dem.upslope_pixels(flow, check=False)
        expected = load_raster(fareau)
        expected[expected == -1] = 1
        expected[2, 1] = 3
        assert np.array_equal(output, expected)

    def test_ignore_nodata(_, fflow8, fareau):
        output = dem.upslope_pixels(fflow8, nodata=0)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:dfha.validate")
    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_check(_, fflow8, value):
        flow = load_raster(fflow8).astype(float)
        flow[0, 0] = value
        with pytest.raises(ValueError) as error:
            dem.upslope_pixels(flow)
        assert_contains(error, "flow_directions")

    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_nocheck(_, fflow8, value):
        flow = load_raster(fflow8).astype(float)
        flow[0, 0] = value
        dem.upslope_pixels(flow, check=False)


class TestUpslopeSum:
    def test_verbose(_, fflow8, fweights, capfd):
        dem.upslope_sum(fflow8, fweights, verbose=True)
        stdout = capfd.readouterr().out
        assert stdout != ""

    def test_quiet(_, fflow8, fweights, capfd):
        dem.upslope_sum(fflow8, fweights, verbose=False)
        stdout = capfd.readouterr().out
        assert stdout == ""

    def test_overwrite(_, fflow8, fweights, fareaw, tmp_path):
        area = tmp_path / "output.tif"
        save_raster(existing_raster, area)
        dem.upslope_sum(fflow8, fweights, path=area, overwrite=True)
        output = load_raster(area)
        expected = load_raster(fareaw)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fflow8, fweights, tmp_path):
        area = tmp_path / "output.tif"
        save_raster(existing_raster, area)
        with pytest.raises(FileExistsError):
            dem.upslope_sum(fflow8, fweights, path=area, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array(_, fflow8, fweights, fareaw, load_input):
        if load_input:
            fflow8 = load_raster(fflow8)
            fweights = load_raster(fweights)
        output = dem.upslope_sum(
            fflow8, fweights, flow_nodata=-32768, values_nodata=-999
        )
        expected = load_raster(fareaw)
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "upslope_sum.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save(_, fflow8, fweights, fareaw, tmp_path, load_input):
        if load_input:
            fflow8 = load_raster(fflow8)
            fweights = load_raster(fweights)
        area = tmp_path / "output.tif"
        output = dem.upslope_sum(
            fflow8, fweights, path=area, flow_nodata=-32768, values_nodata=-999
        )
        assert output == area
        output = load_raster(area)
        expected = load_raster(fareaw)
        assert np.array_equal(output, expected)

    def test_nodata(_, fflow8, fweights, fareaw):
        flow = load_raster(fflow8)
        output = dem.upslope_sum(flow, fweights, flow_nodata=-32768)
        expected = load_raster(fareaw)
        assert np.array_equal(output, expected)

    def test_ignore_nodata(_, fflow8, fweights, fareaw):
        output = dem.upslope_sum(fflow8, fweights, flow_nodata=0, values_nodata=2)
        expected = load_raster(fareaw)
        assert np.array_equal(output, expected)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:dfha.validate")
    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_check(_, fflow8, fweights, value):
        flow = load_raster(fflow8).astype(float)
        flow[0, 0] = value
        with pytest.raises(ValueError) as error:
            dem.upslope_sum(flow, fweights)
        assert_contains(error, "flow_directions")

    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_nocheck(_, fflow8, value, fweights):
        flow = load_raster(fflow8).astype(float)
        flow[0, 0] = value
        dem.upslope_sum(flow, fweights, check=False)

    @pytest.mark.parametrize("load_mask", (True, False))
    def test_mask(_, fflow8, fweights, fmask, faream, load_mask):
        if load_mask:
            fmask = load_raster(fmask)
            fmask[fmask == -1] = 0
        output = dem.upslope_sum(fflow8, fweights, fmask)
        expected = load_raster(faream)
        assert np.array_equal(output, expected)

    def test_mask_nodata(_, fflow8, fweights, fmask, faream):
        mask = load_raster(fmask)
        output = dem.upslope_sum(fflow8, fweights, mask, mask_nodata=-1)
        expected = load_raster(faream)
        assert np.array_equal(output, expected)

    def test_mask_ignore_nodata(_, fflow8, fweights, fmask, faream):
        output = dem.upslope_sum(fflow8, fweights, fmask, mask_nodata=-999)
        expected = load_raster(faream)
        assert np.array_equal(output, expected)

    def test_mask_check(_, fflow8, fweights, fmask):
        mask = load_raster(fmask)
        with pytest.raises(ValueError) as error:
            dem.upslope_sum(fflow8, fweights, mask)
        assert_contains(error, "mask")

    # Only need to test it runs. Output values are unconstrained when check=False
    def test_mask_nocheck(_, fflow8, fweights, fmask):
        mask = load_raster(fmask)
        dem.upslope_sum(fflow8, fweights, mask, check=False)


class TestRelief:
    def test_verbose(_, fpitfilled, fflowi, fslopesi, capfd):
        dem.relief(fpitfilled, fflowi, fslopesi, verbose=True)
        stdout = capfd.readouterr().out
        assert stdout != ""

    def test_quiet(_, fpitfilled, fflowi, fslopesi, capfd):
        dem.relief(fpitfilled, fflowi, fslopesi, verbose=False)
        stdout = capfd.readouterr().out
        assert stdout == ""

    def test_overwrite(_, fpitfilled, fflowi, fslopesi, frelief, tmp_path):
        relief = tmp_path / "output.tif"
        save_raster(existing_raster, relief)
        dem.relief(
            fpitfilled,
            fflowi,
            fslopesi,
            path=relief,
            overwrite=True,
            flow_nodata=fmin,
            slopes_nodata=-1,
        )
        output = load_raster(relief)
        expected = load_raster(frelief)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fpitfilled, fflowi, fslopesi, tmp_path):
        relief = tmp_path / "output.tif"
        save_raster(existing_raster, relief)
        with pytest.raises(FileExistsError):
            dem.relief(
                fpitfilled,
                fflowi,
                fslopesi,
                path=relief,
                overwrite=False,
                flow_nodata=fmin,
                slopes_nodata=-1,
            )

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array(_, fpitfilled, fflowi, fslopesi, frelief, load_input):
        if load_input:
            fpitfilled = load_raster(fpitfilled)
            fflowi = load_raster(fflowi)
            fslopesi = load_raster(fslopesi)
        output = dem.relief(
            fpitfilled,
            fflowi,
            fslopesi,
            flow_nodata=fmin,
            slopes_nodata=-1,
        )
        expected = load_raster(frelief)
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "relief.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save(_, fpitfilled, fflowi, fslopesi, frelief, tmp_path, load_input):
        if load_input:
            fpitfilled = load_raster(fpitfilled)
            fflowi = load_raster(fflowi)
            fslopesi = load_raster(fslopesi)
        relief = tmp_path / "output.tif"
        output = dem.relief(
            fpitfilled,
            fflowi,
            fslopesi,
            path=relief,
            flow_nodata=fmin,
            slopes_nodata=-1,
        )
        assert output == relief
        output = load_raster(relief)
        expected = load_raster(frelief)
        assert np.array_equal(output, expected)

    def test_nodata(_, fpitfilled, fflowi, fslopesi, frelief):
        flow = load_raster(fflowi)
        output = dem.relief(fpitfilled, flow, fslopesi, flow_nodata=fmin)
        expected = load_raster(frelief)
        assert np.array_equal(output, expected)

    def test_ignore_nodata(_, fpitfilled, fflowi, fslopesi, frelief):
        output = dem.relief(
            fpitfilled, fflowi, fslopesi, flow_nodata=0, slopes_nodata=0
        )
        expected = load_raster(frelief)
        assert np.array_equal(output, expected)
