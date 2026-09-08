"""Markdown backend: one Markdown file per package (the historical output).

The rendering logic lives in :mod:`markdownizer.renderer`; this backend
groups the IR by package and drives it.
"""

from __future__ import annotations

from markdownizer.backends.base import RenderOptions
from markdownizer.ir import ModuleInfo, ProjectIR, Symbol
from markdownizer.parser import DocObject
from markdownizer.renderer import render_package_markdown


def _module_docobject(module: ModuleInfo) -> DocObject:
    """Adapt an IR module back into a DocObject for the renderer."""
    return DocObject(
        name=module.path,
        qualified_name=module.path,
        kind="module",
        lineno=1,
        end_lineno=module.line_count,
        anchor_lineno=1,
        docstring=module.docstring,
        source=module.source,
        inline_comments=list(module.inline_comments),
        file_path=module.path,
    )


class MarkdownBackend:
    """Render one ``{package}.md`` file per package."""

    name = "markdown"

    def render(self, ir: ProjectIR, options: RenderOptions) -> dict[str, str]:
        modules_by_package: dict[str, list[ModuleInfo]] = {}
        symbols_by_package: dict[str, list[Symbol]] = {}

        for module in ir.modules:
            modules_by_package.setdefault(module.package, []).append(module)
        for symbol in ir.symbols:
            package = symbol.file_path.rsplit("/", 1)[0] if "/" in symbol.file_path else ""
            symbols_by_package.setdefault(package, []).append(symbol)

        out: dict[str, str] = {}
        for package in sorted(set(modules_by_package) | set(symbols_by_package)):
            label = package.replace("/", ".") if package else options.root_name
            modules = modules_by_package.get(package, [])
            symbols = symbols_by_package.get(package, [])
            if not options.include_undocumented:
                symbols = [s for s in symbols if s.docstring not in (None, "")]
            markdown = render_package_markdown(
                label,
                [_module_docobject(m) for m in modules],
                symbols,  # Symbols duck-type DocObject for the renderer
                None,
                include_source=options.include_source,
                include_comments=options.include_comments,
            )
            out[f"{label}.md"] = markdown
        return out
