"""Deterministic static import analysis.

Collects ``import`` / ``from ... import`` statements from Python source via
``ast`` and resolves them against the set of project modules when the target
can be mapped deterministically to a project file.

Resolution is conservative: unresolved imports are marked ``external`` and
never guessed. Project code is never imported or executed.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any


@dataclass
class ImportEdge:
    """A single import statement resolved against the project, if possible."""

    from_module: str
    imported_module: str
    alias: str | None
    level: int
    resolved: bool
    to_module: str | None
    external: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_module": self.from_module,
            "imported_module": self.imported_module,
            "alias": self.alias,
            "level": self.level,
            "resolved": self.resolved,
            "to_module": self.to_module,
            "external": self.external,
        }


def _package_of(rel_path: str) -> str:
    return rel_path.rsplit("/", 1)[0] if "/" in rel_path else ""


def _resolve_absolute(module: str, module_map: dict[str, str]) -> str | None:
    return module_map.get(module)


def _resolve_relative(
    from_rel_path: str, level: int, module: str, module_map: dict[str, str]
) -> str | None:
    """Resolve a relative import (``from .`` / ``from ..``) to a module path.

    ``level`` is the number of leading dots (1 for ``.``). The base package is
    the package of the importing module, walked up ``level - 1`` times.
    """
    package = _package_of(from_rel_path)
    parts = package.split(".") if package else []
    for _ in range(level - 1):
        if not parts:
            return None
        parts.pop()
    base = ".".join(parts)
    candidate = f"{base}.{module}" if base else module
    return module_map.get(candidate)


def _collect_statement_imports(
    node: ast.AST, module_map: dict[str, str], from_rel_path: str
) -> list[ImportEdge]:
    edges: list[ImportEdge] = []

    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            for alias in child.names:
                target = _resolve_absolute(alias.name, module_map)
                edges.append(
                    ImportEdge(
                        from_module=from_rel_path,
                        imported_module=alias.name,
                        alias=alias.asname,
                        level=0,
                        resolved=target is not None,
                        to_module=target,
                        external=target is None,
                    )
                )
        elif isinstance(child, ast.ImportFrom):
            if child.module is None:
                # ``from . import x`` — the imported names are resolved
                # relative to the current package.
                for alias in child.names:
                    target = _resolve_relative(from_rel_path, child.level, alias.name, module_map)
                    edges.append(
                        ImportEdge(
                            from_module=from_rel_path,
                            imported_module=alias.name,
                            alias=alias.asname,
                            level=child.level,
                            resolved=target is not None,
                            to_module=target,
                            external=target is None,
                        )
                    )
            else:
                if child.level:
                    target = _resolve_relative(from_rel_path, child.level, child.module, module_map)
                else:
                    target = _resolve_absolute(child.module, module_map)
                edges.append(
                    ImportEdge(
                        from_module=from_rel_path,
                        imported_module=child.module,
                        alias=None,
                        level=child.level,
                        resolved=target is not None,
                        to_module=target,
                        external=target is None,
                    )
                )

    return edges


def collect_import_edges(
    source: str, from_rel_path: str, module_map: dict[str, str]
) -> list[ImportEdge]:
    """Collect import edges for one module.

    Args:
        source: The module source text.
        from_rel_path: POSIX path of the module relative to the project root.
        module_map: Mapping of dotted module name -> relative POSIX path for
            every Python file in the project.

    Returns:
        Sorted import edges. Unresolved imports are marked ``external=True``.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    edges = _collect_statement_imports(tree, module_map, from_rel_path)
    edges.sort(key=lambda e: (e.imported_module, e.level, e.alias or ""))
    return edges
