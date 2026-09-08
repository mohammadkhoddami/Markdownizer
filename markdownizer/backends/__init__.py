"""Output backends for the Project IR."""

from __future__ import annotations

from markdownizer.backends.base import Backend, RenderOptions
from markdownizer.backends.compact import CompactBackend
from markdownizer.backends.json import JSONBackend
from markdownizer.backends.markdown import MarkdownBackend

_BACKENDS: dict[str, type[Backend]] = {
    "markdown": MarkdownBackend,
    "json": JSONBackend,
    "compact": CompactBackend,
}


def get_backend(name: str) -> Backend:
    """Instantiate a backend by name (``markdown``, ``json``, or ``compact``)."""
    try:
        return _BACKENDS[name]()
    except KeyError:
        choices = ", ".join(sorted(_BACKENDS))
        raise ValueError(f"unknown format: {name!r} (expected one of: {choices})") from None


__all__ = ["Backend", "RenderOptions", "get_backend"]
