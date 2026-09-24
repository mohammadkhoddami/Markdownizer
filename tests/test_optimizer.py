"""Tests for budget-aware context packing."""

from __future__ import annotations

from pathlib import Path

import pytest

from markdownizer import ProjectIR
from markdownizer.optimizer import get_profile, optimize_context
from markdownizer.optimizer.tokens import count_tokens


def _build(tmp_path: Path) -> ProjectIR:
    from tests.conftest import write_py

    write_py(tmp_path / "pkg" / "__init__.py", '"""Pkg."""\n')
    write_py(
        tmp_path / "pkg" / "models.py",
        '''
        """Models."""

        class User(models.Model):
            """A user."""

            def save(self):
                """Save the user."""
                pass
        ''',
    )
    write_py(
        tmp_path / "pkg" / "views.py",
        '''
        """Views."""

        from .models import User

        class UserViewSet(viewsets.ModelViewSet):
            """A viewset."""

            pass

        def helper():
            pass
        ''',
    )
    write_py(tmp_path / "root_mod.py", '"""Root."""\ndef top():\n    """Top."""\n    pass\n')
    from markdownizer.ir import build_project_ir

    return build_project_ir(tmp_path)


def test_context_within_budget(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=500)
    assert ctx.estimated_tokens <= 500 * 1.1
    assert ctx.text.startswith("# Context:")


def test_context_deterministic(tmp_path):
    ir1 = _build(tmp_path)
    ir2 = _build(tmp_path)
    a = optimize_context(ir1, max_tokens=5000).text
    b = optimize_context(ir2, max_tokens=5000).text
    assert a == b


def test_context_ranks_ir_in_place(tmp_path):
    ir = _build(tmp_path)
    assert all(s.rank == 0.0 for s in ir.symbols)
    optimize_context(ir, max_tokens=5000)
    assert any(s.rank > 0.0 for s in ir.symbols)


def test_profile_api_public_only(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=5000, profile="api")
    assert "# Django Model: User" in ctx.text
    assert "# Function: helper" not in ctx.text  # undocumented
    assert "## Source Code" not in ctx.text
    assert "## Signature" in ctx.text


def test_profile_debugging_includes_source(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=5000, profile="debugging")
    assert "## Source Code" in ctx.text


def test_profile_onboarding_docstrings_only(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=5000, profile="onboarding")
    assert "## Source Code" not in ctx.text
    assert "## Signature" not in ctx.text
    assert "A user." in ctx.text


def test_public_api_subset_invariant(tmp_path):
    """Every public, documented symbol appears in a large api-profile context."""
    from markdownizer.classifier import classify

    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=10000, profile="api")
    public_documented = [s for s in ir.symbols if s.is_public and s.docstring not in (None, "")]
    for symbol in public_documented:
        header = f"# {classify(symbol)}: {symbol.name}"
        assert header in ctx.text, f"missing public symbol: {header}"


def test_unknown_profile_raises(tmp_path):
    ir = _build(tmp_path)
    with pytest.raises(ValueError):
        optimize_context(ir, max_tokens=100, profile="nope")


def test_unknown_rank_method_raises(tmp_path):
    ir = _build(tmp_path)
    with pytest.raises(ValueError):
        optimize_context(ir, max_tokens=100, rank_method="magic")


def test_query_prefilter(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=5000, profile="api", query="User")
    assert "User" in ctx.text
    assert "# Function: top" not in ctx.text


def test_query_requires_all_terms(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=5000, profile="api", query="User nonexistentword")
    assert "Django Model: User" not in ctx.text


def test_edge_placement_highest_rank_first(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=10000, profile="api")
    ranked = sorted(ir.symbols, key=lambda s: -s.rank)
    top_symbol = ranked[0]
    assert top_symbol.qualified_name in ctx.text.split("# Context:")[1]


def test_estimated_tokens_positive(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=1000)
    assert ctx.estimated_tokens > 0
    assert ctx.profile == "architecture"
    assert ctx.rank_method == "pagerank"


def test_get_profile_default_and_presets():
    assert get_profile(None).name == "architecture"
    assert get_profile("django").name == "django"
    with pytest.raises(ValueError):
        get_profile("missing")


def test_count_tokens_fallback():
    text = "x" * 330
    assert count_tokens(text) == pytest.approx(100.0)
    assert count_tokens(text, prefer_tiktoken=True) > 0


def test_tiny_budget_only_header(tmp_path):
    ir = _build(tmp_path)
    ctx = optimize_context(ir, max_tokens=1)
    assert ctx.included_symbols == 0
    assert ctx.text.startswith("# Context:")
