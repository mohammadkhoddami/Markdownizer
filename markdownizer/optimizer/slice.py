"""Budget-aware context packing.

Turns a ranked ProjectIR into an AI-ready context artifact within a token
budget, using deterministic layered emission:

* layer 0 — project index (packages, modules, docstrings)
* layer 1 — per-symbol blocks: full source for the highest-ranked symbols,
  signature-only for the rest (or docstrings only for ``include_source``
  profiles without source)

Each symbol is emitted exactly once. High-ranked symbols are placed at the
start and end of the artifact (primacy/recency bias); lower-ranked content
sits in the middle. The reported token estimate counts the complete
artifact, header included.
"""

from __future__ import annotations

from dataclasses import dataclass

from markdownizer.ir import ProjectIR, Symbol
from markdownizer.optimizer.profiles import Profile, get_profile
from markdownizer.optimizer.rank import rank_ir
from markdownizer.optimizer.tokens import count_tokens
from markdownizer.renderer import render_object

_BUDGET_SLOP = 1.1


@dataclass
class OptimizedContext:
    text: str
    estimated_tokens: float
    max_tokens: float
    profile: str
    rank_method: str
    included_symbols: int
    total_symbols: int


def _query_matches(symbol: Symbol, query: str) -> bool:
    haystack = " ".join(
        (
            symbol.name,
            symbol.qualified_name,
            symbol.framework,
            symbol.docstring or "",
        )
    ).lower()
    return all(part in haystack for part in query.lower().split())


def _select_symbols(ir: ProjectIR, profile: Profile, query: str | None) -> list[Symbol]:
    selected = list(ir.symbols)
    if query:
        selected = [s for s in selected if _query_matches(s, query)]
    if profile.public_only:
        selected = [s for s in selected if s.is_public]
    if not profile.include_undocumented:
        selected = [s for s in selected if s.docstring not in (None, "")]
    selected.sort(key=lambda s: (-s.rank, s.file_path, s.lineno, s.qualified_name))
    return selected


def _edge_place(symbols: list[Symbol]) -> list[Symbol]:
    """Interleave highest-ranked symbols to the start and end of the list."""
    ordered: list[Symbol] = []
    left: list[Symbol] = []
    right: list[Symbol] = []
    for index, symbol in enumerate(symbols):
        if index % 2 == 0:
            left.append(symbol)
        else:
            right.append(symbol)
    ordered.extend(left)
    ordered.extend(reversed(right))
    return ordered


def _render_index(ir: ProjectIR) -> str:
    lines = [
        f"# Project: {ir.name}",
        f"# IR: v{ir.ir_version} | Packages: {ir.stats.package_count} | "
        f"Modules: {ir.stats.module_count} | Symbols: {ir.stats.symbol_count} | "
        f"Lines: {ir.stats.line_count}",
        "",
    ]
    for package in sorted(ir.packages, key=lambda p: p.name):
        lines.append(f"# Package: {package.name}")
        lines.append("")
    return "\n".join(lines)


def _render_module_index(ir: ProjectIR) -> str:
    lines = ["# Modules:", ""]
    for module in sorted(ir.modules, key=lambda m: m.path):
        doc = module.docstring.splitlines()[0] if module.docstring else ""
        lines.append(f"- `{module.path}`{(' — ' + doc) if doc else ''}")
    lines.append("")
    return "\n".join(lines)


def _block_tokens(text: str, prefer_tiktoken: bool) -> float:
    return count_tokens(text, prefer_tiktoken=prefer_tiktoken)


def _symbol_block(
    symbol: Symbol,
    profile: Profile,
    prefer_tiktoken: bool,
    budget: float,
) -> tuple[str, float] | None:
    """Render one symbol exactly once; ``None`` when nothing fits the budget."""
    comments = profile.include_comments
    if profile.include_source is True:
        src_text = render_object(
            symbol,
            None,
            include_source=True,
            include_comments=comments,
        )
        src_cost = _block_tokens(src_text, prefer_tiktoken)
        if src_cost <= budget:
            return src_text, src_cost
        sig_text = render_object(
            symbol,
            None,
            include_source="signature",
            include_comments=comments,
        )
        sig_cost = _block_tokens(sig_text, prefer_tiktoken)
        return (sig_text, sig_cost) if sig_cost <= budget else None

    if profile.include_source == "signature":
        sig_text = render_object(
            symbol,
            None,
            include_source="signature",
            include_comments=comments,
        )
        sig_cost = _block_tokens(sig_text, prefer_tiktoken)
        return (sig_text, sig_cost) if sig_cost <= budget else None

    if symbol.docstring:
        doc_text = render_object(
            symbol,
            None,
            include_source=False,
            include_comments=comments,
        )
        doc_cost = _block_tokens(doc_text, prefer_tiktoken)
        return (doc_text, doc_cost) if doc_cost <= budget else None
    return None


def optimize_context(
    ir: ProjectIR,
    max_tokens: float,
    profile: str | None = None,
    query: str | None = None,
    rank_method: str = "pagerank",
    prefer_tiktoken: bool = False,
) -> OptimizedContext:
    """Produce a budgeted, ranked context artifact from a ProjectIR.

    Args:
        ir: The project IR (ranked in place by this function).
        max_tokens: Target token budget (soft limit, ±10% slop). Must be > 0.
        profile: Profile preset name (see :mod:`markdownizer.optimizer.profiles`).
        query: Optional space-separated keyword prefilter on symbol names,
            frameworks, and docstrings (deterministic substring match).
        rank_method: ``pagerank`` (default), ``fanout``, or ``simple``.
        prefer_tiktoken: Use ``tiktoken`` when installed for token estimates.

    Raises:
        ValueError: If ``max_tokens`` is not positive.
    """
    if float(max_tokens) <= 0:
        raise ValueError(f"max_tokens must be positive, got {max_tokens!r}")
    rank_ir(ir, method=rank_method)
    profile_obj = get_profile(profile)
    total_symbols = len(ir.symbols)

    header = (
        f"# Context: {ir.name} "
        f"(profile={profile_obj.name}, rank={rank_method}, "
        f"max_tokens={int(max_tokens)})"
    )
    header_cost = _block_tokens(header, prefer_tiktoken)
    budget = float(max_tokens) * _BUDGET_SLOP - header_cost

    parts: list[str] = []
    total: float = 0.0

    index = _render_index(ir)
    index_cost = _block_tokens(index, prefer_tiktoken)
    if index_cost <= budget:
        parts.append(index)
        total += index_cost

    module_index = _render_module_index(ir)
    module_cost = _block_tokens(module_index, prefer_tiktoken)
    if module_cost <= budget:
        parts.append(module_index)
        total += module_cost

    symbols = _select_symbols(ir, profile_obj, query)
    ordered = _edge_place(symbols)

    included = 0
    for symbol in ordered:
        block = _symbol_block(symbol, profile_obj, prefer_tiktoken, budget)
        if block is None:
            continue
        text, cost = block
        if total + cost > budget:
            break
        parts.append("---")
        parts.append("")
        parts.append(text)
        total += cost
        included += 1

    text = "\n".join([header, "", *parts]).rstrip() + "\n"
    return OptimizedContext(
        text=text,
        estimated_tokens=_block_tokens(text, prefer_tiktoken),
        max_tokens=float(max_tokens),
        profile=profile_obj.name,
        rank_method=rank_method,
        included_symbols=included,
        total_symbols=total_symbols,
    )
