"""Tests for the extractor orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from markdownizer.extractor import _package_key, _package_label, extract_project


def test_package_key(tmp_path):
    root = tmp_path / "proj"
    (root / "pkg").mkdir(parents=True)
    assert _package_key(root / "pkg" / "a.py", root) == "pkg"
    assert _package_key(root / "a.py", root) == ""
    assert _package_key(root / "nested" / "deep" / "a.py", root) == str(Path("nested/deep"))


def test_package_label():
    assert _package_label("", "_root") == "_root"
    assert _package_label("pkg", "_root") == "pkg"
    assert _package_label("nested/deep", "_root") == "nested.deep"


def test_extract_writes_one_file_per_package(sample_project, tmp_path):
    out = tmp_path / "out"
    written = extract_project(sample_project, out)
    assert sorted(p.name for p in written) == ["_root.md", "pkg.md", "tests.md"]


def test_extract_no_duplicate_package_header(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert md.count("# Package: pkg") == 1


def test_extract_modules_not_concatenated(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "# Module: pkg/models.py" in md
    assert "# Module: pkg/views.py" in md
    assert '"""Models module."""\n\n        class' not in md


def test_extract_detects_framework_kinds(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "# Django Model: User" in md
    assert "# DRF ViewSet: UserViewSet" in md


def test_extract_exclude(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, exclude=["tests/*"])
    written = [p.name for p in (out).glob("*.md")]
    assert "_root.md" in written and "pkg.md" in written
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "test_user" not in md


def test_extract_include_undocumented_false(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, include_undocumented=False)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "# Django Model: User" in md
    assert "# Function: helper" not in md


def test_extract_include_source_false(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, include_source=False)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "## Source Code" not in md


def test_extract_include_comments_false(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, include_comments=False)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "## Comments" not in md


def test_extract_root_name(sample_project, tmp_path):
    out = tmp_path / "out"
    extract_project(sample_project, out, root_name="top")
    assert (out / "top.md").exists()


def test_extract_empty_project(tmp_path):
    out = tmp_path / "out"
    written = extract_project(tmp_path, out)
    assert written == []


def test_extract_creates_output_dir(tmp_path):
    out = tmp_path / "nested" / "out"
    extract_project(tmp_path, out)
    assert out.is_dir()


def test_extract_defaults_match_old_behavior(sample_project, tmp_path):
    """New kwargs default to the pre-0.2.0 behavior."""
    out = tmp_path / "out"
    extract_project(sample_project, out)
    md = (out / "pkg.md").read_text(encoding="utf-8")
    assert "## Source Code" in md
    assert "## Comments" in md
    assert "# Function: helper" in md


def test_extract_error_on_unwritable_output(sample_project, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    if out.stat().st_mode & 0o222:
        pytest.skip("directory is writable; cannot simulate")
    with pytest.raises(OSError):
        extract_project(sample_project, out / "sub" / "nested")
