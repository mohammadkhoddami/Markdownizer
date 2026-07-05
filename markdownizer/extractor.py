"""Orchestrates scanning, parsing, grouping, and writing of Markdown output."""

from __future__ import annotations

from pathlib import Path

from markdownizer.parser import DocObject, parse_file
from markdownizer.renderer import render_package_markdown
from markdownizer.scanner import scan_python_files


def _package_key(file_path: Path, project_root: Path) -> str:
    try:
        rel = file_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        rel = Path(file_path)
    parent = rel.parent
    if parent == Path("."):
        return ""
    return str(parent)


def _package_label(key: str, root_name: str) -> str:
    if key == "":
        return root_name
    return key.replace("/", ".").replace("\\", ".")


def extract_project(
    project_root: Path,
    output_dir: Path,
    root_name: str = "_root",
) -> list[Path]:
    """Scan the project, extract docs, and write one Markdown file per package."""
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[str, tuple[DocObject, list[DocObject]]] = {}

    for py_file in scan_python_files(project_root):
        module_obj, objects = parse_file(str(py_file))
        key = _package_key(py_file, project_root)
        if key in groups:
            existing_module, existing_objects = groups[key]
            merged_module = _merge_module_objects(existing_module, module_obj)
            groups[key] = (merged_module, existing_objects + objects)
        else:
            groups[key] = (module_obj, objects)

    written: list[Path] = []
    for key, (module_obj, objects) in sorted(groups.items()):
        label = _package_label(key, root_name)
        markdown = render_package_markdown(label, module_obj, objects, project_root)
        out_path = output_dir / f"{label}.md"
        out_path.write_text(markdown, encoding="utf-8")
        written.append(out_path)

    return written


def _merge_module_objects(a: DocObject, b: DocObject) -> DocObject:
    docstring = a.docstring if a.docstring else b.docstring
    inline = list(a.inline_comments) + list(b.inline_comments)
    source = (a.source.rstrip() + "\n\n" + b.source.lstrip()).strip()
    return DocObject(
        name=a.name,
        qualified_name=a.qualified_name,
        kind=a.kind,
        lineno=a.lineno,
        end_lineno=max(a.end_lineno, b.end_lineno),
        anchor_lineno=a.anchor_lineno,
        docstring=docstring,
        source=source,
        inline_comments=inline,
        file_path=a.file_path,
    )