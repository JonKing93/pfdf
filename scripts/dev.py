"""
Contains functions used for poetry command line scripts
----------
This module contains functions intended for use as a poetry command line scripts.
To run a script, enter:

    poetry run <function>

from a command line (not the Python interactive shell).
----------
Poetry Scripts:
    tests               - Runs the tests
    format              - Applies isort and black formatters to the code
    lint                - Checks that all code is formatted correctly
    pipeline            - Runs the checks implemented in the Gitlab pipeline

Other Functions:
    run                 - Runs a command as a subprocess
"""

from typing import List
import subprocess

MIN_COVERAGE = 94


def pipeline():
    "Runs the steps of the Gitlab pipeline"
    run(["safety", "check"])
    lint()
    tests()


def tests():
    """
    Runs all tests intended for the Gitlab pipeline. Requires minimum coverage
    and generates a coverage report.

    !!!!! This command has been temporarily altered for a multi-part merge request
    !!!!! It should be restored once the MR is complete.
    """

    command = [
        "pytest",
        "tests/_utils",
        "--cov=pfdf._utils",
        f"--cov-fail-under={MIN_COVERAGE}",
        "--cov-report",
        "xml:coverage.xml",
        "--cov-append"
    ]
    run(command)

    modules = ["errors", "raster", "severity", "watershed"]
    for module in modules:
        command[1] = f"tests/test_{module}.py"
        command[2] = f"--cov=pfdf.{module}"
        run(command)

    run(["coverage", "report"])
    
    # command = [
    #     "pytest",
    #     "tests",
    #     "--cov=pfdf",
    #     f"--cov-fail-under={MIN_COVERAGE}",
    #     "--cov-report",
    #     "xml:coverage.xml",
    # ]
    # run(command)
    # run(["coverage", "report"])


def format():
    "Applies isort and black to pfdf and tests"
    run(["isort", "pfdf"])
    run(["isort", "tests"])
    run(["black", "pfdf"])
    run(["black", "tests"])


def lint():
    "Checks that pfdf and tests follow formatting guidelines"
    run(["isort", "pfdf", "--check"])
    run(["isort", "tests", "--check"])
    run(["black", "pfdf", "--check"])
    run(["black", "tests", "--check"])


def run(command: List[str]):
    "Runs a command as a subprocess. Raises error if encounters an error code"
    subprocess.run(command, check=True)
