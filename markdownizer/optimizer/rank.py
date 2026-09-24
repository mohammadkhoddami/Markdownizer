"""Deterministic symbol ranking.

Ranking answers "which parts of this repository matter most?" using only
static information: the import graph, framework classification, and symbol
metadata. No LLM, no embeddings, no randomness: the same repository always
produces the same ranks.

Methods:

* ``pagerank`` — PageRank power iteration over the module import graph
  (fixed iteration count for full determinism)
* ``fanout`` — in-degree of each module in the import graph
* ``simple`` — uniform file scores (no graph)

Rank values are deterministic for a given platform (IEEE-754 addition
order); the IR hash excludes ranks, so ``ir.hash`` is stable across
platforms even if floating-point tie-breaking ever differs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from markdownizer.imports import ImportEdge

if TYPE_CHECKING:
    from markdownizer.ir import ModuleInfo, ProjectIR, Symbol

_DAMPING = 0.85
_ITERATIONS = 50

_ENTRYPOINT_BOOSTS: dict[str, float] = {
    "urls.py": 1.0,
    "settings.py": 1.0,
    "manage.py": 0.5,
    "wsgi.py": 0.5,
}

_FRAMEWORK_BOOSTS: dict[str, float] = {
    "Management Command": 2.0,
    "Django Model": 1.0,
    "URL Configuration": 1.0,
    "DRF ViewSet": 0.5,
    "DRF Serializer": 0.5,
}

_PUBLIC_FACTOR = 1.5
_PRIVATE_FACTOR = 0.7
_DOCUMENTED_FACTOR = 1.3
_UNDOCUMENTED_FACTOR = 0.8


def _module_graph(
    modules: list[ModuleInfo],
    imports: list[ImportEdge],
) -> tuple[list[str], dict[str, list[str]]]:
    """Return (sorted node paths, adjacency of resolved imports)."""
    nodes = sorted(module.path for module in modules)
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for edge in imports:
        if edge.resolved and edge.to_module in adjacency:
            adjacency[edge.from_module].append(edge.to_module)
    for targets in adjacency.values():
        targets.sort()
    return nodes, adjacency


def _pagerank(nodes: list[str], adjacency: dict[str, list[str]]) -> dict[str, float]:
    if not nodes:
        return {}
    size = len(nodes)
    ranks = {node: 1.0 / size for node in nodes}
    for _ in range(_ITERATIONS):
        dangling = sum(ranks[node] for node in nodes if not adjacency[node])
        new_ranks = {node: (1.0 - _DAMPING) / size for node in nodes}
        dangling_share = _DAMPING * dangling / size
        for node in nodes:
            new_ranks[node] += dangling_share
        for source, targets in adjacency.items():
            if targets:
                share = _DAMPING * ranks[source] / len(targets)
                for target in targets:
                    new_ranks[target] += share
        ranks = new_ranks
    return ranks


def _fanout(nodes: list[str], adjacency: dict[str, list[str]]) -> dict[str, float]:
    indegree = {node: 0 for node in nodes}
    for targets in adjacency.values():
        for target in targets:
            indegree[target] += 1
    return {node: float(indegree[node] + 1) for node in nodes}


def _file_boost(module: ModuleInfo, symbols: list[Symbol]) -> float:
    boost = 1.0
    name = module.path.rsplit("/", 1)[-1]
    boost += _ENTRYPOINT_BOOSTS.get(name, 0.0)
    for symbol in symbols:
        boost += _FRAMEWORK_BOOSTS.get(symbol.framework, 0.0)
    return boost


def compute_file_scores(
    modules: list[ModuleInfo],
    imports: list[ImportEdge],
    symbols: list[Symbol],
    method: str = "pagerank",
) -> dict[str, float]:
    """Compute normalized importance scores for every module file.

    ``method`` is one of ``"pagerank"``, ``"fanout"``, or ``"simple"``.
    """
    nodes, adjacency = _module_graph(modules, imports)
    if method == "pagerank":
        base = _pagerank(nodes, adjacency)
    elif method == "fanout":
        base = _fanout(nodes, adjacency)
    elif method == "simple":
        base = {node: 1.0 for node in nodes}
    else:
        choices = "pagerank, fanout, simple"
        raise ValueError(f"unknown rank method: {method!r} (expected one of: {choices})")

    symbols_by_file: dict[str, list[Symbol]] = {}
    for symbol in symbols:
        symbols_by_file.setdefault(symbol.file_path, []).append(symbol)

    raw = {
        module.path: base.get(module.path, 1.0)
        * _file_boost(module, symbols_by_file.get(module.path, []))
        for module in modules
    }
    maximum = max(raw.values()) if raw else 0.0
    if maximum == 0.0:
        return {path: 0.0 for path in raw}
    return {path: score / maximum for path, score in raw.items()}


def symbol_importance(file_score: float, symbol: Symbol) -> float:
    """Combine file importance with symbol-level factors (public, documented)."""
    visibility = _PUBLIC_FACTOR if symbol.is_public else _PRIVATE_FACTOR
    documented = symbol.docstring not in (None, "")
    documentation = _DOCUMENTED_FACTOR if documented else _UNDOCUMENTED_FACTOR
    return file_score * visibility * documentation


def rank_ir(ir: ProjectIR, method: str = "pagerank") -> ProjectIR:
    """Fill ``ir.file_ranks`` and every ``Symbol.rank`` in place.

    Ranks are deterministic for a given repository state.
    """
    ir.file_ranks = compute_file_scores(ir.modules, ir.imports, ir.symbols, method=method)
    for symbol in ir.symbols:
        symbol.rank = symbol_importance(ir.file_ranks.get(symbol.file_path, 1.0), symbol)
    return ir
