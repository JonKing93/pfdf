"""
Subpackages used to validate user inputs
----------
This module contains two subpackages used to validate user inputs to pfdf commands.
The "core" subpackage contains a variety of validation routines used throughout
pfdf. These routines depend only on the standard library, and third party imports,
and so "core" may be used anywhere in pfdf.

The "raster" subpackage provides additional routines used to validate inputs for
Raster commands. These routines depend on both (1) the projection classes, and
(2) the Raster class itself. As such, these routines can only be used within the
raster module, or by submodules importing the raster module.

The recommended import syntax is as follows:

import pfdf._validate.core as validate
OR
import pfdf._validate.raster as validate
----------
Subpackages:
    core    - Validation routines used throughout pfdf
    raster  - Validation routines for Raster commands
"""
