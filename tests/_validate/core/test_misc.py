import os
from pathlib import Path

import pytest

import pfdf._validate.core._misc as validate
from pfdf.errors import DimensionError

#####
# Paths
#####


class TestInputPath:
    def test_str(_, tmp_path):
        file = Path(tmp_path) / "test.geojson"
        with open(file, "w") as f:
            f.write("test")
        output = validate.input_path(str(file), "")
        assert output == file

    def test_path(_, tmp_path):
        file = Path(tmp_path) / "test.geojson"
        with open(file, "w") as f:
            f.write("test")
        output = validate.input_path(file, "")
        assert output == file

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.input_path(5, "test file")
        assert_contains(error, "test file")

    def test_missing(_, tmp_path):
        file = Path(tmp_path) / "test.geojson"
        with pytest.raises(FileNotFoundError):
            validate.input_path(file, "")

    def test_folder(_, tmp_path, assert_contains):
        path = Path(tmp_path) / "test"
        os.mkdir(path)
        with pytest.raises(ValueError) as error:
            validate.input_path(path, "path")
        assert_contains(error, "path is not a file")


class TestOutputPath:
    def test_valid_string(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output = validate.output_path(str(path), overwrite=False)
        expected = Path(path)
        assert isinstance(output, Path)
        assert output == expected

    def test_valid_path(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        output = validate.output_path(path, overwrite=False)
        expected = Path(path)
        assert isinstance(output, Path)
        assert output == expected

    def test_valid_overwrite(_, tmp_path):
        path = Path(tmp_path) / "output.tif"
        with open(path, "w") as file:
            file.write("This file already exists")
        assert path.is_file()
        output = validate.output_path(path, overwrite=True)
        assert isinstance(output, Path)
        assert output == path

    def test_invalid(_):
        with pytest.raises(TypeError):
            validate.output_path(5, overwrite=False)

    def test_invalid_overwrite(_, tmp_path, assert_contains):
        path = Path(tmp_path) / "output.tif"
        with open(path, "w") as file:
            file.write("This file already exists")
        assert path.is_file()
        with pytest.raises(FileExistsError) as error:
            validate.output_path(path, overwrite=False)
        assert_contains(error, "Output file already exists")


#####
# Misc
#####


class TestOption:
    allowed = ["red", "green", "blue"]

    @pytest.mark.parametrize("input", ("red", "GREEN", "BlUe"))
    def test_valid(self, input):
        output = validate.option(input, "", self.allowed)
        assert output == input.lower()

    def test_not_string(self, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.option(5, "test name", self.allowed)
        assert_contains(error, "test name")

    def test_not_recognized(self, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.option("yellow", "test name", self.allowed)
        assert_contains(error, "test name", "yellow", "red, green, blue")


class TestType:
    def test_success(_):
        validate.type(5, "", int, "int")
        validate.type("test", "", str, "str")

    def test_fail(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.type(5, "test", str, "str")
        assert_contains(error, "test must be a str")


class TestConversion:
    def test_none(_):
        assert validate.conversion(None, "") is None

    def test_valid(_):
        assert validate.conversion(5, "") == 5

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.conversion(0, "dem_per_m")
        assert_contains(error, "dem_per_m must be greater than 0")
