"""Tests for the Markdown renderer."""

from __future__ import annotations

from markdownizer.parser import DocObject
from markdownizer.renderer import render_object, render_package_markdown


def _obj(
    kind: str,
    name: str = "X",
    docstring: str | None = "Docs.",
    file_path: str = "pkg/mod.py",
    lineno: int = 1,
    decorators: list[str] | None = None,
    base_classes: list[str] | None = None,
    source: str = "def X():\n    pass",
    preceding_comments: list[str] | None = None,
    inline_comments: list[str] | None = None,
) -> DocObject:
    return DocObject(
        name=name,
        qualified_name=name,
        kind=kind,
        lineno=lineno,
        end_lineno=lineno + 2,
        anchor_lineno=lineno,
        docstring=docstring,
        decorators=decorators or [],
        source=source,
        preceding_comments=preceding_comments or [],
        inline_comments=inline_comments or [],
        base_classes=base_classes or [],
        file_path=file_path,
    )


def test_render_function_sections(tmp_path):
    md = render_object(_obj("function", name="foo"), tmp_path)
    assert "# Function: foo" in md
    assert "**File:** `pkg/mod.py` · **Line:** 1" in md
    assert "## Description" in md
    assert "Docs." in md
    assert "## Source Code" in md
    assert "```python" in md


def test_render_no_docstring_marker(tmp_path):
    md = render_object(_obj("function", docstring=None), tmp_path)
    assert "_No docstring._" in md


def test_render_decorators(tmp_path):
    md = render_object(_obj("function", decorators=["@decorator", "@other"]), tmp_path)
    assert "## Decorators" in md
    assert "- `@decorator`" in md
    assert "- `@other`" in md


def test_render_base_classes(tmp_path):
    md = render_object(_obj("class", base_classes=["models.Model"]), tmp_path)
    assert "**Inherits from:** `models.Model`" in md


def test_render_comments(tmp_path):
    md = render_object(
        _obj(
            "function",
            preceding_comments=["# before"],
            inline_comments=["# inside"],
        ),
        tmp_path,
    )
    assert "## Comments" in md
    assert "### Preceding" in md
    assert "# before" in md
    assert "### Inline" in md
    assert "# inside" in md


def test_render_include_source_false(tmp_path):
    md = render_object(_obj("function"), tmp_path, include_source=False)
    assert "## Source Code" not in md
    assert "```python" not in md


def test_render_include_comments_false(tmp_path):
    md = render_object(
        _obj("function", inline_comments=["# inside"]),
        tmp_path,
        include_comments=False,
    )
    assert "## Comments" not in md
    assert "# inside" not in md


def test_render_module_file_path(tmp_path):
    md = render_object(_obj("module", file_path="pkg/mod.py"), tmp_path)
    assert "# Module: pkg/mod.py" in md
    assert "**File:** `pkg/mod.py`" in md


def test_render_package_via_init(tmp_path):
    init = _obj("module", file_path="pkg/__init__.py", docstring="Pkg docs.")
    mod = _obj("module", file_path="pkg/mod.py", docstring="Mod docs.")
    obj = _obj("function", name="foo", file_path="pkg/mod.py")
    md = render_package_markdown("pkg", [init, mod], [obj], tmp_path)
    assert md.count("# Package: pkg") == 1
    assert "# Module: pkg/mod.py" in md
    assert "# Function: foo" in md
    assert md.index("# Function: foo") > md.index("# Module: pkg/mod.py")


def test_render_package_without_init(tmp_path):
    mod = _obj("module", file_path="pkg/mod.py", docstring="Mod docs.")
    md = render_package_markdown("pkg", [mod], [], tmp_path)
    assert md.count("# Package: pkg") == 1
    assert "# Module: pkg/mod.py" in md


def test_render_package_without_modules(tmp_path):
    md = render_package_markdown("pkg", [], [], tmp_path)
    assert md.count("# Package: pkg") == 1


def test_render_package_objects_sorted_by_file_and_line(tmp_path):
    b = _obj("function", name="b", file_path="pkg/z.py", lineno=10)
    a = _obj("function", name="a", file_path="pkg/a.py", lineno=1)
    md = render_package_markdown("pkg", [], [b, a], tmp_path)
    assert md.index("# Function: a") < md.index("# Function: b")


def test_relative_path_posix(tmp_path):
    from markdownizer.renderer import _relative_path

    nested = tmp_path / "pkg" / "mod.py"
    nested.parent.mkdir()
    nested.touch()
    assert _relative_path(str(nested), tmp_path) == "pkg/mod.py"
