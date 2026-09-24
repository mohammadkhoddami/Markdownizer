"""Context optimizer: deterministic ranking, token budgets, and profiles.

This layer sits between the Project IR and the output backends. It decides
*which* symbols matter (ranking) and *how much* context fits a token budget
(packing), without any AI involvement.
"""

from __future__ import annotations

from markdownizer.optimizer.profiles import DEFAULT_PROFILE, get_profile
from markdownizer.optimizer.rank import compute_file_scores, rank_ir, symbol_importance
from markdownizer.optimizer.slice import OptimizedContext, optimize_context
from markdownizer.optimizer.tokens import count_tokens, tiktoken_available

__all__ = [
    "OptimizedContext",
    "optimize_context",
    "rank_ir",
    "compute_file_scores",
    "symbol_importance",
    "get_profile",
    "count_tokens",
    "tiktoken_available",
    "DEFAULT_PROFILE",
]
