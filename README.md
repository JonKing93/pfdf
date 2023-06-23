# post-wildfire-debris-flow-hazard-assessment

A Python library to implement post-wildfire debris-flow hazard assessments.

## Installation

### pfdf package

1. Install git, [python 3.9+](https://www.python.org/downloads/), and [poetry 1.3+](https://python-poetry.org/)

(Note that if python is installed, you can install poetry using `pip install poetry`)

2. Clone this repository. You can do this via [the pfdf Gitlab page](https://code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment). You can also do this via the command line if your credentials are set up: 
```
git clone https://code.usgs.gov/ghsc/lhp/post-wildfire-debris-flow-hazard-assessment
```

3. Navigate to the top-level folder of the repository (the folder containing `pyproject.toml`)

4. Run `poetry install`

You should now be able to import the package within python via: `import pfdf`

Alternatively, you can do a developement installation, which enables poetry scripts to run tests and linting. To do a development install, update step 4 to:

```
poetry install --with dev
```


### TauDEM
Much of the pfdf package depends on TauDEM, a C++ library for digital terrain analysis, so you will need to install TauDEM to use most modules. TauDEM is easiest to install for Windows, via the [windows installer](https://hydrology.usu.edu/taudem/taudem5/downloads.html).

Linux/MacOS is much harder. There's some limited information in the [TauDEM documentation](https://hydrology.usu.edu/taudem/taudem5/downloads.html), but the best option is probably using conda:
```
conda install -c conda-forge taudem
```
This works on some machines, but can sometimes create dependency problems with rasterio. Best luck!

We note that future releases aim to replace all TauDEM functionality with the pure Python `pysheds` module.

### Run Tests
You may want to run the pfdf tests to validate your installation. This requires a development installation:
```
poetry install --with dev
```

Once this is complete, you can run the tests using:
```
poetry run tests
```
This will also report the test coverage and requires a minimum coverage (defined in `scripts/poetry.py`). The Gitlab pipeline requires that this script passes before code can be merged.

Note that the Gitlab pipeline does not check tests that rely on TauDEM commands. However, if TauDEM is installed, you can run all tests (including TauDEM) using:
```
poetry run all_tests
```

(Note that we plan to remove the all_tests command with the migration from TauDEM to pysheds).



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
