"""Tests for the deterministic ranking layer."""

from __future__ import annotations

import pytest

from markdownizer.optimizer import compute_file_scores, rank_ir, symbol_importance


def test_rank_deterministic(sample_project, tmp_path):
    from markdownizer.ir import build_project_ir

    ir1 = build_project_ir(tmp_path)
    ir2 = build_project_ir(tmp_path)
    rank_ir(ir1)
    rank_ir(ir2)
    assert [s.rank for s in ir1.symbols] == [s.rank for s in ir2.symbols]
    assert ir1.file_ranks == ir2.file_ranks


def test_rank_fills_ir_fields(sample_project, tmp_path):
    from markdownizer.ir import build_project_ir

    ir = build_project_ir(tmp_path)
    assert all(s.rank == 0.0 for s in ir.symbols)
    rank_ir(ir)
    assert any(s.rank > 0.0 for s in ir.symbols)
    assert ir.file_ranks
    assert all(0.0 <= v <= 1.0 for v in ir.file_ranks.values())


def test_rank_excluded_from_hash(sample_project, tmp_path):
    from markdownizer.ir import build_project_ir

    ir = build_project_ir(tmp_path)
    before = ir.hash
    rank_ir(ir)
    assert ir.hash == before
    assert ir.compute_hash() == before


def test_rank_does_not_change_json_hash(sample_project, tmp_path):
    """JSON artifacts remain deterministic and hash-stable after ranking."""
    from markdownizer.ir import build_project_ir

    ir = build_project_ir(tmp_path)
    text_before = ir.to_json()
    rank_ir(ir)
    assert ir.to_json() != text_before  # rank is now serialized
    assert ir.compute_hash() == ir.hash


def test_imported_modules_rank_higher(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "core.py", "def core_fn():\n    pass\n")
    write_py(
        tmp_path / "app.py",
        "from core import core_fn\n\n\ndef app_fn():\n    pass\n",
    )
    ir = __import__("markdownizer").build_project_ir(tmp_path)
    rank_ir(ir)
    assert ir.file_ranks["core.py"] > ir.file_ranks["app.py"]


def test_framework_boost_raises_file_score(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "models.py", "class User(models.Model):\n    pass\n")
    write_py(tmp_path / "plain.py", "def f():\n    pass\n")
    ir = __import__("markdownizer").build_project_ir(tmp_path)
    rank_ir(ir)
    assert ir.file_ranks["models.py"] > ir.file_ranks["plain.py"]


def test_entrypoint_boost(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "urls.py", "urlpatterns = []\n")
    write_py(tmp_path / "mod.py", "def f():\n    pass\n")
    ir = __import__("markdownizer").build_project_ir(tmp_path)
    rank_ir(ir)
    assert ir.file_ranks["urls.py"] > ir.file_ranks["mod.py"]


def test_public_and_documented_importance():
    from markdownizer.ir import Symbol

    def make(public: bool, docstring: str | None) -> Symbol:
        return Symbol(
            id="x",
            name="x",
            qualified_name="x",
            kind="function",
            file_path="a.py",
            lineno=1,
            end_lineno=2,
            docstring=docstring,
            is_public=public,
        )

    pub_doc = symbol_importance(1.0, make(True, "doc"))
    pub_plain = symbol_importance(1.0, make(True, None))
    priv_doc = symbol_importance(1.0, make(False, "doc"))
    priv_plain = symbol_importance(1.0, make(False, None))
    assert pub_doc > pub_plain > priv_doc > priv_plain
    assert pub_doc == 1.0 * 1.5 * 1.3


def test_rank_methods(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "a.py", "import b\n\n\ndef fa():\n    pass\n")
    write_py(tmp_path / "b.py", "def fb():\n    pass\n")
    ir = __import__("markdownizer").build_project_ir(tmp_path)

    for method in ("pagerank", "fanout", "simple"):
        scores = compute_file_scores(ir.modules, ir.imports, ir.symbols, method=method)
        assert set(scores) == {"a.py", "b.py"}
        assert all(0.0 <= v <= 1.0 for v in scores.values())


def test_rank_method_unknown():
    with pytest.raises(ValueError):
        compute_file_scores([], [], [], method="magic")


def test_fanout_prefers_imported():
    tmp_path = __import__("tempfile").mkdtemp()
    import pathlib

    root = pathlib.Path(tmp_path)
    (root / "a.py").write_text("import b\n\ndef fa():\n    pass\n")
    (root / "b.py").write_text("def fb():\n    pass\n")
    ir = __import__("markdownizer").build_project_ir(root)
    scores = compute_file_scores(ir.modules, ir.imports, ir.symbols, method="fanout")
    assert scores["b.py"] > scores["a.py"]
