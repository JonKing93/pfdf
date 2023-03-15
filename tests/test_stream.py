"""
test_stream  Unit tests for the stream module
----------
The tests for the stream module are grouped into classes. Each class holds the
tests for one function in the stream module. Tests progress from module 
utilites, to low-level functions, to high-level user-facing functions.

The tests rely on scientifically validated outputs from several test fires. 
Each test fire has two associated geodatabases. "validated.gdb" contains input
files required to run the tests, as well as validated output files. (Note that
some validated output files are also used as inputs to later functions). The
"test-output.gdb" geodatabase serves to hold the outputs of the tests. The files
in these geodatabases are overwritten when the tests are run, and the files in
"test-output.gdb" are then compared to the validated files in "validated.gdb".

REQUIREMENTS:
Running these tests requires:
    * 
    * The ArcPy package shipped with ArcGIS Pro 3.0 (Build number 36056).

RUNNING THE TESTS:
To run the tests, you should:
    * Download the validated test data from: !!! INSERT LINK HERE !!!
    * 



gdb" geodatabase is based
on a run of the original hazard assessment code for the COL2022 fire. This input
geodatabase holds (1) data inputs to the code, and (2) output files created by
that original run. The data inputs serve as inputs to these tests, and the
output files provide expected outputs against which the stream module is tested.
The "stream_outputs.gdb" geodatabase holds the outputs of the tests. The files
in this geodatabase are overwritten when the tests are run and the resulting
files compared to the expected values in "stream-inputs.gdb".

Many of the tests in this module rely on the validate_output_files decorator.
This decorator checks that test functions successfully create output files, and
that the contents of the output files match the expected values.

DEPENDENCIES:
    This module requires the arcpy package shipped with ArcGIS Pro 3.0 (Build 
    number 36056).
"""

import sys, functools, pytest
from pathlib import Path
from typing import List, Union, Optional
import arcpy

# Add parent folder to path and import stream module
here = Path(__file__)
sys.path.append(here.parent)
import stream

# Locate test geodatabases
data = here / "data"
fires = [data / "col2022.gdb"]
output = data / "test-outputs.gdb"

# Naming scheme for geodatabase files
total_area = "total_area"
burned_area = "burned_area"
flow_direction = "flow_direction"
stream_links = "stream_links"
raster_unsplit = "stream_raster_unsplit"
split_points = "split_points"
split_links = "split_links"
raster_split = "stream_raster_split"

# Organize test fires as a list of dicts mapping layer names to full paths
files = [total_area, burned_area, flow_direction, stream_links, raster_unsplit,
          split_points, split_links, raster_split]
for f, gdb in enumerate(fires):
    fire = {file: str(gdb/file) for file in files}
    fires[f] = fire

# Set arcpy to overwrite testing outputs
arcpy.env.overwriteOutput = True

# Testing parameters
min_basin_area = 250
min_burned_area = 100
max_segment_length = 500
search_radius = 2

# Type alias
strs: Union[str, List[str]]

# Utility to validate output files
def validate_outputs(fire: dict, files: strs, raster: Optional[int] = None) -> None:
    """
    validate_outputs  Check that output file values match validated outputs
    ----------
    validate_outputs(fire, files)
    Validates each of the listed files in the testing output geodatabase. First
    checks that each file exists in the testing output. Then, checks that the
    values in each output file match the validated output values for the fire.
    Raises an AssertionError if these conditions are not met. This syntax treats
    all listed files as feature layers.

    validate_output(fire, files, raster)
    Indicate that one of the listed files is a raster layer.
    ----------
    Inputs:
        fire (dict): The dict for the test fire being validated
        files (str | List[str]): The list of output files to validate
        raster (int): The index of the raster layer in the list of files

    Raises:
        Assertion error if an output file does not exist or if the file values
        do not match the expected values.

    Returns: None
    """

    # Group files in list. Note whether each file is raster
    if isinstance(files, str):
        files = [files]
    israster = [False] * len(files)
    if raster is not None:
        israster[raster] = True

    # Check each output file exists and that the file's values are identical to
    # the validated outputs
    for file, israster in zip(files, israster):
        assert arcpy.Exists(file), f"Output file does not exist: {file}"

        if israster:
            expected = arcpy.RasterToNumpyArray(fire[file])
            produced = arcpy.RasterToNumpyArray(output[file])
            ismatch = numpy.array_equal(expected, produced, equal_nan=True)
        else:
            expected = arcpy.da.FeatureClassToNumPyArray(fire[file], "SHAPE@WKT")
            produced = arcpy.da.FeatureClassToNumPyArray(output[file], "SHAPE@WKT")
            ismatch = numpy.array_equal(expected, produced)
        assert ismatch, f"Output file values do not match expected values\nFile: {file}"

# Utility to delete output files
def delete(files: str) -> None:
    """
    delete  Deletes files from the testing output geodatabase
    ----------
    delete(*files)
    Deletes the listed files from the testing geodatabase.
    ----------
    Inputs:
        files (str): Each file to delete from the testing geodatabase
        
    Returns: None
    """
    if isinstance(files, str):
        files = [files]
    for file in files:
        arcpy.management.Delete(output[file])
        
