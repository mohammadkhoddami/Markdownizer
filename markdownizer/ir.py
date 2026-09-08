"""Project Intermediate Representation (IR).

The IR is the deterministic internal contract between parsing/analysis and
the output backends. It is:

* versioned (``IR_VERSION``, independent of the package version)
* serializable to JSON
* hashable: the same repository state always produces the same hash
* conservative: every piece of information originates from static analysis
  of the repository; nothing is invented.

Paths stored in the IR are POSIX-style paths relative to the project root.
The machine-specific fields (``root``, ``python_version``, ``git``) are
informational only and are excluded from the deterministic hash.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from markdownizer.classifier import classify
from markdownizer.imports import ImportEdge, collect_import_edges
from markdownizer.parser import DocObject, parse_file
from markdownizer.scanner import scan_python_files

IR_VERSION = 1


@dataclass
class Symbol:
    """A documented object (class, function, signal, urlconf) in the project."""

    id: str
    name: str
    qualified_name: str
    kind: str
    file_path: str
    lineno: int
    end_lineno: int
    docstring: str | None
    decorators: list[str] = field(default_factory=list)
    source: str = ""
    preceding_comments: list[str] = field(default_factory=list)
    inline_comments: list[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    base_classes: list[str] = field(default_factory=list)
    parameters: str = ""
    type_annotation: str = ""
    is_public: bool = True
    framework: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "qualified_name": self.qualified_name,
            "kind": self.kind,
            "file_path": self.file_path,
            "lineno": self.lineno,
            "end_lineno": self.end_lineno,
            "docstring": self.docstring,
            "decorators": list(self.decorators),
            "source": self.source,
            "preceding_comments": list(self.preceding_comments),
            "inline_comments": list(self.inline_comments),
            "is_async": self.is_async,
            "is_method": self.is_method,
            "base_classes": list(self.base_classes),
            "parameters": self.parameters,
            "type_annotation": self.type_annotation,
            "is_public": self.is_public,
            "framework": self.framework,
        }


@dataclass
class InheritsEdge:
    """A class inheriting from a base class (base stored as written)."""

    symbol_id: str
    base: str

    def to_dict(self) -> dict[str, Any]:
        return {"symbol_id": self.symbol_id, "base": self.base}


@dataclass
class DefinesEdge:
    """A module defining a symbol, or a class defining a method."""

    parent_id: str
    child_id: str

    def to_dict(self) -> dict[str, Any]:
        return {"parent_id": self.parent_id, "child_id": self.child_id}


@dataclass
class GitInfo:
    commit: str | None
    branch: str | None
    dirty: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "commit": self.commit,
            "branch": self.branch,
            "dirty": self.dirty,
        }


@dataclass
class ModuleInfo:
    path: str
    name: str
    package: str
    docstring: str | None
    inline_comments: list[str] = field(default_factory=list)
    source: str = ""
    line_count: int = 0
    content_hash: str = ""
    symbol_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "package": self.package,
            "docstring": self.docstring,
            "inline_comments": list(self.inline_comments),
            "source": self.source,
            "line_count": self.line_count,
            "content_hash": self.content_hash,
            "symbol_ids": list(self.symbol_ids),
        }


@dataclass
class PackageInfo:
    name: str
    path: str
    is_namespace: bool
    module_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "is_namespace": self.is_namespace,
            "module_paths": list(self.module_paths),
        }


@dataclass
class ProjectStats:
    package_count: int
    module_count: int
    symbol_count: int
    function_count: int
    class_count: int
    documented_count: int
    public_count: int
    line_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_count": self.package_count,
            "module_count": self.module_count,
            "symbol_count": self.symbol_count,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "documented_count": self.documented_count,
            "public_count": self.public_count,
            "line_count": self.line_count,
        }


@dataclass
class ProjectIR:
    name: str
    root: str
    ir_version: int
    python_version: str
    git: GitInfo | None
    hash: str
    stats: ProjectStats
    packages: list[PackageInfo] = field(default_factory=list)
    modules: list[ModuleInfo] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[ImportEdge] = field(default_factory=list)
    inherits: list[InheritsEdge] = field(default_factory=list)
    defines: list[DefinesEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Full serialization including informational metadata."""
        return {
            "name": self.name,
            "root": self.root,
            "ir_version": self.ir_version,
            "python_version": self.python_version,
            "git": self.git.to_dict() if self.git else None,
            "hash": self.hash,
            "stats": self.stats.to_dict(),
            "packages": [p.to_dict() for p in self.packages],
            "modules": [m.to_dict() for m in self.modules],
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": [e.to_dict() for e in self.imports],
            "inherits": [e.to_dict() for e in self.inherits],
            "defines": [e.to_dict() for e in self.defines],
        }

    def to_json(self) -> str:
        """Deterministic JSON serialization (stable key and list ordering)."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    def content_dict(self) -> dict[str, Any]:
        """The canonical, hashable portion of the IR.

        Excludes machine-specific metadata (``name``, ``root``,
        ``python_version``, ``git``) and the hash itself, so the same
        repository content always yields the same hash regardless of where
        the checkout lives or what the directory is called.
        """
        return {
            "ir_version": self.ir_version,
            "stats": self.stats.to_dict(),
            "packages": [p.to_dict() for p in self.packages],
            "modules": [m.to_dict() for m in self.modules],
            "symbols": [s.to_dict() for s in self.symbols],
            "imports": [e.to_dict() for e in self.imports],
            "inherits": [e.to_dict() for e in self.inherits],
            "defines": [e.to_dict() for e in self.defines],
        }

    def compute_hash(self) -> str:
        """Deterministic blake2b hash of the canonical IR content.

        The same repository state always produces the same hash.
        """
        material = json.dumps(
            self.content_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.blake2b(material.encode("utf-8")).hexdigest()


def _module_dotted_name(rel_path: str) -> str:
    if rel_path.endswith("__init__.py"):
        dotted = rel_path[: -len("/__init__.py")]
        return dotted.replace("/", ".")
    return rel_path[:-3].replace("/", ".")


def _symbol_from_docobject(obj: DocObject, rel_path: str) -> Symbol:
    return Symbol(
        id=f"{rel_path}::{obj.qualified_name}",
        name=obj.name,
        qualified_name=obj.qualified_name,
        kind=obj.kind,
        file_path=rel_path,
        lineno=obj.lineno,
        end_lineno=obj.end_lineno,
        docstring=obj.docstring,
        decorators=list(obj.decorators),
        source=obj.source,
        preceding_comments=list(obj.preceding_comments),
        inline_comments=list(obj.inline_comments),
        is_async=obj.is_async,
        is_method=obj.is_method,
        base_classes=list(obj.base_classes),
        parameters=obj.parameters,
        type_annotation=obj.type_annotation,
        is_public=not obj.name.startswith("_"),
        framework=classify(obj),
    )


def _git_info(root: Path) -> GitInfo | None:
    def _run(args: list[str]) -> str | None:
        try:
            result = subprocess.run(
                args,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=2,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None

    commit = _run(["git", "rev-parse", "HEAD"])
    branch = _run(["git", "branch", "--show-current"])
    if commit is None and branch is None:
        return None
    dirty = _run(["git", "status", "--porcelain"]) is not None
    return GitInfo(commit=commit, branch=branch, dirty=dirty)


def build_project_ir(project_root: Path, exclude: list[str] | None = None) -> ProjectIR:
    """Scan, parse, classify, and analyze a project into a deterministic ProjectIR.

    The analysis is fully static: project code is never imported or executed.
    """
    project_root = project_root.resolve()
    files = sorted(scan_python_files(project_root, exclude=exclude))

    module_map: dict[str, str] = {}
    for py_file in files:
        rel = py_file.relative_to(project_root).as_posix()
        module_map[_module_dotted_name(rel)] = rel

    modules: list[ModuleInfo] = []
    symbols: list[Symbol] = []
    imports: list[ImportEdge] = []

    for py_file in files:
        rel = py_file.relative_to(project_root).as_posix()
        dotted = _module_dotted_name(rel)
        source = py_file.read_text(encoding="utf-8")
        module_obj, objects = parse_file(str(py_file), source=source)

        module_symbols = [_symbol_from_docobject(o, rel) for o in objects]
        symbols.extend(module_symbols)

        symbol_ids = sorted(s.id for s in module_symbols)
        modules.append(
            ModuleInfo(
                path=rel,
                name=dotted,
                package=rel.rsplit("/", 1)[0] if "/" in rel else "",
                docstring=module_obj.docstring,
                inline_comments=list(module_obj.inline_comments),
                source=module_obj.source,
                line_count=len(source.splitlines()),
                content_hash=hashlib.blake2b(source.encode("utf-8")).hexdigest(),
                symbol_ids=symbol_ids,
            )
        )

        imports.extend(collect_import_edges(source, rel, module_map))

    symbols.sort(key=lambda s: (s.file_path, s.lineno, s.qualified_name))
    imports.sort(key=lambda e: (e.from_module, e.imported_module, e.level, e.alias or ""))

    class_ids = {s.id for s in symbols if s.kind == "class"}

    inherits: list[InheritsEdge] = []
    defines: list[DefinesEdge] = []
    for sym in symbols:
        if sym.base_classes:
            for base in sym.base_classes:
                inherits.append(InheritsEdge(symbol_id=sym.id, base=base))
        parent: str | None = None
        if sym.is_method:
            parent_qname = sym.qualified_name.rsplit(".", 1)[0]
            parent_id = f"{sym.file_path}::{parent_qname}"
            if parent_id in class_ids:
                parent = parent_id
        if parent is None:
            parent = sym.file_path
        defines.append(DefinesEdge(parent_id=parent, child_id=sym.id))

    inherits.sort(key=lambda e: (e.symbol_id, e.base))
    defines.sort(key=lambda e: (e.parent_id, e.child_id))

    package_by_path: dict[str, PackageInfo] = {}
    for module in modules:
        if not module.package:
            continue
        pkg = package_by_path.get(module.package)
        if pkg is None:
            pkg_path = module.package.replace(".", "/")
            is_namespace = not (project_root / pkg_path / "__init__.py").is_file()
            pkg = PackageInfo(name=module.package, path=pkg_path, is_namespace=is_namespace)
            package_by_path[module.package] = pkg
        pkg.module_paths.append(module.path)
    packages = sorted(package_by_path.values(), key=lambda p: p.name)
    for pkg in packages:
        pkg.module_paths.sort()

    function_count = sum(1 for s in symbols if s.kind == "function")
    class_count = sum(1 for s in symbols if s.kind == "class")
    documented_count = sum(1 for s in symbols if s.docstring not in (None, ""))
    public_count = sum(1 for s in symbols if s.is_public)
    line_count = sum(m.line_count for m in modules)

    stats = ProjectStats(
        package_count=len(packages),
        module_count=len(modules),
        symbol_count=len(symbols),
        function_count=function_count,
        class_count=class_count,
        documented_count=documented_count,
        public_count=public_count,
        line_count=line_count,
    )

    ir = ProjectIR(
        name=project_root.name,
        root=str(project_root),
        ir_version=IR_VERSION,
        python_version=platform.python_version(),
        git=_git_info(project_root),
        hash="",
        stats=stats,
        packages=packages,
        modules=modules,
        symbols=symbols,
        imports=imports,
        inherits=inherits,
        defines=defines,
    )
    ir.hash = ir.compute_hash()
    return ir
