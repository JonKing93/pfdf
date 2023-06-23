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

from pfdf import dem
from pfdf._rasters import Raster as _Raster
from pfdf.errors import DimensionError, ShapeError
from pfdf.rasters import NumpyRaster

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
    npr = NumpyRaster(araster, nodata=200)
    _Raster(npr).save(path)
    return path


# Saves a file-based raster
def file_raster(raster, dtype, folder, name, nodata=None):
    path = folder / (name + ".tif")
    raster = raster.astype(dtype)
    npr = NumpyRaster(raster, nodata=nodata)
    _Raster(npr).save(path)
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
        dem._validate_d8(False, "invalid")

    def test_pass(_, fflow8):
        flow = _Raster(fflow8)
        dem._validate_d8(True, flow)

    def test_fail(_, fflow8):
        flow = _Raster(fflow8)
        flow.nodata = None
        with pytest.raises(ValueError) as error:
            dem._validate_d8(True, flow)
        assert_contains(error, "flow_directions")


class TestValidateDinf:
    def test_nocheck(_):
        dem._validate_dinf(False, "invalid", "invalid")

    def test_pass(_, fflowi, fslopesi):
        flow = _Raster(fflowi)
        slopes = _Raster(fslopesi)
        dem._validate_dinf(True, flow, slopes)

    def test_fail_flow(_, fflowi, fslopesi):
        flow = _Raster(fflowi)
        slopes = _Raster(fslopesi)
        flow.nodata = None
        with pytest.raises(ValueError) as error:
            dem._validate_dinf(True, flow, slopes)
        assert_contains(error, "flow_directions")

    def test_fail_slopes(_, fflowi, fslopesi):
        flow = _Raster(fflowi)
        slopes = _Raster(fslopesi)
        slopes.nodata = None
        with pytest.raises(ValueError) as error:
            dem._validate_dinf(True, flow, slopes)
        assert_contains(error, "slopes")


class TestValidateMask:
    def test_pass(_, fmask):
        output = dem._validate_mask(True, fmask, shape=(3, 4))
        expected = np.array([[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0]]).astype(bool)
        assert np.array_equal(output, expected)

    def test_invalid_shape(_, fmask):
        with pytest.raises(ShapeError) as error:
            dem._validate_mask(False, fmask, shape=(10, 10))
        assert_contains(error, "mask")

    def test_invalid_raster(_):
        with pytest.raises(TypeError):
            dem._validate_mask(False, np, None)

    def test_invalid_elements(_, fmask):
        mask = _Raster(fmask)
        with pytest.raises(ValueError) as error:
            dem._validate_mask(True, mask.values, shape=(3, 4))  # missing NoData
        assert_contains(error, "mask")

    def test_nocheck(_, fmask):
        mask = _Raster(fmask)
        dem._validate_mask(False, mask.values, shape=(3, 4))


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
            dem._validate_inputs([True], ["test name"])
        assert_contains(error, "test name")

    def test_invalid_array(_):
        a = np.arange(0, 27).reshape(3, 3, 3)
        with pytest.raises(DimensionError) as error:
            dem._validate_inputs([a], ["test name"])
        assert_contains(error, "test name")

    def test_invalid_file(_):
        file = "not-a-file"
        with pytest.raises(FileNotFoundError):
            dem._validate_inputs([file], ["test name"])

    def test_invalid_shapes(_, araster):
        raster1 = araster
        raster2 = araster.reshape(-1)
        with pytest.raises(ShapeError) as error:
            dem._validate_inputs([raster1, raster2], ["test 1", "test 2"])
        assert_contains(error, "test 2")

    def test_valid_array(_, araster):
        rasters = dem._validate_inputs([araster], ["test name"])
        assert isinstance(rasters, list)
        assert len(rasters) == 1
        assert isinstance(rasters[0], _Raster)
        assert np.array_equal(rasters[0].values, araster)

    def test_valid_file(_, fraster):
        rasters = dem._validate_inputs([fraster], ["test 1"])
        assert isinstance(rasters, list)
        assert len(rasters) == 1
        assert isinstance(rasters[0], _Raster)
        assert rasters[0].path == fraster

    def test_multiple(_, araster, fraster):
        rasters = dem._validate_inputs([araster, fraster], ["test 1", "test 2"])
        assert isinstance(rasters, list)
        assert len(rasters) == 2

        assert isinstance(rasters[0], _Raster)
        assert np.array_equal(rasters[0].values, araster)
        assert isinstance(rasters[1], _Raster)
        assert rasters[1].path == fraster


