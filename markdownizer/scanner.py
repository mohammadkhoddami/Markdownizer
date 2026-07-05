"""Recursive project scanner that yields Python source file paths."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

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


def scan_python_files(project_root: Path) -> Iterator[Path]:
    """Yield all `.py` files under `project_root`, skipping ignored directories."""
    project_root = project_root.resolve()
    for path in sorted(project_root.rglob("*.py")):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(project_root).parts[:-1]
        except ValueError:
            continue
        if any(should_skip_dir(part) for part in relative_parts):
            continue
        if should_skip_dir(path.parent.name) and path.parent != project_root:
            continue
        yield path