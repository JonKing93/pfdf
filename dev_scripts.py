"""
dev_scripts  Contains functions used for poetry command line scripts
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
    check_format        - Checks that all code is formatted correctly

Other Functions:
    run                 - Runs a set of commands as a subprocess
"""

import subprocess

MIN_COVERAGE = 95

ignore_npt_warning = "-W ignore::DeprecationWarning:nptyping.typing_ "


def tests():
    """
    Runs all tests intended for the Gitlab pipeline. These are the tests that
    do not require a TauDEM installation. Also generates a coverage report and
    requires a minimum coverage.
    """
    command = (
        "python -m "
        'pytest tests -k "not taudem" '
        "--cov=pfdf.errors --cov=pfdf.utils --cov=pfdf.validate --cov=pfdf.severity --cov=pfdf.segments "
        f"--cov-fail-under={MIN_COVERAGE} --cov-report xml:coverage.xml "
        f"{ignore_npt_warning}"
    )
    run(command)
    run("coverage report")


def all_tests():
    "Can be used by developers with a TauDEM installation to validate all tests"
    command = f"python -m pytest tests {ignore_npt_warning}"
    run(command)


def format():
    "Applies isort and black to pfdf and tests"
    commands = ["isort pfdf", "isort tests", "black pfdf", "black tests"]
    run(commands)


def check_format():
    "Checks that pfdf and tests follow formatting guidelines"
    commands = [
        "isort pfdf -c",
        "isort tests -c",
        "black pfdf --check",
        "black tests --check",
    ]
    run(commands)


def run(commands):
    "Runs a set of commands as a subprocess"
    if not isinstance(commands, list):
        commands = [commands]
    for command in commands:
        subprocess.run(command)
