"""Orchestrates scanning, parsing, IR building, and backend output writing."""

from __future__ import annotations

import logging
from pathlib import Path

from markdownizer.backends import RenderOptions, get_backend
from markdownizer.ir import build_project_ir
from markdownizer.renderer import SourceMode

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
    include_source: SourceMode = True,
    include_comments: bool = True,
    include_undocumented: bool = True,
    format: str = "markdown",
) -> list[Path]:
    """Scan the project, build a Project IR, and write backend output.

    Args:
        project_root: Directory to scan recursively.
        output_dir: Directory where generated files will be written.
        root_name: Filename (without extension) for files that live at the
            project root.
        exclude: Optional glob patterns (e.g. ``"tests/*"``, ``"migrations"``)
            matched against paths relative to ``project_root``.
        include_source: Include source: ``True`` (full), ``False`` (none), or
            ``"signature"`` (declaration line only).
        include_comments: Include the ``## Comments`` section.
        include_undocumented: Keep objects that have no docstring.
        format: Output backend: ``"markdown"`` (default), ``"json"``, or
            ``"compact"``.
    """
    project_root = project_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    ir = build_project_ir(project_root, exclude=exclude)
    backend = get_backend(format)
    options = RenderOptions(
        root_name=root_name,
        include_source=include_source,
        include_comments=include_comments,
        include_undocumented=include_undocumented,
    )
    files = backend.render(ir, options)

    written: list[Path] = []
    for filename, content in files.items():
        out_path = output_dir / filename
        try:
            out_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            logger.error("could not write %s: %s", out_path, exc)
            raise
        written.append(out_path)

    logger.info(
        "Wrote %d file(s) to %s (%d Python file(s) scanned)",
        len(written),
        output_dir,
        len(ir.modules),
    )
    return written
