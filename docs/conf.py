# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project: str = "Jon Zeolla"
copyright: str = "2024, Jon Zeolla"
author: str = "Jon Zeolla"

# -- General configuration --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Consider for the future: sphinx_tippy
extensions: list[str] = [
    "myst_parser",
    "sphinx-prompt",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_last_updated_by_git",
    "sphinx_togglebutton",
    "sphinxcontrib.googleanalytics",
    "sphinxcontrib.mermaid",
]

templates_path: list[str] = ["_templates"]
exclude_patterns: list[str] = []

# -- Options for HTML output --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme: str = "sphinx_rtd_theme"
html_theme_path: list[str] = ["index.rst"]
html_static_path: list[str] = ["_static"]
html_css_files: list[str] = ["css/custom.css"]

# -- Options for MyST --
# https://myst-parser.readthedocs.io/en/latest/configuration.html
# https://myst-parser.readthedocs.io/en/latest/syntax/optional.html

myst_enable_extensions: list[str] = ["attrs_block", "attrs_inline", "colon_fence"]
myst_links_external_new_tab: bool = True

# -- Options for sphinx-copybutton --
# https://github.com/executablebooks/sphinx-copybutton/blob/master/docs/use.md

# True is the default right now, but I prefer explicit over implicit
copybutton_only_copy_prompt_lines: bool = True
# This fixes the copy button for multi-line HEREDOCS that start with a prompt
# However it doesn't play nice with copybutton_exclude. See https://github.com/executablebooks/sphinx-copybutton/issues/185
copybutton_here_doc_delimiter: str = "EOF"
# Currently the default is ".linenos" (as of v0.5.2), so this effectively just adds .go which is the class for console outputs
# Also, the devs don't like my approach: https://github.com/executablebooks/sphinx-copybutton/issues/185#issuecomment-1319059186
copybutton_exclude: str = ".linenos, .gp, .go"
# Disables copying empty lines
copybutton_copy_empty_lines: bool = False
# This allows us to set a :class: no-copybutton to remove the copy button for a code block
copybutton_selector: str = "div:not(.no-copybutton) > div.highlight > pre"

# -- Options for sphinx-togglebutton --
# https://github.com/executablebooks/sphinx-togglebutton/blob/master/docs/use.md

# This removes the hint text to avoid a CSS alignment bug where the hint was not properly aligned
togglebutton_hint: str = ""

# -- Options for sphinxcontrib-googleanalytics --
# https://github.com/sphinx-contrib/googleanalytics#configuration

googleanalytics_id: str = "G-EZSNDVQWPT"
