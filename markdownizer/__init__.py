"""Markdownizer - Extract existing documentation from Python projects into Markdown.

This library never generates, rewrites, summarizes, or improves documentation.
It only extracts what already exists in the source code.
"""

from markdownizer.extractor import extract_project

__version__ = "0.1.0"
__all__ = ["extract_project"]