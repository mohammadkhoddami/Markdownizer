"""Tests for packaging metadata consistency."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

import markdownizer

ROOT = Path(__file__).resolve().parents[1]


def test_version_matches_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["dynamic"] == ["version"]
    assert markdownizer.__version__ == "0.2.0"
    assert re.match(r"^\d+\.\d+\.\d+$", markdownizer.__version__)


def test_no_runtime_dependencies():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["dependencies"] == []


def test_console_script_entrypoint():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["scripts"] == {"markdownizer": "markdownizer.cli:main"}


def test_public_api_surface():
    assert markdownizer.__all__ == ["extract_project"]
    assert callable(markdownizer.extract_project)


def test_py_typed_marker_present():
    assert (ROOT / "markdownizer" / "py.typed").is_file()
