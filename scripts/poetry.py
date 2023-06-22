"""
Contains functions used for poetry command line scripts
----------
This module contains functions intended for use as a poetry command line scripts.
To run a script, enter:

    poetry run <function>

from a command line (not the Python interactive shell).
----------
Poetry Scripts:
    tests               - Runs the (pure Python) tests intended for the Gitlab pipeline
    all_tests           - Runs all tests, including those requiring TauDEM
    format              - Applies isort and black formatters to the code
    lint                - Checks that all code is formatted correctly

Other Functions:
    run                 - Runs a command as a subprocess
"""

from typing import List
import subprocess

MIN_COVERAGE = 75

ignore_npt_warning = "-W ignore::DeprecationWarning:nptyping.typing_ "


def tests():
    """
    Runs all tests intended for the Gitlab pipeline. These are the tests that
    do not require a TauDEM installation. Also generates a coverage report and
    requires a minimum coverage.
    """
    command = [
        "pytest",
        "tests",
        "-k",
        "not taudem",
        "--cov=pfdf",
        f"--cov-fail-under={MIN_COVERAGE}",
        "--cov-report",
        "xml:coverage.xml",
        ignore_npt_warning,
    ]
    run(command)
    run(["coverage", "report"])

def all_tests():
    "Can be used by developers with a TauDEM installation to validate all tests"
    command = ["pytest", "tests", ignore_npt_warning]
    run(command)


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
