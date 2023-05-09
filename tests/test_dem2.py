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



def file_raster(folder, name, raster, nodata):
    path = folder / name
    write_raster(raster, path, nodata)
    return path
    


@pytest.fixture
def fdem(tmp_path):
    dem = np.array([[4, 5, 6, 6], [5, 1, 4, 5], [3, 2, 3, 4]]).astype('float32')
    path = tmp_path / "dem.tif"
    write_raster(dem, path)
    return path


@pytest.fixture
def fpitfilled(tmp_path):
    pitfilled = np.array(
        [
            [4, 5, 6, 6],
            [5, 2, 4, 5],
            [3, 2, 3, 4],
        ]
    ).astype('float32')
    path = tmp_path / "pitfilled.tif"
    write_raster(pitfilled, path)
    return path


@pytest.fixture
def fflow8(tmp_path):
    fill = -32768
    flow = np.array(
        [[fill, fill, fill, fill], [fill, 7, 5, fill], [fill, fill, fill, fill]]
    ).astype('int16')
    path = tmp_path / "flow8.tif"
    write_raster(flow, path, nodata=fill)
    return path


@pytest.fixture
def fslopes8(tmp_path):
    slopes = np.array([[-1, -1, -1, -1], [-1, 0, 0.000599734, -1], [-1, -1, -1, -1]]).astype('float32')
    path = tmp_path / "slopes8.tif"
    write_raster(slopes, path, nodata=-1)
    return path


# D-infinity flow directions
@pytest.fixture
def fflowi(tmp_path):
    fill = -3.4028235e38
    slopes = np.array(
        [
            [fill, fill, fill, fill],
            [fill, 4.7123890, 3.1415927, fill],
            [fill, fill, fill, fill],
        ]
    ).astype('float32')
    path = tmp_path / "slopesi.tif"
    write_raster(slopes, path, nodata=fill)
    return path


# D-infinity slopes are the same as D8 for this simple example
@pytest.fixture
def fslopesi(fslopes8):
    return fslopes8


# Unweighted upslope area
@pytest.fixture
def fareau(tmp_path):
    area = np.array([
        [-1,-1,-1,-1],
        [-1, 2, 1,-1],
        [-1,-1,-1,-1]
    ]).astype('float32')
    path = tmp_path / "area_unweighted.tif"
    write_raster(area, path, nodata=-1)
    return path


# # Area weights
# @pytest.fixture
# def fweights(tmp_path):
#     fill = -999
#     weights = np.array([
#         [fill, fill, fill, fill],
#         [fill, 2, 6, fill],
#         [fill, fill, fill, fill]
#     ])
#     path = tmp_path / "weights.tif"
#     write_raster(weights, path)
#     return path

# # Weighted area
# @pytest.fixture
# def fareaw(tmp_path):
#     fill = -999
#     area = np.array([
#         [fill, fill, fill, fill],
#         [fill, 8, 6, fill],
#         [fill, fill, fill, fill]
#     ])
#     path = tmp_path / "area_weighted.tif"
#     write_raster(area, path)
#     return path



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

        output = load_raster(flow)[1,1:3]
        expected = load_raster(fflowi)[1,1:3]
        assert np.allclose(output, expected, rtol=0, atol=1e-7)

        output = load_raster(slopes)[1,1:3].astype(float)
        expected = load_raster(fslopesi)[1,1:3].astype(float)
        assert np.allclose(output, expected, rtol=0, atol=1e-7)


class TestAreaD8:
    def test_unweighted(_, fflow8, fareau, tmp_path):
        flow1 = '../flow8.tif'
        flow2 = fflow8

        area1 = tmp_path / "output1.tif"
        area2 = tmp_path / "output2.tif"

        dem.area_d8(flow1, None, area1, True)
        dem.area_d8(flow2, None, area2, True)

        area1 = load_raster(area1)
        area2 = load_raster(area2)

        print(area1)
        print(area2)
        print(np.array_equal(area1, area2))
        assert False




        area = tmp_path / "output.tif"
        dem.area_d8(flow, None, area, False)

        flow = load_raster(flow)
        print(flow)

        output = load_raster(area)
        print(output)
        assert False




