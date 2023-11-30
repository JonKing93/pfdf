# pfdf

A Python library to facilitate post-fire debris-flow hazard assessments.


## Summary

The pfdf (post-fire debris-flow) package provides utilities intended to facilitate post-fire debris-flow hazard assessments and research. The package contains routines to:

* Analyze watersheds
* Delineate and filter stream segment networks
* Compute earth-system variables for stream segments in a network
* Assess debris-flow probabilities using the models of Staley and others, 2017
* Assess potential sediment volumes using the models of Gartner and others, 2014
* Classify relative hazards using the methods of Cannon and others, 2010, and
* Export results to GeoJSON and common GIS file formats

Detailed usage instructions can be found in the module docstrings, and further details can be found in the class and function docstrings within each module. The following provides a brief summary of pfdf's key modules:

The pfdf package uses various raster datasets to delineate a stream segment network for a watershed, and then assess post-wildfire debris-flow hazards. The `segments` module forms the core of the package and is used to manage stream segment networks. This module is built around the `Segments` class, which is used to build and filter such networks. The class also computes earth-system variables for segments in a network, and can export networks to GeoJSON and common GIS file formats. Many of these routines require raster datasets as inputs. The `severity` and `watershed` modules can be used to produce rasters pertaining to burn severity and watershed characteristics. See also the `raster` module for further information and support for working with raster datasets.

The hazard assessment modules are all contained in the `models` subpackage. The `staley2017` module implements logistic models that estimate debris-flow probability given rainfall accumulation, and vice versa. The `gartner2014` module provides emergency and long-term estimates of debris-flow potential sediment volume. The `cannon2010` module then groups potential debris-flows into discrete hazard classes based on their probabilities and estimated sediment volumes.

Finally, the pfdf package contains two utility modules, located in the `utils` subpackage. The `slope` module contains functions that convert between different slope metrics. The `driver` module contains information and utility functions for working with various GIS file formats.


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

If you plan to develop `pfdf`, you should instead use:
```
poetry install --with dev
```
which will add various development packages to the installation (for example: pytest for testing, isort and black for linting, etc).


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

## Suggested Citation

King, J., 2023, pfdf - Python library for post-fire debris-flow hazard assessments and research, version 1.0.0: U.S. Geological Survey software release, https://doi.org/10.5066/P9JO58MJ


## DOI

The 1.0.0 release has the following DOI: https://doi.org/10.5066/P9JO58MJ


## IPDS Record

The 1.0.0 release is documented as IPDS record IP-159652.


## References

Cannon, S.H., Gartner, J.E., Rupert, M.G., Michael, J.A., Rea, A.H., and Parrett, C., 2010, Predicting the probability and volume of postwildfire debris flows in the intermountain western United States, GSA Bulletin, 122(1-2), 127-144, https://doi.org/10.1130/B26459.1

Gartner, J.E., Cannon, S.H., and Santi, P.M., 2014, Empirical models for predicting volumes of sediment deposited by debris flows and sediment-laden floods in the transverse ranges of southern California, Engineering Geology, 176, 45-56, https://doi.org/10.1016/j.enggeo.2014.04.008

Staley, D.M., Negri, J.A., Kean, J.W., Laber, J.L., Tillery, A.C., and Youberg, A.M., 2017, Prediction of spatially explicit rainfall intensity–duration thresholds for post-fire debris-flow generation in the western United States, Geomorphology, 278, 149-162, https://doi.org/10.1016/j.geomorph.2016.10.019
