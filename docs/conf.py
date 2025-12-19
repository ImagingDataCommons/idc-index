from __future__ import annotations

import importlib.metadata

project = "idc-index"
copyright = "2024, Imaging Data Commons"
author = "Imaging Data Commons"
version = release = importlib.metadata.version("idc_index")

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_click",
    "sphinxcontrib.mermaid",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

exclude_patterns = [
    "_build",
    "**.ipynb_checkpoints",
    "Thumbs.db",
    ".DS_Store",
    ".env",
    ".venv",
]

html_theme = "furo"

myst_enable_extensions = [
    "colon_fence",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable", None),
}

nitpick_ignore = [
    ("py:class", "_io.StringIO"),
    ("py:class", "_io.BytesIO"),
]

always_document_param_types = True

# Mermaid configuration for better diagram rendering
mermaid_version = "11.12.1"
mermaid_init_js = """
mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    themeVariables: {
        primaryColor: '#E8F4F8',
        primaryTextColor: '#1a1a1a',
        primaryBorderColor: '#2196F3',
        lineColor: '#2196F3',
        secondaryColor: '#FFF8E1',
        tertiaryColor: '#F5F5F5',
        fontSize: '14px'
    },
    er: {
        layoutDirection: 'LR',
        minEntityWidth: 100,
        minEntityHeight: 75,
        entityPadding: 15,
        stroke: 'gray',
        fill: 'honeydew',
        fontSize: 12
    },
    flowchart: {
        htmlLabels: true,
        curve: 'basis'
    }
});
"""

# Enable zoom for Mermaid diagrams
mermaid_d3_zoom = True
