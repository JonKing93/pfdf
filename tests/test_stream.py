"""
test_stream  Unit tests for the stream module
----------
The tests for the stream module are grouped into classes. Each class holds the
tests for one function in the stream module. Tests progress from module 
utilites, to low-level functions, to high-level user-facing functions.

The tests rely on two geodatabases. The "stream-inputs.gdb" geodatabase is based
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

import functools
from typing import Optional, List, Callable, Union
import pytest
import stream
from pathlib import Path
import arcpy
import numpy

# Type aliases
strs = Union[str, List[str]]
bools = Union[bool, List[bool]]

# Locate testing geodatabase layers
in_gdb = Path.cwd() / "stream-inputs.gdb"
out_gdb = Path.cwd() / "stream-outputs.gdb"

output = [
    "stream_links",
    "split_points",
    "split_links",
    "stream_raster_split",
    "stream_raster_unsplit",
]
input = ["total_area", "burned_area", "flow_direction"] + output

output = {name: str(out_gdb / name) for name in output}
input = {name: str(in_gdb / name) for name in input}

# Testing parameters
min_basin_area = 250
min_burned_area = 100
max_segment_length = 500
search_radius = 2

# Overwrite files in output geodatabase
arcpy.env.overwriteOutput = True

# Utility decorators to validate output files and paths
def output_files(files: strs, israster: Optional[bools] = None) -> Callable:
    """
    validate_output_files  Decorator for validating output files.
    ----------
    @validate_output_files(files)
    test_function(*args, **kwargs)
    Deletes the files from the output geodatabase before running the test
    function. After the test completes, checks that the files have been created
    in the output geodatabase and that the file values are identical to the
    values in the corresponding layers of the input geodatabase. Returns the
    test function output after these checks. This syntax requires all output
    files to be feature layers.

    @validate_output_files(files, israster)
    test_function(*args, **kwargs)
    Also specify whether each output file is a raster or feature layer. This
    syntax permits output files that include raster layers.
    ----------
    Inputs:
        files (str | List[str]): A list of output files created by the test function
        israster (bool | List[bool]): A list with one element per output file. Each
            element is a bool that indicates whether the corresponding file is
            a raster layer (True) or feature layer (False). If unspecified, each
            output file is treated as a feature layer.

    Outputs:
        Callable: A decorator for the test function.
    """

    # Default for israster. Group files and israster in lists if not already
    if israster is None:
        israster = [False] * len(files)
    elif isinstance(israster, bool):
        israster = [israster]
    if isinstance(files, str):
        files = [files]

    # Create the decorator and wrapper
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # Delete the files
            for file in files:
                delete(file)

            # Run the test
            output = func(*args, **kwargs)

            # Check each file exists and has expected values
            for file, is_raster in zip(files, israster):
                assert exists(file), f"Did not create output file: {file}"
                if is_raster:
                    ismatch = equal_rasters(file)
                else:
                    ismatch = equal_features(file)
                assert ismatch, f"{file} does not match expected values"

            return output

        return wrapper

    return decorator


def final_paths(feature: str, raster: str) -> Callable:
    """
    final_paths  Check that final paths match expected outputs
    ----------
    @final_paths(feature, raster)
    test_function(*args, **kwargs)
    Checks that the output of the test function is a dict consisting only of the
    two keys 'feature' and 'raster'. Checks that the values of the two keys are
    the expected final paths to the raster and feature layer. The function will
    return the dict of final paths as output.
    ----------
    Inputs:
        feature (str): The expected path to the final feature layer
        raster (str): The expected path to the final raster layer

    Outputs:
        A decorator for the test function.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            final = func(*args, **kwargs)
            assert isinstance(final, dict), "Final paths not returned as dict"

            keys = final.keys()
            assert len(keys) == 2, "Final paths must only have 2 keys"
            assert "feature" in keys, "'feature' must be a final path key"
            assert "raster" in keys, "'raster' must be a final path key"

            assert (
                final["feature"] == output[feature]
            ), f"Final feature path does not match expected value."
            assert (
                final["raster"] == output[raster]
            ), f"Final raster path does not match its expected value"
            return final

        return wrapper

    return decorator


# Decorator utility functions
def delete(name: str) -> None:
    """Deletes a layer from the output geodatabase"""
    arcpy.management.Delete(output[name])


def exists(name: str) -> bool:
    """True if a layer exists in the output geodatabase"""
    return arcpy.Exists(output[name])


