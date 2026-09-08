"""Compact backend: a low-volume, structure-oriented representation.

Contains packages, modules, public symbols, signatures, inheritance,
decorators, and docstrings — without full source bodies. The output is
deterministic and intended as a high-signal overview for AI consumption.
"""

from __future__ import annotations

from markdownizer.backends.base import RenderOptions
from markdownizer.ir import ModuleInfo, ProjectIR, Symbol
from markdownizer.renderer import format_signature


def _symbol_line(symbol: Symbol, options: RenderOptions) -> list[str]:
    lines = [f"# {symbol.framework}: {symbol.qualified_name} — {symbol.file_path}:{symbol.lineno}"]
    if options.include_source is not False:
        signature = format_signature(symbol)
        if signature:
            lines.append(f"```{signature}```")
    if symbol.base_classes:
        lines.append(f"inherits: {', '.join(symbol.base_classes)}")
    if symbol.decorators:
        lines.append(f"decorators: {', '.join(symbol.decorators)}")
    if symbol.docstring not in (None, ""):
        lines.append("")
        lines.append(symbol.docstring.rstrip())
    lines.append("")
    return lines


class CompactBackend:
    """Render a single structure-oriented ``context.compact.md`` file."""

    name = "compact"

    def render(self, ir: ProjectIR, options: RenderOptions) -> dict[str, str]:
        lines = [
            f"# Project: {ir.name} (IR v{ir.ir_version})",
            "",
            (
                f"# Packages: {ir.stats.package_count} | "
                f"Modules: {ir.stats.module_count} | "
                f"Symbols: {ir.stats.symbol_count} | "
                f"Lines: {ir.stats.line_count}"
            ),
            "",
        ]

        modules_by_package: dict[str, list[ModuleInfo]] = {}
        symbols_by_package: dict[str, list[Symbol]] = {}
        for module in ir.modules:
            modules_by_package.setdefault(module.package, []).append(module)
        for symbol in ir.symbols:
            package = symbol.file_path.rsplit("/", 1)[0] if "/" in symbol.file_path else ""
            symbols_by_package.setdefault(package, []).append(symbol)

        for package in sorted(set(modules_by_package) | set(symbols_by_package)):
            lines.append(f"# Package: {package if package else options.root_name}")
            lines.append("")
            for module in modules_by_package.get(package, []):
                lines.append(f"# Module: {module.path}")
                if module.docstring not in (None, ""):
                    lines.append("")
                    lines.append(module.docstring.rstrip())
                lines.append("")
            symbols = symbols_by_package.get(package, [])
            if not options.include_undocumented:
                symbols = [s for s in symbols if s.docstring not in (None, "")]
            for symbol in symbols:
                if not symbol.is_public:
                    continue
                lines.extend(_symbol_line(symbol, options))

        return {"context.compact.md": "\n".join(lines).rstrip() + "\n"}
