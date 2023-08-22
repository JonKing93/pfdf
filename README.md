# post-wildfire-debris-flow-hazard-assessment

A Python library to implement post-wildfire debris-flow hazard assessments.

## Installation

### Prerequisites

This installation requires both [git](https://git-scm.com/downloads) and [conda](https://docs.conda.io/en/latest/miniconda.html). You can check that these are installed by entering:
```
git --version
```
and
```
conda --version
```
from the command line.

If conda is not installed, we recommend using the miniconda installer, rather than the full anaconda suite.


### Clone
First, you should clone this repository to your local machine. You can do this via the [the pfdf Gitlab page](https://code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment), or via the command line if your credentials are set up:
```
git clone https://code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment
```

### Conda Environment
Next, you will need to set up a conda environment for the package. Navigate to the main folder of cloned repository, then enter:
```
conda env create --file environment.yml
```
This will use the `environment.yml` file included in the repository to create a conda environment named `pfdf`. This environment includes Python 3.9, [TauDEM](https://hydrology.usu.edu/taudem/taudem5/documentation.html) and [poetry](https://python-poetry.org/).

Note that if you want to create an environment with a name other than `pfdf`, you can do so using:
```
conda env create --file environment.yml --name <some other name>
```

### Poetry Install
Finally, use poetry to install the package. From the repository folder, enter:
```
poetry install
```

If you plan to develop `pfdf`, you should instead use:
```
poetry install --with dev
```
This will include various development packages in the installation (for example: pytest for testing, isort and black for linting, etc)


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