def equal_rasters(name: str) -> bool:
    """True if an output raster has identical values to the input raster of the same name"""
    expected = arcpy.RasterToNumPyArray(input[name])
    produced = arcpy.RasterToNumPyArray(output[name])
    return numpy.array_equal(expected, produced, equal_nan=True)


def equal_features(name: str) -> bool:
    """True if an output feature has identical value to the input feature of the same name"""
    expected = arcpy.da.FeatureClassToNumPyArray(input[name], "SHAPE@WKT")
    produced = arcpy.da.FeatureClassToNumPyArray(output[name], "SHAPE@WKT")
    return numpy.array_equal(expected, produced)


# Tests for stream module utilities
class TestCheckSplitPaths:
    @pytest.mark.parametrize(
        "split_points",
        "split_links",
        [(None, "a/path"), ("a/path", None), ("a/path", "another/path")],
    )
    @staticmethod
    def test_missing_paths(split_points, split_links):
        with pytest.raises(ValueError):
            stream.check_split_paths(split_points, split_links)

    @staticmethod
    def test_have_both():
        split_points = "a/path"
        split_links = "another/path"
        output = stream.check_split_paths(split_points, split_links)
        assert output is None


class TestRasterSize:
    raster = input["total_area"]

    def test_height(self):
        resolution = stream.raster_size(self.raster, "CELLSIZEX")
        assert resolution == 10

    def test_width(self):
        resolution = stream.raster_size(self.raster, "CELLSIZEY")
        assert resolution == 10


# Tests for low-level functions
class TestLinks:
    @staticmethod
    @output_files("stream_links")
    def test():
        out = stream.links(
            input["total_area"],
            min_basin_area,
            input["burned_area"],
            min_burned_area,
            input["flow_direction"],
            output["stream_links"],
        )
        assert out is None


class TestSplit:
    @staticmethod
    @output_files(["split_points", "split_links"])
    def test():
        out = stream.split(
            input["stream_links"],
            max_segment_length,
            search_radius,
            output["split_points"],
            output["split_links"],
        )
        assert out is None


class TestSearchRadius:
    raster = input["total_area"]

    def test_default(self):
        radius = stream.search_radius(self.raster)
        assert radius == 2

    @pytest.mark.parametrize(
        "divisor,expected_radius", [(10, 1), (5, 2), (2, 5), (1, 10)]
    )
    def test_divisor(self, divisor, expected_radius):
        radius = stream.search_radius(self.raster, divisor)
        assert radius == expected_radius


class TestRaster:
    @staticmethod
    @output_files("stream_raster_unsplit", israster=True)
    def test():
        out = stream.raster(input["stream_links"], output["stream_raster_unsplit"])
        assert out is None


# Tests for high-level user functions
class TestNetwork:
    israster = [False, True]

    # A standard run with no segment splitting
    @staticmethod
    @output_files(["stream_links", "stream_raster_unsplit"], israster)
    @final_paths("stream_links", "stream_raster_unsplit")
    def test_no_split():
        return stream.network(
            input["total_area"],
            min_basin_area,
            input["burned_area"],
            min_burned_area,
            input["flow_direction"],
            output["stream_links"],
            output["stream_raster_unsplit"],
        )

    # A standard run with segment splitting
    @staticmethod
    @output_files(["split_links", "stream_raster_split"], israster)
    @final_paths("split_links", "stream_raster_split")
    def test_split():
        return stream.network(
            input["total_area"],
            min_basin_area,
            input["burned_area"],
            min_burned_area,
            input["flow_direction"],
            output["stream_links"],
            output["stream_raster_split"],
            max_segment_length,
            output["split_points"],
            output["split_links"],
        )

    # Splitting paths should be ignored when there is no maxlength
    @staticmethod
    @output_files(["stream_links", "stream_raster_unsplit"], israster)
    @final_paths("stream_links", "stream_raster_unsplit")
    def test_splitpaths_but_no_maxlength():
        return stream.network(
            input["total_area"],
            min_basin_area,
            input["burned_area"],
            min_burned_area,
            input["flow_direction"],
            output["stream_links"],
            output["stream_raster_unsplit"],
            None,
            output["split_points"],
            output["split_links"],
        )

    # Throw an error when maxlength is specified, but splitting paths are missing
    @staticmethod
    def test_split_missing_path():
        with pytest.raises(ValueError):
            return stream.network(
                input["total_area"],
                min_basin_area,
                input["burned_area"],
                min_burned_area,
                input["flow_direction"],
                output["stream_links"],
                output["stream_raster_split"],
                max_segment_length,
                None,
                output["split_links"],
            )
