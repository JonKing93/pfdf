# pfdf

A Python library to facilitate post-wildfire debris-flow hazard assessments.

## Installation

### Prerequisites

This installation requires both [git](https://git-scm.com/downloads) and [Python 3.11+](https://www.python.org/downloads/). You can check that these are installed by entering:
```
git --version
```
and
```
python --version
```
from the command line.


### Clone
First, you should clone this repository to your local machine. You can do this via the [the pfdf Gitlab page](https://code.usgs.gov/ghsc/lhp/pfdf), or via the command line if your credentials are set up:
```
git clone https://code.usgs.gov/ghsc/lhp/pfdf
```

### Poetry Install

You can install the package using [poetry](https://python-poetry.org/docs/). You can install poetry itself by entering:
```
pip install poetry
```
at the command line.

To install the `pfdf` package, you should first navigate to the cloned repository. Then enter:
```
poetry install
```
in the command line.

If you plan to develope `pfdf`, you should instead use:
```
poetry install --with dev
```
which will add various developement packages to the installation (for example: pytest for testing, isort and black for linting, etc).


## Developer scripts
Developers may find the following scripts useful - many of these scripts are used in the Gitlab pipeline to ensure that `pfdf` code meets various quality standards. Note that you must do a dev installation to run these scripts.

Check for security vulnerabilities
```
poetry run safety check
```

Apply formatting guidelines to code:
```
poetry run format
```

Lint (check that formatting guidelines are met):
```
poetry run lint
```

Tests and coverage report:
```
poetry run tests
```

You can also use `poetry run pytest <pytest args>` to run specific tests in the suite.

### Gitlab Pipeline

The Gitlab pipeline runs the safety check, lint, and testing scripts, and all three scripts must pass before code can be merged. You can confirm that these checks pass using:
```
poetry run pipeline
```



## Status
This project is motivated by an unpublished collection of scripts written by Dennis Staley. The project is currently focused on adapting those scripts into a modern Python library.

Currently, the project is focused on modularizing the original code. Once this is done, additional work will need to:
  * open source the code
  * optimize runtimes
  * validate user inputs
  * provide comprehensive documentation
before the project should be considered for public release.

## Branches

main: This holds the current Python library. The code on this branch should be approved before merging.

original: This branch serves as a reference. It holds the original scripts that the project is based on.
