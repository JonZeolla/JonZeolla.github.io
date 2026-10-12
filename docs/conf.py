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

exclude_patterns: list[str] = []

# -- Options for HTML output --
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Furo, skinned to the same tokens as the Astro site (src/styles/global.css). Fonts are copied from
# node_modules into _static/fonts by the Taskfile (build-labs) so nothing loads from a third party.
html_theme: str = "furo"
html_title: str = "Jon Zeolla · Labs"
html_static_path: list[str] = ["_static"]
html_css_files: list[str] = ["css/fonts.css", "css/custom.css"]
html_sidebars: dict[str, list[str]] = {
    "**": [
        "sidebar/scroll-start.html",
        "sidebar/home.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "sidebar/scroll-end.html",
    ],
}
templates_path: list[str] = ["_templates"]
_light: dict[str, str] = {
    "color-brand-primary": "#0a6fc2",
    "color-brand-content": "#0a6fc2",
    "color-background-primary": "#f6f4ee",
    "color-background-secondary": "#ece9e1",
    "color-background-border": "#d8d3c6",
    "color-foreground-primary": "#171c24",
    "color-foreground-secondary": "#5a6677",
    "color-foreground-muted": "#8b95a3",
    "color-sidebar-background": "#ece9e1",
    "color-sidebar-background-border": "#d8d3c6",
    "color-code-background": "#ffffff",
}
_dark: dict[str, str] = {
    "color-brand-primary": "#5ab4ff",
    "color-brand-content": "#5ab4ff",
    "color-background-primary": "#0c1118",
    "color-background-secondary": "#121a24",
    "color-background-border": "#253142",
    "color-foreground-primary": "#e7e3da",
    "color-foreground-secondary": "#93a0b1",
    "color-foreground-muted": "#5f6c7d",
    "color-sidebar-background": "#121a24",
    "color-sidebar-background-border": "#253142",
    "color-code-background": "#16202c",
    "color-highlight-on-target": "#163044",
}
_fonts: dict[str, str] = {
    "font-stack": '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif',
    "font-stack--headings": '"Bricolage Grotesque Variable", "Helvetica Neue", Arial, sans-serif',
    "font-stack--monospace": '"JetBrains Mono Variable", "SFMono-Regular", Menlo, monospace',
}
html_theme_options: dict = {
    "light_css_variables": {**_light, **_fonts},
    "dark_css_variables": {**_dark, **_fonts},
    "top_of_page_buttons": [],
}

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
