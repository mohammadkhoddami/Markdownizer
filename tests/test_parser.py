"""Tests for the AST + tokenize based parser."""

from __future__ import annotations

from pathlib import Path

from markdownizer.parser import DocObject, parse_file


def test_module_docstring(write_file):
    path = write_file("mod.py", '"""Module docstring."""\n\nx = 1\n')
    module, objects = parse_file(str(path))
    assert module.kind == "module"
    assert module.docstring == "Module docstring."
    assert objects == []


def test_module_without_docstring(write_file):
    path = write_file("mod.py", "x = 1\n")
    module, _ = parse_file(str(path))
    assert module.docstring is None


def test_first_string_is_not_docstring(write_file):
    path = write_file("mod.py", 'x = """not a docstring"""\ndef f():\n    pass\n')
    module, objects = parse_file(str(path))
    assert module.docstring is None
    assert [o.name for o in objects] == ["f"]


def test_function_docstring_and_metadata(write_file):
    path = write_file(
        "mod.py",
        '''
        def foo(x: int) -> int:
            """Foo docs."""
            return x
        ''',
    )
    module, objects = parse_file(str(path))
    foo = objects[0]
    assert foo.name == "foo"
    assert foo.kind == "function"
    assert foo.docstring == "Foo docs."
    assert foo.is_async is False
    assert foo.is_method is False
    assert foo.lineno == 1
    assert "def foo" in foo.source


def test_async_function(write_file):
    path = write_file("mod.py", "async def fetch():\n    pass\n")
    _, objects = parse_file(str(path))
    assert objects[0].is_async is True


def test_class_and_methods(write_file):
    path = write_file(
        "mod.py",
        '''
        class Outer:
            """Outer docs."""

            def method(self):
                pass

            async def amethod(self):
                pass
        ''',
    )
    _, objects = parse_file(str(path))
    names = [(o.name, o.kind, o.is_method, o.is_async) for o in objects]
    assert names == [
        ("Outer", "class", False, False),
        ("method", "function", True, False),
        ("amethod", "function", True, True),
    ]
    assert objects[0].qualified_name == "Outer"
    assert objects[1].qualified_name == "Outer.method"


def test_base_classes(write_file):
    path = write_file("mod.py", "class Foo(models.Model, Mixin):\n    pass\n")
    _, objects = parse_file(str(path))
    assert objects[0].base_classes == ["models.Model", "Mixin"]


def test_decorators_preserved(write_file):
    path = write_file(
        "mod.py",
        """
        @decorator
        @with_args(1, key="value")
        def foo():
            pass
        """,
    )
    _, objects = parse_file(str(path))
    assert objects[0].decorators == ["@decorator", '@with_args(1, key="value")']


def test_preceding_comments(write_file):
    path = write_file(
        "mod.py",
        """
        # Comment one.
        # Comment two.

        def foo():
            pass
        """,
    )
    _, objects = parse_file(str(path))
    assert objects[0].preceding_comments == ["# Comment one.", "# Comment two."]


def test_inline_comments(write_file):
    path = write_file(
        "mod.py",
        """
        def foo():
            # inside
            y = 1  # trailing
            return y
        """,
    )
    _, objects = parse_file(str(path))
    assert objects[0].inline_comments == ["# inside", "# trailing"]


def test_class_inline_comments_not_stolen_by_methods(write_file):
    path = write_file(
        "mod.py",
        '''
        class C:
            """Doc."""

            # class level comment
            x = 1  # field comment

            def m(self):
                # method comment
                y = 1  # trailing
        ''',
    )
    _, objects = parse_file(str(path))
    cls = objects[0]
    method = objects[1]
    assert "# class level comment" in cls.inline_comments
    assert "# field comment" in cls.inline_comments
    assert method.inline_comments == ["# method comment", "# trailing"]


def test_signal_assignment(write_file):
    path = write_file(
        "mod.py",
        """
        # A signal doc.
        user_created = Signal()
        """,
    )
    _, objects = parse_file(str(path))
    sig = objects[0]
    assert sig.kind == "signal"
    assert sig.name == "user_created"
    assert sig.preceding_comments == ["# A signal doc."]


def test_urlpatterns_assignment(write_file):
    path = write_file(
        "mod.py",
        """
        urlpatterns = []
        """,
    )
    _, objects = parse_file(str(path))
    assert objects[0].kind == "urlconf"
    assert objects[0].name == "urlpatterns"


def test_plain_assignment_not_extracted(write_file):
    path = write_file("mod.py", "SOME_CONST = 42\n")
    _, objects = parse_file(str(path))
    assert objects == []


def test_module_level_comments_unowned_go_to_module(write_file):
    path = write_file(
        "mod.py",
        """
        # A free floating comment.
        x = 1

        def foo():
            pass
        """,
    )
    module, objects = parse_file(str(path))
    assert "# A free floating comment." in module.inline_comments


def test_syntax_error_falls_back_to_raw_module(write_file):
    path = write_file("mod.py", "def broken(\n    x =")
    module, objects = parse_file(str(path))
    assert module.kind == "module"
    assert module.source == "def broken(\n    x ="
    assert objects == [module]


def test_empty_file(write_file):
    path = write_file("mod.py", "")
    module, objects = parse_file(str(path))
    assert module.docstring is None
    assert objects == []


def test_only_comments_file(write_file):
    path = write_file("mod.py", "# just a comment\n# another\n")
    module, objects = parse_file(str(path))
    assert module.inline_comments == ["# just a comment", "# another"]
    assert objects == []


def test_returns_docobject_instances(write_file):
    path = write_file("mod.py", "def f():\n    pass\n")
    module, objects = parse_file(str(path))
    assert isinstance(module, DocObject)
    assert isinstance(objects[0], DocObject)


def test_file_path_populated(write_file):
    path = write_file("mod.py", "def f():\n    pass\n")
    _, objects = parse_file(str(path))
    assert Path(objects[0].file_path) == path
