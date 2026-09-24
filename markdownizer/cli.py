"""Command-line interface for Markdownizer."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from markdownizer import __version__
from markdownizer.extractor import extract_project
from markdownizer.ir import build_project_ir

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
            "selection; the legacy form below is kept as a compatibility "
            "alias. If your project directory is named 'build', 'context', "
            "or 'stats', prefix it with './'."
        ),
    )
    parser.set_defaults(command="build")
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
    parser.set_defaults(command="build")
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Python project root to scan.",
    )
    _add_common_arguments(parser)
    _add_verbose_arguments(parser)
    return parser


def build_context_parser() -> argparse.ArgumentParser:
    """Parser for ``markdownizer context <project>``."""
    parser = argparse.ArgumentParser(
        prog="markdownizer context",
        description=(
            "Produce a budgeted, ranked context artifact from a project: "
            "the best possible representation within --max-tokens."
        ),
    )
    parser.set_defaults(command="context")
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Python project root to scan.",
    )
    _add_verbose_arguments(parser)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("docs"),
        help="Directory where context.md will be written (default: ./docs).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="GLOB",
        help="Glob pattern of paths to skip, e.g. 'tests/*'. May be repeated.",
    )
    parser.add_argument(
        "--max-tokens",
        type=float,
        default=20000.0,
        help="Target token budget (soft limit, default: 20000).",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help=(
            "Context profile: architecture (default), api, debugging, refactor, django, onboarding."
        ),
    )
    parser.add_argument(
        "--rank",
        choices=["pagerank", "fanout", "simple"],
        default="pagerank",
        help="File importance method (default: pagerank).",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Space-separated keywords to prefilter symbols (deterministic).",
    )
    parser.add_argument(
        "--prefer-tiktoken",
        action="store_true",
        help="Use tiktoken for token estimates when installed.",
    )
    return parser


def build_stats_parser() -> argparse.ArgumentParser:
    """Parser for ``markdownizer stats <project>``."""
    parser = argparse.ArgumentParser(
        prog="markdownizer stats",
        description="Show deterministic statistics for a project.",
    )
    parser.set_defaults(command="stats")
    parser.add_argument(
        "project",
        type=Path,
        help="Path to the Python project root to scan.",
    )
    _add_verbose_arguments(parser)
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="GLOB",
        help="Glob pattern of paths to skip, e.g. 'tests/*'. May be repeated.",
    )
    parser.add_argument(
        "--rank",
        choices=["pagerank", "fanout", "simple"],
        default="pagerank",
        help="File importance method (default: pagerank).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human summary.",
    )
    return parser


def _validate_project(project: Path) -> int | None:
    if not project.exists():
        print(f"error: project path does not exist: {project}", file=sys.stderr)
        return 2
    if not project.is_dir():
        print(f"error: project path is not a directory: {project}", file=sys.stderr)
        return 2
    return None


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

    command = getattr(args, "command", "build")
    project: Path = args.project.resolve()

    error = _validate_project(project)
    if error is not None:
        return error

    if command == "context":
        return _run_context(args, project)
    if command == "stats":
        return _run_stats(args, project)

    output: Path = args.output.resolve()
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


def _run_context(args: argparse.Namespace, project: Path) -> int:
    from markdownizer.optimizer import optimize_context

    output: Path = args.output.resolve()
    try:
        ir = build_project_ir(project, exclude=args.exclude)
        context = optimize_context(
            ir,
            max_tokens=args.max_tokens,
            profile=args.profile,
            query=args.query,
            rank_method=args.rank,
            prefer_tiktoken=args.prefer_tiktoken,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        output.mkdir(parents=True, exist_ok=True)
        out_path = output / "context.md"
        out_path.write_text(context.text, encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(
            f"Wrote context.md ({context.included_symbols}/{context.total_symbols} "
            f"symbols, ~{context.estimated_tokens:.0f} tokens, "
            f"profile={context.profile}, rank={context.rank_method}) to {output}"
        )
    return 0


def _run_stats(args: argparse.Namespace, project: Path) -> int:
    from markdownizer.optimizer import count_tokens, rank_ir

    try:
        ir = build_project_ir(project, exclude=args.exclude)
        rank_ir(ir, method=args.rank)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        import json

        payload = {
            "name": ir.name,
            "ir_version": ir.ir_version,
            "hash": ir.hash,
            "stats": ir.stats.to_dict(),
            "rank_method": args.rank,
            "top_files": _top_files(ir, limit=10),
            "top_symbols": _top_symbols(ir, limit=10),
        }
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    token_estimate = sum(count_tokens(m.source) for m in ir.modules)
    print(f"Project: {ir.name} (IR v{ir.ir_version})")
    print(f"Hash: {ir.hash}")
    print(f"Python files: {ir.stats.module_count}")
    print(f"Packages: {ir.stats.package_count}")
    print(
        f"Symbols: {ir.stats.symbol_count} (public: {ir.stats.public_count}, "
        f"documented: {ir.stats.documented_count})"
    )
    print(f"Lines: {ir.stats.line_count}")
    print(f"Estimated tokens (chars/3.3): ~{token_estimate:.0f}")
    print()
    print("Top files by importance:")
    for path, score in _top_files(ir, limit=10):
        print(f"  {score:.3f}  {path}")
    print()
    print("Top symbols:")
    for name, score in _top_symbols(ir, limit=10):
        print(f"  {score:.3f}  {name}")
    return 0


def _top_files(ir: Any, limit: int) -> list[tuple[str, float]]:
    ranked = sorted(ir.file_ranks.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:limit]


def _top_symbols(ir: Any, limit: int) -> list[tuple[str, float]]:
    ranked = sorted(
        ir.symbols,
        key=lambda s: (-s.rank, s.file_path, s.lineno),
    )
    return [(f"{s.file_path}::{s.qualified_name}", s.rank) for s in ranked[:limit]]


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list:
        command = args_list[0]
        if command == "build":
            parser = build_build_parser()
            args = parser.parse_args(args_list[1:])
        elif command == "context":
            parser = build_context_parser()
            args = parser.parse_args(args_list[1:])
        elif command == "stats":
            parser = build_stats_parser()
            args = parser.parse_args(args_list[1:])
        else:
            parser = build_parser()
            args = parser.parse_args(args_list)
    else:
        parser = build_parser()
        args = parser.parse_args(args_list)
    return _run(args)


if __name__ == "__main__":
    sys.exit(main())