# Base class for tests that check multiple fires
@pytest.mark.parametrize("fire", fires)
class CheckAllFires:
    pass

# Base class for tests that rely on raster properties
class UsesRaster:
    raster = fires[0][total_area]


###
# Tests for Module Utilities
###
class TestCheckSplitPaths:
    @pytest.mark.parametrize(
        "split_points",
        "split_links",
        [(None, "a/path"), ("a/path", None), (None, None)],
    )
    def test_missing_paths(_, split_points, split_links):
        with pytest.raises(ValueError):
            stream.check_split_paths(split_points, split_links)

    def test_have_both(_):
        split_points = "a/path"
        split_links = "another/path"
        output = stream.check_split_paths(split_points, split_links)
        assert output is None


class TestRasterSize(UsesRaster):
    def test_height(self):
        resolution = stream.raster_size(self.raster, "CELLSIZEX")
        assert resolution == 10

    def test_width(self):
        resolution = stream.raster_size(self.raster, "CELLSIZEY")
        assert resolution == 10


###
# Tests of Low-level Functions
###
class TestLinks(CheckAllFires):
    def test(_, fire):
        delete(stream_links)
        out = stream.links(fire[total_area], min_basin_area,
                           fire[burned_area], min_burned_area,
                           fire[flow_direction], output[stream_links])
        assert out is None
        validate_outputs(fire, stream_links)


class TestSplit(CheckAllFires):
    def test(_, fire):
        outputs = [split_points, split_links]
        delete(outputs)
        out = stream.split(fire[stream_links], max_segment_length,
                           search_radius,
                           output[split_points], output[split_links])
        assert out is None
        validate_outputs(fire, outputs)


class TestSearchRadius(UsesRaster):
    def test_default(self):
        radius = stream.search_radius(self.raster)
        assert radius == 2

    @pytest.mark.parametrize(
        "divisor,expected_radius", [(10, 1), (5, 2), (2, 5), (1, 10)]
    )
    def test_divisor(self, divisor, expected_radius):
        radius = stream.search_radius(self.raster, divisor)
        assert radius == expected_radius


class TestRaster(CheckAllFires):
    def test(_, fire):
        delete(raster_unsplit)
        out = stream.raster(fire[stream_links], output[raster_unsplit])
        assert out is None
        validate_outputs(fire, raster_unsplit, raster=0)


###
# Test of High-level user-facing functions
###
class TestNetwork(CheckAllFires):
    israster = [False, True]

    # Validate the output dict of final stream paths
    def check_dict(output, feature, raster):
        assert isinstance(output, dict), "output is not a dict"
        keys = output.keys
        assert len(keys)==2, "output must have exactly 2 keys"
        assert "feature" in keys, "'feature' must be a key in the output dict"
        assert "raster" in keys, "'raster' must be a key in the output dict"
        assert output['feature']==feature, f"The output feature path is incorrect\nExpected: {feature}\nReturned: {output['feature']}"
        assert output['raster']==raster, f"The output raster path is incorrect\nExpected: {raster}\nReturned: {output['raster']}"

    # Standard run without segment splitting
    def test_no_split(self, fire):
        outputs = [stream_links, raster_unsplit]
        delete(outputs)
        out = stream.network(fire[total_area], min_basin_area,
                             fire[burned_area], min_burned_area,
                             fire[flow_direction],
                             output[stream_links], output[raster_unsplit])
        self.check_dict(out, stream_links, raster_unsplit)
        validate_outputs(fire, outputs, raster=1)

    # Standard run with segment splitting
    def test_split(self, fire):
        outputs = [stream_links, split_points, split_links, raster_split]
        delete(outputs)
        out = stream.network(fire[total_area], min_basin_area,
                             fire[burned_area], min_burned_area,
                             fire[flow_direction],
                             output[stream_links], output[raster_split],
                             max_segment_length, output[split_points], output[split_links])
        self.check_dict(out, split_links, raster_split)
        validate_outputs(fire, outputs, raster=3)

    # Ignore splitting paths when there is no maxlength
    def test_ignore_splitting_paths(self, fire):
        outputs = [stream_links, raster_unsplit]
        delete(outputs)
        out = stream.network(fire[total_area], min_basin_area,
                             fire[burned_area], min_burned_area,
                             fire[flow_direction],
                             output[stream_links], output[raster_split],
                             None, output[split_points], output[split_links])
        self.check_dict(out, stream_links, raster_unsplit)
        validate_outputs(fire, outputs, raster=1)

    # ValueError if maxlength is set, but splitting paths are missing
    def test_missing_path(_, fire):
        with pytest.rases(ValueError):
            out = stream.network(fire[total_area], min_basin_area,
                                 fire[burned_area], min_burned_area,
                                 fire[flow_direction],
                                 output[stream_links], output[raster_split],
                                 max_segment_length, None, None)
