"""Deterministic context profiles.

A profile maps to a set of rendering/budgeting options; each profile is a
deterministic preset that selects what to include and how to rank.
"""

from __future__ import annotations

from dataclasses import dataclass

from markdownizer.renderer import SourceMode


@dataclass(frozen=True)
class Profile:
    """A deterministic preset for context generation."""

    name: str
    include_source: SourceMode
    include_comments: bool
    include_undocumented: bool
    public_only: bool = False
    description: str = ""


PROFILES: dict[str, Profile] = {
    "architecture": Profile(
        name="architecture",
        include_source="signature",
        include_comments=True,
        include_undocumented=False,
        description="Signatures + docstrings; best structural overview.",
    ),
    "api": Profile(
        name="api",
        include_source="signature",
        include_comments=False,
        include_undocumented=False,
        public_only=True,
        description="Public API surface only (signatures, no comments).",
    ),
    "debugging": Profile(
        name="debugging",
        include_source=True,
        include_comments=True,
        include_undocumented=True,
        description="Full source for the highest-ranked symbols.",
    ),
    "refactor": Profile(
        name="refactor",
        include_source="signature",
        include_comments=True,
        include_undocumented=True,
        description="Signatures, inheritance, and comments for all symbols.",
    ),
    "django": Profile(
        name="django",
        include_source="signature",
        include_comments=True,
        include_undocumented=True,
        description="Django/DRF-aware signatures with comments.",
    ),
    "onboarding": Profile(
        name="onboarding",
        include_source=False,
        include_comments=True,
        include_undocumented=False,
        description="Package/module overviews and docstrings only.",
    ),
}

DEFAULT_PROFILE = "architecture"


def get_profile(name: str | None) -> Profile:
    """Return a profile by name, or the default profile when ``name`` is None."""
    if name is None:
        return PROFILES[DEFAULT_PROFILE]
    try:
        return PROFILES[name]
    except KeyError:
        choices = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile: {name!r} (expected one of: {choices})") from None
