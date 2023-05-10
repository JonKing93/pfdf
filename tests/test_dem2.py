"""
test_dem2  Unit tests for the dem module with updated backend
"""

import pytest, subprocess
import numpy as np
from pathlib import Path
from dfha import dem, validate
from dfha.utils import write_raster, load_raster

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
    write_raster(araster, path)
    return path


# Saves a file-based raster
def file_raster(raster, dtype, folder, name, nodata=None):
    path = folder / (name + ".tif")
    raster = raster.astype(dtype)
    write_raster(raster, path, nodata)
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
    return filled_raster(
        "float32", tmp_path, "slopes8", center=[0, 0.000599734], fill=-1
    )


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


# Weighted area
@pytest.fixture
def fareaw(tmp_path):
    return filled_raster("float32", tmp_path, "area_weighted", center=[8, 6], fill=-1)


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
        with pytest.raises(validate.DimensionError) as error:
            dem._validate_inputs([a], ["test name"])
        assert_contains(error, "test name")

    def test_invalid_file(_):
        file = "not-a-file"
        with pytest.raises(FileNotFoundError) as error:
            dem._validate_inputs([file], ["test name"])

    def test_invalid_shapes(_, araster):
        raster1 = araster
        raster2 = araster.reshape(-1)
        with pytest.raises(validate.ShapeError) as error:
            dem._validate_inputs([raster1, raster2], ["test 1", "test 2"])
        assert_contains(error, "test 2")

    def test_valid_array(_, araster):
        output = dem._validate_inputs([araster], ["test name"])
        assert isinstance(output, list)
        assert len(output) == 1
        assert np.array_equal(output[0], araster)

    def test_valid_file(_, fraster):
        output = dem._validate_inputs([fraster], ["test 1", "test 2"])
        assert isinstance(output, list)
        assert len(output) == 1
        assert np.array_equal(output[0], fraster)

    def test_multiple(_, araster, fraster):
        output = dem._validate_inputs([araster, fraster], ["test 1", "test 2"])
        assert isinstance(output, list)
        assert len(output) == 2
        assert np.array_equal(output[0], araster)
        assert np.array_equal(output[1], fraster)


class TestNoData:
    def test_file(_, fdem):
        output = dem._nodata(["ignore me"], ["test name"], [fdem])
        assert output == ["ignore me"]

    @pytest.mark.parametrize("value", (np.nan, np.inf, 5, -999))
    def test_valid(_, fdem, value):
        raster = load_raster(fdem)
        output = dem._nodata([value], ["test name"], [raster])
        expected = validate.scalar(value, "")
        assert np.array_equal(output, [expected], equal_nan=True)

    def test_none(_, fdem):
        raster = load_raster(fdem)
        output = dem._nodata([None], ["test name"], raster)
        assert output == [None]

    # NaN (floating) should convert to 0 for integer rasters
    def test_converted(_, fflow8):
        raster = load_raster(fflow8)
        output = dem._nodata([np.nan], 'test name', [raster])
        assert output == [0]

    def test_nonscalar(_, fdem):
        raster = load_raster(fdem)
        with pytest.raises(validate.DimensionError) as error:
            dem._nodata([raster], ["test name"], [raster])
            assert_contains(error, "test name")

    def test_not_real(_, fdem):
        raster = load_raster(fdem)
        with pytest.raises(TypeError) as error:
            dem._nodata([True], ["test name"], [raster])
            assert_contains(error, "test name")

    def test_mixed_valid(_, fdem):
        raster = load_raster(fdem)
        rasters = [raster, raster, fdem]
        values = [None, -999, "ignored"]
        output = dem._nodata(values, ["", "", ""], rasters)
        assert output == values

    def test_mixed_invalid(_, fdem):
        raster = load_raster(fdem)
        rasters = [raster, raster, fdem]
        with pytest.raises(TypeError) as error:
            dem._nodata(
                [5, "invalid", "ignored"],
                ["test1", "test2", "test3"],
                rasters,
            )
            assert_contains(error, "test2")


class TestValidateOutput:
    @pytest.mark.parametrize("input", (True, 5, np.arange(0, 100)))
    def test_invalid(_, input):
        with pytest.raises(TypeError):
            dem._validate_output(input, True)

    def test_invalid_overwrite(_, fraster):
        with pytest.raises(FileExistsError):
            dem._validate_output(fraster, overwrite=False)

    @pytest.mark.parametrize("overwrite", (True, False))
    def test_none(_, overwrite):
        path, save = dem._validate_output(None, overwrite)
        assert path is None
        assert save == False

    @pytest.mark.parametrize(
        "path", ("some-file", "some-file.tif", "some-file.tiff", "some-file.TiFf")
    )
    def test_valid(_, path):
        output, save = dem._validate_output(path, True)
        assert output == Path("some-file.tif")
        assert save == True

    def test_valid_overwrite(_, fraster):
        output, save = dem._validate_output(fraster, True)
        assert output == fraster
        assert save == True


class TestPaths:
    def test(_, tmp_path, araster, fraster):
        output = dem._paths(
            tmp_path,
            rasters=[araster, fraster, fraster, None],
            save=[None, None, True, False],
            names=["input-1", "input-2", "output-1", "output-2"],
        )

        assert isinstance(output, list)
        assert len(output) == 4
        assert output[0] == tmp_path / "input-1.tif"
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
        write_raster(existing_raster, pitfilled)
        dem.pitfill(fdem, path=pitfilled, overwrite=True)
        output = load_raster(pitfilled)
        expected = load_raster(fpitfilled)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fdem, tmp_path):
        pitfilled = tmp_path / "output.tif"
        write_raster(existing_raster, pitfilled)
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


class TestUpslopePixels:
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
        write_raster(existing_raster, area)
        dem.upslope_pixels(fflow8, path=area, overwrite=True)
        output = load_raster(area)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)

    def test_invalid_overwrite(_, fflow8, tmp_path):
        area = tmp_path / "output.tif"
        write_raster(existing_raster, area)
        with pytest.raises(FileExistsError):
            dem.upslope_pixels(fflow8, path=area, overwrite=False)

    @pytest.mark.parametrize("load_input", (True, False))
    def test_array(_, fflow8, fareau, load_input):
        if load_input:
            fflow8 = load_raster(fflow8)
            fill = np.nonzero(fflow8) == -32768
            fflow8[np.nonzero(fill)] = np.nan
        output = dem.upslope_pixels(fflow8)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)
        assert not (Path.cwd() / "dem.tif").is_file()

    @pytest.mark.parametrize("load_input", (True, False))
    def test_save(_, fflow8, fareau, tmp_path, load_input):
        if load_input:
            fflow8 = load_raster(fflow8)
        area = tmp_path / "output.tif"
        output = dem.upslope_pixels(fflow8, path=area)
        assert output == area
        output = load_raster(area)
        expected = load_raster(fareau)
        assert np.array_equal(output, expected)
