"""Deterministic token estimation for context budgeting.

Uses ``tiktoken`` (cl100k_base) when it is installed, otherwise falls back to
the standard heuristic ``characters / 3.3``. Both estimates are deterministic
for a given text.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 3.3

try:
    import tiktoken as _tiktoken  # type: ignore[import-not-found]

    _ENCODER = _tiktoken.get_encoding("cl100k_base")
    _HAS_TIKTOKEN = True
except (ImportError, OSError):  # pragma: no cover - depends on optional dependency
    _ENCODER = None
    _HAS_TIKTOKEN = False


def count_tokens(text: str, prefer_tiktoken: bool = False) -> float:
    """Estimate the number of tokens in ``text``.

    If ``tiktoken`` is installed and ``prefer_tiktoken`` is true, the
    cl100k_base encoder is used; otherwise ``len(text) / 3.3``.
    """
    if prefer_tiktoken and _HAS_TIKTOKEN and _ENCODER is not None:
        return float(len(_ENCODER.encode(text)))
    return len(text) / _CHARS_PER_TOKEN


def tiktoken_available() -> bool:
    """Whether the optional ``tiktoken`` dependency is installed."""
    return _HAS_TIKTOKEN
