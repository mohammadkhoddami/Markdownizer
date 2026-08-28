"""Tests for the recursive project scanner."""

from __future__ import annotations

from markdownizer.scanner import IGNORED_DIR_NAMES, scan_python_files, should_skip_dir


def test_should_skip_dir_ignores_common_dirs():
    for name in IGNORED_DIR_NAMES:
        assert should_skip_dir(name), name


def test_should_skip_dir_ignores_dot_dirs():
    assert should_skip_dir(".github")
    assert should_skip_dir(".hidden")


def test_should_skip_dir_accepts_normal_dirs():
    assert not should_skip_dir("src")
    assert not should_skip_dir("migrations")


def test_scan_finds_only_python_files(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    (tmp_path / "b.txt").write_text("not python")
    files = list(scan_python_files(tmp_path))
    assert [f.name for f in files] == ["a.py"]


def test_scan_skips_ignored_dirs(tmp_path):
    for name in ("venv", "__pycache__", ".venv", "build", "dist", ".git"):
        d = tmp_path / name
        d.mkdir(parents=True)
        (d / "skip.py").write_text("x = 1")
    (tmp_path / "keep.py").write_text("x = 1")
    files = list(scan_python_files(tmp_path))
    assert [f.name for f in files] == ["keep.py"]


def test_scan_skips_hidden_files_even_at_root(tmp_path):
    (tmp_path / ".hidden.py").write_text("x = 1")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.py").write_text("x = 1")
    d = tmp_path / "normal"
    d.mkdir()
    (d / "ok.py").write_text("x = 1")
    files = sorted(scan_python_files(tmp_path))
    assert files == [d / "ok.py"]


def test_scan_exclude_glob(tmp_path):
    d = tmp_path / "tests"
    d.mkdir()
    (d / "test_x.py").write_text("x = 1")
    d = tmp_path / "migrations"
    d.mkdir()
    (d / "0001.py").write_text("x = 1")
    d = tmp_path / "src"
    d.mkdir()
    (d / "a.py").write_text("x = 1")
    files = list(scan_python_files(tmp_path, exclude=["tests/*", "migrations"]))
    assert [f.relative_to(tmp_path).as_posix() for f in files] == ["src/a.py"]


def test_scan_exclude_deep_glob(tmp_path):
    d = tmp_path / "pkg" / "sub"
    d.mkdir(parents=True)
    (d / "ok.py").write_text("x = 1")
    (d / "skip.py").write_text("x = 1")
    files = list(scan_python_files(tmp_path, exclude=["**/skip.py"]))
    assert [f.name for f in files] == ["ok.py"]


def test_scan_exclude_none_is_noop(tmp_path):
    (tmp_path / "a.py").write_text("x = 1")
    files = list(scan_python_files(tmp_path))
    assert [f.name for f in files] == ["a.py"]


def test_scan_ignores_non_py_extension(tmp_path):
    (tmp_path / "a.pyi").write_text("x: int")
    assert list(scan_python_files(tmp_path)) == []


def test_scan_sorted_order(tmp_path):
    d = tmp_path / "b"
    d.mkdir()
    (d / "z.py").write_text("x = 1")
    d = tmp_path / "a"
    d.mkdir()
    (d / "y.py").write_text("x = 1")
    files = list(scan_python_files(tmp_path))
    assert [f.relative_to(tmp_path).as_posix() for f in files] == [
        "a/y.py",
        "b/z.py",
    ]


def test_scan_missing_root_returns_empty(tmp_path):
    assert list(scan_python_files(tmp_path / "nope")) == []
