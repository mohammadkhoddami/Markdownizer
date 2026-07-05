"""AST + tokenize based documentation extractor for a single Python file."""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class DocObject:
    name: str
    qualified_name: str
    kind: str
    lineno: int
    end_lineno: int
    anchor_lineno: int
    docstring: str | None
    decorators: list[str] = field(default_factory=list)
    source: str = ""
    preceding_comments: list[str] = field(default_factory=list)
    inline_comments: list[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    base_classes: list[str] = field(default_factory=list)
    file_path: str = ""


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _base_name(node.value) + "." + node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    if isinstance(node, ast.Call):
        return _base_name(node.func)
    return ""


def _rightmost_name(name: str) -> str:
    return name.rsplit(".", 1)[-1] if name else ""


def _decorator_source(node: ast.expr, source_lines: list[str]) -> str:
    if isinstance(node, ast.Name):
        return "@" + node.id
    if isinstance(node, ast.Attribute):
        return "@" + _base_name(node)
    if isinstance(node, ast.Call):
        head = _decorator_source(node.func, source_lines)
        try:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            segment = "\n".join(source_lines[start:end])
            at_pos = segment.find("@")
            if at_pos != -1:
                return segment[at_pos:].strip()
        except Exception:
            pass
        return head + "(...)"
    return "@" + _base_name(node)


def _collect_comments(source: str) -> list[tuple[int, str]]:
    """Return (lineno, text) for every comment in the source."""
    comments: list[tuple[int, str]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok_type, tok_string, start, _end, _line in tokens:
            if tok_type == tokenize.COMMENT:
                comments.append((start[0], tok_string))
    except tokenize.TokenError:
        for lineno, line in enumerate(source.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                comments.append((lineno, stripped))
    return comments


def _blank_or_comment(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _preceding_comment_block(
    anchor_lineno: int, source_lines: list[str], all_comment_linenos: set[int]
) -> list[str]:
    """Walk upward from anchor_lineno - 1 collecting consecutive comment/blank lines."""
    collected: list[str] = []
    idx = anchor_lineno - 2
    while idx >= 0:
        line = source_lines[idx]
        if _blank_or_comment(line):
            collected.append(line)
            idx -= 1
        else:
            break
    collected.reverse()
    return [ln for ln in collected if ln.strip().startswith("#")]


def _inline_comments(
    start_lineno: int,
    end_lineno: int,
    all_comments: list[tuple[int, str]],
    owned_linenos: set[int],
) -> list[str]:
    result: list[str] = []
    for lineno, text in all_comments:
        if start_lineno < lineno <= end_lineno and lineno not in owned_linenos:
            result.append(text)
    return result


def _module_docstring(module: ast.Module) -> str | None:
    if not module.body:
        return None
    first = module.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        value = first.value.value
        if isinstance(value, str):
            return value
    return None


def _extract_object(
    node: ast.AST,
    source: str,
    source_lines: list[str],
    all_comments: list[tuple[int, str]],
    comment_linenos: set[int],
    prefix: str,
    file_path: str,
    is_method: bool,
) -> DocObject | None:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return None

    name = node.name
    qualified_name = f"{prefix}.{name}" if prefix else name
    decorators = [_decorator_source(d, source_lines) for d in node.decorator_list]

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        kind = "function"
        base_classes: list[str] = []
    else:
        kind = "class"
        base_classes = [_base_name(b) for b in node.bases]

    anchor_lineno = (
        node.decorator_list[0].lineno if node.decorator_list else node.lineno
    )
    end_lineno = getattr(node, "end_lineno", node.lineno)

    docstring = ast.get_docstring(node, clean=False)

    preceding = _preceding_comment_block(anchor_lineno, source_lines, comment_linenos)
    owned_linenos: set[int] = set()

    children: list[DocObject] = []
    if isinstance(node, ast.ClassDef):
        for child in node.body:
            child_obj = _extract_object(
                child,
                source,
                source_lines,
                all_comments,
                comment_linenos,
                qualified_name,
                file_path,
                is_method=True,
            )
            if child_obj is not None:
                children.append(child_obj)
                owned_linenos.update(
                    range(child_obj.anchor_lineno, child_obj.end_lineno + 1)
                )
                owned_linenos.update(
                    ln
                    for ln, _ in all_comments
                    if child_obj.anchor_lineno - len(child_obj.preceding_comments)
                    <= ln
                    < child_obj.anchor_lineno
                )

    inline = _inline_comments(node.lineno, end_lineno, all_comments, owned_linenos)

    try:
        obj_source = ast.get_source_segment(source, node) or ""
    except Exception:
        obj_source = ""
    if not obj_source:
        start = node.lineno - 1
        obj_source = "\n".join(source_lines[start:end_lineno])

    obj = DocObject(
        name=name,
        qualified_name=qualified_name,
        kind=kind,
        lineno=node.lineno,
        end_lineno=end_lineno,
        anchor_lineno=anchor_lineno,
        docstring=docstring,
        decorators=decorators,
        source=obj_source,
        preceding_comments=preceding,
        inline_comments=inline,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        is_method=is_method,
        base_classes=base_classes,
        file_path=file_path,
    )
    obj._children = children  # type: ignore[attr-defined]
    return obj


def _extract_module_level_assignment(
    node: ast.stmt,
    source: str,
    source_lines: list[str],
    all_comments: list[tuple[int, str]],
    comment_linenos: set[int],
    file_path: str,
) -> DocObject | None:
    """Detect module-level signal instantiations and urlpatterns."""
    if not isinstance(node, ast.Assign):
        return None

    value = node.value
    target_names: list[str] = []
    for target in node.targets:
        if isinstance(target, ast.Name):
            target_names.append(target.id)

    kind: str | None = None
    name: str | None = None

    if "urlpatterns" in target_names:
        kind = "urlconf"
        name = "urlpatterns"
    elif isinstance(value, ast.Call):
        func_name = _rightmost_name(_base_name(value.func))
        if func_name == "Signal":
            kind = "signal"
            name = target_names[0] if target_names else "signal"

    if kind is None or name is None:
        return None

    anchor_lineno = node.lineno
    end_lineno = getattr(node, "end_lineno", node.lineno)
    preceding = _preceding_comment_block(anchor_lineno, source_lines, comment_linenos)
    inline = _inline_comments(node.lineno, end_lineno, all_comments, set())

    try:
        obj_source = ast.get_source_segment(source, node) or ""
    except Exception:
        obj_source = ""
    if not obj_source:
        obj_source = "\n".join(source_lines[node.lineno - 1 : end_lineno])

    return DocObject(
        name=name,
        qualified_name=name,
        kind=kind,
        lineno=node.lineno,
        end_lineno=end_lineno,
        anchor_lineno=anchor_lineno,
        docstring=None,
        decorators=[],
        source=obj_source,
        preceding_comments=preceding,
        inline_comments=inline,
        file_path=file_path,
    )


def parse_file(file_path: str) -> tuple[DocObject, list[DocObject]]:
    """Parse a Python file and return (module_object, flat_list_of_all_objects)."""
    with open(file_path, "r", encoding="utf-8") as fh:
        source = fh.read()

    source_lines = source.splitlines()
    all_comments = _collect_comments(source)
    comment_linenos = {ln for ln, _ in all_comments}

    try:
        module = ast.parse(source, filename=file_path)
    except SyntaxError:
        module_obj = DocObject(
            name=file_path,
            qualified_name=file_path,
            kind="module",
            lineno=1,
            end_lineno=len(source_lines),
            anchor_lineno=1,
            docstring=None,
            source=source,
            file_path=file_path,
        )
        return module_obj, [module_obj]

    module_docstring = _module_docstring(module)
    module_end = len(source_lines) or 1

    owned_linenos: set[int] = set()
    objects: list[DocObject] = []

    for top in module.body:
        obj = _extract_object(
            top, source, source_lines, all_comments, comment_linenos, "", file_path, False
        )
        if obj is not None:
            objects.append(obj)
            children = getattr(obj, "_children", [])
            objects.extend(children)
            owned_linenos.update(range(obj.anchor_lineno, obj.end_lineno + 1))
            for ln, _ in all_comments:
                if obj.anchor_lineno - len(obj.preceding_comments) <= ln < obj.anchor_lineno:
                    owned_linenos.add(ln)
            for child in children:
                owned_linenos.update(
                    range(child.anchor_lineno, child.end_lineno + 1)
                )
                for ln, _ in all_comments:
                    if (
                        child.anchor_lineno - len(child.preceding_comments)
                        <= ln
                        < child.anchor_lineno
                    ):
                        owned_linenos.add(ln)
            continue

        assign_obj = _extract_module_level_assignment(
            top, source, source_lines, all_comments, comment_linenos, file_path
        )
        if assign_obj is not None:
            objects.append(assign_obj)
            owned_linenos.update(range(assign_obj.anchor_lineno, assign_obj.end_lineno + 1))
            for ln, _ in all_comments:
                if (
                    assign_obj.anchor_lineno - len(assign_obj.preceding_comments)
                    <= ln
                    < assign_obj.anchor_lineno
                ):
                    owned_linenos.add(ln)

    module_inline = [
        text for ln, text in all_comments if ln not in owned_linenos
    ]

    module_obj = DocObject(
        name=file_path,
        qualified_name=file_path,
        kind="module",
        lineno=1,
        end_lineno=module_end,
        anchor_lineno=1,
        docstring=module_docstring,
        source=source,
        preceding_comments=[],
        inline_comments=module_inline,
        file_path=file_path,
    )

    for obj in objects:
        if hasattr(obj, "_children"):
            delattr(obj, "_children")

    return module_obj, objects