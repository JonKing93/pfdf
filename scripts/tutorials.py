"""
Developer scripts for working with tutorial resources
----------
Functions:
"""

import sys
import json
from pathlib import Path
from zipfile import ZipFile
import shutil
import subprocess

def _repo() -> Path:
    "Returns the path to the repository root"

    return Path(__file__).resolve().parents[1]

def _notebook_paths(folder = "tutorials") -> list[Path]:
    "Returns the paths of the tutorial notebooks"

    tutorials = _repo() / folder
    return [path for path in tutorials.iterdir() if path.suffix == ".ipynb"]


def _load_notebooks() -> dict[Path, dict]:
    "Returns a dict with the Path and JSON dict for each tutorial notebook"

    notebooks = {}
    for path in _notebook_paths():
        with open(path) as file:
            notebook = json.load(file)
        notebooks[path] = notebook
    return notebooks


def clean():
    "Removes empty cells, output, and execution counts from tutorial notebooks"

    # Load the contents of each notebook
    for path, notebook in _load_notebooks().items():
        cells = notebook['cells']

        # Remove empty cells, strip output, and reset execution count
        cells = [cell for cell in cells if cell["source"] != []]
        for cell in cells:
            if cell["cell_type"] == "code":
                cell["execution_count"] = None
                cell["outputs"] = []

        # Update the notebook
        notebook["cells"] = cells
        with open(path, "w") as file:
            json.dump(notebook, file, indent=1)


def check():
    "Checks tutorial notebooks do not have output, execution counts, or empty cells"

    for path, notebook in _load_notebooks().items():
        for cell in notebook["cells"]:
            if cell["source"] == []:
                raise RuntimeError(f"{path} has empty cells")
            elif cell["cell_type"] == "code":
                if cell["outputs"] != []:
                    raise RuntimeError(f"{path} has output")
                elif cell["execution_count"] is not None:
                    raise RuntimeError(f"{path} has execution counts")


def precommit(interpreter: Path = None):
    "Sets up a git precommit hook to check that the tutorial notebooks are clean"

    # If no interpreter was provided, locate from CLI args
    if interpreter is None:
        interpreter = sys.argv[1]

    # Write the hook file
    path = _repo().parent[1] / ".git" / "hooks" / "pre-commit"
    content = f"#!/bin/sh\n{interpreter} scripts/tutorials.py check"
    path.write_text(content)


def _content_paths():
    "Returns the paths to the contents of the tutorial zipfile"

    # Initialize list with the tutorial notebooks
    tutorials = _repo() / "tutorials"
    paths = _notebook_paths()

    # Add data files
    data = ["perimeter.geojson", "dnbr.tif"]
    for file in data:
        path = tutorials / "data" / file
        paths.append(path)

    # Add code
    packages = ["check_installation", "tools"]
    for package in packages:
        package = tutorials / package
        contents = [path for path in package.iterdir() if path.suffix==".py"]
        paths += contents
    return paths

def build():
    "Zips the tutorials into the build folder and extracts the contents"

    # Get named paths
    tutorials = _repo() / "tutorials"
    build = _repo() / "tutorial-builds"
    zipped = build / "tutorials.zip"

    # Empty the build folder
    if build.exists():
        shutil.rmtree(build)
    build.mkdir()

    # Build zip archive
    with ZipFile(zipped, 'w') as archive:
        for path in _content_paths():
            archive.write(path, arcname=path.relative_to(tutorials))

    # Extract zip archive in clean namespace
    with ZipFile(zipped) as archive:
        archive.extractall(build)
        
def run():
    "Runs the tutorials in the build folder"

    paths = _notebook_paths("tutorial-builds")
    for path in paths:
        subprocess.run(
            [
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                str(path),
                "--execute",
                "--inplace",
            ],
            check=True
        )



def copy():
    "Copies tutorial resources into the docs"

    # Collect the notebooks
    repo = Path(__file__).parents[1]
    builds = repo / "tutorial-builds"
    paths = [path for path in builds.iterdir() if path.suffix == ".ipynb"]

    # Remove zip archive if it exists
    docs = repo / "docs" / "tutorials"
    archive = docs / "tutorials.zip"
    if archive.exists():
        archive.unlink()

    # Reset the notebooks folder
    notebooks = docs / "notebooks"
    if notebooks.exists():
        shutil.rmtree(notebooks)
    notebooks.mkdir()

    # Copy the notebooks
    for path in paths:
        if path.name == "01_Start_Here.ipynb":
            continue
        dst = notebooks / path.name
        if dst.exists():
            dst.unlink()
        path.rename(dst)

    # Also copy the tutorial zip folder
    zipped = builds / "tutorials.zip"
    dst = docs / "tutorials.zip"
    zipped.rename(dst)


"Runs the indicated command from the CLI"
if __name__ == "__main__":
    here = sys.modules[__name__]
    command = getattr(here, sys.argv[1])
    command()

