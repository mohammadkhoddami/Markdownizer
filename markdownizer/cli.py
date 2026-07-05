"""Command-line interface for Markdownizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markdownizer.extractor import extract_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="markdownizer",
        description="Extract existing documentation from a Python project into Markdown files.",
    )
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Python project root to scan.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("docs"),
        help="Directory where generated Markdown files will be written (default: ./docs).",
    )
    parser.add_argument(
        "--root-name",
        default="_root",
        help="Filename (without extension) for files that live at the project root (default: _root).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project: Path = args.project.resolve()
    output: Path = args.output.resolve()

    if not project.exists():
        print(f"error: project path does not exist: {project}", file=sys.stderr)
        return 2
    if not project.is_dir():
        print(f"error: project path is not a directory: {project}", file=sys.stderr)
        return 2

    written = extract_project(project, output, root_name=args.root_name)
    print(f"Wrote {len(written)} Markdown file(s) to {output}")
    for path in written:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())