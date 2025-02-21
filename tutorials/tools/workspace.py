"""
Tools to clean and validate the tutorial workspace
----------
Paths:
    workspace           - Returns the workspace path

Validation:
    _check              - Checks a folder contains required datasets
    check_datasets      - Checks that hazard assessment datasets are present
    check_preprocessed  - Checks that preprocessed datasets are present

Cleaning:
    _remove             - Removes files and folders from the workspace
    remove_examples     - Removes example datasets from the workspace
    remove_downloads    - Removes downloaded datasets from the workspace
"""

import shutil
from pathlib import Path


def workspace() -> Path:
    "Returns the path to the tutorial workspace"
    return Path(__file__).resolve().parents[1]


#####
# Validation
#####


def _check(folder: str, datasets: list[str], description: str, prereq):
    "Checks that the indicated folder has the required datasets."

    folder = workspace() / folder
    for file in datasets:
        path = folder / file
        if not path.exists():
            raise FileNotFoundError(
                f"Could not find the {description} {file} dataset.\n"
                f"Expected Path: {path}\n"
                f"Try running the {prereq} tutorial."
            )
    print(f"The {description} datasets are present")


def check_datasets():
    "Checks that download datasets are present"

    datasets = [
        "buffered-perimeter.tif",
        "dem.tif",
        "dnbr.tif",
        "kf.tif",
        "evt.tif",
        "la-county-retainments.gdb",
    ]
    _check(
        folder="data", datasets=datasets, description="required", prereq="Download Data"
    )


def check_preprocessed():

    datasets = [
        "perimeter",
        "dem",
        "dnbr",
        "kf",
        "barc4",
        "iswater",
        "isdeveloped",
        "retainments",
    ]
    datasets = [f"{file}.tif" for file in datasets]
    _check("preprocessed", datasets, description="preprocessed", prereq="Preprocessing")


#####
# Cleaning
#####


def _remove(folder, files: list[str], folders: list[str] = []):

    # Remove files
    data = workspace() / folder
    for file in files:
        path = data / file
        if path.exists():
            path.unlink()

    # Use shutil to remove folders
    for folder in folders:
        path = data / folder
        if path.exists():
            shutil.rmtree(path)


def remove_examples():
    "Removes example datasets from the workspace"
    examples = workspace() / "examples"
    if not examples.exists():
        examples.mkdir()
    _remove("examples", ["example-raster.tif", "example-mask.tif", "my-raster.tif"])
    print("Cleaned workspace of example files")


def remove_downloads():
    _remove(
        "data",
        files=["noaa-atlas14-mean-pds-intensity-metric.csv"],
        folders=["la-county-retainments.gdb", "huc8-18070106"],
    )
    print("Cleaned workspace of downloaded datasets")
