"""Recursive project scanner that yields Python source file paths."""

from __future__ import annotations

import fnmatch
from collections.abc import Iterator
from pathlib import Path

IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".nox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        "site-packages",
        ".eggs",
        "build",
        "dist",
    }
)


def should_skip_dir(name: str) -> bool:
    return name in IGNORED_DIR_NAMES or name.startswith(".")


def _matches_exclude(relative: Path, exclude: list[str]) -> bool:
    for pattern in exclude:
        if fnmatch.fnmatch(str(relative), pattern) or fnmatch.fnmatch(
            str(relative), f"**/{pattern}"
        ):
            return True
        if any(
            fnmatch.fnmatch(part, pattern) or fnmatch.fnmatch(part, f"**/{pattern}")
            for part in relative.parts
        ):
            return True
    return False


def scan_python_files(project_root: Path, exclude: list[str] | None = None) -> Iterator[Path]:
    """Yield all `.py` files under `project_root`, skipping ignored directories.

    Args:
        project_root: Directory to scan recursively.
        exclude: Optional glob patterns (e.g. ``"tests/*"``, ``"migrations"``)
            matched against paths relative to ``project_root``. Both the full
            relative path and individual path components are matched.
    """
    project_root = project_root.resolve()
    patterns = list(exclude) if exclude else []
    for path in sorted(project_root.rglob("*.py")):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(project_root)
        except ValueError:
            continue
        if path.name.startswith("."):
            continue
        if any(should_skip_dir(part) for part in relative.parts[:-1]):
            continue
        if patterns and _matches_exclude(relative, patterns):
            continue
        yield path
