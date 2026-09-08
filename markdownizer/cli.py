"""Command-line interface for Markdownizer."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from markdownizer import __version__
from markdownizer.extractor import extract_project

logger = logging.getLogger(__name__)


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("docs"),
        help="Directory where generated files will be written (default: ./docs).",
    )
    parser.add_argument(
        "--root-name",
        default="_root",
        help=(
            "Filename (without extension) for files that live at the project root (default: _root)."
        ),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="GLOB",
        help="Glob pattern of paths to skip, e.g. 'tests/*' or 'migrations'. May be repeated.",
    )
    parser.add_argument(
        "--no-source",
        action="store_true",
        help="Omit the '## Source Code' section from the output.",
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Omit the '## Comments' section from the output.",
    )
    parser.add_argument(
        "--only-documented",
        action="store_true",
        help="Only include objects that have a docstring.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "compact"],
        default="markdown",
        help="Output backend (default: markdown).",
    )


def _add_verbose_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (repeat for debug-level detail).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress non-error output.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Parser for the legacy invocation ``markdownizer <project> -o <out>``."""
    parser = argparse.ArgumentParser(
        prog="markdownizer",
        description=(
            "Extract existing documentation from a Python project into "
            "Markdown files. Use 'markdownizer build <project>' for format "
            "selection; the legacy form below is kept as a compatibility alias."
        ),
    )
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Python project root to scan.",
    )
    _add_common_arguments(parser)
    _add_verbose_arguments(parser)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def build_build_parser() -> argparse.ArgumentParser:
    """Parser for ``markdownizer build <project>``."""
    parser = argparse.ArgumentParser(
        prog="markdownizer build",
        description=(
            "Scan a project and emit a deterministic representation: "
            "Markdown (default), JSON project IR, or compact context."
        ),
    )
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Python project root to scan.",
    )
    _add_common_arguments(parser)
    _add_verbose_arguments(parser)
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.quiet:
        level = logging.ERROR
    elif args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    project: Path = args.project.resolve()
    output: Path = args.output.resolve()

    if not project.exists():
        print(f"error: project path does not exist: {project}", file=sys.stderr)
        return 2
    if not project.is_dir():
        print(f"error: project path is not a directory: {project}", file=sys.stderr)
        return 2

    try:
        written = extract_project(
            project,
            output,
            root_name=args.root_name,
            exclude=args.exclude,
            include_source=not args.no_source,
            include_comments=not args.no_comments,
            include_undocumented=not args.only_documented,
            format=args.format,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Wrote {len(written)} file(s) to {output}")
        for path in written:
            print(f"  - {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list and args_list[0] == "build":
        parser = build_build_parser()
        args = parser.parse_args(args_list[1:])
    else:
        parser = build_parser()
        args = parser.parse_args(args_list)
    return _run(args)


if __name__ == "__main__":
    sys.exit(main())
