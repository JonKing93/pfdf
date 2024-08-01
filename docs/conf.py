# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import tomllib
from pathlib import Path


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pfdf"
copyright = "2024, USGS"
author = "Jonathan King"

# Parse the release string from pyproject.toml
_pyproject = Path(__file__).parents[1] / "pyproject.toml"
with open(_pyproject, 'rb') as file:
    _pyproject = tomllib.load(file)
release = _pyproject['tool']['poetry']['version']

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx_rtd_theme", "sphinx_design"]
exclude_patterns = ["images","tutorials/download"]
highlight_language = "pycon"
pygments_style = "sphinx"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_copy_source = False
html_theme = "sphinx_rtd_theme"
html_theme_options = {'navigation_depth': -1}