class TestValidateOutput:
    @pytest.mark.parametrize("overwrite", (True, False))
    def test_none(_, overwrite):
        path, save = dem._validate_output(None, overwrite)
        assert path is None
        assert save == False

    def test_valid(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output, save = dem._validate_output(path, False)
        assert output == path.resolve()
        assert save == True

    def test_invalid(_):
        with pytest.raises(TypeError):
            dem._validate_output(5, True)

    def test_overwrite(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        _Raster(existing_raster).save(path)
        output, save = dem._validate_output(path, overwrite=True)
        assert output == path.resolve()
        assert save == True

    def test_invalid_overwrite(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        _Raster(existing_raster).save(path)
        with pytest.raises(FileExistsError):
            dem._validate_output(path, overwrite=False)


class TestPaths:
    @pytest.mark.filterwarnings("ignore::rasterio.errors.NotGeoreferencedWarning")
    def test(_, tmp_path, araster, fraster):
        output = dem._paths(
            tmp_path,
            names=["input-1", "input-2", "output-1", "output-2"],
            rasters=[_Raster(araster), _Raster(fraster), fraster, None],
        )

        assert isinstance(output, list)
        assert len(output) == 4
        assert isinstance(output, list)
        assert len(output) == 4
        assert output[0] == tmp_path / "input-1.tif"
        assert output[0].is_file()
        output0 = _Raster(output[0])
        assert np.array_equal(output0.values, araster)
        assert output[1] == fraster
        assert output[2] == fraster
        assert output[3] == tmp_path / "output-2.tif"

@pytest.mark.taudem
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
        output = dem._output(fraster, saved=False)
        assert np.array_equal(output.array, araster)

    def test_path(_, fraster):
        output = dem._output(fraster, saved=True)
        assert output == fraster


#####
# Low Level
#####

@pytest.mark.taudem
class TestPitRemove:
    def test(_, fdem, fpitfilled, tmp_path):
        pitfilled = tmp_path / "output.tif"
        assert not pitfilled.is_file()
        dem.pitremove(fdem, pitfilled, False)
        assert pitfilled.is_file()

        output = _Raster(pitfilled)
        expected = _Raster(fpitfilled)
        assert np.array_equal(output.values, expected.values)

@pytest.mark.taudem

class TestFlowD8:
    def test(_, fpitfilled, fflow8, fslopes8, tmp_path):
        flow = tmp_path / "output-1.tif"
        slopes = tmp_path / "output-2.tif"
        assert not flow.is_file()
        assert not slopes.is_file()
        dem.flow_d8(fpitfilled, flow, slopes, False)
        assert flow.is_file()
        assert slopes.is_file()

        output = _Raster(flow).values
        expected = _Raster(fflow8).values
        assert np.array_equal(output, expected)

        output = _Raster(slopes).values.astype(float)
        expected = _Raster(fslopes8).values.astype(float)
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

@pytest.mark.taudem

class TestFlowDinf:
    def test_flow_dinf(_, fpitfilled, fflowi, fslopesi, tmp_path):
        flow = tmp_path / "output-1.tif"
        slopes = tmp_path / "output-2.tif"
        assert not flow.is_file()
        assert not slopes.is_file()
        dem.flow_dinf(fpitfilled, flow, slopes, False)
        assert flow.is_file()
        assert slopes.is_file()

        output = _Raster(flow).values[1, 1:3]
        expected = _Raster(fflowi).values[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

        output = _Raster(slopes).values[1, 1:3].astype(float)
        expected = _Raster(fslopesi).values[1, 1:3].astype(float)
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

@pytest.mark.taudem

class TestAreaD8:
    def test_unweighted(_, fflow8, fareau, tmp_path):
        area = tmp_path / "output.tif"
        assert not area.is_file()
        dem.area_d8(fflow8, None, area, False)
        assert area.is_file()

        output = _Raster(area).values
        expected = _Raster(fareau).values
        assert np.array_equal(output, expected)

    def test_weighted(_, fflow8, fweights, fareaw, tmp_path):
        area = tmp_path / "output.tif"
        assert not area.is_file()
        dem.area_d8(fflow8, fweights, area, False)
        assert area.is_file()

        output = _Raster(area).values
        expected = _Raster(fareaw).values
        assert np.array_equal(output, expected)

@pytest.mark.taudem

class TestReliefDinf:
    def test(_, fpitfilled, fflowi, fslopesi, frelief, tmp_path):
        relief = tmp_path / "output.tif"
        assert not relief.is_file()
        dem.relief_dinf(fpitfilled, fflowi, fslopesi, relief, False)
        assert relief.is_file()

        output = _Raster(relief).values
        expected = _Raster(frelief).values
        assert np.array_equal(output, expected)


#####
# User Functions
#####

@pytest.mark.taudem

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
        _Raster(existing_raster).save(pitfilled)
        dem.pitfill(fdem, path=pitfilled, overwrite=True)
        output = _Raster(pitfilled).values
        expected = _Raster(fpitfilled).values
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fdem, tmp_path):
        pitfilled = tmp_path / "output.tif"
        _Raster(existing_raster).save(pitfilled)
        with pytest.raises(FileExistsError):
            dem.pitfill(fdem, path=pitfilled, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array(_, fdem, fpitfilled, load_input):
        if load_input:
            fdem = _Raster(fdem).values
        output = dem.pitfill(fdem).array
        expected = _Raster(fpitfilled).values
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "dem.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save(_, fdem, fpitfilled, tmp_path, load_input):
        if load_input:
            fdem = _Raster(fdem).values
        pitfilled = tmp_path / "output.tif"
        output = dem.pitfill(fdem, path=pitfilled)
        assert output == pitfilled
        output = _Raster(pitfilled).values
        expected = _Raster(fpitfilled).values
        assert np.array_equal(output, expected)

@pytest.mark.taudem

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
        _Raster(existing_raster).save(flow)
        dem.flow_directions("D8", fpitfilled, path=flow, overwrite=True)
        output = _Raster(flow).values
        expected = _Raster(fflow8).values
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fpitfilled, tmp_path):
        flow = tmp_path / "output.tif"
        _Raster(existing_raster).save(flow)
        with pytest.raises(FileExistsError):
            dem.upslope_pixels(fpitfilled, path=flow, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array8(_, fpitfilled, fflow8, load_input):
        if load_input:
            fpitfilled = _Raster(fpitfilled).values
        output = dem.flow_directions("D8", fpitfilled)
        expected = _Raster(fflow8).values
        assert np.array_equal(output.array, expected)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    def test_array8_slopes(_, fpitfilled, fflow8, fslopes8):
        output = dem.flow_directions("D8", fpitfilled, return_slopes=True)
        assert isinstance(output, tuple)
        assert len(output) == 2
        flow, slopes = output
        expected = _Raster(fflow8).values
        assert np.array_equal(flow.array, expected)
        expected = _Raster(fslopes8).values
        assert np.allclose(slopes.array, expected, rtol=0, atol=1e-7)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save8(_, fpitfilled, fflow8, tmp_path, load_input):
        if load_input:
            fpitfilled = _Raster(fpitfilled).values
        flow = tmp_path / "output.tif"
        output = dem.flow_directions("D8", fpitfilled, path=flow)
        assert output == flow
        output = _Raster(flow).values
        expected = _Raster(fflow8).values
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
        output = _Raster(flow_path).values
        expected = _Raster(fflow8).values
        assert np.array_equal(output, expected)
        assert slopes == slopes_path
        output = _Raster(slopes_path).values
        expected = _Raster(fslopes8).values
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_arrayI(_, fpitfilled, fflowi, load_input):
        if load_input:
            fpitfilled = _Raster(fpitfilled).values
        output = dem.flow_directions("DInf", fpitfilled).array[1, 1:3]
        expected = _Raster(fflowi).values[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    def test_arrayI_slopes(_, fpitfilled, fflowi, fslopesi):
        output = dem.flow_directions("DInf", fpitfilled, return_slopes=True)
        assert isinstance(output, tuple)
        assert len(output) == 2
        flow, slopes = output
        flow = flow.array[1, 1:3]
        slopes = slopes.array[1, 1:3]
        expected = _Raster(fflowi).values[1, 1:3]
        assert np.allclose(flow, expected, rtol=0, atol=1e-7)
        expected = _Raster(fslopesi).values[1, 1:3]
        assert np.allclose(slopes, expected, rtol=0, atol=1e-7)
        assert not (Path.cwd() / "flow_directions.tif").is_file()
        assert not (Path.cwd() / "slopes.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_saveI(_, fpitfilled, fflowi, tmp_path, load_input):
        if load_input:
            fpitfilled = _Raster(fpitfilled).values
        flow = tmp_path / "output.tif"
        output = dem.flow_directions("DInf", fpitfilled, path=flow)
        assert output == flow
        output = _Raster(flow).values[1, 1:3]
        expected = _Raster(fflowi).values[1, 1:3]
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
        output = _Raster(flow_path).values[1, 1:3]
        expected = _Raster(fflowi).values[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)
        assert slopes == slopes_path
        output = _Raster(slopes_path).values[1, 1:3]
        expected = _Raster(fslopesi).values[1, 1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

@pytest.mark.taudem

class TestUpslopePixels:
    def test_warnings(_, fflow8, capfd):
        _Raster(fflow8).values
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
        _Raster(existing_raster).save(area)
        dem.upslope_pixels(fflow8, path=area, overwrite=True)
        output = _Raster(area).values
        expected = _Raster(fareau).values
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fflow8, tmp_path):
        area = tmp_path / "output.tif"
        _Raster(existing_raster).save(area)
        with pytest.raises(FileExistsError):
            dem.upslope_pixels(fflow8, path=area, overwrite=False)

    def test_array(_, fflow8, fareau):
        output = dem.upslope_pixels(fflow8)
        expected = _Raster(fareau).values
        assert np.array_equal(output.array, expected)
        assert not (Path.cwd() / "upslope_pixels.tif").is_file()

    def test_save(_, fflow8, fareau, tmp_path):
        area = tmp_path / "output.tif"
        output = dem.upslope_pixels(fflow8, path=area)
        assert output == area
        output = _Raster(area).values
        expected = _Raster(fareau).values
        assert np.array_equal(output, expected)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:pfdf.validate")
    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_check(_, fflow8, value):
        flow = _Raster(fflow8).values.astype(float)
        flow[0, 0] = value
        with pytest.raises(ValueError) as error:
            dem.upslope_pixels(flow)
        assert_contains(error, "flow_directions")

    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_nocheck(_, fflow8, value):
        flow = _Raster(fflow8).values.astype(float)
        flow[0, 0] = value
        dem.upslope_pixels(flow, check=False)

@pytest.mark.taudem

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
        _Raster(existing_raster).save(area)
        dem.upslope_sum(fflow8, fweights, path=area, overwrite=True)
        output = _Raster(area).values
        expected = _Raster(fareaw).values
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fflow8, fweights, tmp_path):
        area = tmp_path / "output.tif"
        _Raster(existing_raster).save(area)
        with pytest.raises(FileExistsError):
            dem.upslope_sum(fflow8, fweights, path=area, overwrite=False)

    def test_array(_, fflow8, fweights, fareaw):
        output = dem.upslope_sum(fflow8, fweights)
        expected = _Raster(fareaw).values
        assert np.array_equal(output.array, expected)
        assert not (Path.cwd() / "upslope_sum.tif").is_file()

    def test_save(_, fflow8, fweights, fareaw, tmp_path):
        area = tmp_path / "output.tif"
        output = dem.upslope_sum(fflow8, fweights, path=area)
        assert output == area
        output = _Raster(area).values
        expected = _Raster(fareaw).values
        assert np.array_equal(output, expected)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning:pfdf.validate")
    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_check(_, fflow8, fweights, value):
        flow = _Raster(fflow8).values.astype(float)
        flow[0, 0] = value
        with pytest.raises(ValueError) as error:
            dem.upslope_sum(flow, fweights)
        assert_contains(error, "flow_directions")

    @pytest.mark.parametrize("value", (np.nan, np.inf, 0, 1.1, -3, 9))
    def test_nocheck(_, fflow8, value, fweights):
        flow = _Raster(fflow8).values.astype(float)
        flow[0, 0] = value
        dem.upslope_sum(flow, fweights, check=False)

    @pytest.mark.parametrize("load_mask", (True, False))
    def test_mask(_, fflow8, fweights, fmask, faream, load_mask):
        if load_mask:
            fmask = _Raster(fmask).values
            fmask[fmask == -1] = 0
        output = dem.upslope_sum(fflow8, fweights, fmask)
        expected = _Raster(faream).values
        assert np.array_equal(output.array, expected)

    def test_mask_check(_, fflow8, fweights, fmask):
        mask = _Raster(fmask).values
        with pytest.raises(ValueError) as error:
            dem.upslope_sum(fflow8, fweights, mask)
        assert_contains(error, "mask")

    # Only need to test it runs. Output values are unconstrained when check=False
    def test_mask_nocheck(_, fflow8, fweights, fmask):
        mask = _Raster(fmask).values
        dem.upslope_sum(fflow8, fweights, mask, check=False)

@pytest.mark.taudem

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
        _Raster(existing_raster).save(relief)
        dem.relief(fpitfilled, fflowi, fslopesi, path=relief, overwrite=True)
        output = _Raster(relief).values
        expected = _Raster(frelief).values
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fpitfilled, fflowi, fslopesi, tmp_path):
        relief = tmp_path / "output.tif"
        _Raster(existing_raster).save(relief)
        with pytest.raises(FileExistsError):
            dem.relief(fpitfilled, fflowi, fslopesi, path=relief, overwrite=False)

    def test_array(_, fpitfilled, fflowi, fslopesi, frelief):
        output = dem.relief(fpitfilled, fflowi, fslopesi)
        expected = _Raster(frelief).values
        assert np.array_equal(output.array, expected)
        assert not (Path.cwd() / "relief.tif").is_file()

    def test_save(_, fpitfilled, fflowi, fslopesi, frelief, tmp_path):
        relief = tmp_path / "output.tif"
        output = dem.relief(fpitfilled, fflowi, fslopesi, path=relief)
        assert output == relief
        output = _Raster(relief).values
        expected = _Raster(frelief).values
        assert np.array_equal(output, expected)
