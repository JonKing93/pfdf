from pathlib import Path

import pytest

import pfdf._validate.core._path as validate


class TestInputFile:
    def test_str(_, tmp_path):
        file = tmp_path / "test.geojson"
        file.write_text("test")
        output = validate.input_file(str(file))
        assert output == file

    def test_path(_, tmp_path):
        file = tmp_path / "test.geojson"
        file.write_text("test")
        output = validate.input_file(file)
        assert output == file

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.input_file(5)
        assert_contains(error, "path must be a filepath")

    def test_missing(_, tmp_path):
        file = tmp_path / "test.geojson"
        with pytest.raises(FileNotFoundError):
            validate.input_file(file)

    def test_folder(_, tmp_path, assert_contains):
        path = tmp_path / "test"
        path.mkdir()
        output = validate.input_file(path)
        assert output == path


class TestOutpuFile:
    def test_valid_string(_, tmp_path):
        path = tmp_path / "output.tif"
        output = validate.output_file(str(path), overwrite=False)
        expected = Path(path)
        assert isinstance(output, Path)
        assert output == expected

    def test_valid_path(_, tmp_path):
        path = tmp_path / "output.tif"
        output = validate.output_file(path, overwrite=False)
        expected = Path(path)
        assert isinstance(output, Path)
        assert output == expected

    def test_valid_overwrite(_, tmp_path):
        path = tmp_path / "output.tif"
        path.write_text("This file already exists")
        assert path.is_file()
        output = validate.output_file(path, overwrite=True)
        assert isinstance(output, Path)
        assert output == path

    def test_invalid(_):
        with pytest.raises(TypeError):
            validate.output_file(5, overwrite=False)

    def test_invalid_overwrite(_, tmp_path, assert_contains):
        path = tmp_path / "output.tif"
        path.write_text("This file already exists")
        assert path.is_file()
        with pytest.raises(FileExistsError) as error:
            validate.output_file(path, overwrite=False)
        assert_contains(error, "Output file already exists")


class TestOutputFolder:
    def test_default(_):
        output = validate.output_folder(None, default="test")
        assert output == Path.cwd() / "test"

    def test_not_exist(_):
        path = Path.cwd() / "does-not-exist"
        assert not path.exists()
        output = validate.output_folder(path.name, default="test")
        assert output == path

    def test_exists(_, tmp_path, assert_contains):
        path = tmp_path / "this-path-exists"
        path.mkdir()
        with pytest.raises(FileExistsError) as error:
            validate.output_folder(path, default="test")
        assert_contains(error, "`path` already exists")

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.output_folder(5, default="test")
        assert_contains(error, "path must be a filepath")
