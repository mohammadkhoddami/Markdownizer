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


def test_context_command_writes_file(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\ndef documented():\n    """yes"""\n    pass\n')
    out = tmp_path / "out"
    assert main(["context", str(tmp_path), "-o", str(out), "--max-tokens", "2000"]) == 0
    text = (out / "context.md").read_text(encoding="utf-8")
    assert text.startswith("# Context:")
    captured = capsys.readouterr()
    assert "Wrote context.md" in captured.out


def test_context_command_respects_budget(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\ndef documented():\n    """yes"""\n    pass\n')
    out = tmp_path / "out"
    main(["context", str(tmp_path), "-o", str(out), "--max-tokens", "100", "-q"])
    text = (out / "context.md").read_text(encoding="utf-8")
    assert "# Context:" in text


def test_context_command_quiet(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    out = tmp_path / "out"
    assert main(["context", str(tmp_path), "-o", str(out), "-q"]) == 0
    assert capsys.readouterr().out == ""


def test_context_invalid_profile_returns_1(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    assert main(["context", str(tmp_path), "--profile", "nope"]) == 1
    assert "unknown profile" in capsys.readouterr().err


def test_context_missing_project_returns_2():
    assert main(["context", "/definitely/not/here"]) == 2


def test_stats_command(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\ndef f():\n    pass\n')
    assert main(["stats", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "Project:" in captured.out
    assert "Symbols:" in captured.out
    assert "Top files by importance:" in captured.out


def test_stats_json(tmp_path, capsys):
    import json

    (tmp_path / "mod.py").write_text('"""docs"""\ndef f():\n    pass\n')
    assert main(["stats", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stats"]["module_count"] == 1
    assert "top_files" in payload
    assert "top_symbols" in payload


def test_stats_rank_method(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\ndef f():\n    pass\n')
    assert main(["stats", str(tmp_path), "--rank", "simple"]) == 0
    assert "Symbols:" in capsys.readouterr().out


def test_stats_invalid_rank_exits(tmp_path):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    with pytest.raises(SystemExit):
        main(["stats", str(tmp_path), "--rank", "magic"])


def test_stats_empty_project(tmp_path, capsys):
    assert main(["stats", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert "Symbols: 0" in captured.out


def test_context_query_flag(tmp_path, capsys):
    (tmp_path / "auth.py").write_text('"""Auth."""\ndef login():\n    """Login."""\n    pass\n')
    (tmp_path / "other.py").write_text(
        '"""Other."""\ndef unrelated():\n    """Nope."""\n    pass\n'
    )
    out = tmp_path / "out"
    assert main(["context", str(tmp_path), "-o", str(out), "--query", "login"]) == 0
    text = (out / "context.md").read_text(encoding="utf-8")
    assert "login" in text
    assert "unrelated" not in text


def test_context_negative_max_tokens_returns_1(tmp_path, capsys):
    (tmp_path / "mod.py").write_text('"""docs"""\n')
    assert main(["context", str(tmp_path), "--max-tokens", "-10"]) == 1
    assert "max_tokens must be positive" in capsys.readouterr().err


def _assert_exits_with(argv: list[str], expected: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(argv)
    assert expected in capsys.readouterr().out
