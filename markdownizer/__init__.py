"""Markdownizer - Extract existing documentation from Python projects into Markdown.

This library never generates, rewrites, summarizes, or improves documentation.
It only extracts what already exists in the source code.
"""

from markdownizer.extractor import extract_project
from markdownizer.ir import IR_VERSION, ProjectIR, build_project_ir

__version__ = "0.3.0"
__all__ = ["extract_project", "build_project_ir", "IR_VERSION", "ProjectIR"]
