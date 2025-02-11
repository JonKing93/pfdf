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


class TestDownloadPath:
    def test_default(_):
        output = validate.download_path(
            None, None, default_name="test.tif", overwrite=False
        )
        assert output == Path.cwd() / "test.tif"

    def test_not_exist(_, tmp_path):
        parent = tmp_path
        name = "does-not-exist.tif"
        output = validate.download_path(
            parent, name, default_name="other-name", overwrite=False
        )
        assert output == parent / name

    def test_valid_overwrite(_, tmp_path):
        parent = tmp_path
        name = "test.tif"
        path = parent / name
        path.write_text("This file exists")

        output = validate.download_path(parent, name, default_name="", overwrite=True)
        assert output == path

    def test_invalid_overwrite(_, tmp_path, assert_contains):
        parent = tmp_path
        name = "test.tif"
        path = parent / name
        path.write_text("This file exists")

        with pytest.raises(FileExistsError) as error:
            validate.download_path(parent, name, "", overwrite=False)
        assert_contains(error, "Download path already exists")

    def test_invalid_overwrite_path_type(_, tmp_path, assert_contains):
        parent = tmp_path
        name = "test"
        path = parent / name
        path.mkdir()

        with pytest.raises(FileExistsError) as error:
            validate.download_path(parent, name, "", overwrite=True)
        assert_contains(
            error, "Cannot overwrite because the current path is not a file"
        )

    def test_invalid_parent(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.download_path(5, None, default_name="test", overwrite=False)
        assert_contains(error, "parent must be a path")

    def test_invalid_name(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.download_path(None, 5, default_name="test", overwrite=False)
        assert_contains(error, "name must be a string")
