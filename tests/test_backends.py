"""Tests for the output backends: markdown, json, compact."""

from __future__ import annotations

import json

import pytest

from markdownizer.backends import get_backend
from markdownizer.extractor import extract_project


def test_get_backend_unknown():
    with pytest.raises(ValueError):
        get_backend("html")


def test_markdown_backend_legacy_output(sample_project, tmp_path):
    out = tmp_path / "out"
    written = extract_project(sample_project, out)
    assert sorted(p.name for p in written) == ["_root.md", "pkg.md", "tests.md"]
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert md.count("# Package: pkg") == 1
    assert "# Module: pkg/models.py" in md
    assert "# Django Model: User" in md
    assert "# DRF ViewSet: UserViewSet" in md
    assert "## Source Code" in md
    assert "## Comments" in md


def test_markdown_backend_defaults_match_legacy(tmp_path):
    """Backend render via format selection equals the legacy default call."""
    from tests.conftest import write_py

    write_py(tmp_path / "root_mod.py", '"""Root."""\ndef f():\n    pass\n')
    write_py(tmp_path / "pkg" / "__init__.py", '"""Pkg."""\n')
    write_py(
        tmp_path / "pkg" / "mod.py",
        '''
        """Models."""

        class User(models.Model):
            """A user."""

            def save(self):
                pass
        ''',
    )
    a = tmp_path / "a"
    b = tmp_path / "b"
    extract_project(tmp_path, a)
    extract_project(tmp_path, b, format="markdown")
    assert (a / "pkg.md").read_text(encoding="utf-8") == (b / "pkg.md").read_text(encoding="utf-8")
    assert (a / "_root.md").read_text(encoding="utf-8") == (b / "_root.md").read_text(
        encoding="utf-8"
    )


def test_json_backend(sample_project, tmp_path):
    out = tmp_path / "out"
    written = extract_project(sample_project, out, format="json")
    assert [p.name for p in written] == ["project.json"]
    data = json.loads((out / "project.json").read_text(encoding="utf-8"))
    assert data["ir_version"] == 1
    assert data["hash"]
    assert data["name"] == tmp_path.name
    assert data["symbols"][0]["file_path"] == "pkg/models.py"
    assert data["symbols"][0]["framework"] == "Django Model"
    assert "imports" in data and "defines" in data and "inherits" in data


def test_json_backend_is_deterministic(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, format="json")
    first = (out / "project.json").read_text(encoding="utf-8")
    extract_project(sample_project, out, format="json")
    second = (out / "project.json").read_text(encoding="utf-8")
    assert first == second


def test_compact_backend(sample_project, tmp_path):
    out = tmp_path / "out"
    written = extract_project(sample_project, out, format="compact")
    assert [p.name for p in written] == ["context.compact.md"]
    text = (out / "context.compact.md").read_text(encoding="utf-8")
    assert text.startswith("# Project:")
    assert "# Package: pkg" in text
    assert "# Package: _root" in text
    assert "# Module: pkg/models.py" in text
    assert "# Django Model: User — pkg/models.py:" in text
    assert "# Function: helper — pkg/views.py:" in text
    assert "## Source Code" not in text
    assert "## Comments" not in text
    assert "```class User(models.Model):```" in text


def test_compact_public_only(sample_project, tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "pkg" / "private.py",
        "def public_fn():\n    pass\n\n\ndef _hidden():\n    pass\n",
    )
    out = tmp_path / "out"
    extract_project(tmp_path, out, format="compact")
    text = (out / "context.compact.md").read_text(encoding="utf-8")
    assert "# Function: public_fn" in text
    assert "_hidden" not in text


def test_compact_respects_only_documented(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, format="compact", include_undocumented=False)
    text = (out / "context.compact.md").read_text(encoding="utf-8")
    assert "# Function: helper" not in text
    assert "# Django Model: User" in text


def test_compact_no_signatures_when_source_off(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, format="compact", include_source=False)
    text = (out / "context.compact.md").read_text(encoding="utf-8")
    assert "```" not in text


def test_compact_deterministic(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, format="compact")
    first = (out / "context.compact.md").read_text(encoding="utf-8")
    extract_project(sample_project, out, format="compact")
    second = (out / "context.compact.md").read_text(encoding="utf-8")
    assert first == second


def test_signature_mode_functions(tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "mod.py",
        '''
        def plain(a, b=2):
            """Plain."""
            pass

        async def afetch(url: str) -> dict:
            """Async."""
            return {}
        ''',
    )
    out = tmp_path / "out"
    extract_project(tmp_path, out, include_source="signature")
    text = (out / "_root.md").read_text(encoding="utf-8")
    assert "def plain(a, b=2):" in text
    assert "async def afetch(url: str) -> dict:" in text
    assert "## Source Code" not in text
    assert "## Signature" in text


def test_signature_mode_class_and_inheritance(tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "mod.py",
        '''
        class User(models.Model, Mixin):
            """A user."""

            def save(self, force: bool = False) -> None:
                """Save."""
                pass
        ''',
    )
    out = tmp_path / "out"
    extract_project(tmp_path, out, include_source="signature")
    text = (out / "_root.md").read_text(encoding="utf-8")
    assert "class User(models.Model, Mixin):" in text
    assert "def save(self, force: bool=False) -> None:" in text
    assert "## Source Code" not in text


def test_signature_mode_property(tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "mod.py",
        '''
        class C:
            @property
            def name(self) -> str:
                """The name."""
                return "x"
        ''',
    )
    out = tmp_path / "out"
    extract_project(tmp_path, out, include_source="signature")
    text = (out / "_root.md").read_text(encoding="utf-8")
    assert "def name(self) -> str:" in text
    assert "@property" in text


def test_signature_mode_modules_have_no_source(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "mod.py", '"""Docs."""\nx = 1\n')
    out = tmp_path / "out"
    extract_project(tmp_path, out, include_source="signature")
    text = (out / "_root.md").read_text(encoding="utf-8")
    assert "## Source Code" not in text
    assert "## Signature" not in text
    assert "Docs." in text


def test_boolean_modes_still_work(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "mod.py", '"""Docs."""\ndef f():\n    pass\n')
    out1 = tmp_path / "a"
    extract_project(tmp_path, out1, include_source=True)
    assert "## Source Code" in (out1 / "_root.md").read_text(encoding="utf-8")
    out2 = tmp_path / "b"
    extract_project(tmp_path, out2, include_source=False)
    text = (out2 / "_root.md").read_text(encoding="utf-8")
    assert "## Source Code" not in text
    assert "## Signature" not in text


def test_backend_render_options_root_name(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, root_name="top")
    assert (out / "top.md").exists()


def test_all_backends_consume_same_ir(sample_project, tmp_path):
    """Backends must not re-analyze: output hashes align with a single IR."""
    import markdownizer

    ir1 = markdownizer.build_project_ir(tmp_path)
    out = tmp_path / "out"
    extract_project(tmp_path, out, format="json")
    data = json.loads((out / "project.json").read_text(encoding="utf-8"))
    assert data["hash"] == ir1.hash
