import sys
import os
import django
import sphinx_rtd_theme

sys.path.insert(0, os.path.abspath('../..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'BaCa2.settings'
django.setup()

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'BaCa2'
copyright = '2023, Bartosz Deptuła, Małgorzata Drąg, Izabela Golec, Krzysztof Kalita; supervisor: PhD Tomasz Kapela'
author = 'Bartosz Deptuła, Małgorzata Drąg, Izabela Golec, Krzysztof Kalita; supervisor: PhD Tomasz Kapela'
release = '0.1.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.githubpages',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',

    'sphinx_rtd_theme',
    # 'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    "show_navbar_depth": 5,
}
html_static_path = ['_static']
