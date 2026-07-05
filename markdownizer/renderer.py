"""Render DocObjects into Markdown text."""

from __future__ import annotations

from pathlib import Path

from markdownizer.classifier import classify
from markdownizer.parser import DocObject


def _format_comments(comments: list[str]) -> str:
    if not comments:
        return ""
    return "\n".join(comments).rstrip() + "\n"


def render_object(obj: DocObject, project_root: Path) -> str:
    """Render a single DocObject to a Markdown section."""
    label = classify(obj)

    if obj.kind == "module":
        rel = _relative_path(obj.file_path, project_root)
        name = rel or obj.name
        if label == "Package":
            title = f"# {label}: {_package_name_from_path(rel)}"
        else:
            title = f"# {label}: {name}"
    else:
        title = f"# {label}: {obj.name}"

    sections: list[str] = [title, ""]

    if obj.kind == "module":
        rel = _relative_path(obj.file_path, project_root)
        sections.append(f"**File:** `{rel}`")
        sections.append("")
    else:
        rel = _relative_path(obj.file_path, project_root)
        sections.append(f"**File:** `{rel}` · **Line:** {obj.lineno}")
        sections.append("")

    if obj.decorators:
        sections.append("## Decorators")
        sections.append("")
        for dec in obj.decorators:
            sections.append(f"- `{dec}`")
        sections.append("")

    if obj.kind == "class" and obj.base_classes:
        bases = ", ".join(f"`{b}`" for b in obj.base_classes)
        sections.append(f"**Inherits from:** {bases}")
        sections.append("")

    sections.append("## Description")
    sections.append("")
    if obj.docstring is not None and obj.docstring != "":
        sections.append(obj.docstring.rstrip())
        sections.append("")
    else:
        sections.append("_No docstring._")
        sections.append("")

    preceding_text = _format_comments(obj.preceding_comments)
    inline_text = _format_comments(obj.inline_comments)
    if preceding_text or inline_text:
        sections.append("## Comments")
        sections.append("")
        if preceding_text and inline_text:
            sections.append("### Preceding")
            sections.append("")
            sections.append(preceding_text.rstrip())
            sections.append("")
            sections.append("### Inline")
            sections.append("")
            sections.append(inline_text.rstrip())
            sections.append("")
        else:
            text = preceding_text or inline_text
            sections.append(text.rstrip())
            sections.append("")

    source = obj.source.rstrip()
    if source:
        sections.append("## Source Code")
        sections.append("")
        sections.append("```python")
        sections.append(source)
        sections.append("```")
        sections.append("")

    return "\n".join(sections)


def render_package_markdown(
    package_name: str,
    module_obj: DocObject,
    objects: list[DocObject],
    project_root: Path,
) -> str:
    """Render all objects belonging to one package into a single Markdown document."""
    parts: list[str] = []

    header = [f"# Package: {package_name}", ""]
    parts.append("\n".join(header))

    module_section = render_object(module_obj, project_root)
    parts.append(module_section)

    objects_sorted = sorted(objects, key=lambda o: (o.file_path, o.lineno))
    for obj in objects_sorted:
        parts.append("---")
        parts.append("")
        parts.append(render_object(obj, project_root))

    return "\n".join(parts).rstrip() + "\n"


def _relative_path(file_path: str, project_root: Path) -> str:
    try:
        return str(Path(file_path).resolve().relative_to(project_root.resolve()))
    except ValueError:
        return file_path


def _package_name_from_path(rel_path: str) -> str:
    parts = Path(rel_path).parts
    if not parts:
        return rel_path
    if parts[-1] == "__init__.py":
        return ".".join(parts[:-1]) if len(parts) > 1 else parts[0]
    return ".".join(parts)