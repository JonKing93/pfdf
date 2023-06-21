"""
dev_scripts  Contains functions used for poetry command line scripts
----------
Functions:
    tests       - Runs the (pure Python) tests intended for the Gitlab pipeline
    all_tests   - Runs all tests, including those requiring TauDEM
    lint        - Checks code conforms to isort and black formatting
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
        "--cov=pfdf.errors --cov=pfdf.utils --cov=pfdf.validate --cov=pfdf.severity "
        f"--cov-fail-under={MIN_COVERAGE} --cov-report xml "
        f"{ignore_npt_warning}"
    )
    subprocess.run(command, check=True)
    subprocess.run("coverage report")


def all_tests():
    "Can be used by developers with a TauDEM installation to validate all tests"
    command = f"python -m pytest tests {ignore_npt_warning}"
    subprocess.run(command)


def lint():
    commands = [
        "isort pfdf -c",
        "isort tests -c",
        "black pfdf --check",
        "black tests --check",
    ]
    for command in commands:
        subprocess.run(command)
