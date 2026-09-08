"""Tests for the deterministic import graph."""

from __future__ import annotations

from markdownizer.imports import ImportEdge, collect_import_edges


def _module_map() -> dict[str, str]:
    return {
        "pkg": "pkg/__init__.py",
        "pkg.models": "pkg/models.py",
        "pkg.views": "pkg/views.py",
        "pkg.sub": "pkg/sub/__init__.py",
        "pkg.sub.utils": "pkg/sub/utils.py",
        "pkg.helper": "pkg/helper.py",
        "utils": "utils.py",
        "root_mod": "root_mod.py",
    }


def _edges(source: str, from_module: str = "pkg/views.py") -> list[ImportEdge]:
    return collect_import_edges(source, from_module, _module_map())


def test_absolute_import_resolved():
    edges = _edges("import pkg.models\n")
    assert len(edges) == 1
    e = edges[0]
    assert e.imported_module == "pkg.models"
    assert e.resolved is True
    assert e.to_module == "pkg/models.py"
    assert e.external is False
    assert e.level == 0
    assert e.from_module == "pkg/views.py"


def test_absolute_import_external():
    edges = _edges("import os\nimport third_party\n")
    assert len(edges) == 2
    for e in edges:
        assert e.resolved is False
        assert e.to_module is None
        assert e.external is True


def test_import_with_alias():
    edges = _edges("import pkg.models as m\n")
    assert edges[0].alias == "m"
    assert edges[0].resolved is True


def test_from_import_resolved():
    edges = _edges("from pkg import models\n")
    assert edges[0].imported_module == "pkg"
    assert edges[0].to_module == "pkg/__init__.py"
    assert edges[0].resolved is True


def test_from_import_external():
    edges = _edges("from django.db import models\n")
    e = edges[0]
    assert e.resolved is False
    assert e.external is True
    assert e.imported_module == "django.db"


def test_relative_single_dot_module():
    edges = _edges("from . import helper\n")
    e = edges[0]
    assert e.level == 1
    assert e.imported_module == "helper"
    assert e.resolved is True
    assert e.to_module == "pkg/helper.py"


def test_relative_single_dot_submodule():
    edges = _edges("from .sub import utils\n")
    e = edges[0]
    assert e.level == 1
    assert e.to_module == "pkg/sub/__init__.py"
    assert e.resolved is True


def test_relative_double_dot():
    edges = _edges("from ..utils import helper\n", from_module="pkg/sub/mod.py")
    e = edges[0]
    assert e.level == 2
    assert e.resolved is True
    assert e.to_module == "utils.py"


def test_relative_double_dot_package_file():
    edges = _edges("from .. import root_mod\n", from_module="pkg/sub/mod.py")
    e = edges[0]
    assert e.level == 2
    assert e.resolved is True
    assert e.to_module == "root_mod.py"


def test_relative_too_deep_external():
    edges = _edges("from .... import x\n", from_module="pkg/views.py")
    e = edges[0]
    assert e.resolved is False
    assert e.external is True


def test_relative_unresolved_external():
    edges = _edges("from . import missing\n")
    assert edges[0].resolved is False
    assert edges[0].external is True


def test_root_module_relative():
    edges = _edges("from . import root_mod\n", from_module="a.py")
    e = edges[0]
    assert e.level == 1
    assert e.resolved is True
    assert e.to_module == "root_mod.py"


def test_multiple_imports_ordered():
    source = "import pkg.models\nimport os\nimport pkg.views\n"
    edges = _edges(source)
    assert len(edges) == 3
    names = [e.imported_module for e in edges]
    assert names == ["os", "pkg.models", "pkg.views"]
    assert [e.resolved for e in edges] == [False, True, True]


def test_syntax_error_returns_no_edges():
    assert _edges("def broken(\n  x =") == []


def test_import_star():
    edges = _edges("from pkg import *\n")
    assert len(edges) == 1
    assert edges[0].imported_module == "pkg"


def test_dotted_import_resolution_to_init():
    edges = _edges("import pkg\n")
    assert edges[0].to_module == "pkg/__init__.py"


def test_empty_source():
    assert _edges("") == []
