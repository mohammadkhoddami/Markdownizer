"""Tests for the command-line interface."""

from __future__ import annotations

import pytest

import markdownizer
from markdownizer.cli import main


def test_version_flag(capsys):
    _assert_exits_with(["--version"], f"markdownizer {markdownizer.__version__}", capsys)


def test_help_flag(capsys):
    _assert_exits_with(["--help"], "usage: markdownizer", capsys)


def test_missing_project_returns_2(capsys):
    assert main(["/definitely/not/a/real/path"]) == 2


def test_file_as_project_returns_2(tmp_path, capsys):
    f = tmp_path / "a.py"
    f.write_text("x = 1")
    assert main([str(f)]) == 2


def test_success_returns_0(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main([str(tmp_path), "-o", str(out)]) == 0
    captured = capsys.readouterr()
    assert "Wrote 1 file(s)" in captured.out
    assert (out / "_root.md").exists()


def test_quiet_suppresses_output(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main([str(tmp_path), "-o", str(out), "-q"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_exclude_flag(tmp_path, capsys):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("x = 1")
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main([str(tmp_path), "-o", str(out), "--exclude", "tests/*"]) == 0
    assert not (out / "tests.md").exists()


def test_no_source_flag(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    main([str(tmp_path), "-o", str(out), "--no-source"])
    md = (out / "_root.md").read_text(encoding="utf-8")
    assert "## Source Code" not in md


def test_only_documented_flag(tmp_path, capsys):
    (tmp_path / "mod.py").write_text(
        '"""docs"""\n\ndef documented():\n    """yes"""\n    pass\n\n'
        "def undocumented():\n    pass\n"
    )
    out = tmp_path / "out"
    main([str(tmp_path), "-o", str(out), "--only-documented"])
    md = (out / "_root.md").read_text(encoding="utf-8")
    assert "# Function: documented" in md
    assert "# Function: undocumented" not in md


def test_verbose_runs(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main([str(tmp_path), "-o", str(out), "-v"]) == 0


def test_python_m_module_runs(tmp_path):
    import subprocess
    import sys

    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, "-m", "markdownizer", str(tmp_path), "-o", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (out / "_root.md").exists()


def test_python_m_module_exit_code(tmp_path):
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "markdownizer", "/definitely/not/here"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2


def test_build_subcommand_markdown(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main(["build", str(tmp_path), "-o", str(out)]) == 0
    assert (out / "_root.md").exists()


def test_build_subcommand_json(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main(["build", str(tmp_path), "-o", str(out), "--format", "json"]) == 0
    assert (out / "project.json").exists()
    captured = capsys.readouterr()
    assert "Wrote 1 file(s)" in captured.out


def test_build_subcommand_compact(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main(["build", str(tmp_path), "-o", str(out), "--format", "compact"]) == 0
    assert (out / "context.compact.md").exists()


def test_build_invalid_format_exits(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    with pytest.raises(SystemExit) as exc:
        main(["build", str(tmp_path), "--format", "html"])
    assert exc.value.code == 2


def test_build_missing_project_returns_2(capsys):
    assert main(["build", "/definitely/not/here"]) == 2


def test_build_quiet(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main(["build", str(tmp_path), "-o", str(out), "-q"]) == 0
    assert capsys.readouterr().out == ""


def test_build_exclude(tmp_path, capsys):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "t.py").write_text("x = 1")
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main(["build", str(tmp_path), "-o", str(out), "--exclude", "tests/*"]) == 0
    assert not (out / "tests.md").exists()


def _assert_exits_with(argv: list[str], expected: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(argv)
    assert expected in capsys.readouterr().out
