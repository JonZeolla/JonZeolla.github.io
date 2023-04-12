# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project: str = "Jon Zeolla"
copyright: str = "2023, Jon Zeolla"
author: str = "Jon Zeolla"

# -- General configuration --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions: list[str] = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx-prompt",
    "sphinx_design",
    "sphinx_tippy",
    "sphinx_togglebutton",
    "sphinxcontrib.mermaid",
]

templates_path: list[str] = ["_templates"]
exclude_patterns: list[str] = []

# -- Options for HTML output --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme: str = "sphinx_rtd_theme"
html_theme_path: list[str] = ["index.rst"]

# -- Options for MyST --
# https://myst-parser.readthedocs.io/en/latest/configuration.html
# https://myst-parser.readthedocs.io/en/latest/syntax/optional.html

myst_enable_extensions: list[str] = []
