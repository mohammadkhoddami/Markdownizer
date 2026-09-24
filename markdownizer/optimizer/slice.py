"""Budget-aware context packing.

Turns a ranked ProjectIR into an AI-ready context artifact within a token
budget, using deterministic layered emission:

* layer 0 — project index (packages, modules, docstrings)
* layer 1 — signatures + docstrings for public symbols
* layer 2 — full source for ranked symbols
* layer 3 — remaining symbol docstrings/comments when budget allows

High-ranked symbols are placed at the start and end of the artifact
(primacy/recency bias); lower-ranked content sits in the middle.
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
        max_tokens: Target token budget (soft limit, ±10% slop).
        profile: Profile preset name (see :mod:`markdownizer.optimizer.profiles`).
        query: Optional space-separated keyword prefilter on symbol names,
            frameworks, and docstrings (deterministic substring match).
        rank_method: ``pagerank`` (default), ``fanout``, or ``simple``.
        prefer_tiktoken: Use ``tiktoken`` when installed for token estimates.
    """
    rank_ir(ir, method=rank_method)
    profile_obj = get_profile(profile)
    budget = float(max_tokens) * _BUDGET_SLOP
    parts: list[str] = []
    total: float = 0.0
    included: int = 0
    total_symbols = len(ir.symbols)

    header = (
        f"# Context: {ir.name} "
        f"(profile={profile_obj.name}, rank={rank_method}, "
        f"max_tokens={int(max_tokens)})"
    )

    index = _render_index(ir)
    if _block_tokens(index, prefer_tiktoken) <= budget:
        parts.append(index)
        total += _block_tokens(index, prefer_tiktoken)

    module_index = _render_module_index(ir)
    if _block_tokens(module_index, prefer_tiktoken) <= budget:
        parts.append(module_index)
        total += _block_tokens(module_index, prefer_tiktoken)

    symbols = _select_symbols(ir, profile_obj, query)
    ordered = _edge_place(symbols)

    signatures: list[tuple[Symbol, str, float]] = []
    sources: list[tuple[Symbol, str, float]] = []
    remainder: list[tuple[Symbol, str, float]] = []

    for symbol in ordered:
        if profile_obj.include_source is not False:
            sig_text = render_object(
                symbol,
                None,
                include_source="signature",
                include_comments=profile_obj.include_comments,
            )
            sig_cost = _block_tokens(sig_text, prefer_tiktoken)
            if sig_cost <= budget:
                signatures.append((symbol, sig_text, sig_cost))

        if profile_obj.include_source is True:
            src_text = render_object(
                symbol,
                None,
                include_source=True,
                include_comments=profile_obj.include_comments,
            )
            src_cost = _block_tokens(src_text, prefer_tiktoken)
            sources.append((symbol, src_text, src_cost))

        if profile_obj.include_source is False and symbol.docstring:
            doc_text = render_object(
                symbol,
                None,
                include_source=False,
                include_comments=profile_obj.include_comments,
            )
            doc_cost = _block_tokens(doc_text, prefer_tiktoken)
            remainder.append((symbol, doc_text, doc_cost))

    if profile_obj.include_source is not False:
        for _, sig_text, sig_cost in signatures:
            if total + sig_cost > budget:
                break
            parts.append("---")
            parts.append("")
            parts.append(sig_text)
            total += sig_cost
            included += 1

    if profile_obj.include_source is True:
        for _, src_text, src_cost in sources:
            if total + src_cost > budget:
                break
            parts.append("---")
            parts.append("")
            parts.append(src_text)
            total += src_cost
            included += 1

    if profile_obj.include_source is False:
        for _, doc_text, doc_cost in remainder:
            if total + doc_cost > budget:
                break
            parts.append("---")
            parts.append("")
            parts.append(doc_text)
            total += doc_cost
            included += 1

    text = "\n".join([header, "", *parts]).rstrip() + "\n"
    return OptimizedContext(
        text=text,
        estimated_tokens=total,
        max_tokens=float(max_tokens),
        profile=profile_obj.name,
        rank_method=rank_method,
        included_symbols=included,
        total_symbols=total_symbols,
    )
