"""Tests for the Project IR: schema, builder, serialization, hashing."""

from __future__ import annotations

import json
from pathlib import Path

from markdownizer.imports import ImportEdge
from markdownizer.ir import (
    IR_VERSION,
    DefinesEdge,
    InheritsEdge,
    build_project_ir,
)


def test_ir_version_constant():
    assert IR_VERSION == 1


def test_build_structure(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    assert ir.name == tmp_path.name
    assert ir.ir_version == IR_VERSION
    assert ir.git is None  # tmp dirs are not git repositories
    assert sorted(p.name for p in ir.packages) == ["pkg", "tests"]
    assert [m.path for m in ir.modules] == [
        "pkg/__init__.py",
        "pkg/models.py",
        "pkg/views.py",
        "root_mod.py",
        "tests/test_models.py",
    ]
    assert ir.stats.package_count == 2
    assert ir.stats.module_count == 5
    assert ir.stats.symbol_count == 5


def test_symbol_fields(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    user = next(s for s in ir.symbols if s.name == "User")
    assert user.kind == "class"
    assert user.qualified_name == "User"
    assert user.file_path == "pkg/models.py"
    assert user.framework == "Django Model"
    assert user.is_public is True
    assert user.docstring == "A documented user model."
    helper = next(s for s in ir.symbols if s.name == "helper")
    assert helper.is_method is False
    assert helper.id == "pkg/views.py::helper"


def test_symbol_parameters_and_annotations(tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "api.py",
        '''
        def fetch(url: str, retries: int = 3) -> dict:
            """Fetch."""
            return {}

        async def run():
            pass
        ''',
    )
    ir = build_project_ir(tmp_path)
    fetch = next(s for s in ir.symbols if s.name == "fetch")
    assert fetch.parameters == "url: str, retries: int=3"
    assert fetch.type_annotation == "dict"
    run = next(s for s in ir.symbols if s.name == "run")
    assert run.is_async is True
    assert run.type_annotation == ""


def test_public_private(tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "mod.py",
        "def public_fn():\n    pass\n\n\ndef _private_fn():\n    pass\n",
    )
    ir = build_project_ir(tmp_path)
    by_name = {s.name: s for s in ir.symbols}
    assert by_name["public_fn"].is_public is True
    assert by_name["_private_fn"].is_public is False


def test_relationships(tmp_path):
    from tests.conftest import write_py

    write_py(
        tmp_path / "pkg" / "__init__.py",
        '"""Pkg."""\n',
    )
    write_py(
        tmp_path / "pkg" / "models.py",
        '''
        """Models."""

        class User(models.Model):
            """A user."""

            def save(self):
                """Save."""
                pass
        ''',
    )
    ir = build_project_ir(tmp_path)
    user = next(s for s in ir.symbols if s.name == "User")
    save = next(s for s in ir.symbols if s.name == "save")
    inherits = [e for e in ir.inherits if e.symbol_id == user.id]
    assert inherits == [InheritsEdge(symbol_id=user.id, base="models.Model")]
    class_defines = {e.child_id for e in ir.defines if e.parent_id == user.id}
    assert class_defines == {save.id}
    module_defines = {e.child_id for e in ir.defines if e.parent_id == "pkg/models.py"}
    assert module_defines == {user.id}


def test_defines_module_edges(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    helper = next(s for s in ir.symbols if s.name == "helper")
    edge = next(e for e in ir.defines if e.child_id == helper.id)
    assert edge.parent_id == helper.file_path


def test_exclude_respected(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "a.py", "def f():\n    pass\n")
    write_py(tmp_path / "tests" / "test_a.py", "def test_f():\n    pass\n")
    ir = build_project_ir(tmp_path, exclude=["tests/*"])
    assert [m.path for m in ir.modules] == ["a.py"]


def test_deterministic_hash_same_root(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "a.py", "def f():\n    pass\n")
    ir1 = build_project_ir(tmp_path)
    ir2 = build_project_ir(tmp_path)
    assert ir1.hash == ir2.hash
    assert ir1.to_json() == ir2.to_json()


def test_deterministic_hash_across_roots(tmp_path):
    """Same content in different directories -> same hash and content dict."""
    from tests.conftest import write_py

    def make(root: Path) -> None:
        write_py(root / "pkg" / "__init__.py", '"""Pkg."""\n')
        write_py(
            root / "pkg" / "models.py",
            '''
            """Models."""

            class User(models.Model):
                """A user."""

                def save(self):
                    pass
            ''',
        )
        write_py(root / "root_mod.py", '"""Root."""\ndef top():\n    pass\n')

    make(tmp_path / "proj_a")
    make(tmp_path / "proj_b")
    ir_a = build_project_ir(tmp_path / "proj_a")
    ir_b = build_project_ir(tmp_path / "proj_b")
    assert ir_a.hash == ir_b.hash
    assert ir_a.content_dict() == ir_b.content_dict()
    assert ir_a.to_dict()["name"] == "proj_a"
    assert ir_b.to_dict()["name"] == "proj_b"


def test_hash_excludes_metadata(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "a.py", "def f():\n    pass\n")
    ir = build_project_ir(tmp_path)
    assert ir.hash == ir.compute_hash()
    assert ir.hash not in ir.content_dict().values()


def test_content_hash_per_module(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    models = next(m for m in ir.modules if m.path == "pkg/models.py")
    assert models.content_hash
    assert models.line_count > 0
    assert models.package == "pkg"
    assert models.symbol_ids == sorted(models.symbol_ids)


def test_json_serialization(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    text = ir.to_json()
    data = json.loads(text)
    assert data["ir_version"] == IR_VERSION
    assert data["hash"] == ir.hash
    assert data["name"] == ir.name
    assert isinstance(data["symbols"], list)
    assert isinstance(data["imports"], list)
    assert isinstance(data["modules"], list)
    assert isinstance(data["packages"], list)
    assert data["git"] is None


def test_json_stable_key_order(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    first = json.loads(ir.to_json())
    second = json.loads(build_project_ir(tmp_path).to_json())
    assert list(first.keys()) == list(second.keys())
    assert first == second


def test_namespace_package(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "ns" / "mod.py", "def f():\n    pass\n")
    ir = build_project_ir(tmp_path)
    ns = next(p for p in ir.packages if p.name == "ns")
    assert ns.is_namespace is True
    assert ns.module_paths == ["ns/mod.py"]


def test_regular_package_not_namespace(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    pkg = next(p for p in ir.packages if p.name == "pkg")
    assert pkg.is_namespace is False
    assert pkg.path == "pkg"


def test_import_edges_present(sample_project, tmp_path):
    ir = build_project_ir(tmp_path)
    assert all(isinstance(e, ImportEdge) for e in ir.imports)
    assert all(isinstance(e, InheritsEdge) for e in ir.inherits)
    assert all(isinstance(e, DefinesEdge) for e in ir.defines)


def test_unsorted_input_still_sorted(tmp_path):
    from tests.conftest import write_py

    write_py(tmp_path / "b" / "z.py", "def z():\n    pass\n")
    write_py(tmp_path / "a" / "y.py", "def y():\n    pass\n")
    ir = build_project_ir(tmp_path)
    assert [m.path for m in ir.modules] == ["a/y.py", "b/z.py"]
    assert [s.qualified_name for s in ir.symbols] == ["y", "z"]
