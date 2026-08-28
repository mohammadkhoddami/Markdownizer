"""Shared fixtures for the Markdownizer test suite."""

from __future__ import annotations

import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest


def write_py(path: Path, source: str) -> Path:
    """Write ``source`` (dedented) to ``path`` and return it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source).lstrip("\n"), encoding="utf-8")
    return path


@pytest.fixture
def write_file(tmp_path: Path) -> Callable[[str, str], Path]:
    """Fixture returning a helper to write a dedented Python source file."""

    def _write(rel_path: str, source: str) -> Path:
        return write_py(tmp_path / rel_path, source)

    return _write


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Create a small multi-package project and return its root."""
    write_py(
        tmp_path / "pkg" / "__init__.py",
        '"""Package docstring."""\n',
    )
    write_py(
        tmp_path / "pkg" / "models.py",
        '''
        """Models module."""

        # This model is documented.
        class User(models.Model):
            """A documented user model."""

            name = models.CharField(max_length=100)
        ''',
    )
    write_py(
        tmp_path / "pkg" / "views.py",
        '''
        """Views module."""

        class UserViewSet(viewsets.ModelViewSet):
            """A documented viewset."""

            queryset = User.objects.all()

        def helper():
            return 42
        ''',
    )
    write_py(
        tmp_path / "tests" / "test_models.py",
        '''
        """Test module."""

        def test_user():
            """A test."""
            assert True
        ''',
    )
    write_py(
        tmp_path / "root_mod.py",
        '''
        """Root module."""

        def root_func():
            """Root function."""
            return 1
        ''',
    )
    return tmp_path
