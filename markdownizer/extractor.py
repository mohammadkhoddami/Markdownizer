"""Orchestrates scanning, parsing, grouping, and writing of Markdown output."""

from __future__ import annotations

import logging
from pathlib import Path

from markdownizer.parser import DocObject, parse_file
from markdownizer.renderer import render_package_markdown
from markdownizer.scanner import scan_python_files

logger = logging.getLogger(__name__)


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
    exclude: list[str] | None = None,
    include_source: bool = True,
    include_comments: bool = True,
    include_undocumented: bool = True,
) -> list[Path]:
    """Scan the project, extract docs, and write one Markdown file per package.

    Args:
        project_root: Directory to scan recursively.
        output_dir: Directory where generated Markdown files will be written.
        root_name: Filename (without extension) for files that live at the
            project root.
        exclude: Optional glob patterns (e.g. ``"tests/*"``, ``"migrations"``)
            matched against paths relative to ``project_root``.
        include_source: Include the ``## Source Code`` section for every object.
        include_comments: Include the ``## Comments`` section for every object.
        include_undocumented: Keep objects that have no docstring.
    """
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[str, tuple[list[DocObject], list[DocObject]]] = {}
    scanned = 0

    for py_file in scan_python_files(project_root, exclude=exclude):
        scanned += 1
        module_obj, objects = parse_file(str(py_file))
        if not include_undocumented:
            objects = [o for o in objects if o.docstring not in (None, "")]
        key = _package_key(py_file, project_root)
        modules, existing_objects = groups.get(key, ([], []))
        modules.append(module_obj)
        groups[key] = (modules, existing_objects + objects)

    written: list[Path] = []
    for key, (modules, objects) in sorted(groups.items()):
        label = _package_label(key, root_name)
        markdown = render_package_markdown(
            label,
            modules,
            objects,
            project_root,
            include_source=include_source,
            include_comments=include_comments,
        )
        out_path = output_dir / f"{label}.md"
        try:
            out_path.write_text(markdown, encoding="utf-8")
        except OSError as exc:
            logger.error("could not write %s: %s", out_path, exc)
            raise
        written.append(out_path)

    logger.info(
        "Wrote %d Markdown file(s) to %s (%d Python file(s) scanned)",
        len(written),
        output_dir,
        scanned,
    )
    return written
